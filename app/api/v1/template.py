# -*- coding: utf-8 -*-
"""
教案模板 CRUD API 接口

提供模板的增删改查功能
"""
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Path, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.lesson_template_model import LessonTemplateModel
from app.models.lesson_model import LessonModel
from app.ai.langchain.templates import generate_template_id

router = APIRouter()


# ========== Schema 定义 ==========

class TemplateSectionSchema(BaseModel):
    """模板章节定义"""
    key: str = Field(..., description="章节唯一标识")
    title: str = Field(..., description="章节显示标题")
    type: str = Field(..., description="章节内容类型: text/markdown/structured_json等")
    required: bool = Field(default=True, description="是否必填章节")
    repeatable: bool = Field(default=False, description="是否允许重复")
    children: Optional[List["TemplateSectionSchema"]] = Field(default=None, description="子章节")


class TemplateCreateIn(BaseModel):
    """创建模板请求"""
    name: str = Field(..., min_length=1, max_length=128, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    is_public: bool = Field(default=False, description="是否为公共模板")
    sections: List[TemplateSectionSchema] = Field(..., min_length=1, description="模板章节结构")


class TemplateUpdateIn(BaseModel):
    """更新模板请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=128, description="模板名称")
    description: Optional[str] = Field(None, description="模板描述")
    is_public: Optional[bool] = Field(None, description="是否为公共模板")
    sections: Optional[List[TemplateSectionSchema]] = Field(None, description="模板章节结构")


class TemplateResponse(BaseModel):
    """模板响应"""
    id: int
    template_id: str
    teacher_id: Optional[int]
    name: str
    description: Optional[str]
    is_public: bool
    sections: List[Dict[str, Any]]
    created_at: str
    updated_at: str


# ========== CRUD 接口 ==========

@router.get("")
async def list_templates(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    include_system: bool = Query(default=True, description="是否包含系统模板"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取模板列表
    
    返回：系统模板 + 公共模板 + 当前用户的私有模板
    """
    from app.ai.langchain.templates import list_templates as list_builtin_templates
    
    result = {
        "total": 0,
        "page": page,
        "page_size": page_size,
        "templates": []
    }
    
    # 1. 内置模板（如果需要）
    if include_system:
        builtin = list_builtin_templates()
        result["templates"].extend([
            {
                **t,
                "is_builtin": True,
                "teacher_id": None,
                "created_at": None,
                "updated_at": None
            }
            for t in builtin
        ])
    
    # 2. 数据库模板查询
    query = db.query(LessonTemplateModel).filter(
        (LessonTemplateModel.is_public == True) | 
        (LessonTemplateModel.teacher_id == current_user.id)
    )
    
    total = query.count()
    templates = query.order_by(LessonTemplateModel.updated_at.desc()) \
                     .offset((page - 1) * page_size) \
                     .limit(page_size) \
                     .all()
    
    db_templates = [
        {
            **t.to_dict(),
            "is_builtin": False
        }
        for t in templates
    ]
    
    result["templates"].extend(db_templates)
    result["total"] = len(result["templates"]) if include_system else total
    
    return result


@router.get("/{template_id}")
async def get_template_detail(
    template_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取模板详情
    """
    from app.ai.langchain.templates import get_template as get_builtin_template
    
    # 1. 先查内置模板
    builtin = get_builtin_template(template_id)
    if builtin:
        return {
            "id": builtin.template_id,
            "template_id": builtin.template_id,
            "teacher_id": None,
            "name": builtin.name,
            "description": builtin.description,
            "is_public": True,
            "is_builtin": True,
            "sections": [s.model_dump() for s in builtin.sections],
            "created_at": None,
            "updated_at": None
        }
    
    # 2. 查数据库模板
    template = db.query(LessonTemplateModel).filter(
        LessonTemplateModel.template_id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 权限检查：公共模板或自己的模板
    if not template.is_public and template.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此模板")
    
    return {
        **template.to_dict(),
        "is_builtin": False
    }


@router.post("")
async def create_template(
    body: TemplateCreateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    创建自定义模板
    """
    # 生成唯一 template_id
    new_template_id = generate_template_id()
    
    # 转换 sections 为 dict
    sections_json = [s.model_dump() for s in body.sections]
    
    template = LessonTemplateModel(
        template_id=new_template_id,
        teacher_id=current_user.id,
        name=body.name,
        description=body.description,
        is_public=body.is_public,
        sections=sections_json
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {
        "message": "模板创建成功",
        "template": template.to_dict()
    }


@router.put("/{template_id}")
async def update_template(
    body: TemplateUpdateIn,
    template_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新模板
    
    仅允许更新自己创建的模板
    """
    template = db.query(LessonTemplateModel).filter(
        LessonTemplateModel.template_id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 权限检查：只能更新自己的模板
    if template.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权修改此模板")
    
    # 更新字段
    update_data = body.model_dump(exclude_unset=True, exclude_none=True)
    
    # 特殊处理 sections
    if "sections" in update_data:
        update_data["sections"] = [s.model_dump() for s in body.sections]
    
    for key, value in update_data.items():
        setattr(template, key, value)
    
    db.commit()
    db.refresh(template)
    
    return {
        "message": "模板更新成功",
        "template": template.to_dict()
    }


@router.delete("/{template_id}")
async def delete_template(
    template_id: str = Path(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除模板
    
    仅允许删除自己创建的模板，且不能有课程正在使用
    """
    template = db.query(LessonTemplateModel).filter(
        LessonTemplateModel.template_id == template_id
    ).first()
    
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 权限检查
    if template.teacher_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除此模板")
    
    # 检查是否有课程使用此模板
    lessons_using = db.query(LessonModel).filter(
        LessonModel.template_id == template_id,
        LessonModel.teacher_id == current_user.id
    ).count()
    
    if lessons_using > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"此模板正被 {lessons_using} 个课程使用，无法删除"
        )
    
    db.delete(template)
    db.commit()
    
    return {"message": "模板删除成功"}
