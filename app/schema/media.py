"""
智谱媒体生成 Schema 定义
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


# ==============================================
# 图像生成
# ==============================================

class ImageGenerateRequest(BaseModel):
    """图像生成请求"""
    prompt: str = Field(..., description="图像描述", min_length=1, max_length=1000)
    size: str = Field(default="1024x1024", description="图像尺寸")
    quality: Literal["standard", "hd"] = Field(default="standard", description="图像质量")
    optimize_prompt: bool = Field(default=True, description="是否使用 LLM 优化提示词")
    watermark_enabled: bool = Field(default=False, description="是否添加水印")


class ImageGenerateResponse(BaseModel):
    """图像生成响应"""
    original_prompt: str = Field(..., description="原始提示词")
    optimized_prompt: Optional[str] = Field(None, description="优化后的提示词")
    image_url: str = Field(..., description="生成的图像 URL")
    created: int = Field(..., description="创建时间戳")


# ==============================================
# 视频生成
# ==============================================

class VideoGenerateRequest(BaseModel):
    """视频生成请求"""
    prompt: str = Field(..., description="视频描述", min_length=1, max_length=500)
    size: str = Field(default="1024x1024", description="视频尺寸")
    fps: int = Field(default=30, ge=15, le=60, description="帧率")
    quality: Literal["speed", "quality"] = Field(default="speed", description="生成质量")
    with_audio: bool = Field(default=True, description="是否包含音频")
    optimize_prompt: bool = Field(default=True, description="是否使用 LLM 优化提示词")
    watermark_enabled: bool = Field(default=False, description="是否添加水印")


class VideoGenerateResponse(BaseModel):
    """视频生成响应"""
    task_id: str = Field(..., description="任务 ID")
    original_prompt: str = Field(..., description="原始提示词")
    optimized_prompt: Optional[str] = Field(None, description="优化后的提示词")
    task_status: str = Field(..., description="任务状态")
    message: str = Field(default="视频生成任务已提交，请通过任务 ID 查询进度", description="提示信息")


class VideoStatusResponse(BaseModel):
    """视频状态查询响应"""
    task_id: str = Field(..., description="任务 ID")
    task_status: str = Field(..., description="任务状态: PROCESSING, SUCCESS, FAIL")
    video_url: Optional[str] = Field(None, description="视频 URL（成功时返回）")
    cover_image_url: Optional[str] = Field(None, description="封面图 URL（成功时返回）")
    error: Optional[str] = Field(None, description="错误信息（失败时返回）")
