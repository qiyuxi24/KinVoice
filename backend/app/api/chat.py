"""
chat 接口---注意与session.py(用于数据库读写)的区分, 该部分属于用户端与AI模型的的直接对话
"""


from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from app.services.llm_service import call_llm
from app.services.cloudie_prompt import CLOUDIE_SYSTEM_PROMPT
from app.schemas.chat import ChatRequest, ChatResponse
from app.models.card import Conversation, ChatMessage
from app.db.session import AsyncSessionLocal
from app.utils.logger import logger

from app.middleware.user_identity import get_user_id

router = APIRouter(tags=["陪伴对话"])


async def get_or_create_conversation(session, conv_id: int | None, first_message: str, user_id: str) -> Conversation:
    if conv_id:
        result = await session.execute(select(Conversation).where(Conversation.id == conv_id))
        conv = result.scalar_one_or_none()
        if conv:
            return conv
        # 如果传入的 conv_id 不存在，fallback 到自动复用
        logger.warning(f"传入的会话 {conv_id} 不存在，尝试自动复用")

    # ✅ 自动复用该用户最近一次会话（不再排除 user_id="1"）
    result = await session.execute(
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.created_at.desc())
        .limit(1)
    )
    recent = result.scalar_one_or_none()
    if recent:
        logger.info(f"自动复用会话 id={recent.id} for user={user_id}")
        return recent

    # 确实没有历史会话，新建并关联用户
    title = first_message[:50] if first_message else "新对话"
    conv = Conversation(title=title, user_id=user_id)
    session.add(conv)
    await session.flush()
    logger.info(f"新建会话 id={conv.id} for user={user_id}")
    return conv

# ── 构建历史消息列表（仅数据库记录） ──
async def build_history(session, conv_id: int) -> list[dict]:
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return [{"role": m.role, "content": m.content} for m in result.scalars()]

# ── POST /chat ──
@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, user_id: str = Depends(get_user_id)):
    try:
        async with AsyncSessionLocal() as session:
            # 自动复用或创建会话
            conv = await get_or_create_conversation(
                session, request.conversation_id, request.message, user_id
            )

            # 保存用户消息
            user_msg = ChatMessage(conversation_id=conv.id, role="user", content=request.message)
            session.add(user_msg)
            await session.flush()

            # 构建完整对话历史（包含系统提示词）
            history = await build_history(session, conv.id)
            full_messages = [{"role": "system", "content": CLOUDIE_SYSTEM_PROMPT}] + history

            # 调用大模型
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

# ── GET /chat/conversations ──
@router.get("/conversations")
async def list_conversations(user_id: str = Depends(get_user_id)):
    """获取当前用户的会话列表（按时间倒序）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.created_at.desc())
        )
        convs = result.scalars().all()
        return {
            "conversations": [
                {
                    "id": c.id,
                    "title": c.title,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                }
                for c in convs
            ]
        }

# ── GET /chat/history ──
@router.get("/history")
async def get_history(conversation_id: int = Query(...), user_id: str = Depends(get_user_id)):
    """获取某个会话的完整消息历史"""
    async with AsyncSessionLocal() as session:
        # 验证会话属于当前用户
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="会话不存在或无权访问")

        msgs = await build_history(session, conversation_id)
        return {
            "conversation_id": conversation_id,
            "messages": msgs
        }

# ── DELETE /chat/conversations/{conversation_id} ──
@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int, user_id: str = Depends(get_user_id)):
    """删除指定会话及其所有消息（硬删除）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id
            )
        )
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="会话不存在或无权操作")

        # 先删消息，再删会话（外键约束）
        await session.execute(
            delete(ChatMessage).where(ChatMessage.conversation_id == conversation_id)
        )
        await session.delete(conv)
        await session.commit()
        logger.info(f"用户 {user_id} 删除会话 {conversation_id}")
        return {"ok": True, "deleted_id": conversation_id}