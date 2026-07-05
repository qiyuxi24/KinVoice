"""
用户个人文档接口 —— CRUD (按 user_id 隔离)

GET    /profiles          — 获取当前用户的全部文档列表
POST   /profiles          — 创建文档
PUT    /profiles/{id}     — 更新文档
DELETE /profiles/{id}     — 删除文档

设计决策：
- 所有操作通过 X-User-Id Header 注入 user_id, 实现数据隔离
- 用户只能操作自己的文档，不能跨用户访问
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.profile import UserDocument
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileOut, ProfileListOut
from app.middleware.user_identity import get_user_id
from app.utils.logger import logger

router = APIRouter(prefix="/profiles", tags=["用户个人文档"])


@router.get("", response_model=ProfileListOut)
async def list_profiles(
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """获取当前用户的全部文档（按创建时间倒序）"""
    stmt = (
        select(UserDocument)
        .where(UserDocument.user_id == user_id)
        .order_by(UserDocument.created_at.desc())
    )
    result = await session.execute(stmt)
    documents = result.scalars().all()

    count_stmt = select(func.count(UserDocument.id)).where(UserDocument.user_id == user_id)
    count_result = await session.execute(count_stmt)
    total = count_result.scalar() or 0

    return ProfileListOut(
        profiles=[ProfileOut.model_validate(d) for d in documents],
        total=total,
    )


@router.post("", response_model=ProfileOut, status_code=201)
async def create_profile(
    data: ProfileCreate,
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """创建个人文档"""
    doc = UserDocument(
        user_id=user_id,
        name=data.name,
        tags=data.tags,
        content_md=data.content_md,
    )
    session.add(doc)
    await session.flush()
    await session.refresh(doc)
    logger.info(f"创建文档: id={doc.id}, user_id={user_id}, name={doc.name}")
    return ProfileOut.model_validate(doc)


@router.put("/{profile_id}", response_model=ProfileOut)
async def update_profile(
    profile_id: int,
    data: ProfileUpdate,
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """更新个人文档（仅允许操作自己的文档）"""
    result = await session.execute(
        select(UserDocument).where(
            UserDocument.id == profile_id,
            UserDocument.user_id == user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(doc, key, value)

    await session.flush()
    await session.refresh(doc)
    logger.info(f"更新文档: id={profile_id}, user_id={user_id}, name={doc.name}")
    return ProfileOut.model_validate(doc)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: int,
    user_id: str = Depends(get_user_id),
    session: AsyncSession = Depends(get_session),
):
    """删除个人文档（仅允许删除自己的文档）"""
    result = await session.execute(
        select(UserDocument).where(
            UserDocument.id == profile_id,
            UserDocument.user_id == user_id,
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    await session.delete(doc)
    logger.info(f"删除文档: id={profile_id}, user_id={user_id}")