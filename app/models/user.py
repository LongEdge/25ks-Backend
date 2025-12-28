from sqlalchemy import Column, String, Boolean, Integer
from app.models.base import BaseModel


class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    role = Column(String(20), default="teacher", comment="角色：admin/teacher")
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
