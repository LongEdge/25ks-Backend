from sqlalchemy import Column, String, Boolean, Integer,JSON
from app.models.base import BaseModel


class User(BaseModel):
    """用户模型"""
    __tablename__ = "teacher"
    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, index=True, nullable=False, comment="用户名")
    email = Column(String(100), unique=True, index=True, nullable=False, comment="邮箱")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    role = Column(String(20), default="teacher", comment="角色：admin/teacher")
    teaching_style=Column(JSON, nullable=False, comment="教学风格")
    personal_desc=Column(JSON, nullable=False, comment="个人简介")

    is_active = Column(Boolean, default=True, comment="是否激活")
    is_deleted = Column(Boolean, default=False, comment="是否删除")
