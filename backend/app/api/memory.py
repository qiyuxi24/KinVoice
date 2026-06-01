"""
经验卡片接口 —— CRUD
GET /cards         — 获取卡片列表
POST /cards        — 创建卡片
DELETE /cards/{id} — 删除卡片
"""
from fastapi import APIRouter, Depends, HTTPException, Query
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
    card = Card(**data.model_dump())
    session.add(card)
    await session.flush()
    await session.refresh(card)
    logger.info(f"创建卡片: id={card.id}, emotion={card.emotion}")
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
