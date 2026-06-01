"""
陪伴对话接口 —— POST /chat
温柔倾听、NVC 风格回应
"""
from fastapi import APIRouter
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.llm_service import chat_with_system
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["陪伴对话"])


@router.post("", response_model=ChatResponse)
async def chat_with_companion(req: ChatRequest):
    """
    陪伴式 AI 对话 —— 用 NVC 方式温柔回应
    """
    logger.info(f"收到对话: msg_len={len(req.message)}, history={len(req.history or [])}")

    reply = await chat_with_system(
        user_message=req.message,
        history=req.history,
    )

    return ChatResponse(
        reply=reply,
        emotion=req.emotion_state,
        need_hint=None,
    )
