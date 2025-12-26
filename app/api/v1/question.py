from fastapi import APIRouter, Depends, Path
from typing import List

router = APIRouter()


# 题目CRUD
@router.post("")
async def create_question():
    """新增题目（手动录入）"""
    return {"message": "新增题目功能待实现"}


@router.get("/{id}")
async def get_question_detail(id: int = Path(...)):
    """题目详情"""
    return {"message": f"获取题目详情功能待实现，题目ID: {id}"}


@router.put("/{id}")
async def update_question(id: int = Path(...)):
    """更新题目"""
    return {"message": f"更新题目功能待实现，题目ID: {id}"}


@router.delete("/{id}")
async def delete_question(id: int = Path(...)):
    """删除题目"""
    return {"message": f"删除题目功能待实现，题目ID: {id}"}


# 题库查询 / 标签管理
@router.get("/list")
async def get_question_list():
    """查询题库（可按科目、知识点、难度筛选）"""
    return {"message": "查询题库功能待实现"}


@router.get("/tags")
async def get_question_tags():
    """获取标签列表"""
    return {"message": "获取题目标签列表功能待实现"}


@router.post("/tags")
async def create_question_tag():
    """创建标签"""
    return {"message": "创建题目标签功能待实现"}


@router.delete("/tags/{tag}")
async def delete_question_tag(tag: str = Path(...)):
    """删除标签"""
    return {"message": f"删除题目标签功能待实现，标签: {tag}"}
