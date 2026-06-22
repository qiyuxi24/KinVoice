"""
Chat 接口 —— 陪伴式 AI 对话
兼容 si 无状态模式 + xia 会话持久化模式
"""
from fastapi import APIRouter
from sqlalchemy import select
from app.services.llm_service import call_llm, chat_with_system
from app.services.cloudie_prompt import CLOUDIE_SYSTEM_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.card import Conversation, ChatMessage
from app.db.session import AsyncSessionLocal
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["陪伴对话"])


# ── xia 分支辅助函数 ──

async def get_or_create_conversation(session, conv_id: int | None, first_message: str) -> Conversation:
    """获取或创建会话"""
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
    """从数据库构建对话历史"""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return [{"role": m.role, "content": m.content} for m in result.scalars()]


# ── POST /chat ──

@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    陪伴式 AI 对话：
    - 传 conversation_id → 续接已有会话（xia 模式，自动持久化）
    - 不传 conversation_id → 新建会话或无状态对话（si 兼容）
    """
    logger.info(f"收到对话: msg_len={len(req.message)}, conv_id={req.conversation_id}")

    # 判断使用哪种模式
    if req.conversation_id is not None:
        # ── xia 模式：会话持久化 ──
        try:
            async with AsyncSessionLocal() as session:
                conv = await get_or_create_conversation(session, req.conversation_id, req.message)

                # 保存用户消息
                user_msg = ChatMessage(conversation_id=conv.id, role="user", content=req.message)
                session.add(user_msg)
                await session.flush()

                # 构建历史
                history = await build_history(session, conv.id)
                full_messages = [{"role": "system", "content": CLOUDIE_SYSTEM_PROMPT}] + history

                try:
                    reply_text = await call_llm(full_messages)
                except Exception as e:
                    logger.error(f"LLM 调用失败: {e}")
                    reply_text = "我暂时无法回复，请稍后再试。"

                # 保存 AI 回复
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
            raise

    else:
        # ── si 模式：无状态对话（兼容旧前端） ──
        reply = await chat_with_system(
            user_message=req.message,
            history=req.history,
        )

        return ChatResponse(
            reply=reply,
            emotion=req.emotion_state,
            need_hint=None,
            conversation_id=None,
            message_id=None,
            tokens_used=0,
        )
