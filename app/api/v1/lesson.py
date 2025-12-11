from fastapi import APIRouter, Depends, Path
from typing import List
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()


# 教案CRUD基本操作
@router.get("/list")
async def get_lesson_list(current_user: User = Depends(get_current_user)):
    """获取教师的所有教案"""
    return {"message": "获取教案列表功能待实现"}


@router.post("")
async def create_lesson(current_user: User = Depends(get_current_user)):
    """新建空白教案"""
    return {"message": "新建教案功能待实现"}


@router.get("/{id}")
async def get_lesson_detail(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """获取教案详情"""
    return {"message": f"获取教案详情功能待实现，教案ID: {id}"}


@router.put("/{id}")
async def update_lesson(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """编辑教案（整体更新）"""
    return {"message": f"编辑教案功能待实现，教案ID: {id}"}


@router.patch("/{id}")
async def patch_lesson(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """局部更新教案"""
    return {"message": f"局部更新教案功能待实现，教案ID: {id}"}


@router.delete("/{id}")
async def delete_lesson(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """删除教案"""
    return {"message": f"删除教案功能待实现，教案ID: {id}"}


# 教案版本管理
@router.get("/{id}/versions")
async def get_lesson_versions(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """获取某教案的所有版本"""
    return {"message": f"获取教案版本列表功能待实现，教案ID: {id}"}


@router.get("/{id}/version/{version_id}")
async def get_lesson_version_detail(id: int = Path(...), version_id: int = Path(...), current_user: User = Depends(get_current_user)):
    """查看单个版本详情"""
    return {"message": f"查看教案版本详情功能待实现，教案ID: {id}, 版本ID: {version_id}"}


@router.post("/{id}/version")
async def save_lesson_version(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """保存当前内容为新版本"""
    return {"message": f"保存教案版本功能待实现，教案ID: {id}"}


@router.post("/{id}/version/{version_id}/restore")
async def restore_lesson_version(id: int = Path(...), version_id: int = Path(...), current_user: User = Depends(get_current_user)):
    """回滚版本"""
    return {"message": f"回滚教案版本功能待实现，教案ID: {id}, 版本ID: {version_id}"}


# 教案文件上传
@router.post("/{id}/upload")
async def upload_lesson_file(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """上传教师自己的PDF/Word教案文件"""
    return {"message": f"上传教案文件功能待实现，教案ID: {id}"}


# 教案导出接口
@router.get("/{id}/export/md")
async def export_lesson_md(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """导出Markdown"""
    return {"message": f"导出Markdown教案功能待实现，教案ID: {id}"}


@router.get("/{id}/export/pdf")
async def export_lesson_pdf(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """导出PDF"""
    return {"message": f"导出PDF教案功能待实现，教案ID: {id}"}


@router.get("/{id}/export/docx")
async def export_lesson_docx(id: int = Path(...), current_user: User = Depends(get_current_user)):
    """导出Word"""
    return {"message": f"导出Word教案功能待实现，教案ID: {id}"}
