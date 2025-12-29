"""
媒体生成 API 路由

提供图像生成（同步）和视频生成（异步）接口
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from app.core.security import get_current_user
from app.models.user import User
from app.core.zhipu_media import zhipu_media_service
from app.schema.media import (
    ImageGenerateRequest,
    ImageGenerateResponse,
    VideoGenerateRequest,
    VideoGenerateResponse,
    VideoStatusResponse
)

router = APIRouter()


# ==============================================
# 图像生成 API
# ==============================================

@router.post("/image/generate", response_model=ImageGenerateResponse)
async def generate_image(
    body: ImageGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    生成图像（同步）

    流程：用户输入 → LLM 优化提示词（可选）→ 调用智谱 API → 返回图像 URL
    """
    try:
        original_prompt = body.prompt
        optimized_prompt = None

        # 优化提示词
        if body.optimize_prompt:
            optimized_prompt = await zhipu_media_service.optimize_prompt(
                body.prompt, "image"
            )
            final_prompt = optimized_prompt
        else:
            final_prompt = original_prompt

        # 生成图像
        result = await zhipu_media_service.generate_image(
            prompt=final_prompt,
            size=body.size,
            quality=body.quality,
            watermark_enabled=body.watermark_enabled
        )

        return ImageGenerateResponse(
            original_prompt=original_prompt,
            optimized_prompt=optimized_prompt,
            image_url=result.url,
            created=result.created
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


# ==============================================
# 视频生成 API
# ==============================================

@router.post("/video/generate", response_model=VideoGenerateResponse)
async def generate_video(
    body: VideoGenerateRequest,
    current_user: User = Depends(get_current_user)
):
    """
    发起视频生成任务（异步）

    流程：用户输入 → LLM 优化提示词（可选）→ 提交生成任务 → 返回任务 ID
    通过 /video/status/{task_id} 查询生成进度
    """
    try:
        original_prompt = body.prompt
        optimized_prompt = None

        # 优化提示词
        if body.optimize_prompt:
            optimized_prompt = await zhipu_media_service.optimize_prompt(
                body.prompt, "video"
            )
            final_prompt = optimized_prompt
        else:
            final_prompt = original_prompt

        # 提交视频生成任务
        result = await zhipu_media_service.generate_video(
            prompt=final_prompt,
            size=body.size,
            fps=body.fps,
            quality=body.quality,
            with_audio=body.with_audio,
            watermark_enabled=body.watermark_enabled
        )

        return VideoGenerateResponse(
            task_id=result.task_id,
            original_prompt=original_prompt,
            optimized_prompt=optimized_prompt,
            task_status=result.task_status
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"视频生成任务提交失败: {str(e)}")


@router.get("/video/status/{task_id}", response_model=VideoStatusResponse)
async def query_video_status(
    task_id: str = Path(..., description="视频生成任务 ID"),
    current_user: User = Depends(get_current_user)
):
    """
    查询视频生成任务状态

    返回任务状态，成功时包含视频 URL 和封面图 URL
    """
    try:
        result = await zhipu_media_service.query_video_task(task_id)

        return VideoStatusResponse(
            task_id=task_id,
            task_status=result.task_status,
            video_url=result.video_url,
            cover_image_url=result.cover_image_url,
            error=result.error
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询任务状态失败: {str(e)}")
