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

# 教案生成相关导入
from app.ai.langchain.utils.lesson_session import (
    lesson_clarify_chat,
    get_lesson_clarify_state,
    update_lesson_clarify,
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


class LessonClarifyUpdateIn(BaseModel):
    """教案澄清数据直接更新请求"""
    session_id: str
    clarify_data: Dict[str, Any] = Field(..., description="要更新的澄清数据")


class LessonGenerateIn(BaseModel):
    """触发教案生成请求"""
    session_id: Optional[str] = Field(None, description="会话 ID（从会话获取 clarify）")
    clarify: Optional[LessonClarifySchema] = Field(None, description="直接提供的澄清数据")
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


@router.post("/lesson/clarify/update")
def lesson_clarify_update_api(
    body: LessonClarifyUpdateIn,
    current_user: User = Depends(get_current_user)
):
    """
    直接更新澄清数据
    
    用于前端表单直接提交场景
    """
    state = update_lesson_clarify(body.session_id, body.clarify_data)
    return {
        "clarify": state.clarify.model_dump(),
        "stage": state.stage,
        "is_complete": state.stage == "confirmed"
    }


@router.post("/lesson/clarify/confirm")
def lesson_clarify_confirm_api(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    确认澄清完成
    
    将会话状态标记为可生成
    """
    state = confirm_lesson_clarify(session_id)
    return {
        "clarify": state.clarify.model_dump(),
        "stage": state.stage,
        "message": "澄清已确认，可以开始生成教案"
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
    触发教案异步生成
    
    返回 task_id，前端通过轮询 /lesson/generate/status 查看进度
    """
    # 获取澄清数据
    clarify = None
    if body.clarify:
        clarify = body.clarify
    elif body.session_id:
        state = get_lesson_clarify_state(body.session_id)
        if state and state.stage == "confirmed":
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


# ==============================================
# 其他 AI 教案功能（待实现）
# ==============================================

@router.post("/lesson/expand")
async def expand_lesson():
    """扩展/补全教案段落"""
    return {"message": "AI扩展教案功能待实现"}


@router.post("/lesson/optimize")
async def optimize_lesson():
    """优化教案风格/逻辑"""
    return {"message": "AI优化教案功能待实现"}


@router.post("/lesson/summary")
async def summarize_lesson():
    """教案摘要生成"""
    return {"message": "AI生成教案摘要功能待实现"}


# AI 教案解析（文件解析）
@router.post("/lesson/parse")
async def parse_lesson():
    """上传 PDF/DOCX → 解析成 JSON 结构"""
    return {"message": "AI解析教案文件功能待实现"}


# AI 题目生成
@router.post("/question/generate")
async def generate_question():
    """根据知识点批量生成题目"""
    return {"message": "AI生成题目功能待实现"}


@router.post("/question/analysis")
async def analyze_question():
    """对题目生成解析（可分开提供）"""
    return {"message": "AI生成题目解析功能待实现"}


# AI 配图 / 插画生成
@router.post("/image/generate")
async def generate_image():
    """根据描述生成插图"""
    return {"message": "AI生成插图功能待实现"}


@router.post("/board/generate")
async def generate_board():
    """生成板书风格图片"""
    return {"message": "AI生成板书功能待实现"}


# AI PPT 生成
@router.post("/ppt/generate")
async def generate_ppt():
    """根据教案自动生成 PPT（返回下载地址）"""
    return {"message": "AI生成PPT功能待实现"}


# AI 学情分析（可选）
@router.post("/analysis/mistakes")
async def analyze_mistakes():
    """根据错误题生成学情分析报告"""
    return {"message": "AI生成学情分析报告功能待实现"}


@router.post("/analysis/class")
async def analyze_class():
    """班级整体画像（可模拟数据）"""
    return {"message": "AI生成班级画像功能待实现"}


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
def exercise_generate(body: GenerateIn):
    state = get_state(body.session_id)
    if state.stage != "generate" or not state.confirm_md_final:
        return {"error": "请先完成澄清与确认（confirm_md_final）再生成"}

    payload = {
        **state.request.dict(),
        "confirm_md_final": state.confirm_md_final,
        "exercise_set_id":uuid.uuid4()
    }

    result = exercise_agent.invoke(payload)
    exercise_set = exercise_parser.parse(result["output"])
    return exercise_set.dict()

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
