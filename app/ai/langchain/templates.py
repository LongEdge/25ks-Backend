# -*- coding: utf-8 -*-
"""
内置教案模板配置

职责：
1. 定义默认教案模板结构
2. 定义生成 pipeline 顺序
3. 提供模板获取函数
"""
import uuid
from typing import Optional

from app.ai.langchain.schema.lesson import LessonTemplate, LessonTemplateSection


# ========== 默认教案模板 ==========

DEFAULT_LESSON_TEMPLATE = LessonTemplate(
    template_id="default-v1",  # 内置模板使用固定 ID
    name="标准教案模板",
    description="适用于常规课堂教学的标准教案结构",
    sections=[
        LessonTemplateSection(
            key="objectives",
            title="教学目标",
            type="markdown",
            required=True
        ),
        LessonTemplateSection(
            key="key_points",
            title="教学重难点",
            type="markdown",
            required=True
        ),
        LessonTemplateSection(
            key="teaching_flow",
            title="教学过程",
            type="structured_json",
            required=True,
            children=[
                LessonTemplateSection(
                    key="introduction",
                    title="导入新课",
                    type="markdown",
                    required=True
                ),
                LessonTemplateSection(
                    key="main",
                    title="新授环节",
                    type="markdown",
                    required=True
                ),
                LessonTemplateSection(
                    key="practice",
                    title="课堂练习",
                    type="markdown",
                    required=True
                ),
                LessonTemplateSection(
                    key="summary",
                    title="课堂小结",
                    type="markdown",
                    required=True
                ),
            ]
        ),
        LessonTemplateSection(
            key="homework",
            title="作业布置",
            type="markdown",
            required=False
        ),
        LessonTemplateSection(
            key="board_design",
            title="板书设计",
            type="text",
            required=False
        ),
        LessonTemplateSection(
            key="remarks",
            title="教学反思",
            type="text",
            required=False
        ),
    ]
)


# ========== 生成 Pipeline 定义 ==========

GENERATION_PIPELINE = [
    "objectives",
    "key_points",
    "teaching_flow.introduction",
    "teaching_flow.main",
    "teaching_flow.practice",
    "teaching_flow.summary",
    "homework",
    "board_design",
    "remarks"
]


# ========== 章节标题映射（用于 Prompt 中） ==========

SECTION_TITLES = {
    "objectives": "教学目标",
    "key_points": "教学重难点",
    "teaching_flow.introduction": "导入新课",
    "teaching_flow.main": "新授环节",
    "teaching_flow.practice": "课堂练习",
    "teaching_flow.summary": "课堂小结",
    "homework": "作业布置",
    "board_design": "板书设计",
    "remarks": "教学反思",
}


# ========== 模板管理函数 ==========

# 内置模板注册表
_TEMPLATE_REGISTRY = {
    "default-v1": DEFAULT_LESSON_TEMPLATE,
}


def get_template(template_id: str, db=None) -> Optional[LessonTemplate]:
    """
    获取模板
    
    优先从数据库查询自定义模板，如果未找到则回退到内置模板
    
    Args:
        template_id: 模板 ID
        db: 数据库会话（可选）
        
    Returns:
        模板对象，不存在返回 None
    """
    # 1. 如果提供了 db，先查询数据库
    if db:
        from app.models.lesson_template_model import LessonTemplateModel
        db_template = db.query(LessonTemplateModel).filter(
            LessonTemplateModel.template_id == template_id
        ).first()
        
        if db_template:
            # 转换为 LessonTemplate 对象
            return db_model_to_template(db_template)
    
    # 2. 回退到内置模板注册表
    return _TEMPLATE_REGISTRY.get(template_id)



def get_default_template() -> LessonTemplate:
    """获取默认模板"""
    return DEFAULT_LESSON_TEMPLATE


def generate_template_id() -> str:
    """生成新的模板 ID（用于自定义模板）"""
    return f"custom-{uuid.uuid4().hex[:8]}"


def register_template(template: LessonTemplate) -> None:
    """注册自定义模板"""
    _TEMPLATE_REGISTRY[template.template_id] = template


def list_templates() -> list:
    """列出所有可用模板"""
    return [
        {"id": t.template_id, "name": t.name, "description": t.description}
        for t in _TEMPLATE_REGISTRY.values()
    ]


def db_model_to_template(db_model) -> LessonTemplate:
    """
    将数据库模型转换为 LessonTemplate 对象
    
    Args:
        db_model: LessonTemplateModel 实例
        
    Returns:
        LessonTemplate 对象
    """
    # 转换 sections JSON 为 LessonTemplateSection 对象列表
    sections = [
        LessonTemplateSection(**section_data)
        for section_data in db_model.sections
    ]
    
    return LessonTemplate(
        template_id=db_model.template_id,
        name=db_model.name,
        description=db_model.description,
        sections=sections
    )

