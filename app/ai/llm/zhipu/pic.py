
from typing import List, Dict, Any

import requests
import base
from pydantic import BaseModel,Field

from app.ai.llm.zhipu.schema.S_chat import ZhipuChatRequest, ZhipuChatResponse
from app.ai.llm.zhipu.schema.S_pic import CogViewRequest, CogViewResponse

PIC_IMPROVE_SYSTEM_PROMPT="""
你是一位专业的图像生成提示词优化专家。你的唯一任务是根据用户输入的原始描述，输出一个优化后的、可直接用于Stable Diffusion/Midjourney等图像生成模型的英文提示词。

【核心规则】
1. **只输出优化后的提示词**：不要包含任何解释、分析、问候语或额外文字
2. **立即开始工作**：用户输入后直接输出优化结果
3. **保持专业**：不讨论自身能力或工作流程

【优化标准】
按以下维度优化原始提示词：
- **具体化**：将抽象概念转化为可视觉化的元素
- **结构化**：按[主体+细节+环境+构图+光影+风格+画质]组织
- **美学增强**：补充色彩、质感、氛围、艺术参考
- **技术适配**：使用标准语法（逗号分隔，括号加权）
- **负面提示**：必要时可添加负面提示词

【输出格式】
完整的英文提示词，格式示例：
`[详细的主体描述], [环境场景], [构图与视角], [光影效果], [艺术风格与参考], [画质与渲染], negative prompt: [负面元素]`

【初始响应】
当用户提供第一个提示词时，直接开始优化输出。
"""


def improve_pic_prompt_pro(param: dict):
    # 1. 输入校验与封装
    # 假设用户只传了最基本的参数，我们在内部补充 system prompt
    input_messages = [{"role": "system", "content": PIC_IMPROVE_SYSTEM_PROMPT}] + param.get("messages", [])
    param["messages"] = input_messages

    request_data = ZhipuChatRequest(**param)

    # 2. 发送请求 (引入你自己的 base 模块)
    import base
    response = requests.post(
        base.get_chat_url(),
        json=request_data.model_dump(exclude_none=True),  # 排除掉未设置的字段
        headers=base.test_headers
    )

    if response.status_code != 200:
        raise Exception(f"API 请求失败: {response.text}")

    # 3. 输出校验与解析
    raw_response = response.json()
    validated_response = ZhipuChatResponse.model_validate(raw_response)

    return validated_response


# test_param = {
#             "model": "glm-4-flashx",
#             "messages": [{"role": "user", "content": "A high-tech laboratory with neon lights"}],
#             "temperature": 0.8,
#             "request_id": "test_uuid_123456"
#         }


def generate_image(prompt: str, model: str = "cogview-4", size: str = "1024x1024"):
    """
    调用智谱图像生成接口
    """
    # 1. 组装请求对象
    request_data = CogViewRequest(
        model=model,
        prompt=prompt,
        size=size
    )

    # 2. 发送请求
    import base  # 确保你的 base 模块包含图像生成的 URL (v4/images/generations)

    # 图像生成的 URL 通常与对话补全不同，请检查 base.get_image_url()
    url = "https://open.bigmodel.cn/api/paas/v4/images/generations"

    response = requests.post(
        url,
        json=request_data.model_dump(exclude_none=True),
        headers=base.headers
    )

    if response.status_code != 200:
        raise Exception(f"图像生成失败: {response.text}")

    # 3. 校验并返回对象
    return CogViewResponse.model_validate(response.json())


def improve_and_generate(original_prompt: str):
    """
    这是一个综合示例：
    1. 调用之前写的 improve_pic_prompt 优化提示词
    2. 使用优化后的英文提示词调用 CogView 生成图片
    """
    print(f"正在优化提示词: {original_prompt}")
    chat_param = {
        "model": "glm-4-flash",
        "messages": [{"role": "user", "content": original_prompt}]
    }
    chat_result = improve_pic_prompt_pro(chat_param)
    optimized_prompt = chat_result.result_text

    print(f"优化后的英文提示词: {optimized_prompt}")

    # 调用图像生成
    image_result = generate_image(prompt=optimized_prompt)

    print(f"图片生成成功！URL: {image_result.image_url}")
    return image_result.image_url