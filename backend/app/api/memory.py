"""
笔记文件夹 + 卡片接口（精简版）
文件夹: GET/POST /folders（只创建和列表，不重命名/删除）
卡片:   GET/POST/PUT/DELETE /cards  +  /cards/sync  +  /cards/favorite
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session, AsyncSessionLocal
from app.models.card import Card, ChatMessage, Conversation
from app.models.folder import Folder
from app.schemas.memory import (
    FolderCreate, FolderOut, FolderListOut,
    CardCreate, CardUpdate, CardOut, CardListOut, DeleteResponse,
)
from app.middleware.user_identity import get_user_id
from app.services.family_service import get_user_family_id
from app.utils.logger import logger

router = APIRouter(tags=["笔记+文件夹"])


# ── 辅助 ─────────────────────────────────────────────

async def resolve_family_id(user_id: str) -> str:
    async with AsyncSessionLocal() as session:
        fid = await get_user_family_id(session, user_id)
        return fid if fid is not None else "1"


# ═══════════════════════════════════════════════════
#  文件夹 CRUD
# ═══════════════════════════════════════════════════

@router.get("/folders", response_model=FolderListOut)
async def list_folders(
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_user_id),
):
    """获取当前家庭组的所有文件夹（含笔记计数）"""
    family_id = await resolve_family_id(user_id)

    # 查文件夹
    f_result = await session.execute(
        select(Folder).where(Folder.family_id == family_id).order_by(Folder.created_at.asc())
    )
    folders = f_result.scalars().all()

    # 统计每个文件夹的笔记数
    out_list = []
    for f in folders:
        cnt_result = await session.execute(
            select(func.count(Card.id)).where(Card.folder_id == f.id, Card.family_id == family_id)
        )
        count = cnt_result.scalar() or 0
        out_list.append(FolderOut(
            id=f.id,
            name=f.name,
            family_id=f.family_id,
            note_count=count,
            created_at=f.created_at,
        ))

    return FolderListOut(folders=out_list)


@router.post("/folders", response_model=FolderOut, status_code=201)
async def create_folder(
    data: FolderCreate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_user_id),
):
    """创建新文件夹"""
    family_id = await resolve_family_id(user_id)
    folder = Folder(name=data.name, family_id=family_id)
    session.add(folder)
    await session.flush()
    await session.refresh(folder)
    logger.info(f"创建文件夹: id={folder.id} name={folder.name}")
    return FolderOut(id=folder.id, name=folder.name, family_id=family_id, note_count=0)


# ═══════════════════════════════════════════════════
#  卡片 CRUD
# ═══════════════════════════════════════════════════

@router.get("/cards", response_model=CardListOut)
async def list_cards(
    folder_id: int | None = Query(None, description="按文件夹筛选，不传则返回全部"),
    type: str | None = Query(None, description="按类型筛选"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_user_id),
):
    """获取笔记列表（按 family_id 隔离，可选按文件夹筛选）"""
    family_id = await resolve_family_id(user_id)

    stmt = select(Card).where(Card.family_id == family_id)
    count_stmt = select(func.count(Card.id)).where(Card.family_id == family_id)

    if folder_id is not None:
        if folder_id == 0:
            stmt = stmt.where(Card.folder_id.is_(None))
            count_stmt = count_stmt.where(Card.folder_id.is_(None))
        else:
            stmt = stmt.where(Card.folder_id == folder_id)
            count_stmt = count_stmt.where(Card.folder_id == folder_id)

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


@router.post("/cards", response_model=CardOut, status_code=201)
async def create_card(
    data: CardCreate,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_user_id),
):
    """创建新笔记"""
    family_id = await resolve_family_id(user_id)
    orm_fields = {c.name for c in Card.__table__.columns}
    payload = {k: v for k, v in data.model_dump().items() if k in orm_fields and v is not None}

    if "type" not in payload:
        payload["type"] = "nvc"

    # 动态注入 family_id（覆盖前端可能传的值）
    payload["family_id"] = family_id if family_id is not None else 1

    card = Card(**payload)
    session.add(card)
    await session.flush()
    await session.refresh(card)
    logger.info(f"创建笔记: id={card.id} title={card.title} folder_id={card.folder_id}")
    return CardOut.model_validate(card)


@router.put("/cards/{card_id}", response_model=CardOut)
async def update_card(
    card_id: int,
    data: CardUpdate,
    session: AsyncSession = Depends(get_session),
):
    """更新笔记"""
    result = await session.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="笔记不存在")

    orm_fields = {c.name for c in Card.__table__.columns}
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key in orm_fields:
            setattr(card, key, value)

    await session.flush()
    await session.refresh(card)
    logger.info(f"更新笔记: id={card_id}")
    return CardOut.model_validate(card)


@router.delete("/cards/{card_id}")
async def delete_card(
    card_id: int,
    session: AsyncSession = Depends(get_session),
):
    """删除笔记"""
    result = await session.execute(select(Card).where(Card.id == card_id))
    card = result.scalar_one_or_none()
    if not card:
        raise HTTPException(status_code=404, detail="笔记不存在")
    await session.delete(card)
    await session.flush()
    logger.info(f"删除笔记: id={card_id}")
    return DeleteResponse(success=True)


# ═══════════════════════════════════════════════════
#  双向同步
# ═══════════════════════════════════════════════════

class LocalCard(BaseModel):
    """前端本地卡片结构"""
    id: int | None = None
    tag: str = ""
    title: str = ""
    content: str = ""
    author: str = "我"
    emotion: str = "感慨"
    date: str = ""
    folder_id: int | None = None


class SyncRequest(BaseModel):
    cards: list[LocalCard] = Field(default_factory=list)


class SyncResult(BaseModel):
    cards: list[LocalCard]
    added_to_backend: int = 0
    added_to_local: int = 0
    total: int


@router.post("/cards/sync", response_model=SyncResult)
async def sync_cards(
    req: SyncRequest,
    session: AsyncSession = Depends(get_session),
    user_id: str = Depends(get_user_id),
):
    """双向同步：只增不减"""
    family_id = await resolve_family_id(user_id)
    # ensure family_id is resolved to a concrete value
    family_id = family_id if family_id is not None else 1

    result = await session.execute(
        select(Card).where(Card.family_id == family_id).order_by(Card.created_at.desc())
    )
    db_cards = result.scalars().all()
    db_map: dict[int, Card] = {c.id: c for c in db_cards}
    local_ids: set[int] = {c.id for c in req.cards if c.id is not None}

    added_to_backend = 0
    added_to_local = 0

    # 本地 → 后端
    for local in req.cards:
        if local.id is not None and local.id in db_map:
            continue
        card = Card(
            type="simple",
            title=local.title or "",
            content=local.content or "",
            author=local.author or "我",
            emotion=local.emotion or "感慨",
            folder_id=local.folder_id,
            family_id=family_id,
        )
        session.add(card)
        await session.flush()
        await session.refresh(card)
        local.id = card.id
        if not local.date:
            local.date = card.created_at.strftime("%Y.%m.%d") if card.created_at else ""
        added_to_backend += 1

    # 后端 → 本地
    merged = list(req.cards)
    for db_card in db_cards:
        if db_card.id not in local_ids:
            merged.append(LocalCard(
                id=db_card.id,
                date=db_card.created_at.strftime("%Y.%m.%d") if db_card.created_at else "",
                title=db_card.title or "",
                content=db_card.content or "",
                author=db_card.author or "我",
                emotion=db_card.emotion or "感慨",
                folder_id=db_card.folder_id,
            ))
            added_to_local += 1

    await session.flush()
    logger.info(f"sync: →后端 +{added_to_backend}, →本地 +{added_to_local}, 合并 {len(merged)} 条")

    return SyncResult(
        cards=sorted(merged, key=lambda c: c.id or 0, reverse=True),
        added_to_backend=added_to_backend,
        added_to_local=added_to_local,
        total=len(merged),
    )


# ═══════════════════════════════════════════════════
#  收藏对话消息
# ═══════════════════════════════════════════════════

class FavoriteRequest(BaseModel):
    message_id: int = Field(..., description="要收藏的消息 ID")


@router.post("/cards/favorite", response_model=CardOut, status_code=201)
async def favorite_message(
    req: FavoriteRequest,
    user_id: str = Depends(get_user_id),
):
    """
    将一条对话消息收藏为卡片（xia 新增）
    自动关联用户消息和 AI 回复
    """
    family_id = await resolve_family_id(user_id)
    family_id = family_id if family_id is not None else 1

    async with AsyncSessionLocal() as session:
        # 查询目标消息
        result = await session.execute(
            select(ChatMessage)
            .join(Conversation, ChatMessage.conversation_id == Conversation.id)
            .where(ChatMessage.id == req.message_id, Conversation.user_id == user_id)
        )
        msg = result.scalar_one_or_none()
        if not msg:
            raise HTTPException(status_code=404, detail="消息不存在")
        if msg.role != "assistant":
            raise HTTPException(status_code=400, detail="只能收藏 AI 回复")

        user_result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == msg.conversation_id)
            .where(ChatMessage.role == "user")
            .where(ChatMessage.created_at < msg.created_at)
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
        )
        user_msg = user_result.scalar_one_or_none()

        card = Card(
            type="chat_message",
            message_id=msg.id,
            conversation_id=msg.conversation_id,
            title="收藏的 AI 回复",
            content=msg.content,
            original_text=user_msg.content if user_msg else None,
            family_id=family_id,
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        logger.info(f"收藏消息 {req.message_id} → 笔记 id={card.id}")
        return CardOut.model_validate(card)
