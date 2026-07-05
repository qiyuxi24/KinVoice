"""
家庭成员档案接口 —— CRUD
GET    /profiles          — 获取全部档案列表
POST   /profiles          — 创建档案
PUT    /profiles/{id}     — 更新档案
DELETE /profiles/{id}     — 删除档案
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.profile import FamilyMember
from app.schemas.profile import ProfileCreate, ProfileUpdate, ProfileOut, ProfileListOut
from app.utils.logger import logger

router = APIRouter(prefix="/profiles", tags=["家庭成员档案"])


@router.get("", response_model=ProfileListOut)
async def list_profiles(
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
        total=total,
    )


@router.post("", response_model=ProfileOut, status_code=201)
async def create_profile(
    data: ProfileCreate,
    session: AsyncSession = Depends(get_session),
):
    """创建家庭成员档案"""
    member = FamilyMember(**data.model_dump())
    session.add(member)
    await session.flush()
    await session.refresh(member)
    logger.info(f"创建档案: id={member.id}, name={member.name}, relation={member.relation}")
    return ProfileOut.model_validate(member)


@router.put("/{profile_id}", response_model=ProfileOut)
async def update_profile(
    profile_id: int,
    data: ProfileUpdate,
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


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: int,
    session: AsyncSession = Depends(get_session),
):
    """删除家庭成员档案"""
    result = await session.execute(select(FamilyMember).where(FamilyMember.id == profile_id))
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=404, detail="档案不存在")
    await session.delete(member)
    logger.info(f"删除档案: id={profile_id}")
