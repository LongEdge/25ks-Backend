# -*- coding: utf-8 -*-
"""
教案澄清会话管理

职责：
1. 管理多轮对话澄清过程
2. LessonClarify 数据的收集和 merge
3. 会话状态管理
"""
import json
from typing import Dict, Tuple, Optional, List, Any

from langchain_classic.chains.conversation.base import ConversationChain
from langchain_classic.memory import ConversationBufferMemory
from langchain_community.chat_models import ChatZhipuAI
from pydantic import BaseModel, Field

from app.ai.langchain.prompts.LESSON import LESSON_CHAT_CLARIFY_PROMPT
from app.ai.langchain.schema.lesson import LessonClarifySchema
from app.core.config import settings


# ========== 会话状态定义 ==========

class LessonClarifyState(BaseModel):
    """教案澄清会话状态"""
    clarify: LessonClarifySchema = Field(default_factory=LessonClarifySchema)
    stage: str = Field(default="clarify", description="当前阶段: clarify/confirmed")
    history: List[Dict[str, str]] = Field(default_factory=list, description="对话历史")


# ========== 会话存储（进程内，速度优先） ==========

_LESSON_SESSIONS: Dict[str, Dict] = {}


def _get_llm(temperature: float = 0.3):
    """获取 LLM 实例"""
    return ChatZhipuAI(
        model="glm-4-flashx-250414",
        temperature=temperature,
        zhipuai_api_key=settings.AI_API_KEY
    )


def _get_or_create_session(session_id: str) -> Dict:
    """获取或创建会话"""
    if session_id not in _LESSON_SESSIONS:
        memory = ConversationBufferMemory(
            return_messages=True,
            memory_key="history"
        )
        
        _LESSON_SESSIONS[session_id] = {
            "memory": memory,
            "state": LessonClarifyState(),
            "llm": _get_llm(0.3)
        }
    return _LESSON_SESSIONS[session_id]


# ========== 核心函数 ==========

def lesson_clarify_chat(session_id: str, user_message: str) -> Tuple[str, LessonClarifyState]:
    """
    处理教案澄清对话
    
    Args:
        session_id: 会话 ID
        user_message: 用户消息
        
    Returns:
        (助手回复, 当前状态)
    """
    sess = _get_or_create_session(session_id)
    state: LessonClarifyState = sess["state"]
    llm = sess["llm"]
    memory: ConversationBufferMemory = sess["memory"]
    
    # 记录用户消息到历史
    state.history.append({"role": "user", "content": user_message})
    
    # 构建 prompt 输入
    history_text = "\n".join([
        f"{h['role']}: {h['content']}" 
        for h in state.history[:-1]  # 不包括当前消息
    ]) if len(state.history) > 1 else "（无历史对话）"
    
    clarify_json = state.clarify.model_dump_json(indent=2, exclude_none=True)
    
    # 调用 LLM
    prompt = LESSON_CHAT_CLARIFY_PROMPT.format(
        clarify_json=clarify_json,
        history=history_text,
        input=user_message
    )
    
    response = llm.invoke(prompt)
    assistant_reply = response.content
    
    # 记录助手回复
    state.history.append({"role": "assistant", "content": assistant_reply})
    
    # 尝试从用户消息中提取信息并 merge 到 clarify
    extracted = _try_extract_clarify_info(user_message, llm)
    if extracted:
        state.clarify = merge_clarify(state.clarify, extracted)
    
    # 检查是否确认
    confirm_words = ["确认", "可以了", "开始生成", "就这样", "没问题"]
    if any(w in user_message for w in confirm_words):
        # 检查核心字段是否完整
        if _is_clarify_complete(state.clarify):
            state.stage = "confirmed"
    
    sess["state"] = state
    return assistant_reply, state


def _try_extract_clarify_info(user_message: str, llm) -> Optional[Dict[str, Any]]:
    """
    尝试从用户消息中提取澄清信息
    
    使用 LLM 解析用户输入，提取结构化信息
    """
    extract_prompt = f"""
从以下用户输入中提取教案相关信息，输出 JSON 格式。
只提取明确提到的信息，不要推测。如果某个字段没有提到，不要包含在输出中。

用户输入：{user_message}

可提取的字段：
- subject: 学科
- grade: 年级  
- lesson_title: 课题名称
- lesson_type: 课程类型（新授/复习/实验/综合）
- class_duration: 课时长度（分钟）
- lesson_count: 课时数
- teaching_goal_focus: 教学侧重点
- difficulty_level: 难度水平
- notes: 补充说明

只输出 JSON，不要有其他内容。如果没有可提取的信息，输出空对象 {{}}
"""
    try:
        result = llm.invoke(extract_prompt)
        content = result.content.strip()
        
        # 清理可能的 markdown 代码块
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        
        extracted = json.loads(content)
        return extracted if extracted else None
    except Exception:
        return None


def merge_clarify(existing: LessonClarifySchema, new_data: Dict[str, Any]) -> LessonClarifySchema:
    """
    合并澄清数据
    
    规则：
    1. null/None 值不覆盖已有值
    2. 新的非空值覆盖旧值
    3. 返回合并后的新对象
    """
    existing_dict = existing.model_dump()
    
    for key, new_value in new_data.items():
        if new_value is not None and key in existing_dict:
            existing_dict[key] = new_value
    
    return LessonClarifySchema(**existing_dict)


def _is_clarify_complete(clarify: LessonClarifySchema) -> bool:
    """检查核心字段是否完整"""
    return all([
        clarify.subject,
        clarify.grade,
        clarify.lesson_title
    ])


def get_lesson_clarify_state(session_id: str) -> Optional[LessonClarifyState]:
    """获取会话状态"""
    if session_id in _LESSON_SESSIONS:
        return _LESSON_SESSIONS[session_id]["state"]
    return None


def update_lesson_clarify(session_id: str, clarify_data: Dict[str, Any]) -> LessonClarifyState:
    """
    直接更新澄清数据（用于用户直接提交表单）
    """
    sess = _get_or_create_session(session_id)
    state: LessonClarifyState = sess["state"]
    
    state.clarify = merge_clarify(state.clarify, clarify_data)
    
    if _is_clarify_complete(state.clarify):
        state.stage = "confirmed"
    
    sess["state"] = state
    return state


def confirm_lesson_clarify(session_id: str) -> LessonClarifyState:
    """确认澄清完成，进入可生成状态"""
    sess = _get_or_create_session(session_id)
    state: LessonClarifyState = sess["state"]
    state.stage = "confirmed"
    sess["state"] = state
    return state


def reset_lesson_session(session_id: str) -> None:
    """重置会话"""
    if session_id in _LESSON_SESSIONS:
        del _LESSON_SESSIONS[session_id]


def get_all_session_ids() -> List[str]:
    """获取所有会话 ID（调试用）"""
    return list(_LESSON_SESSIONS.keys())
