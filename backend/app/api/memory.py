"""
经验卡片接口 —— CRUD
GET /cards         — 获取卡片列表
POST /cards        — 创建卡片
DELETE /cards/{id} — 删除卡片
"""

# main.py 依赖：(调用api即可)
#   └── api/memory.py (router)

# api/memory.py(中枢) 依赖：
#   ├── db/session.py (AsyncSessionLocal)
#   ├── schemas/memory.py (CardCreate, CardResponse, DeleteResponse)
#   └── models/card.py (Card)

# schemas/memory.py 依赖：
#   └── pydantic (BaseModel)


from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.card import Card, Conversation, ChatMessage
from app.schemas.memory import CardCreate, CardResponse, DeleteResponse
from app.utils.logger import logger

router = APIRouter(prefix="/cards", tags=["经验卡片"])


# 原有 CRUD
@router.get("", response_model=list[CardResponse])
async def get_cards(family_id: int = 1):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Card).where(Card.family_id == family_id).order_by(Card.created_at.desc())
        )
        return result.scalars().all()


@router.post("", response_model=CardResponse, status_code=201)
async def create_card(card: CardCreate):
    async with AsyncSessionLocal() as session:
        new_card = Card(
            type="nvc",
            category=card.category,
            emotion=card.emotion,
            observation=card.observation,
            feeling=card.feeling,
            need=card.need,
            request=card.request,
            family_id=card.family_id,
        )
        session.add(new_card)
        await session.commit()
        await session.refresh(new_card)
        logger.info(f"手动创建 NVC 卡片 id={new_card.id}")
        return new_card


@router.delete("/{card_id}", response_model=DeleteResponse)
async def delete_card(card_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Card).where(Card.id == card_id))
        card = result.scalar_one_or_none()
        if not card:
            raise HTTPException(status_code=404, detail="卡片不存在")
        await session.delete(card)
        await session.commit()
        logger.info(f"删除卡片 id={card_id}")
        return DeleteResponse(success=True)


# 收藏整个会话
@router.post("/from-conversation/{conv_id}", response_model=CardResponse, status_code=201)
async def create_card_from_conversation(conv_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Conversation).where(Conversation.id == conv_id))
        conv = result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="会话不存在")

        conv.is_favorited = True

        msg_result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conv_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = msg_result.scalars().all()

        content_lines = []
        original_text = None
        for m in messages:
            if m.role == "user" and original_text is None:
                original_text = m.content
            role_label = "我" if m.role == "user" else "Cloudie"
            content_lines.append(f"{role_label}：{m.content}")

        content = "\n".join(content_lines)
        title = conv.title or (original_text[:50] if original_text else "收藏的对话")

        card = Card(
            type="chat_conversation",
            conversation_id=conv.id,
            title=title,
            content=content,
            original_text=original_text,
            family_id=conv.family_id,
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        logger.info(f"收藏会话 {conv_id} → 卡片 id={card.id}")
        return card


# 收藏单条 AI 回复
@router.post("/from-chat/{message_id}", response_model=CardResponse, status_code=201)
async def create_card_from_chat(message_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ChatMessage).where(ChatMessage.id == message_id))
        msg = result.scalar_one_or_none()
        if not msg or msg.role != "assistant":
            raise HTTPException(status_code=404, detail="消息不存在或不是助手回复")

        user_result = await session.execute(
            select(ChatMessage)
            .where(
                ChatMessage.conversation_id == msg.conversation_id,
                ChatMessage.role == "user",
                ChatMessage.created_at < msg.created_at
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        user_msg = user_result.scalar_one_or_none()

        msg.is_favorited = True

        card = Card(
            type="chat_message",
            message_id=msg.id,
            conversation_id=msg.conversation_id,
            title="收藏的 AI 回复",
            content=msg.content,
            original_text=user_msg.content if user_msg else None,
            family_id=1,
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        logger.info(f"收藏消息 {message_id} → 卡片 id={card.id}")
        return card