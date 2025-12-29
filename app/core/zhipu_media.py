"""
智谱 AI 媒体生成服务

提供图像生成（同步）和视频生成（异步）功能
"""

import httpx
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel
from app.core.config import settings


# ==============================================
# 数据模型
# ==============================================

class ImageResult(BaseModel):
    """图像生成结果"""
    url: str
    created: int


class VideoTaskResult(BaseModel):
    """视频生成任务结果"""
    task_id: str
    model: str
    request_id: str
    task_status: str


class VideoQueryResult(BaseModel):
    """视频查询结果"""
    task_status: str
    request_id: str
    video_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    error: Optional[str] = None


# ==============================================
# 智谱媒体服务
# ==============================================

class ZhipuMediaService:
    """智谱 AI 媒体生成服务"""

    def __init__(self):
        self.api_key = settings.ZHIPU_API_KEY
        self.base_url = settings.ZHIPU_BASE_URL
        self.timeout = 60.0

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def optimize_prompt(
        self,
        prompt: str,
        media_type: Literal["image", "video"] = "image"
    ) -> str:
        """
        使用 LLM 优化用户提示词

        Args:
            prompt: 用户原始提示词
            media_type: 媒体类型 (image/video)

        Returns:
            优化后的提示词
        """
        if media_type == "image":
            system_prompt = """你是一个专业的图像提示词优化专家。
请将用户的简单描述优化为适合 AI 图像生成的详细提示词。
优化要求：
1. 保留用户的核心意图
2. 添加画面风格、光线、色彩等细节描述
3. 使用英文中括号包裹关键词，如 [high quality], [4K resolution]
4. 添加 negative prompt 排除不想要的元素
5. 保持提示词简洁有力，不超过 200 字

只输出优化后的提示词，不要任何解释。"""
        else:
            system_prompt = """你是一个专业的视频提示词优化专家。
请将用户的简单描述优化为适合 AI 视频生成的详细提示词。
优化要求：
1. 保留用户的核心意图
2. 添加场景、动作、镜头运动等描述
3. 描述画面氛围和情感基调
4. 保持提示词简洁有力，不超过 150 字

只输出优化后的提示词，不要任何解释。"""

        payload = {
            "model": "glm-4-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请优化以下描述：{prompt}"}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # 提取生成的内容
            optimized = data["choices"][0]["message"]["content"]
            return optimized.strip()

    async def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        watermark_enabled: bool = False
    ) -> ImageResult:
        """
        同步生成图像

        Args:
            prompt: 图像描述提示词
            size: 图像尺寸，可选 1024x1024, 768x1344, 1344x768 等
            quality: 质量，可选 standard, hd
            watermark_enabled: 是否添加水印

        Returns:
            ImageResult 包含图像 URL
        """
        payload = {
            "model": "cogview-3-flash",
            "prompt": prompt,
            "size": size,
            "quality": quality,
            "watermark_enabled": watermark_enabled
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/images/generations",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            # 解析响应
            return ImageResult(
                url=data["data"][0]["url"],
                created=data["created"]
            )

    async def generate_video(
        self,
        prompt: str,
        size: str = "1024x1024",
        fps: int = 30,
        quality: str = "speed",
        with_audio: bool = True,
        watermark_enabled: bool = False
    ) -> VideoTaskResult:
        """
        异步提交视频生成任务

        Args:
            prompt: 视频描述提示词
            size: 视频尺寸
            fps: 帧率
            quality: 质量，可选 speed, quality
            with_audio: 是否包含音频
            watermark_enabled: 是否添加水印

        Returns:
            VideoTaskResult 包含任务 ID
        """
        payload = {
            "model": "cogvideox-flash",
            "prompt": prompt,
            "size": size,
            "fps": fps,
            "quality": quality,
            "with_audio": with_audio,
            "watermark_enabled": watermark_enabled
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/videos/generations",
                headers=self._get_headers(),
                json=payload
            )
            response.raise_for_status()
            data = response.json()

            return VideoTaskResult(
                task_id=data["id"],
                model=data["model"],
                request_id=data["request_id"],
                task_status=data["task_status"]
            )

    async def query_video_task(self, task_id: str) -> VideoQueryResult:
        """
        查询视频生成任务状态

        Args:
            task_id: 任务 ID

        Returns:
            VideoQueryResult 包含任务状态和视频 URL
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.base_url}/async-result/{task_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            data = response.json()

            result = VideoQueryResult(
                task_status=data["task_status"],
                request_id=data["request_id"]
            )

            # 如果任务完成，提取视频 URL
            if data["task_status"] == "SUCCESS" and "video_result" in data:
                video_info = data["video_result"][0]
                result.video_url = video_info.get("url")
                result.cover_image_url = video_info.get("cover_image_url")
            elif data["task_status"] == "FAIL":
                result.error = data.get("error", "视频生成失败")

            return result


# 创建服务实例
zhipu_media_service = ZhipuMediaService()
