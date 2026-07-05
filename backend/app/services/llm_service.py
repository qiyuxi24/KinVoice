"""
大模型调用封装 —— 含超时、降级、Mock 模式
兼容 xia 分支的 call_llm/chat + si 分支的 chat_completion/chat_with_system
"""
import asyncio
import uuid
import httpx
from app.config import settings
from app.utils.logger import logger

FALLBACK_MESSAGE = "我暂时无法回答，请稍后再试"
TIMEOUT_SECONDS = 3600
<<<<<<< HEAD

# 需要 request_id 的 vivo 模型列表
VIVO_MODELS = ["qwen3.5-plus", "Volc-DeepSeek-V3.2", "Doubao-Seed-2.0-mini", "Doubao-Seed-2.0-lite", "Doubao-Seed-2.0-pro"]

SYSTEM_PROMPT_CHAT = (
    "你是一个温柔、善解人意的陪伴者。你擅长用温和的方式倾听和回应。"
    "你会关注对方的感受和需要，用温暖的语气给予回应。"
    "回复长度控制在 80-200 字之间，语气自然亲切。"
)
=======

# 需要 request_id 的 vivo 模型列表
VIVO_MODELS = ["qwen3.5-plus", "Volc-DeepSeek-V3.2", "Doubao-Seed-2.0-mini", "Doubao-Seed-2.0-lite", "Doubao-Seed-2.0-pro"]
>>>>>>> si

# 提示词统一从 cloudie_prompt 导入
from app.services.cloudie_prompt import CLOUDIE_SYSTEM_PROMPT as SYSTEM_PROMPT_CHAT


async def call_llm(messages: list[dict]) -> str:
    """xia 风格：统一 LLM 调用，含 Mock 降级"""
    # Mock 模式
    if "your-key" in settings.llm_api_key.lower() or "your-appkey" in settings.llm_api_key.lower() or not settings.llm_api_key:
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
    """Mock 降级回复"""
    if "管" in user_input or "烦" in user_input or "别" in user_input:
        return "我知道你是关心我，但我需要一些空间。我们可以好好聊聊这件事吗？"
    elif "谢谢" in user_input or "感谢" in user_input:
        return "你的感谢让我感到很温暖。"
    elif "对不起" in user_input or "抱歉" in user_input:
        return "没关系，我理解你的感受。我们一起来解决这个问题。"
    else:
        return "我理解你想表达的意思。让我们用更温和的方式沟通，好吗？"


async def chat(prompt: str, system_prompt: str | None = None) -> str:
    """xia 风格：带系统提示的单轮对话"""
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


# ── 以下为 si 分支兼容接口 ──

async def call_llm(messages: list[dict]) -> str:
    """xia 风格：统一 LLM 调用，含 Mock 降级"""
    # Mock 模式
    if "your-key" in settings.llm_api_key.lower() or "your-appkey" in settings.llm_api_key.lower() or not settings.llm_api_key:
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
    """Mock 降级回复"""
    if "管" in user_input or "烦" in user_input or "别" in user_input:
        return "我知道你是关心我，但我需要一些空间。我们可以好好聊聊这件事吗？"
    elif "谢谢" in user_input or "感谢" in user_input:
        return "你的感谢让我感到很温暖。"
    elif "对不起" in user_input or "抱歉" in user_input:
        return "没关系，我理解你的感受。我们一起来解决这个问题。"
    else:
        return "我理解你想表达的意思。让我们用更温和的方式沟通，好吗？"


async def chat(prompt: str, system_prompt: str | None = None) -> str:
    """xia 风格：带系统提示的单轮对话"""
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


# ── 以下为 si 分支兼容接口 ──

async def chat_completion(
    messages: list[dict],
    temperature: float = 0.7,
    max_tokens: int = 512,
) -> str:
    """
    si 风格：调用 LLM 对话接口，返回模型回复文本
    """
    return await call_llm(messages)


async def chat_with_system(
    user_message: str,
    history: list[dict] | None = None,
    system_prompt: str = SYSTEM_PROMPT_CHAT,
) -> str:
    """
    si 风格：携带系统提示的对话
    """
    messages = [{"role": "system", "content": system_prompt}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_message})

    return await chat_completion(messages)
