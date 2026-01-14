import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    get_password_hash, 
    verify_password, 
    create_access_token,
    get_current_user
)
from app.models.user import User
from app.schema.user import (
    UserCreate, 
    UserResponse,
    UserProfileResponse,
    UserProfileUpdate,
    PasswordUpdate,
    AvatarResponse
)
from fastapi.responses import JSONResponse

router = APIRouter()


# ==============================================
# 注册/登录/登出
# ==============================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """教师注册"""
    # 检查用户名是否已存在
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )

    # 检查邮箱是否已存在
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已存在"
        )

    try:
        hashed_password = get_password_hash(str(user_data.password))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码哈希失败"
        )

    # 创建用户
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
        full_name=user_data.full_name
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="数据库操作失败"
        )
    
    return UserResponse.model_validate(db_user)


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    db: Session = Depends(get_db)
):
    """登录，返回JWT Token"""
    user = db.query(User).filter(User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(data={"sub": str(user.id)})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """退出登录"""
    # JWT 无状态，客户端删除 token 即可
    return {"message": "退出登录成功"}


@router.post("/refresh")
async def refresh_token(current_user: User = Depends(get_current_user)):
    """刷新Token"""
    access_token = create_access_token(data={"sub": str(current_user.id)})
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


# ==============================================
# 用户档案管理
# ==============================================

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """获取当前用户完整信息"""
    return UserProfileResponse.model_validate(current_user)


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    profile_data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户信息"""
    # 获取需要更新的字段
    update_data = profile_data.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有提供需要更新的字段"
        )
    
    # 更新字段
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    try:
        db.commit()
        db.refresh(current_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )
    
    return UserProfileResponse.model_validate(current_user)


@router.put("/password")
async def update_password(
    password_data: PasswordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """修改密码"""
    # 验证旧密码
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    # 检查新旧密码是否相同
    if password_data.old_password == password_data.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="新密码不能与旧密码相同"
        )
    
    # 更新密码
    current_user.password_hash = get_password_hash(password_data.new_password)
    
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="密码修改失败"
        )
    
    return {"message": "密码修改成功"}


@router.post("/avatar", response_model=AvatarResponse)
async def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传头像（转换为 Base64 存储）"""
    import base64
    
    # 验证文件类型
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不支持的图片格式，仅支持 JPEG/PNG/GIF/WebP"
        )
    
    # 验证文件大小（最大 5MB）
    max_size = 5 * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="文件大小超过限制（最大 5MB）"
        )
    
    try:
        # 将图片内容转换为 Base64 编码
        base64_content = base64.b64encode(contents).decode('utf-8')
        
        # 构建 Data URL 格式（包含 MIME 类型）
        avatar_base64 = f"data:{file.content_type};base64,{base64_content}"
        
        # 更新用户头像
        current_user.avatar_base64 = avatar_base64
        db.commit()
        
        return AvatarResponse(avatar_base64=avatar_base64)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"头像上传失败: {str(e)}"
        )

