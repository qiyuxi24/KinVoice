"""
经验卡片接口 —— CRUD + 双向同步 + 对话收藏
GET    /cards              — 获取卡片列表
POST   /cards              — 创建卡片
PUT    /cards/{id}         — 更新卡片
DELETE /cards/{id}         — 删除卡片
POST   /cards/sync         — 双向同步（只增不减）
POST   /cards/favorite     — 收藏对话消息为卡片（xia 新增）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session, AsyncSessionLocal
from app.models.card import Card, ChatMessage
from app.schemas.memory import CardCreate, CardUpdate, CardOut, CardListOut, DeleteResponse
from app.utils.logger import logger

router = APIRouter(prefix="/cards", tags=["经验卡片"])


# ── GET /cards ──

@router.get("", response_model=CardListOut)
async def list_cards(
    category: str | None = Query(None, description="按分类筛选"),
    type: str | None = Query(None, description="按类型筛选: nvc/chat_message/chat_conversation"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """获取经验卡片列表"""
    stmt = select(Card)
    count_stmt = select(func.count(Card.id))

    if category:
        stmt = stmt.where(Card.category == category)
        count_stmt = count_stmt.where(Card.category == category)
    if type:
        stmt = stmt.where(Card.type == type)
        count_stmt = count_stmt.where(Card.type == type)

    stmt = stmt.order_by(Card.created_at.desc()).offset(offset).limit(limit)

    result = await session.execute(stmt)
    cards = result.scalars().all()

    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    return CardListOut(
        cards=[CardOut.model_validate(c) for c in cards],
        total=total,
    )


# ── POST /cards ──

@router.post("", response_model=CardOut, status_code=201)
async def create_card(
    data: CardCreate,
    session: AsyncSession = Depends(get_session),
):
    """创建新卡片（兼容 NVC + 对话收藏）"""
    orm_fields = {c.name for c in Card.__table__.columns}
    payload = {k: v for k, v in data.model_dump().items() if k in orm_fields and v is not None}

    # 默认 type 为 nvc（兼容旧前端不传 type 的情况）
    if "type" not in payload:
        payload["type"] = "nvc"

    card = Card(**payload)
    session.add(card)
    await session.flush()
    await session.refresh(card)
    logger.info(f"创建卡片: id={card.id}, type={card.type}, category={card.category}")
    return CardOut.model_validate(card)


# ── PUT /cards/{card_id} ──

@router.put("/{card_id}", response_model=CardOut)
async def update_card(
    card_id: int,
    data: CardUpdate,
    session: AsyncSession = Depends(get_session),
):
    """更新卡片"""
    result = await session.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")

    orm_fields = {c.name for c in Card.__table__.columns}
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in orm_fields:
            setattr(card, key, value)

    await session.flush()
    await session.refresh(card)
    logger.info(f"更新卡片: id={card_id}")
    return CardOut.model_validate(card)


# ── DELETE /cards/{card_id} ──

@router.delete("/{card_id}")
async def delete_card(
    card_id: int,
    session: AsyncSession = Depends(get_session),
):
    """删除卡片"""
    result = await session.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="卡片不存在")
    await session.delete(card)
    await session.flush()
    logger.info(f"删除卡片: id={card_id}")
    return DeleteResponse(success=True)


# ── 双向同步专用 schema ────────────────────────────────

class LocalCard(BaseModel):
    """前端本地缓存的卡片结构"""
    id: int | None = None
    tag: str = "人生阅历"
    date: str = ""
    title: str = ""
    author: str = "家人"
    content: str = ""
    emotion: str = "感慨"
    need: str = "记录与传承"
    # 以下为 xia 分支扩展字段，前端可能用到
    category: str | None = None
    observation: str | None = None
    feeling: str | None = None
    request: str | None = None


class SyncRequest(BaseModel):
    """前端发来的本地全部卡片"""
    cards: list[LocalCard] = Field(default_factory=list)


class SyncResult(BaseModel):
    """同步结果：合并后的完整卡片列表"""
    cards: list[LocalCard]
    added_to_backend: int = 0
    added_to_local: int = 0
    total: int


# ── POST /cards/sync ──

@router.post("/sync", response_model=SyncResult)
async def sync_cards(
    req: SyncRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    双向同步：只增不减
    1. 前端本地有 id 的卡片 → 后端不存在则创建
    2. 前端本地无 id 的卡片 → 创建到后端，分配 id
    3. 后端有但本地没有的卡片 → 返回给前端
    """
    result = await session.execute(select(Card).order_by(Card.created_at.desc()))
    db_cards = result.scalars().all()
    db_map: dict[int, Card] = {c.id: c for c in db_cards}

    local_ids: set[int] = {c.id for c in req.cards if c.id is not None}

    added_to_backend = 0
    added_to_local = 0

    # 步骤1：本地 → 后端
    for local in req.cards:
        if local.id is not None and local.id in db_map:
            continue
        card = Card(
            type="nvc",
            category=local.tag,
            emotion=local.emotion or "感慨",
            observation=local.title or "",
            feeling=local.content or "",
            need=local.need or "记录与传承",
            request=f"来自{local.author}" if local.author and local.author != "家人" else None,
            title=local.title or "",
            content=local.content or "",
            family_id=1,
        )
        session.add(card)
        await session.flush()
        await session.refresh(card)
        local.id = card.id
        if not local.date:
            local.date = card.created_at.strftime("%Y.%m.%d") if card.created_at else ""
        added_to_backend += 1
        logger.info(f"sync: 本地→后端 创建卡片 id={card.id} category={card.category}")

    # 步骤2：后端 → 本地
    merged = list(req.cards)
    for db_card in db_cards:
        if db_card.id not in local_ids:
            author = (db_card.request or "").replace("来自", "") or "家人"
            merged.append(LocalCard(
                id=db_card.id,
                tag=db_card.category or "人生阅历",
                date=db_card.created_at.strftime("%Y.%m.%d") if db_card.created_at else "",
                title=db_card.title or db_card.observation or "",
                author=author,
                content=db_card.content or "\n".join(filter(None, [db_card.feeling or "", db_card.need or ""])),
                emotion=db_card.emotion or "感慨",
                need=db_card.need or "记录与传承",
                category=db_card.category,
                observation=db_card.observation,
                feeling=db_card.feeling,
                request=db_card.request,
            ))
            added_to_local += 1

    await session.flush()
    logger.info(f"sync 完成: 本地→后端 +{added_to_backend}, 后端→本地 +{added_to_local}, 合并后共 {len(merged)} 张")

    return SyncResult(
        cards=sorted(merged, key=lambda c: c.id or 0, reverse=True),
        added_to_backend=added_to_backend,
        added_to_local=added_to_local,
        total=len(merged),
    )


# ── xia 新增：收藏对话消息 ────────────────────────────────

class FavoriteRequest(BaseModel):
    """收藏请求"""
    message_id: int = Field(..., description="要收藏的消息 ID")


@router.post("/favorite", response_model=CardOut, status_code=201)
async def favorite_message(
    req: FavoriteRequest,
):
    """
    将一条对话消息收藏为卡片（xia 新增）
    自动关联用户消息和 AI 回复
    """
    async with AsyncSessionLocal() as session:
        # 查询目标消息
        result = await session.execute(select(ChatMessage).where(ChatMessage.id == req.message_id))
        msg = result.scalar_one_or_none()
        if not msg:
            raise HTTPException(status_code=404, detail="消息不存在")
        if msg.role != "assistant":
            raise HTTPException(status_code=400, detail="只能收藏 AI 回复")

        # 找到对应的用户消息
        user_result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == msg.conversation_id)
            .where(ChatMessage.role == "user")
            .where(ChatMessage.created_at < msg.created_at)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        user_msg = user_result.scalar_one_or_none()

        # 创建卡片
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
        logger.info(f"收藏消息 {req.message_id} → 卡片 id={card.id}")
        return CardOut.model_validate(card)
