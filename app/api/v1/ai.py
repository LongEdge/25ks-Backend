import uuid
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, Path, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.langchain.agents.LearnAnalysisAgent import get_learning_profiles, build_learning_analysis_tool
from app.core.security import get_current_user
from app.models.user import User
from app.ai.langchain.utils.session import clarify_chat, apply_confirm_md, get_state
from app.ai.langchain.agents.ExerciseAgent import build_exercise_agent
from app.core.database import get_db
from app.service.learning_profile import get_LA
from app.service.exercise_service import (
    save_exercise_set,
    get_exercise_list,
    get_exercise_by_id,
    delete_exercise,
    update_exercise
)

# 教案生成相关导入
from app.ai.langchain.utils.lesson_session import (
    lesson_clarify_chat,
    get_lesson_clarify_state,
    confirm_lesson_clarify,
    reset_lesson_session,
    LessonClarifyState
)
from app.ai.langchain.schema.lesson import LessonClarifySchema
from app.core.redis_util import (
    init_lesson_task,
    get_lesson_task
)
from app.ai.langchain.orchestrator.lesson_orchestrator import create_orchestrator
from app.ai.langchain.templates import get_default_template, list_templates
from app.service.lesson_context import build_lesson_context

router = APIRouter()


# ==============================================
# 教案生成相关 API - Schema 定义
# ==============================================

class LessonClarifyChatIn(BaseModel):
    """教案澄清对话请求"""
    session_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="用户消息")


class LessonGenerateIn(BaseModel):
    """触发教案生成请求"""
    session_id: Optional[str] = Field(None, description="会话 ID（从会话获取 clarify）")
    clarify: Optional[LessonClarifySchema] = Field(None, description="直接提供的澄清数据")
    confirm_md_final: Optional[str] = Field(None, description="用户确认的最终说明（对话模式时提供）")
    template_id: Optional[str] = Field(None, description="模板 ID，默认使用标准模板")
    locked_sections: Optional[List[str]] = Field(default=[], description="锁定的章节 key 列表")


# ==============================================
# 教案澄清 API
# ==============================================

@router.post("/lesson/clarify/chat")
def lesson_clarify_chat_api(
    body: LessonClarifyChatIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    教案澄清对话
    
    多轮对话收集教案生成所需信息
    """
    assistant_reply, state = lesson_clarify_chat(body.session_id, body.message)
    return {
        "reply": assistant_reply,
        "clarify": state.clarify.model_dump(),
        "stage": state.stage,
        "is_complete": state.stage == "confirmed"
    }




@router.get("/lesson/clarify/state")
def lesson_clarify_state_api(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    获取澄清会话状态
    """
    state = get_lesson_clarify_state(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "clarify": state.clarify.model_dump(),
        "stage": state.stage,
        "history": state.history
    }


@router.delete("/lesson/clarify/session")
def lesson_clarify_reset_api(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    重置澄清会话
    """
    reset_lesson_session(session_id)
    return {"message": "Session reset successfully"}


# ==============================================
# 教案生成 API
# ==============================================

@router.post("/lesson/generate")
async def lesson_generate_api(
    body: LessonGenerateIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    触发教案异步生成（包含确认功能）
    
    支持两种模式：
    1. **对话模式**：通过 session_id 从澄清会话中获取数据
       - 会自动确认会话并记录 confirm_md_final（可选）
       - 请求示例：{"session_id": "xxx", "confirm_md_final": "..."}
    
    2. **直接模式**：直接提供完整的澄清数据（跳过对话和确认）
       - 适合需求明确的场景
       - 请求示例：{"clarify": {...}}
    
    返回 task_id，前端通过轮询 /lesson/generate/status 查看进度
    """
    # 获取澄清数据
    clarify = None
    
    if body.clarify:
        # 直接模式：使用提供的 clarify
        clarify = body.clarify
    elif body.session_id:
        # 对话模式：从会话获取并自动确认
        state = get_lesson_clarify_state(body.session_id)
        if state:
            # 如果提供了 confirm_md_final，执行确认
            if body.confirm_md_final:
                state = confirm_lesson_clarify(body.session_id, body.confirm_md_final)
            
            clarify = state.clarify
    
    if not clarify:
        raise HTTPException(
            status_code=400,
            detail="请先完成澄清阶段，或直接提供 clarify 数据"
        )
    
    # 检查核心字段
    if not all([clarify.subject, clarify.grade, clarify.lesson_title]):
        raise HTTPException(
            status_code=400,
            detail="缺少核心字段：subject, grade, lesson_title"
        )
    
    # 生成任务 ID
    task_id = str(uuid.uuid4())
    
    # 获取模板
    template = get_default_template()
    template_id = body.template_id or template.template_id
    
    # 初始化 Redis 任务
    init_lesson_task(
        task_id=task_id,
        template_id=template_id,
        teacher_id=current_user.id,
        locked_sections=body.locked_sections or [],
        clarify_data=clarify.model_dump()
    )
    
    # 构建上下文
    context = build_lesson_context(
        db=db,
        teacher_id=current_user.id,
        clarify=clarify,
        include_student_profile=True
    )
    
    # 创建 Orchestrator
    orchestrator = create_orchestrator(
        task_id=task_id,
        clarify=clarify,
        teacher_id=current_user.id,
        template_id=template_id,
        student_profile=context.student_profile
    )
    
    # 启动后台任务
    background_tasks.add_task(orchestrator.run_pipeline_sync)
    
    return {
        "task_id": task_id,
        "message": "教案生成任务已启动",
        "template_id": template_id
    }


@router.get("/lesson/generate/status")
def lesson_generate_status_api(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    查询教案生成任务状态
    
    返回当前进度和已生成的内容（partial_lesson）
    """
    task = get_lesson_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return {
        "task_id": task.get("task_id"),
        "status": task.get("status"),
        "current_stage": task.get("current_stage"),
        "progress": task.get("progress"),
        "partial_lesson": task.get("partial_lesson"),
        "locked_sections": task.get("locked_sections"),
        "error": task.get("error"),
        "lesson_id": task.get("lesson_id")
    }


# ==============================================
# 教案模板 API
# ==============================================

@router.get("/lesson/templates")
def lesson_templates_api(
    current_user: User = Depends(get_current_user)
):
    """
    获取可用的教案模板列表
    """
    return {
        "templates": list_templates()
    }


#==============================================
# 题目生成相关API
exercise_agent, exercise_parser = build_exercise_agent()

class ClarifyChatIn(BaseModel):
    session_id: str
    message: str


class ClarifyConfirmIn(BaseModel):
    session_id: str
    confirm_md_final: str


class GenerateIn(BaseModel):
    session_id: str


# ==============================================
# 作业CRUD相关Schema
# ==============================================

class ExerciseListQuery(BaseModel):
    """作业列表查询参数"""
    page: int = Field(1, ge=1, description="页码，从1开始")
    page_size: int = Field(10, ge=1, le=100, description="每页数量")
    subject: Optional[str] = Field(None, description="学科筛选")
    difficulty: Optional[str] = Field(None, description="难度筛选")


class ExerciseUpdateRequest(BaseModel):
    """作业更新请求"""
    title: Optional[str] = Field(None, description="作业标题")
    purpose: Optional[str] = Field(None, description="作业用途")
    overall_difficulty: Optional[str] = Field(None, description="整体难度")
    suggested_duration_minutes: Optional[int] = Field(None, description="建议时长")
    exercises: Optional[List[Dict[str, Any]]] = Field(None, description="题目列表")


@router.post("/exercise/clarify/chat")
def exercise_clarify_chat(body: ClarifyChatIn):
    assistant_reply, state = clarify_chat(body.session_id, body.message)
    return {
        "assistant_reply": assistant_reply,
        "stage": state.stage,
        "request": state.request.dict(),
        "confirm_md": state.confirm_md,
    }


@router.post("/exercise/clarify/confirm")
def exercise_clarify_confirm(body: ClarifyConfirmIn):
    state = apply_confirm_md(body.session_id, body.confirm_md_final)
    return {
        "stage": state.stage,
        "request": state.request.dict(),
        "confirm_md_final": state.confirm_md_final,
    }


@router.post("/exercise/generate")
def exercise_generate(
    body: GenerateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """作业生成（带数据库保存）"""
    state = get_state(body.session_id)
    if state.stage != "generate" or not state.confirm_md_final:
        return {"error": "请先完成澄清与确认（confirm_md_final）再生成"}

    payload = {
        **state.request.dict(),
        "confirm_md_final": state.confirm_md_final,
        "exercise_set_id": str(uuid.uuid4())
    }

    # 调用AI生成作业
    result = exercise_agent.invoke(payload)
    exercise_set = exercise_parser.parse(result["output"])
    
    # 保存到数据库
    try:
        db_exercise = save_exercise_set(
            db=db,
            exercise_set=exercise_set,
            teacher_id=current_user.id
        )
        
        # 返回结果（包含数据库ID）
        response = exercise_set.dict()
        response["db_id"] = db_exercise.id
        response["saved_to_database"] = True
        return response
    except Exception as e:
        # 如果保存失败，仍然返回生成结果，但标记未保存
        response = exercise_set.dict()
        response["db_id"] = None
        response["saved_to_database"] = False
        response["save_error"] = str(e)
        return response


# ==============================================
# 作业CRUD API
# ==============================================

@router.get("/exercise/list")
def get_exercises(
    page: int = 1,
    page_size: int = 10,
    subject: Optional[str] = None,
    difficulty: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    查询作业列表
    
    支持分页和筛选，仅返回当前用户的作业
    """
    exercise_sets, total = get_exercise_list(
        db=db,
        teacher_id=current_user.id,
        page=page,
        page_size=page_size,
        subject=subject,
        difficulty=difficulty
    )
    
    # 转换为简化的列表格式（不包含完整题目）
    items = []
    for ex in exercise_sets:
        items.append({
            "id": ex.id,
            "exercise_set_id": ex.exercise_set_id,
            "title": ex.title,
            "subject": ex.subject,
            "overall_difficulty": ex.overall_difficulty,
            "exercise_count": ex.exercise_count,
            "total_score": ex.total_score,
            "purpose": ex.purpose,
            "created_at": ex.created_at.isoformat() if ex.created_at else None
        })
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }


@router.get("/exercise/{exercise_id}")
def get_exercise_detail(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取作业详情
    
    返回完整的作业信息（包括所有题目）
    """
    exercise_set = get_exercise_by_id(
        db=db,
        exercise_id=exercise_id,
        teacher_id=current_user.id
    )
    
    if not exercise_set:
        raise HTTPException(
            status_code=404,
            detail="作业不存在或无权访问"
        )
    
    return exercise_set.to_dict()


@router.delete("/exercise/{exercise_id}")
def delete_exercise_api(
    exercise_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除作业（软删除）
    
    仅能删除自己创建的作业
    """
    success = delete_exercise(
        db=db,
        exercise_id=exercise_id,
        teacher_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="作业不存在或无权删除"
        )
    
    return {
        "success": True,
        "message": "作业已删除"
    }


@router.put("/exercise/{exercise_id}")
def update_exercise_api(
    exercise_id: int,
    update_data: ExerciseUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    更新作业信息
    
    可更新标题、用途、难度、时长和题目内容
    """
    # 过滤掉None值
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    
    if not update_dict:
        raise HTTPException(
            status_code=400,
            detail="没有提供要更新的字段"
        )
    
    updated_exercise = update_exercise(
        db=db,
        exercise_id=exercise_id,
        teacher_id=current_user.id,
        update_data=update_dict
    )
    
    if not updated_exercise:
        raise HTTPException(
            status_code=404,
            detail="作业不存在或无权更新"
        )
    
    return updated_exercise.to_dict()

# @router.post("/lesson/clarify")
# def lesson_clarify(body: ClarifyChatIn):
#     assistant_reply, state = lesson_clarify_chat(body.session_id, body.message)
#     return {
#         "assistant_reply": assistant_reply,
#         "stage": state.stage,
#         "request": state.request.dict(),
#         "confirm_md": state.confirm_md,
#     }

@router.get("/lps/analyze")
def lps_analyze(msg: str,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)
                ):
    return get_LA(db=db,teacher=current_user,msg=msg)

@router.post("/lps/test")
def lps_analyze(msg: str,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)
                ):
    print(current_user.id)
    return get_learning_profiles(db=db, current_user=current_user)

#==============================================
@router.get("/lps/analyze")
def lps_analyze(
    msg: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    la_tool = build_learning_analysis_tool(db, current_user)

    # 直接调用（不通过 Agent）
    return la_tool.run(msg)
