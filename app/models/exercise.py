# -*- coding: utf-8 -*-
"""
作业集 SQLAlchemy ORM 模型

对应数据库表: exercise_sets
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, func
from sqlalchemy.dialects.mysql import JSON as MySQLJSON

from app.core.database import Base


class ExerciseSetModel(Base):
    """作业集数据库模型"""
    
    __tablename__ = "exercise_sets"
    
    # ===== 主键和关联 =====
    id = Column(Integer, primary_key=True, index=True, autoincrement=True, comment="主键ID")
    teacher_id = Column(Integer, nullable=False, index=True, comment="教师ID（关联users表）")
    exercise_set_id = Column(String(64), nullable=False, unique=True, index=True, comment="作业集UUID")
    
    # ===== 基础信息 =====
    title = Column(String(256), nullable=False, comment="作业标题")
    subject = Column(String(64), nullable=False, index=True, comment="学科")
    
    # ===== 作业属性 =====
    overall_difficulty = Column(String(32), nullable=True, comment="整体难度：基础/中等/困难/挑战")
    total_score = Column(Integer, nullable=False, default=100, comment="总分")
    exercise_count = Column(Integer, nullable=False, default=0, comment="题目数量")
    
    # ===== JSON字段 =====
    covered_knowledge_points = Column(
        JSON, 
        nullable=True, 
        default=list,
        comment="覆盖的知识点列表 JSON"
    )
    
    purpose = Column(String(128), nullable=True, comment="作业用途")
    suggested_duration_minutes = Column(Integer, nullable=True, comment="建议完成时长（分钟）")
    
    # ===== 核心内容 =====
    # 存储完整的题目列表，每个题目是一个ExerciseItem的JSON对象
    exercises = Column(
        JSON, 
        nullable=False, 
        default=list,
        comment="题目列表 JSON（ExerciseItem数组）"
    )
    
    # ===== 生成元数据 =====
    generation_metadata = Column(
        JSON, 
        nullable=True, 
        default=dict,
        comment="生成元数据 JSON（包含generation_timestamp, generated_by等）"
    )
    
    # ===== 状态管理 =====
    is_deleted = Column(Boolean, default=False, nullable=False, comment="是否已删除（软删除）")
    
    # ===== 时间戳 =====
    created_at = Column(
        DateTime, 
        nullable=False, 
        server_default=func.now(),
        index=True,
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
        return f"<ExerciseSet(id={self.id}, title='{self.title}', teacher_id={self.teacher_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "teacher_id": self.teacher_id,
            "exercise_set_id": self.exercise_set_id,
            "title": self.title,
            "subject": self.subject,
            "overall_difficulty": self.overall_difficulty,
            "total_score": self.total_score,
            "exercise_count": self.exercise_count,
            "covered_knowledge_points": self.covered_knowledge_points,
            "purpose": self.purpose,
            "suggested_duration_minutes": self.suggested_duration_minutes,
            "exercises": self.exercises,
            "generation_metadata": self.generation_metadata,
            "is_deleted": self.is_deleted,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
