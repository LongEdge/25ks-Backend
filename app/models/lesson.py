from typing import Dict, Any

from pydantic import BaseModel, Field


class LessonContent(BaseModel):
    """
    key 来自 LessonTemplateSection.key
    value 是具体内容（文本 / markdown / JSON 等）
    """
    data: Dict[str, Any] = Field(
        default_factory=dict,
        description="章节内容映射"
    )



from typing import List, Optional
from datetime import datetime


class LessonEntitySchema(BaseModel):
    # ===== 基础信息 =====
    id: Optional[int] = None
    teacher_id: Optional[int] = None

    template_id: str = Field(
        ..., description="使用的教案模板 ID"
    )

    # ===== 来自 clarify 的确认结果 =====
    subject: str
    grade: str
    lesson_title: str
    lesson_type: Optional[str] = None

    # ===== 教案内容 =====
    content: LessonContent = Field(
        default_factory=LessonContent
    )

    # ===== 生成与编辑状态 =====
    generation_status: Optional[str] = Field(
        None, description="当前生成阶段"
    )
    locked_sections: List[str] = Field(
        default_factory=list,
        description="被用户锁定的章节 key 列表"
    )

    # ===== 时间 =====
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
