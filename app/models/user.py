from sqlalchemy import Column, String, Boolean, Integer, Text, JSON
from app.models.base import BaseModel


class User(BaseModel):
    """用户模型（包含教师信息）"""
    __tablename__ = "users"
    
    # 基本账户信息
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    role = Column(String(20), default="teacher", comment="角色：admin/teacher")
    
    # 教师信息字段
    avatar_base64 = Column(Text, nullable=True, comment="头像Base64编码")
    phone = Column(String(20), nullable=True, comment="手机号")
    subject = Column(String(50), nullable=True, comment="教授学科")
    teaching_style = Column(JSON, nullable=True, comment="教学风格")
    personal_desc = Column(Text, nullable=True, comment="个人简介")
    years_of_experience = Column(Integer, nullable=True, comment="教龄")
    school = Column(String(100), nullable=True, comment="所在学校")
    title = Column(String(50), nullable=True, comment="职称")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
