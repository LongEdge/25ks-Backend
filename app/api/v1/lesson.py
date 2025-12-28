# -*- coding: utf-8 -*-
"""
教案 CRUD API 接口

提供教案的增删改查功能
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Path, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.lesson_model import LessonModel

router = APIRouter()


# ========== Schema 定义 ==========

class LessonCreateIn(BaseModel):
    """创建教案请求"""
    template_id: str = Field(default="default-v1", description="模板 ID")
    subject: Optional[str] = None
    grade: Optional[str] = None
    lesson_title: str = Field(..., description="课题名称")
    lesson_type: Optional[str] = None
    class_duration: Optional[int] = Field(default=45)
    lesson_count: Optional[int] = Field(default=1)
    content: Optional[Dict[str, Any]] = Field(default_factory=dict)
    notes: Optional[str] = None


class LessonUpdateIn(BaseModel):
    """更新教案请求（完整更新）"""
    subject: Optional[str] = None
    grade: Optional[str] = None
    lesson_title: Optional[str] = None
    lesson_type: Optional[str] = None
    class_duration: Optional[int] = None
    lesson_count: Optional[int] = None
    content: Optional[Dict[str, Any]] = None
    locked_sections: Optional[List[str]] = None
    notes: Optional[str] = None


class LessonPatchIn(BaseModel):
    """局部更新教案请求"""
    subject: Optional[str] = None
    grade: Optional[str] = None
    lesson_title: Optional[str] = None
    lesson_type: Optional[str] = None
    content: Optional[Dict[str, Any]] = None
    locked_sections: Optional[List[str]] = None
    notes: Optional[str] = None


class LessonSectionUpdateIn(BaseModel):
    """更新单个章节内容"""
    section_key: str = Field(..., description="章节 key，如 objectives, teaching_flow.main")
    content: Any = Field(..., description="章节内容")
    lock: Optional[bool] = Field(default=None, description="是否锁定该章节")


# ========== CRUD 接口 ==========

@router.get("/list")
async def get_lesson_list(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取教师的所有教案列表
    
    支持分页和筛选
    """
    query = db.query(LessonModel).filter(
        LessonModel.teacher_id == current_user.id
    )
    
    # 筛选条件
    if subject:
        query = query.filter(LessonModel.subject == subject)
    if grade:
        query = query.filter(LessonModel.grade == grade)
    
    # 排序和分页
    total = query.count()
    lessons = query.order_by(LessonModel.updated_at.desc()) \
                   .offset((page - 1) * page_size) \
                   .limit(page_size) \
                   .all()
    
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "lessons": [lesson.to_dict() for lesson in lessons]
    }


@router.post("")
async def create_lesson(
    body: LessonCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    新建教案
    
    可以创建空白教案或带初始内容的教案
    """
    lesson = LessonModel(
        teacher_id=current_user.id,
        template_id=body.template_id,
        subject=body.subject,
        grade=body.grade,
        lesson_title=body.lesson_title,
        lesson_type=body.lesson_type,
        class_duration=body.class_duration,
        lesson_count=body.lesson_count,
        content=body.content or {},
        generation_status="draft",
        locked_sections=[],
        notes=body.notes
    )
    
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    
    return {
        "message": "教案创建成功",
        "lesson": lesson.to_dict()
    }


@router.get("/{id}")
async def get_lesson_detail(
    id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取教案详情
    """
    lesson = db.query(LessonModel).filter(
        LessonModel.id == id,
        LessonModel.teacher_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="教案不存在")
    
    return lesson.to_dict()


@router.put("/{id}")
async def update_lesson(
    body: LessonUpdateIn,
    id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    编辑教案（整体更新）
    """
    lesson = db.query(LessonModel).filter(
        LessonModel.id == id,
        LessonModel.teacher_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="教案不存在")
    
    # 更新字段
    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(lesson, key, value)
    
    db.commit()
    db.refresh(lesson)
    
    return {
        "message": "教案更新成功",
        "lesson": lesson.to_dict()
    }


@router.patch("/{id}")
async def patch_lesson(
    body: LessonPatchIn,
    id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    局部更新教案
    """
    lesson = db.query(LessonModel).filter(
        LessonModel.id == id,
        LessonModel.teacher_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="教案不存在")
    
    # 只更新提供的字段
    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    for key, value in update_data.items():
        setattr(lesson, key, value)
    
    db.commit()
    db.refresh(lesson)
    
    return {
        "message": "教案更新成功",
        "lesson": lesson.to_dict()
    }


@router.patch("/{id}/section")
async def update_lesson_section(
    body: LessonSectionUpdateIn,
    id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新教案的单个章节内容
    
    支持嵌套 key，如 teaching_flow.main
    """
    lesson = db.query(LessonModel).filter(
        LessonModel.id == id,
        LessonModel.teacher_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="教案不存在")
    
    # 更新 content
    content = lesson.content or {}
    
    if "." in body.section_key:
        # 处理嵌套 key
        parts = body.section_key.split(".")
        current = content
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = body.content
    else:
        content[body.section_key] = body.content
    
    lesson.content = content
    
    # 处理锁定
    if body.lock is not None:
        locked_sections = lesson.locked_sections or []
        if body.lock and body.section_key not in locked_sections:
            locked_sections.append(body.section_key)
        elif not body.lock and body.section_key in locked_sections:
            locked_sections.remove(body.section_key)
        lesson.locked_sections = locked_sections
    
    db.commit()
    db.refresh(lesson)
    
    return {
        "message": f"章节 {body.section_key} 更新成功",
        "lesson": lesson.to_dict()
    }


@router.delete("/{id}")
async def delete_lesson(
    id: int = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除教案
    """
    lesson = db.query(LessonModel).filter(
        LessonModel.id == id,
        LessonModel.teacher_id == current_user.id
    ).first()
    
    if not lesson:
        raise HTTPException(status_code=404, detail="教案不存在")
    
    db.delete(lesson)
    db.commit()
    
    return {"message": "教案删除成功"}


# ========== 版本管理（待实现） ==========

@router.get("/{id}/versions")
async def get_lesson_versions(id: int = Path(...)):
    """获取某教案的所有版本"""
    return {"message": f"获取教案版本列表功能待实现，教案ID: {id}"}


@router.get("/{id}/version/{version_id}")
async def get_lesson_version_detail(id: int = Path(...), version_id: int = Path(...)):
    """查看单个版本详情"""
    return {"message": f"查看教案版本详情功能待实现，教案ID: {id}, 版本ID: {version_id}"}


@router.post("/{id}/version")
async def save_lesson_version(id: int = Path(...)):
    """保存当前内容为新版本"""
    return {"message": f"保存教案版本功能待实现，教案ID: {id}"}


@router.post("/{id}/version/{version_id}/restore")
async def restore_lesson_version(id: int = Path(...), version_id: int = Path(...)):
    """回滚版本"""
    return {"message": f"回滚教案版本功能待实现，教案ID: {id}, 版本ID: {version_id}"}


# ========== 文件上传（待实现） ==========

@router.post("/{id}/upload")
async def upload_lesson_file(id: int = Path(...)):
    """上传教师自己的PDF/Word教案文件"""
    return {"message": f"上传教案文件功能待实现，教案ID: {id}"}


# ========== 导出接口（待实现） ==========

@router.get("/{id}/export/md")
async def export_lesson_md(id: int = Path(...)):
    """导出Markdown"""
    return {"message": f"导出Markdown教案功能待实现，教案ID: {id}"}


@router.get("/{id}/export/pdf")
async def export_lesson_pdf(id: int = Path(...)):
    """导出PDF"""
    return {"message": f"导出PDF教案功能待实现，教案ID: {id}"}


@router.get("/{id}/export/docx")
async def export_lesson_docx(id: int = Path(...)):
    """导出Word"""
    return {"message": f"导出Word教案功能待实现，教案ID: {id}"}
