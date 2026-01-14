from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名（3-50个字符）")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")


class UserCreate(UserBase):
    """用户创建模型（注册用）"""
    password: str = Field(..., min_length=6, max_length=50, description="密码（6-50个字符）")


class UserLogin(BaseModel):
    """用户登录模型"""
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ==============================================
# 教师档案相关 Schema
# ==============================================

class UserProfileResponse(BaseModel):
    """用户完整档案响应"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    role: str
    
    # 教师信息
    avatar_base64: Optional[str] = None
    phone: Optional[str] = None
    subject: Optional[str] = None
    teaching_style: Optional[List[str]] = None
    personal_desc: Optional[str] = None
    years_of_experience: Optional[int] = None
    school: Optional[str] = None
    title: Optional[str] = None
    
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfileUpdate(BaseModel):
    """用户档案更新请求"""
    full_name: Optional[str] = Field(None, max_length=100, description="真实姓名")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    subject: Optional[str] = Field(None, max_length=50, description="教授学科")
    teaching_style: Optional[List[str]] = Field(None, description="教学风格")
    personal_desc: Optional[str] = Field(None, description="个人简介")
    years_of_experience: Optional[int] = Field(None, ge=0, le=50, description="教龄")
    school: Optional[str] = Field(None, max_length=100, description="所在学校")
    title: Optional[str] = Field(None, max_length=50, description="职称")


class PasswordUpdate(BaseModel):
    """密码修改请求"""
    old_password: str = Field(..., min_length=6, description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=50, description="新密码")


class AvatarResponse(BaseModel):
    """头像上传响应"""
    avatar_base64: str = Field(..., description="头像 Base64 编码")
    message: str = Field(default="头像上传成功")


# ==============================================
# Token 相关
# ==============================================

class Token(BaseModel):
    """令牌响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """令牌数据模型"""
    user_id: Optional[int] = None
