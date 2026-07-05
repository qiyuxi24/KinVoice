"""
<<<<<<< HEAD
家庭成员档案接口 —— CRUD
GET    /profiles          — 获取全部档案列表
POST   /profiles          — 创建档案
PUT    /profiles/{id}     — 更新档案
DELETE /profiles/{id}     — 删除档案
=======
用户个人文档接口 —— CRUD（按 user_id 隔离）

GET    /profiles          — 获取当前用户的全部文档列表
POST   /profiles          — 创建文档
PUT    /profiles/{id}     — 更新文档
DELETE /profiles/{id}     — 删除文档

设计决策：
- 所有操作通过 X-User-Id Header 注入 user_id，实现数据隔离
- 用户只能操作自己的文档，不能跨用户访问
>>>>>>> si
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
<<<<<<< HEAD
from app.models.profile import FamilyMember
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileOut, ProfileListOut
from app.utils.logger import logger

router = APIRouter(prefix="/profiles", tags=["家庭成员档案"])
=======
from app.models.profile import UserDocument
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileOut, ProfileListOut
from app.middleware.user_identity import get_user_id
from app.utils.logger import logger

router = APIRouter(prefix="/profiles", tags=["用户个人文档"])
>>>>>>> si


@router.get("", response_model=ProfileListOut)
async def list_profiles(
<<<<<<< HEAD
    session: AsyncSession = Depends(get_session),
):
    """获取全部家庭成员档案（按创建时间倒序）"""
    stmt = select(FamilyMember).order_by(FamilyMember.created_at.desc())
    result = await session.execute(stmt)
    members = result.scalars().all()

    count_result = await session.execute(select(func.count(FamilyMember.id)))
    total = count_result.scalar() or 0

    return ProfileListOut(
        profiles=[ProfileOut.model_validate(m) for m in members],
=======
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
>>>>>>> si
        total=total,
    )


@router.post("", response_model=ProfileOut, status_code=201)
async def create_profile(
    data: ProfileCreate,
<<<<<<< HEAD
    session: AsyncSession = Depends(get_session),
):
    """创建家庭成员档案"""
    member = FamilyMember(**data.model_dump())
    session.add(member)
    await session.flush()
    await session.refresh(member)
    logger.info(f"创建档案: id={member.id}, name={member.name}, relation={member.relation}")
    return ProfileOut.model_validate(member)
=======
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
>>>>>>> si


@router.put("/{profile_id}", response_model=ProfileOut)
async def update_profile(
    profile_id: int,
    data: ProfileUpdate,
<<<<<<< HEAD
    session: AsyncSession = Depends(get_session),
):
    """更新家庭成员档案"""
    result = await session.execute(select(FamilyMember).where(FamilyMember.id == profile_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="档案不存在")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(member, key, value)

    await session.flush()
    await session.refresh(member)
    logger.info(f"更新档案: id={profile_id}, name={member.name}")
    return ProfileOut.model_validate(member)
=======
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
>>>>>>> si


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: int,
<<<<<<< HEAD
    session: AsyncSession = Depends(get_session),
):
    """删除家庭成员档案"""
    result = await session.execute(select(FamilyMember).where(FamilyMember.id == profile_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="档案不存在")
    await session.delete(member)
    logger.info(f"删除档案: id={profile_id}")
=======
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
>>>>>>> si
