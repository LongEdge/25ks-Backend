# -*- coding: utf-8 -*-
"""
Redis 工具层 - 教案生成任务状态管理

职责：
1. Redis 连接管理
2. 教案生成任务状态的初始化、更新、读取
3. partial_lesson（已生成章节内容）的管理
"""
import json
from typing import Optional, List, Dict, Any
from functools import lru_cache

import redis

from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis:
    """
    获取 Redis 客户端（单例模式）
    从 settings.REDIS_URL 解析 host:port
    """
    host_port = settings.REDIS_URL.split(":")
    host = host_port[0] if len(host_port) > 0 else "localhost"
    port = int(host_port[1]) if len(host_port) > 1 else 6379
    password = settings.REDIS_KEY if settings.REDIS_KEY else None
    
    return redis.Redis(
        host=host,
        port=port,
        password=password,
        decode_responses=True,
        socket_connect_timeout=5,
        socket_timeout=5
    )


# ========== 常量定义 ==========
LESSON_TASK_PREFIX = "lesson:gen:"
TASK_TTL = 3600  # 任务记录保留 1 小时


def _get_task_key(task_id: str) -> str:
    """生成 Redis key"""
    return f"{LESSON_TASK_PREFIX}{task_id}"


# ========== 任务状态管理 ==========

def init_lesson_task(
    task_id: str,
    template_id: str,
    teacher_id: int,
    locked_sections: Optional[List[str]] = None,
    clarify_data: Optional[Dict[str, Any]] = None
) -> None:
    """
    初始化教案生成任务
    
    Args:
        task_id: 任务唯一标识
        template_id: 使用的模板 ID
        teacher_id: 教师 ID
        locked_sections: 被用户锁定的章节 key 列表
        clarify_data: 澄清阶段收集的数据
    """
    client = get_redis_client()
    key = _get_task_key(task_id)
    
    task_data = {
        "task_id": task_id,
        "status": "running",
        "current_stage": None,
        "progress": 0.0,
        "partial_lesson": {},
        "locked_sections": locked_sections or [],
        "error": None,
        "lesson_id": None,
        "template_id": template_id,
        "teacher_id": teacher_id,
        "clarify_data": clarify_data or {}
    }
    
    client.setex(key, TASK_TTL, json.dumps(task_data, ensure_ascii=False))


def get_lesson_task(task_id: str) -> Optional[Dict[str, Any]]:
    """
    获取任务状态
    
    Returns:
        任务数据字典，如果不存在返回 None
    """
    client = get_redis_client()
    key = _get_task_key(task_id)
    data = client.get(key)
    
    if data:
        return json.loads(data)
    return None


def update_lesson_task(task_id: str, **kwargs) -> bool:
    """
    更新任务状态（部分更新）
    
    Args:
        task_id: 任务 ID
        **kwargs: 要更新的字段，如 status="end", progress=0.5
        
    Returns:
        更新是否成功
    """
    client = get_redis_client()
    key = _get_task_key(task_id)
    
    data = client.get(key)
    if not data:
        return False
    
    task_data = json.loads(data)
    task_data.update(kwargs)
    
    # 重新设置并刷新 TTL
    client.setex(key, TASK_TTL, json.dumps(task_data, ensure_ascii=False))
    return True


def update_partial_lesson(task_id: str, stage: str, content: Any) -> bool:
    """
    更新已生成的章节内容
    
    Args:
        task_id: 任务 ID
        stage: 章节 key（如 "objectives", "teaching_flow.introduction"）
        content: 章节内容
        
    Returns:
        更新是否成功
    """
    client = get_redis_client()
    key = _get_task_key(task_id)
    
    data = client.get(key)
    if not data:
        return False
    
    task_data = json.loads(data)
    
    # 支持嵌套路径，如 "teaching_flow.introduction"
    if "." in stage:
        parts = stage.split(".")
        current = task_data["partial_lesson"]
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = content
    else:
        task_data["partial_lesson"][stage] = content
    
    client.setex(key, TASK_TTL, json.dumps(task_data, ensure_ascii=False))
    return True


def mark_task_completed(task_id: str, lesson_id: int) -> bool:
    """
    标记任务完成并记录落库的教案 ID
    
    Args:
        task_id: 任务 ID
        lesson_id: MySQL 中的教案主键
        
    Returns:
        更新是否成功
    """
    return update_lesson_task(
        task_id,
        status="end",
        progress=1.0,
        lesson_id=lesson_id
    )


def mark_task_failed(task_id: str, error: str) -> bool:
    """
    标记任务失败
    
    Args:
        task_id: 任务 ID
        error: 错误信息
        
    Returns:
        更新是否成功
    """
    return update_lesson_task(
        task_id,
        status="failed",
        error=error
    )


def delete_lesson_task(task_id: str) -> bool:
    """
    删除任务记录（可选，通常依赖 TTL 自动过期）
    """
    client = get_redis_client()
    key = _get_task_key(task_id)
    return client.delete(key) > 0


def extend_task_ttl(task_id: str, additional_seconds: int = 3600) -> bool:
    """
    延长任务 TTL（用于长时间生成场景）
    """
    client = get_redis_client()
    key = _get_task_key(task_id)
    return client.expire(key, additional_seconds)
