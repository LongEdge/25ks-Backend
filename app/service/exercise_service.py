# -*- coding: utf-8 -*-
"""
作业集业务逻辑层

提供作业集的CRUD操作
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.exercise import ExerciseSetModel
from app.ai.langchain.schema.exercise import ExerciseSet


def save_exercise_set(
    db: Session,
    exercise_set: ExerciseSet,
    teacher_id: int
) -> ExerciseSetModel:
    """
    保存作业集到数据库
    
    Args:
        db: 数据库会话
        exercise_set: AI生成的作业集对象
        teacher_id: 教师ID
        
    Returns:
        ExerciseSetModel: 保存后的数据库模型实例
    """
    # 准备生成元数据
    generation_metadata = {
        "generation_timestamp": exercise_set.generation_timestamp.isoformat() if exercise_set.generation_timestamp else datetime.utcnow().isoformat(),
        "generated_by": exercise_set.generated_by or "System AI"
    }
    
    # 创建数据库模型实例
    db_exercise_set = ExerciseSetModel(
        teacher_id=teacher_id,
        exercise_set_id=exercise_set.exercise_set_id,
        title=exercise_set.title,
        subject=exercise_set.subject,
        overall_difficulty=exercise_set.overall_difficulty,
        total_score=int(exercise_set.total_score),
        exercise_count=exercise_set.exercise_count,
        covered_knowledge_points=exercise_set.covered_knowledge_points,
        purpose=exercise_set.purpose,
        suggested_duration_minutes=exercise_set.suggested_duration_minutes,
        exercises=[item.model_dump() for item in exercise_set.exercises],  # 转换为dict列表
        generation_metadata=generation_metadata,
        is_deleted=False
    )
    
    # 保存到数据库
    db.add(db_exercise_set)
    db.commit()
    db.refresh(db_exercise_set)
    
    return db_exercise_set


def get_exercise_list(
    db: Session,
    teacher_id: int,
    page: int = 1,
    page_size: int = 10,
    subject: Optional[str] = None,
    difficulty: Optional[str] = None
) -> tuple[List[ExerciseSetModel], int]:
    """
    查询作业列表（带分页和筛选）
    
    Args:
        db: 数据库会话
        teacher_id: 教师ID
        page: 页码（从1开始）
        page_size: 每页数量
        subject: 学科筛选（可选）
        difficulty: 难度筛选（可选）
        
    Returns:
        tuple: (作业列表, 总数)
    """
    # 构建查询
    query = db.query(ExerciseSetModel).filter(
        ExerciseSetModel.teacher_id == teacher_id,
        ExerciseSetModel.is_deleted == False
    )
    
    # 应用筛选条件
    if subject:
        query = query.filter(ExerciseSetModel.subject == subject)
    if difficulty:
        query = query.filter(ExerciseSetModel.overall_difficulty == difficulty)
    
    # 获取总数
    total = query.count()
    
    # 分页查询
    offset = (page - 1) * page_size
    exercise_sets = query.order_by(desc(ExerciseSetModel.created_at)).offset(offset).limit(page_size).all()
    
    return exercise_sets, total


def get_exercise_by_id(
    db: Session,
    exercise_id: int,
    teacher_id: int
) -> Optional[ExerciseSetModel]:
    """
    根据ID获取作业详情
    
    Args:
        db: 数据库会话
        exercise_id: 作业ID
        teacher_id: 教师ID（用于权限验证）
        
    Returns:
        ExerciseSetModel: 作业模型实例，如果不存在或权限不符则返回None
    """
    return db.query(ExerciseSetModel).filter(
        ExerciseSetModel.id == exercise_id,
        ExerciseSetModel.teacher_id == teacher_id,
        ExerciseSetModel.is_deleted == False
    ).first()


def delete_exercise(
    db: Session,
    exercise_id: int,
    teacher_id: int
) -> bool:
    """
    软删除作业
    
    Args:
        db: 数据库会话
        exercise_id: 作业ID
        teacher_id: 教师ID（用于权限验证）
        
    Returns:
        bool: 是否删除成功
    """
    exercise_set = db.query(ExerciseSetModel).filter(
        ExerciseSetModel.id == exercise_id,
        ExerciseSetModel.teacher_id == teacher_id,
        ExerciseSetModel.is_deleted == False
    ).first()
    
    if not exercise_set:
        return False
    
    exercise_set.is_deleted = True
    db.commit()
    return True


def update_exercise(
    db: Session,
    exercise_id: int,
    teacher_id: int,
    update_data: Dict[str, Any]
) -> Optional[ExerciseSetModel]:
    """
    更新作业信息
    
    Args:
        db: 数据库会话
        exercise_id: 作业ID
        teacher_id: 教师ID（用于权限验证）
        update_data: 要更新的字段字典
        
    Returns:
        ExerciseSetModel: 更新后的作业模型实例，如果不存在或权限不符则返回None
    """
    exercise_set = db.query(ExerciseSetModel).filter(
        ExerciseSetModel.id == exercise_id,
        ExerciseSetModel.teacher_id == teacher_id,
        ExerciseSetModel.is_deleted == False
    ).first()
    
    if not exercise_set:
        return None
    
    # 允许更新的字段
    allowed_fields = {
        "title", "purpose", "overall_difficulty", 
        "suggested_duration_minutes", "exercises"
    }
    
    # 更新字段
    for field, value in update_data.items():
        if field in allowed_fields and hasattr(exercise_set, field):
            setattr(exercise_set, field, value)
    
    db.commit()
    db.refresh(exercise_set)
    
    return exercise_set
