# -*- coding: utf-8 -*-
"""
教案模板 SQLAlchemy ORM 模型

对应数据库表: lesson_templates
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, func, Index

from app.core.database import Base


class LessonTemplateModel(Base):
    """教案模板数据库模型"""
    
    __tablename__ = "lesson_templates"
    
    # ===== 主键和关联 =====
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    template_id = Column(String(64), nullable=False, unique=True, index=True, comment="唯一模板标识符")
    teacher_id = Column(Integer, nullable=True, index=True, comment="创建者 ID，NULL 表示系统模板")
    
    # ===== 基础信息 =====
    name = Column(String(128), nullable=False, comment="模板名称")
    description = Column(Text, nullable=True, comment="模板描述")
    is_public = Column(Boolean, nullable=False, default=False, comment="是否为公共模板")
    
    # ===== 模板结构 =====
    # 存储 sections 数组，每个 section 包含: key, title, type, required, children 等
    sections = Column(JSON, nullable=False, comment="模板章节结构 JSON")
    
    # ===== 时间戳 =====
    created_at = Column(
        DateTime, 
        nullable=False, 
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        DateTime, 
        nullable=False, 
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )
    
    # 索引：组合索引用于快速查询某教师的模板
    __table_args__ = (
        Index('idx_teacher_public', 'teacher_id', 'is_public'),
    )
    
    def __repr__(self):
        return f"<LessonTemplate(id={self.id}, template_id='{self.template_id}', name='{self.name}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "template_id": self.template_id,
            "teacher_id": self.teacher_id,
            "name": self.name,
            "description": self.description,
            "is_public": self.is_public,
            "sections": self.sections,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
