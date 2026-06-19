"""
大模型调用封装 —— 含超时、降级、Mock 模式
"""

import asyncio
import uuid
import httpx
from app.config import settings
from app.utils.logger import logger

FALLBACK_MESSAGE = "我暂时无法回答，请稍后再试"
TIMEOUT_SECONDS = 10

# 需要 request_id 的 vivo 模型列表
VIVO_MODELS = ["qwen3.5-plus", "Volc-DeepSeek-V3.2", "Doubao-Seed-2.0-mini", "Doubao-Seed-2.0-lite", "Doubao-Seed-2.0-pro"]


async def call_llm(messages: list[dict]) -> str:
    # Mock 模式
    if "your-key" in settings.llm_api_key.lower() or "your-appkey" in settings.llm_api_key.lower():
        logger.warning("使用 Mock 模式")
        await asyncio.sleep(0.5)
        return _mock_response(messages[-1]["content"])

    # 真实调用
    request_id = str(uuid.uuid4())
    url = f"{settings.llm_api_base}/chat/completions"

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Bearer {settings.llm_api_key}",
    }

    # vivo 大模型需要 request_id 作为 query 参数
    params = {}
    if settings.llm_model in VIVO_MODELS:
        params["request_id"] = request_id

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
        response = await client.post(
            url,
            headers=headers,
            params=params,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


def _mock_response(user_input: str) -> str:
    if "管" in user_input or "烦" in user_input or "别" in user_input:
        return "我知道你是关心我，但我需要一些空间。我们可以好好聊聊这件事吗？"
    elif "谢谢" in user_input or "感谢" in user_input:
        return "你的感谢让我感到很温暖。"
    elif "对不起" in user_input or "抱歉" in user_input:
        return "没关系，我理解你的感受。我们一起来解决这个问题。"
    else:
        return "我理解你想表达的意思。让我们用更温和的方式沟通，好吗？"


async def chat(prompt: str, system_prompt: str | None = None) -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        result = await call_llm(messages)
        logger.info("LLM 调用成功")
        return result
    except httpx.TimeoutException:
        logger.error(f"LLM 超时（>{TIMEOUT_SECONDS}秒）")
        return FALLBACK_MESSAGE
    except Exception as e:
        logger.error(f"LLM 调用失败: {str(e)}")
        return FALLBACK_MESSAGE