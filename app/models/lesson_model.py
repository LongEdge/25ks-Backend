# -*- coding: utf-8 -*-
"""
教案 SQLAlchemy ORM 模型

对应数据库表: lessons
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, func
from sqlalchemy.dialects.mysql import JSON as MySQLJSON

from app.core.database import Base


class LessonModel(Base):
    """教案数据库模型"""
    
    __tablename__ = "lessons"
    
    # ===== 主键和关联 =====
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    teacher_id = Column(Integer, nullable=False, index=True, comment="教师 ID")
    template_id = Column(String(64), nullable=False, comment="使用的模板 ID")
    
    # ===== 基础信息（来自 Clarify） =====
    subject = Column(String(32), nullable=True, comment="学科")
    grade = Column(String(32), nullable=True, comment="年级")
    lesson_title = Column(String(256), nullable=False, comment="课题名称")
    lesson_type = Column(String(32), nullable=True, comment="课程类型")
    class_duration = Column(Integer, nullable=True, comment="课时长度（分钟）")
    lesson_count = Column(Integer, nullable=True, default=1, comment="课时数")
    
    # ===== 教案内容 =====
    # 存储结构化内容，key 对应模板的 section key
    # 例如: {"objectives": "...", "key_points": "...", "teaching_flow": {...}}
    content = Column(JSON, nullable=True, default=dict, comment="教案内容 JSON")
    
    # ===== 状态管理 =====
    generation_status = Column(
        String(32), 
        nullable=True, 
        default="draft",
        comment="生成状态: draft/generating/completed/failed"
    )
    locked_sections = Column(
        JSON, 
        nullable=True, 
        default=list,
        comment="被用户锁定的章节 key 列表"
    )
    
    # ===== 扩展字段 =====
    teaching_goal_focus = Column(String(64), nullable=True, comment="教学侧重点")
    difficulty_level = Column(String(32), nullable=True, comment="难度水平")
    notes = Column(Text, nullable=True, comment="教师备注")
    
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
    
    def __repr__(self):
        return f"<Lesson(id={self.id}, title='{self.lesson_title}', status='{self.generation_status}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "template_id": self.template_id,
            "subject": self.subject,
            "grade": self.grade,
            "lesson_title": self.lesson_title,
            "lesson_type": self.lesson_type,
            "class_duration": self.class_duration,
            "lesson_count": self.lesson_count,
            "content": self.content,
            "generation_status": self.generation_status,
            "locked_sections": self.locked_sections,
            "teaching_goal_focus": self.teaching_goal_focus,
            "difficulty_level": self.difficulty_level,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
