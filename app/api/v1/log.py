from fastapi import APIRouter, Depends, Path
from typing import List
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


@router.get("/list")
async def get_log_list(current_user: User = Depends(get_current_user)):
    """获取教师操作日志（分页）"""
    return {"message": "获取日志列表功能待实现"}


@router.get("/{id}")
async def get_log_detail(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """查看日志详情"""
    return {"message": f"查看日志详情功能待实现，日志ID: {id}"}
