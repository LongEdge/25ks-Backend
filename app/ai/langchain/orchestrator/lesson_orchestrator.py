# -*- coding: utf-8 -*-
"""
教案生成 Orchestrator

职责：
1. 按 pipeline 逐章节生成教案内容
2. 管理 Redis 任务状态
3. 生成完成后落库 MySQL
"""
import json
import traceback
from typing import Dict, Any, Optional, List

from langchain_community.chat_models import ChatZhipuAI

from app.ai.langchain.schema.lesson import LessonContext, LessonTemplate, LessonClarifySchema
from app.ai.langchain.templates import GENERATION_PIPELINE, SECTION_TITLES, get_default_template
from app.ai.langchain.prompts.LESSON import get_section_prompt
from app.core.config import settings
from app.core.redis_util import (
    get_lesson_task,
    update_lesson_task,
    update_partial_lesson,
    mark_task_completed,
    mark_task_failed,
    extend_task_ttl
)
from app.service.lesson_context import (
    format_student_profile_for_prompt,
    format_partial_lesson_for_prompt
)


class LessonOrchestrator:
    """
    教案生成编排器
    
    负责按 pipeline 顺序逐章节调用 LLM 生成教案内容
    """
    
    def __init__(
        self,
        task_id: str,
        context: LessonContext,
        template: Optional[LessonTemplate] = None,
        teacher_id: Optional[int] = None
    ):
        """
        初始化 Orchestrator
        
        Args:
            task_id: Redis 任务 ID
            context: 教案生成上下文
            template: 教案模板（默认使用标准模板）
            teacher_id: 教师 ID（用于落库）
        """
        self.task_id = task_id
        self.context = context
        self.template = template or get_default_template()
        self.teacher_id = teacher_id
        
        # 初始化 LLM
        self.llm = ChatZhipuAI(
            model="glm-4-flashx-250414",
            temperature=0.3,
            zhipuai_api_key=settings.AI_API_KEY
        )
        
        # 获取 pipeline
        self.pipeline = GENERATION_PIPELINE
    
    async def run_pipeline(self) -> None:
        """
        执行生成 pipeline
        
        按顺序生成每个章节，更新 Redis 状态，最后落库
        """
        try:
            total_stages = len(self.pipeline)
            
            for i, stage in enumerate(self.pipeline):
                # 检查任务状态
                task = get_lesson_task(self.task_id)
                if not task:
                    raise Exception("Task not found in Redis")
                
                if task.get("status") == "failed":
                    return  # 任务已失败，停止执行
                
                # 检查是否被锁定
                locked_sections = task.get("locked_sections", [])
                if stage in locked_sections:
                    # 跳过锁定的章节
                    continue
                
                # 更新当前阶段和进度
                progress = (i + 1) / total_stages
                update_lesson_task(
                    self.task_id,
                    current_stage=stage,
                    progress=progress * 0.9  # 最后 10% 留给落库
                )
                
                # 延长 TTL（防止长时间生成导致过期）
                if i % 3 == 0:
                    extend_task_ttl(self.task_id, 3600)
                
                # 获取当前已生成的内容
                partial_lesson = task.get("partial_lesson", {})
                
                # 生成该章节
                content = await self._generate_section(stage, partial_lesson)
                
                # 写回 Redis
                update_partial_lesson(self.task_id, stage, content)
            
            # 所有章节生成完成，落库
            lesson_id = await self._save_to_mysql()
            
            # 更新任务状态为完成
            mark_task_completed(self.task_id, lesson_id)
            
        except Exception as e:
            error_msg = f"生成失败: {str(e)}\n{traceback.format_exc()}"
            mark_task_failed(self.task_id, error_msg)
            raise
    
    async def _generate_section(self, stage: str, partial_lesson: Dict[str, Any]) -> str:
        """
        生成单个章节
        
        Args:
            stage: 章节 key（如 "objectives", "teaching_flow.introduction"）
            partial_lesson: 当前已生成的内容
            
        Returns:
            生成的章节内容（Markdown 格式）
        """
        # 获取该章节的 Prompt
        prompt_template = get_section_prompt(stage)
        
        # 准备 Prompt 变量
        clarify = self.context.clarify
        
        prompt_vars = {
            "subject": clarify.subject or "未知学科",
            "grade": clarify.grade or "未知年级",
            "lesson_title": clarify.lesson_title or "未知课题",
            "lesson_type": clarify.lesson_type or "新授课",
            "lesson_count": clarify.lesson_count or 1,
            "class_duration": clarify.class_duration or 45,
            "section_title": SECTION_TITLES.get(stage, stage),
            "student_profile": format_student_profile_for_prompt(self.context.student_profile),
            "partial_lesson": format_partial_lesson_for_prompt(partial_lesson)
        }
        
        # 格式化 Prompt
        messages = prompt_template.format_messages(**prompt_vars)
        
        # 调用 LLM
        response = self.llm.invoke(messages)
        
        return response.content
    
    async def _save_to_mysql(self) -> int:
        """
        将生成的教案保存到 MySQL
        
        Returns:
            新创建的教案 ID
        """
        # 获取最终的 partial_lesson
        task = get_lesson_task(self.task_id)
        if not task:
            raise Exception("Task not found when saving to MySQL")
        
        partial_lesson = task.get("partial_lesson", {})
        clarify_data = task.get("clarify_data", {})
        
        # 导入数据库相关模块（延迟导入避免循环依赖）
        from app.core.database import SessionLocal
        from app.models.lesson_model import LessonModel
        
        db = SessionLocal()
        try:
            # 创建教案记录
            lesson = LessonModel(
                teacher_id=self.teacher_id or task.get("teacher_id"),
                template_id=self.template.template_id,
                subject=clarify_data.get("subject"),
                grade=clarify_data.get("grade"),
                lesson_title=clarify_data.get("lesson_title"),
                lesson_type=clarify_data.get("lesson_type"),
                content=partial_lesson,
                generation_status="completed",
                locked_sections=task.get("locked_sections", [])
            )
            
            db.add(lesson)
            db.commit()
            db.refresh(lesson)
            
            return lesson.id
            
        finally:
            db.close()
    
    def run_pipeline_sync(self) -> None:
        """
        同步版本的 pipeline 执行（用于非异步环境）
        """
        import asyncio
        
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            # 如果已经在异步上下文中，创建新任务
            asyncio.create_task(self.run_pipeline())
        else:
            # 否则直接运行
            loop.run_until_complete(self.run_pipeline())


def create_orchestrator(
    task_id: str,
    clarify: LessonClarifySchema,
    teacher_id: int,
    template_id: Optional[str] = None,
    student_profile: Optional[Dict[str, Any]] = None
) -> LessonOrchestrator:
    """
    工厂函数：创建 Orchestrator 实例
    
    Args:
        task_id: 任务 ID
        clarify: 澄清数据
        teacher_id: 教师 ID
        template_id: 模板 ID（可选）
        student_profile: 学情数据（可选）
        
    Returns:
        LessonOrchestrator 实例
    """
    from app.ai.langchain.templates import get_template
    
    # 获取模板
    template = None
    if template_id:
        template = get_template(template_id)
    if not template:
        template = get_default_template()
    
    # 构建上下文
    context = LessonContext(
        clarify=clarify,
        student_profile=student_profile
    )
    
    return LessonOrchestrator(
        task_id=task_id,
        context=context,
        template=template,
        teacher_id=teacher_id
    )
