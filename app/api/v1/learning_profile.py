from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schema.learning_profiles_schema import LearningProfileCreate, LearningProfileOut
from app.ai.langchain.schema.learning_profiles import LearningProfile
from app.service.learning_profile import (
    create_learning_profile,
    list_learning_profiles,
    get_learning_profile,
    update_learning_profile,
    delete_learning_profile
)

router = APIRouter()

@router.post("/", response_model=LearningProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    profile_data: LearningProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建学习档案"""
    try:
        profile = create_learning_profile(
            db=db,
            teacher_id=current_user.id,
            data=profile_data
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"创建学习档案失败: {str(e)}"
        )
    
    # 将JSON字符串反序列化为LearningProfile对象
    profile_obj = LearningProfile.model_validate_json(profile.profile_json)
    
    return LearningProfileOut(
        id=profile.id,
        title=profile.title,
        subject=profile.subject,
        grade=profile.grade,
        related_chapter=profile.related_chapter,
        profile=profile_obj
    )

@router.get("/", response_model=list[LearningProfileOut])
def list_profiles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取当前用户的所有学习档案"""
    profiles = list_learning_profiles(db=db, teacher_id=current_user.id)
    
    result = []
    for profile in profiles:
        # 将JSON字符串反序列化为LearningProfile对象
        profile_obj = LearningProfile.model_validate_json(profile.profile_json)
        result.append(LearningProfileOut(
            id=profile.id,
            title=profile.title,
            subject=profile.subject,
            grade=profile.grade,
            related_chapter=profile.related_chapter,
            profile=profile_obj
        ))
    
    return result

@router.get("/{profile_id}", response_model=LearningProfileOut)
def get_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """根据ID获取学习档案"""
    profile = get_learning_profile(
        db=db,
        profile_id=profile_id,
        teacher_id=current_user.id
    )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学习档案不存在"
        )
    
    # 将JSON字符串反序列化为LearningProfile对象
    profile_obj = LearningProfile.model_validate_json(profile.profile_json)
    
    return LearningProfileOut(
        id=profile.id,
        title=profile.title,
        subject=profile.subject,
        grade=profile.grade,
        related_chapter=profile.related_chapter,
        profile=profile_obj
    )

@router.put("/{profile_id}", response_model=LearningProfileOut)
def update_profile(
    profile_id: int,
    profile_data: LearningProfileCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新学习档案"""
    profile = update_learning_profile(
        db=db,
        profile_id=profile_id,
        teacher_id=current_user.id,
        data=profile_data
    )
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学习档案不存在"
        )
    
    # 将JSON字符串反序列化为LearningProfile对象
    profile_obj = LearningProfile.model_validate_json(profile.profile_json)
    
    return LearningProfileOut(
        id=profile.id,
        title=profile.title,
        subject=profile.subject,
        grade=profile.grade,
        related_chapter=profile.related_chapter,
        profile=profile_obj
    )

@router.delete("/{profile_id}")
def delete_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除学习档案"""
    success = delete_learning_profile(
        db=db,
        profile_id=profile_id,
        teacher_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="学习档案不存在"
        )
    
    return {"message": "学习档案删除成功"}