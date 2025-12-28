# -*- coding: utf-8 -*-
"""
教案上下文聚合服务

职责：
1. 整合澄清数据和学情信息
2. 构建 LessonContext 用于生成
"""
from typing import Optional, Dict, Any

from sqlalchemy.orm import Session

from app.ai.langchain.schema.lesson import LessonContext, LessonClarifySchema
from app.service.learning_profile import build_learning_profiles_set


def build_lesson_context(
    db: Session,
    teacher_id: int,
    clarify: LessonClarifySchema,
    include_student_profile: bool = True
) -> LessonContext:
    """
    构建教案生成上下文
    
    Args:
        db: 数据库会话
        teacher_id: 教师 ID
        clarify: 澄清阶段收集的数据
        include_student_profile: 是否包含学情信息
        
    Returns:
        LessonContext 实例
    """
    student_profile = None
    
    if include_student_profile:
        try:
            # 获取教师的学情档案
            profile_set = build_learning_profiles_set(db, teacher_id)
            if profile_set and profile_set.lps:
                # 根据学科和年级过滤相关学情
                relevant_profiles = _filter_relevant_profiles(
                    profile_set.model_dump(),
                    clarify.subject,
                    clarify.grade
                )
                student_profile = relevant_profiles
        except Exception as e:
            # 学情获取失败不影响主流程
            print(f"Warning: Failed to get student profile: {e}")
    
    return LessonContext(
        clarify=clarify,
        student_profile=student_profile,
        rag_context=None,  # 未来扩展
        kg_context=None    # 未来扩展
    )


def _filter_relevant_profiles(
    profiles_data: Dict[str, Any],
    subject: Optional[str],
    grade: Optional[str]
) -> Dict[str, Any]:
    """
    根据学科和年级过滤相关的学情档案
    """
    if not profiles_data or "lps" not in profiles_data:
        return profiles_data
    
    lps = profiles_data.get("lps", [])
    
    if not subject and not grade:
        return profiles_data
    
    # 过滤匹配的学情档案
    filtered = []
    for lp in lps:
        scope = lp.get("scope", {})
        lp_subject = scope.get("subject", "")
        lp_grade = scope.get("grade", "")
        
        # 宽松匹配：只要有一个匹配就保留
        subject_match = not subject or subject in lp_subject or lp_subject in subject
        grade_match = not grade or grade in lp_grade or lp_grade in grade
        
        if subject_match or grade_match:
            filtered.append(lp)
    
    return {
        "teacher_id": profiles_data.get("teacher_id"),
        "lps": filtered if filtered else lps[:3]  # 如果没有匹配的，返回前3个
    }


def format_student_profile_for_prompt(student_profile: Optional[Dict[str, Any]]) -> str:
    """
    格式化学情信息用于 Prompt
    """
    if not student_profile:
        return "（暂无学情信息）"
    
    lps = student_profile.get("lps", [])
    if not lps:
        return "（暂无学情信息）"
    
    formatted_parts = []
    for i, lp in enumerate(lps[:3], 1):  # 最多取3个
        scope = lp.get("scope", {})
        analysis = lp.get("analysis", {})
        
        part = f"""
学情档案 {i}:
- 范围: {scope.get('subject', '')} {scope.get('grade', '')} {scope.get('related_chapter', '')}
- 整体水平: {analysis.get('overall_level', '未知')}
- 主要问题: {', '.join(analysis.get('main_issues', [])[:3]) if analysis.get('main_issues') else '无'}
- 教学建议: {analysis.get('teaching_suggestions', '无')[:100] if analysis.get('teaching_suggestions') else '无'}
"""
        formatted_parts.append(part)
    
    return "\n".join(formatted_parts)


def format_partial_lesson_for_prompt(partial_lesson: Dict[str, Any]) -> str:
    """
    格式化已生成的教案内容用于 Prompt
    """
    if not partial_lesson:
        return "（尚未生成任何内容）"
    
    formatted_parts = []
    section_names = {
        "objectives": "教学目标",
        "key_points": "教学重难点",
        "teaching_flow": "教学过程",
        "homework": "作业布置",
        "board_design": "板书设计",
        "remarks": "教学反思"
    }
    
    for key, value in partial_lesson.items():
        name = section_names.get(key, key)
        if isinstance(value, dict):
            # 处理嵌套结构如 teaching_flow
            sub_parts = []
            for sub_key, sub_value in value.items():
                sub_parts.append(f"  - {sub_key}: {str(sub_value)[:200]}...")
            formatted_parts.append(f"【{name}】:\n" + "\n".join(sub_parts))
        else:
            content = str(value)[:300] + "..." if len(str(value)) > 300 else str(value)
            formatted_parts.append(f"【{name}】:\n{content}")
    
    return "\n\n".join(formatted_parts)
