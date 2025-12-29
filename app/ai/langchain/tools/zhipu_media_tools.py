"""
智谱媒体生成 LangChain 工具

提供图像和视频生成工具供 Agent 调用
"""

import asyncio
from typing import Optional
from langchain_core.tools import tool, Tool
from app.core.zhipu_media import zhipu_media_service


def _run_async(coro):
    """在同步环境中运行异步函数"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果已有事件循环在运行，创建新任务
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@tool
def zhipu_generate_image(prompt: str, optimize: bool = True) -> str:
    """
    根据描述生成图像。

    Args:
        prompt: 图像描述，如"一个现代化的实验室"
        optimize: 是否使用 AI 优化提示词，默认 True

    Returns:
        生成的图像 URL
    """
    async def _generate():
        final_prompt = prompt
        if optimize:
            final_prompt = await zhipu_media_service.optimize_prompt(prompt, "image")

        result = await zhipu_media_service.generate_image(final_prompt)
        return f"图像生成成功！\n优化后提示词：{final_prompt}\n图像URL：{result.url}"

    return _run_async(_generate())


@tool
def zhipu_generate_video(prompt: str, optimize: bool = True) -> str:
    """
    根据描述生成视频（异步任务）。

    Args:
        prompt: 视频描述，如"苏轼泛舟赤壁"
        optimize: 是否使用 AI 优化提示词，默认 True

    Returns:
        任务 ID，需使用 zhipu_query_video_status 工具查询结果
    """
    async def _generate():
        final_prompt = prompt
        if optimize:
            final_prompt = await zhipu_media_service.optimize_prompt(prompt, "video")

        result = await zhipu_media_service.generate_video(final_prompt)
        return (
            f"视频生成任务已提交！\n"
            f"任务ID：{result.task_id}\n"
            f"状态：{result.task_status}\n"
            f"优化后提示词：{final_prompt}\n"
            f"请使用 zhipu_query_video_status 工具查询生成结果"
        )

    return _run_async(_generate())


@tool
def zhipu_query_video_status(task_id: str) -> str:
    """
    查询视频生成任务状态。

    Args:
        task_id: 视频生成任务的 ID

    Returns:
        任务状态和视频 URL（如果生成完成）
    """
    async def _query():
        result = await zhipu_media_service.query_video_task(task_id)

        if result.task_status == "SUCCESS":
            return (
                f"视频生成完成！\n"
                f"视频URL：{result.video_url}\n"
                f"封面图URL：{result.cover_image_url}"
            )
        elif result.task_status == "PROCESSING":
            return f"视频正在生成中，请稍后再查询。任务ID：{task_id}"
        else:
            return f"视频生成失败：{result.error or '未知错误'}"

    return _run_async(_query())


# ==============================================
# 工具列表导出
# ==============================================

ZHIPU_MEDIA_TOOLS = [
    zhipu_generate_image,
    zhipu_generate_video,
    zhipu_query_video_status
]

# 兼容旧的 Tool 类方式
zhipu_generate_image_tool = Tool(
    name="zhipu_generate_image",
    description="根据描述生成图像，返回图像 URL",
    func=lambda prompt: zhipu_generate_image.invoke({"prompt": prompt})
)

zhipu_generate_video_tool = Tool(
    name="zhipu_generate_video",
    description="根据描述生成视频，返回任务 ID（需轮询查询结果）",
    func=lambda prompt: zhipu_generate_video.invoke({"prompt": prompt})
)

zhipu_query_video_tool = Tool(
    name="zhipu_query_video_status",
    description="查询视频生成任务状态，返回视频 URL 或进度信息",
    func=lambda task_id: zhipu_query_video_status.invoke({"task_id": task_id})
)
