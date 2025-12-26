from fastapi import APIRouter, Depends, Path
from typing import List

router = APIRouter()


@router.get("/subjects")
async def get_subjects():
    """获取系统支持的科目列表"""
    return {"message": "获取科目列表功能待实现"}


@router.get("/list")
async def get_course_list():
    """获取教师的课程列表"""
    return {"message": "获取课程列表功能待实现"}


@router.post("")
async def create_course():
    """新建课程"""
    return {"message": "新建课程功能待实现"}


@router.get("/{id}")
async def get_course_detail(id: int = Path(...)):
    """查看课程详情"""
    return {"message": f"查看课程详情功能待实现，课程ID: {id}"}


@router.put("/{id}")
async def update_course(id: int = Path(...)):
    """修改课程信息"""
    return {"message": f"修改课程信息功能待实现，课程ID: {id}"}


@router.delete("/{id}")
async def delete_course(id: int = Path(...)):
    """删除课程"""
    return {"message": f"删除课程功能待实现，课程ID: {id}"}
