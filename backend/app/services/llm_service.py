"""
统一大模型调用 —— 兼容 OpenAI 兼容接口（蓝心/阿里/千问 等）
"""
import httpx
from app.config import get_settings
from app.utils.logger import logger

settings = get_settings()

SYSTEM_PROMPT_CHAT = (
    "你是一个温柔、善解人意的陪伴者。你擅长用非暴力沟通（NVC）的方式倾听和回应。"
    "你会关注对方的感受和需要，用温暖的语气给予回应。"
    "回复长度控制在 80-200 字之间，语气自然亲切。"
)


async def chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    """
    调用 LLM 对话接口，返回模型回复文本
    """
    url = f"{settings.llm_api_base}/chat/completions"

    payload = {
        "model": settings.llm_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {settings.llm_api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM HTTP 错误: {e.response.status_code} {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"LLM 调用异常: {e}")
            raise


async def chat_with_system(
    user_message: str,
    history: list[dict] | None = None,
    system_prompt: str = SYSTEM_PROMPT_CHAT,
) -> str:
    """
    携带系统提示的对话
    """
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    return await chat_completion(messages)
