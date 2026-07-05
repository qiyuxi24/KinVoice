"""
chat 接口---注意与session.py(用于数据库读写)的区分, 该部分属于用户端与AI模型的的直接对话
"""


from fastapi import APIRouter
from sqlalchemy import select

from app.services.llm_service import call_llm
from app.services.cloudie_prompt import CLOUDIE_SYSTEM_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.card import Conversation, ChatMessage
from app.db.session import AsyncSessionLocal
from app.utils.logger import logger

from app.middleware.user_identity import get_user_id

router = APIRouter(tags=["陪伴对话"])


async def get_or_create_conversation(session, conv_id: int | None, first_message: str) -> Conversation:
    if conv_id:
        result = await session.execute(select(Conversation).where(Conversation.id == conv_id))
        conv = result.scalar_one_or_none()
        if conv:
            return conv
    title = first_message[:50] if first_message else "新对话"
    conv = Conversation(title=title)
    session.add(conv)
    await session.flush()
    return conv


async def build_history(session, conv_id: int) -> list[dict]:
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return [{"role": m.role, "content": m.content} for m in result.scalars()]


@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        async with AsyncSessionLocal() as session:
            conv = await get_or_create_conversation(session, request.conversation_id, request.message)

            user_msg = ChatMessage(conversation_id=conv.id, role="user", content=request.message)
            session.add(user_msg)
            await session.flush()

            history = await build_history(session, conv.id)
            full_messages = [{"role": "system", "content": CLOUDIE_SYSTEM_PROMPT}] + history

            try:
                reply_text = await call_llm(full_messages)
            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                reply_text = "我暂时无法回复，请稍后再试。"

            asst_msg = ChatMessage(conversation_id=conv.id, role="assistant", content=reply_text)
            session.add(asst_msg)
            await session.commit()
            await session.refresh(asst_msg)

            return ChatResponse(
                reply=reply_text,
                conversation_id=conv.id,
                message_id=asst_msg.id,
                tokens_used=0,
            )
    except Exception as e:
        logger.error(f"聊天接口异常: {str(e)}")
        raise  # 交给全局异常处理器统一返回 500