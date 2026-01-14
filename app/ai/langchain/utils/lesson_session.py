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
从以下用户输入中提取教案相关信息,输出 JSON 格式。
只提取明确提到的信息,不要推测。如果某个字段没有提到,不要包含在输出中。

用户输入:{user_message}

可提取的字段:
- subject: 学科
- grade: 年级  
- lesson_title: 课题名称
- lesson_type: 课程类型(新授/复习/实验/综合)
- class_duration: 课时长度(分钟),**必须是纯数字**,例如 45 表示45分钟
- lesson_count: 课时数,**必须是纯数字**,例如 2 表示2课时
- teaching_goal_focus: 教学侧重点
- difficulty_level: 难度水平
- notes: 补充说明

**重要格式要求**:
1. class_duration 和 lesson_count 必须是整数,不能包含单位(如"分钟"、"课时"等)
2. 如果用户说"2小时",class_duration 应该输出 120(分钟)
3. 如果用户说"45分钟",class_duration 应该输出 45
4. 如果用户说"2课时",lesson_count 应该输出 2

只输出 JSON,不要有其他内容。如果没有可提取的信息,输出空对象 {{}}
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


def _sanitize_clarify_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    清洗澄清数据，处理 LLM 可能返回的带单位字符串
    
    Args:
        data: 原始数据字典
        
    Returns:
        清洗后的数据字典
    """
    import re
    
    sanitized = data.copy()
    
    # 处理 class_duration: "2小时" -> 120, "45分钟" -> 45
    if "class_duration" in sanitized and isinstance(sanitized["class_duration"], str):
        duration_str = sanitized["class_duration"]
        
        # 尝试提取小时
        hour_match = re.search(r'(\d+(?:\.\d+)?)\s*小时', duration_str)
        if hour_match:
            sanitized["class_duration"] = int(float(hour_match.group(1)) * 60)
        else:
            # 尝试提取分钟
            minute_match = re.search(r'(\d+(?:\.\d+)?)\s*分钟?', duration_str)
            if minute_match:
                sanitized["class_duration"] = int(float(minute_match.group(1)))
            else:
                # 尝试直接提取数字
                number_match = re.search(r'(\d+)', duration_str)
                if number_match:
                    sanitized["class_duration"] = int(number_match.group(1))
                else:
                    # 无法解析，设为 None
                    sanitized["class_duration"] = None
    
    # 处理 lesson_count: "2课时" -> 2
    if "lesson_count" in sanitized and isinstance(sanitized["lesson_count"], str):
        count_str = sanitized["lesson_count"]
        
        # 提取数字
        number_match = re.search(r'(\d+)', count_str)
        if number_match:
            sanitized["lesson_count"] = int(number_match.group(1))
        else:
            sanitized["lesson_count"] = None
    
    return sanitized


def merge_clarify(existing: LessonClarifySchema, new_data: Dict[str, Any]) -> LessonClarifySchema:
    """
    合并澄清数据
    
    规则：
    1. null/None 值不覆盖已有值
    2. 新的非空值覆盖旧值
    3. 返回合并后的新对象
    """
    # 先清洗数据
    sanitized_data = _sanitize_clarify_data(new_data)
    
    existing_dict = existing.model_dump()
    
    for key, new_value in sanitized_data.items():
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
