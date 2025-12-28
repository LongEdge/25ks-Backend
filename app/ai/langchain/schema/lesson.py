from typing import Optional
from pydantic import BaseModel, Field


class LessonClarifySchema(BaseModel):
    # ===== 核心字段（逻辑必需，但技术上允许为空）=====
    subject: Optional[str] = Field(None, description="学科")
    grade: Optional[str] = Field(None, description="年级")
    lesson_title: Optional[str] = Field(None, description="课题名称")

    # ===== 课程基本属性 =====
    lesson_type: Optional[str] = Field(
        None, description="课程类型，如 新授 / 复习 / 实验 / 综合"
    )
    class_duration: Optional[int] = Field(
        None, description="单课时长度（分钟）"
    )
    lesson_count: Optional[int] = Field(
        None, description="课时数"
    )

    # ===== 教学取向 =====
    teaching_goal_focus: Optional[str] = Field(
        None, description="教学侧重点，如 知识 / 能力 / 素养 / 应试"
    )
    difficulty_level: Optional[str] = Field(
        None, description="难度水平，如 基础 / 中等 / 提高"
    )

    # ===== 约束 & 补充 =====
    exam_related: Optional[bool] = Field(
        None, description="是否与考试相关"
    )
    curriculum_standard: Optional[str] = Field(
        None, description="对应课程标准"
    )
    constraints: Optional[str] = Field(
        None, description="特殊约束条件"
    )
    notes: Optional[str] = Field(
        None, description="教师补充说明"
    )


from typing import List, Optional, Literal
from pydantic import BaseModel, Field


SectionType = Literal[
    "text",
    "markdown",
    "rich_text",
    "structured_json",
    "teaching_flow_block"
]


class LessonTemplateSection(BaseModel):
    key: str = Field(..., description="章节唯一标识，用于 lesson.content 的 key")
    title: str = Field(..., description="章节显示标题")
    type: SectionType = Field(..., description="章节内容类型")

    required: bool = Field(
        default=True, description="是否必填章节"
    )
    repeatable: bool = Field(
        default=False, description="是否允许重复出现"
    )

    children: Optional[List["LessonTemplateSection"]] = Field(
        default=None, description="子章节（可选）"
    )


from typing import Dict, Any, List, Literal


class LessonTemplate(BaseModel):
    """教案模板容器 - 定义章节树结构"""
    template_id: str = Field(..., description="系统生成的模板 UUID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    sections: List["LessonTemplateSection"] = Field(default_factory=list, description="章节列表")

    class Config:
        # 支持自引用（children）
        arbitrary_types_allowed = True


class LessonContext(BaseModel):
    """教案生成上下文 - 聚合澄清结果和学情信息"""
    clarify: "LessonClarifySchema"
    student_profile: Optional[Dict[str, Any]] = Field(None, description="学情聚合结果")
    rag_context: Optional[Dict[str, Any]] = Field(None, description="RAG 检索增强内容（未来扩展）")
    kg_context: Optional[Dict[str, Any]] = Field(None, description="知识图谱增强内容（未来扩展）")


class LessonGenerationTask(BaseModel):
    """Redis 任务状态 - 用于异步生成过程中的状态管理"""
    task_id: str = Field(..., description="任务唯一 ID")
    status: Literal["running", "end", "failed"] = Field(default="running", description="任务状态")
    current_stage: Optional[str] = Field(None, description="当前生成阶段")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="生成进度 0-1")
    partial_lesson: Dict[str, Any] = Field(default_factory=dict, description="已生成的章节内容")
    locked_sections: List[str] = Field(default_factory=list, description="被用户锁定的章节 key")
    error: Optional[str] = Field(None, description="错误信息")
    lesson_id: Optional[int] = Field(None, description="落库后的教案 ID")
    template_id: Optional[str] = Field(None, description="使用的模板 ID")
    teacher_id: Optional[int] = Field(None, description="教师 ID")


