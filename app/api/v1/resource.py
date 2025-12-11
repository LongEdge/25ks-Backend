from fastapi import APIRouter, Depends, Path
from typing import List
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


# 资源上传与管理
@router.post("/upload")
async def upload_resource(current_user: User = Depends(get_current_user)):
    """上传本地图片（教师素材）"""
    return {"message": "上传资源功能待实现"}


@router.get("/list")
async def get_resource_list(current_user: User = Depends(get_current_user)):
    """获取资源库内容（分页/分类）"""
    return {"message": "获取资源列表功能待实现"}


@router.delete("/{id}")
async def delete_resource(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """删除资源"""
    return {"message": f"删除资源功能待实现，资源ID: {id}"}


@router.put("/{id}")
async def update_resource(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """修改资源信息（名称/标签）"""
    return {"message": f"修改资源信息功能待实现，资源ID: {id}"}


# 资源标签
@router.get("/tags")
async def get_resource_tags(current_user: User = Depends(get_current_user)):
    """获取全部标签"""
    return {"message": "获取资源标签列表功能待实现"}


@router.post("/tags")
async def create_resource_tag(current_user: User = Depends(get_current_user)):
    """新增标签"""
    return {"message": "新增资源标签功能待实现"}


@router.delete("/tags/{tag}")
async def delete_resource_tag(tag: str = Path(...), current_user: User = Depends(get_current_user)):
    """删除标签"""
    return {"message": f"删除资源标签功能待实现，标签: {tag}"}
