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


from typing import Dict, Any



