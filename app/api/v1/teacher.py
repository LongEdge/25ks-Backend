from fastapi import APIRouter, Depends
from typing import Dict

router = APIRouter()


@router.get("/profile")
async def get_teacher_profile():
    """获取教师个人信息"""
    return {"message": "获取教师个人信息功能待实现"}


@router.put("/profile")
async def update_teacher_profile():
    """修改教师信息"""
    return {"message": "修改教师信息功能待实现"}


@router.put("/password")
async def update_password():
    """修改密码"""
    return {"message": "修改密码功能待实现"}


@router.post("/avatar")
async def upload_avatar():
    """上传头像"""
    return {"message": "上传头像功能待实现"}
