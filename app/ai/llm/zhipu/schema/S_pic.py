from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict


class CogViewRequest(BaseModel):
    model: str = "cogview-4"
    prompt: str = Field(..., description="所需图像的文本描述")
    quality: Optional[str] = "standard"  # hd, standard
    size: Optional[str] = "1024x1024"
    watermark_enabled: bool = True
    user_id: Optional[str] = Field(None, min_length=6, max_length=128)

# ==========================================
# 2. 图像生成响应模型 (Response Models)
# ==========================================

class ImageUrl(BaseModel):
    url: str

class ContentFilter(BaseModel):
    role: str = "assistant"
    level: int

class CogViewResponse(BaseModel):
    created: int
    data: List[ImageUrl]
    content_filter: Optional[List[ContentFilter]] = None

    @property
    def image_url(self) -> Optional[str]:
        """快捷获取生成的第一张图片链接"""
        return self.data[0].url if self.data else None