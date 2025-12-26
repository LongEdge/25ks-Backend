from pydantic import BaseModel
import requests
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class ThinkingConfig(BaseModel):
    type: str = "enabled"
    clear_thinking: bool = True

class ResponseFormat(BaseModel):
    type: str = "text"

class ChatMessageInput(BaseModel):
    role: str # system, user, assistant, tool
    content: str

class ZhipuChatRequest(BaseModel):
    model: str
    messages: List[ChatMessageInput]
    stream: bool = False
    thinking: Optional[ThinkingConfig] = Field(default_factory=ThinkingConfig)
    do_sample: bool = True
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    top_p: float = Field(default=0.95, ge=0.01, le=1.0)
    max_tokens: Optional[int] = None
    tool_stream: bool = False
    response_format: Optional[ResponseFormat] = Field(default_factory=ResponseFormat)
    stop: Optional[List[str]] = None
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    # 注意：tools 字段较为复杂，此处预留接口
    tools: Optional[List[Dict[str, Any]]] = None
    tool_choice: Optional[str] = "auto"

# ==========================================
# 2. 响应模型 (Response Models)
# ==========================================

class AudioOutput(BaseModel):
    id: Optional[str] = None
    data: Optional[str] = None
    expires_at: Optional[str] = None

class ToolFunction(BaseModel):
    name: str
    arguments: str

class ToolCall(BaseModel):
    id: str
    type: str
    function: Optional[ToolFunction] = None
    # 智谱特有的 mcp 结构
    mcp: Optional[Dict[str, Any]] = None

class ChatMessageOutput(BaseModel):
    role: str
    content: Optional[str] = None
    reasoning_content: Optional[str] = None # 思考过程内容
    audio: Optional[AudioOutput] = None
    tool_calls: Optional[List[ToolCall]] = None

class ChatChoice(BaseModel):
    index: int
    message: ChatMessageOutput
    finish_reason: str

class TokenDetails(BaseModel):
    cached_tokens: Optional[int] = 0

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    prompt_tokens_details: Optional[TokenDetails] = None

class WebSearchHit(BaseModel):
    icon: Optional[str] = None
    title: Optional[str] = None
    link: Optional[str] = None
    media: Optional[str] = None
    publish_date: Optional[str] = None
    content: Optional[str] = None
    refer: Optional[str] = None

class ContentFilter(BaseModel):
    role: str
    level: int

class ZhipuChatResponse(BaseModel):
    id: str
    request_id: str
    created: int
    model: str
    choices: List[ChatChoice]
    usage: Usage
    web_search: Optional[List[WebSearchHit]] = None
    content_filter: Optional[List[ContentFilter]] = None
    video_result: Optional[List[Dict[str, str]]] = None

    @property
    def result_text(self) -> str:
        """获取模型最终生成的文本结果"""
        return self.choices[0].message.content or ""

    @property
    def thinking_process(self) -> Optional[str]:
        """获取思维链内容 (如果开启了思考模式)"""
        return self.choices[0].message.reasoning_content