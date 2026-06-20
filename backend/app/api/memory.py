"""
经验卡片接口 —— CRUD + 双向同步
GET    /cards          — 获取卡片列表
POST   /cards          — 创建卡片
PUT    /cards/{id}     — 更新卡片
DELETE /cards/{id}     — 删除卡片
POST   /cards/sync     — 双向同步（只增不减）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.card import Card
from app.schemas.memory import CardCreate, CardUpdate, CardOut, CardListOut
from app.utils.logger import logger

router = APIRouter(prefix="/cards", tags=["经验卡片"])


@router.get("", response_model=CardListOut)
async def list_cards(
    category: str | None = Query(None, description="按分类筛选"),
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

    stmt = stmt.order_by(Card.created_at.desc()).offset(offset).limit(limit)

    result = await session.execute(stmt)
    cards = result.scalars().all()

    total_result = await session.execute(count_stmt)
    total = total_result.scalar() or 0

    return CardListOut(
        cards=[CardOut.model_validate(c) for c in cards],
        total=total,
    )


@router.post("", response_model=CardOut, status_code=201)
async def create_card(
    data: CardCreate,
    session: AsyncSession = Depends(get_session),
):
    """创建新卡片"""
    # 只取 ORM 实际存在的字段，过滤掉前端额外字段（title/content/author/tag）
    orm_fields = {c.name for c in Card.__table__.columns}
    payload = {k: v for k, v in data.model_dump().items() if k in orm_fields and v is not None}

    card = Card(**payload)
    session.add(card)
    await session.flush()
    await session.refresh(card)
    logger.info(f"创建卡片: id={card.id}, category={card.category}, emotion={card.emotion}")
    return CardOut.model_validate(card)


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

    # 只更新 ORM 存在的字段，过滤掉前端额外字段
    orm_fields = {c.name for c in Card.__table__.columns}
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in orm_fields:
            setattr(card, key, value)

    await session.flush()
    await session.refresh(card)
    logger.info(f"更新卡片: id={card_id}")
    return CardOut.model_validate(card)


@router.delete("/{card_id}", status_code=204)
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
    logger.info(f"删除卡片: id={card_id}")


# ── 双向同步专用 schema ────────────────────────────────


class LocalCard(BaseModel):
    """前端本地缓存的卡片结构"""
    # 有 id 表示从后端同步过的；无 id 表示离线新增的
    id: int | None = None
    tag: str = "人生阅历"
    date: str = ""
    title: str = ""
    author: str = "家人"
    content: str = ""
    emotion: str = "感慨"
    need: str = "记录与传承"


class SyncRequest(BaseModel):
    """前端发来的本地全部卡片"""
    cards: list[LocalCard] = Field(default_factory=list)


class SyncResult(BaseModel):
    """同步结果：合并后的完整卡片列表（前端可直接渲染）"""
    cards: list[LocalCard]
    added_to_backend: int = 0      # 从本地新增到后端的数量
    added_to_local: int = 0        # 从后端新增到本地的数量
    total: int


@router.post("/sync", response_model=SyncResult)
async def sync_cards(
    req: SyncRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    双向同步：只增不减
    1. 前端本地有 id 的卡片 → 如果后端存在则跳过，如果后端不存在则创建到后端
    2. 前端本地无 id 的卡片 → 创建到后端，分配 id
    3. 后端有但本地没有的卡片 → 返回给前端，前端追加到本地
    合并后的完整列表返回给前端保存
    """
    # 获取后端全部卡片
    result = await session.execute(select(Card).order_by(Card.created_at.desc()))
    db_cards = result.scalars().all()
    db_map: dict[int, Card] = {c.id: c for c in db_cards}

    # 收集本地有 id 的卡片
    local_ids: set[int] = {c.id for c in req.cards if c.id is not None}

    added_to_backend = 0
    added_to_local = 0

    # ── 步骤1：把本地卡片同步到后端 ──
    for local in req.cards:
        if local.id is not None and local.id in db_map:
            # 后端已存在，跳过（只增不减，不覆盖）
            continue
        # 本地没有 id 或 id 在后端不存在 → 创建到后端
        card = Card(
            category=local.tag,
            emotion=local.emotion or "感慨",
            observation=local.title or "",
            feeling=local.content or "",
            need=local.need or "记录与传承",
            request=f"来自{local.author}" if local.author and local.author != "家人" else None,
        )
        session.add(card)
        await session.flush()
        await session.refresh(card)
        # 更新本地对象的 id
        local.id = card.id
        if local.date:
            pass  # date 保留本地值
        else:
            local.date = card.created_at.strftime("%Y.%m.%d") if card.created_at else ""
        added_to_backend += 1
        logger.info(f"sync: 本地→后端 创建卡片 id={card.id} category={card.category}")

    # ── 步骤2：把后端有但本地没有的卡片加到本地列表 ──
    merged = list(req.cards)
    for db_card in db_cards:
        if db_card.id not in local_ids:
            # 后端有、本地没有 → 追加到结果
            merged.append(LocalCard(
                id=db_card.id,
                tag=db_card.category or "人生阅历",
                date=db_card.created_at.strftime("%Y.%m.%d") if db_card.created_at else "",
                title=db_card.observation or "",
                author=(db_card.request or "").replace("来自", "") or "家人",
                content="\n".join(filter(None, [db_card.feeling, db_card.need])),
                emotion=db_card.emotion or "感慨",
                need=db_card.need or "记录与传承",
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
