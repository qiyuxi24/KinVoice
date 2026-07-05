"""
AI 档案编写接口

POST /profile/ai/update-dynamic  — 从今日对话自动更新动态档案（Companion onHide 调用）
POST /profile/ai/update-stable   — 更新固定档案（Profile 页面手动触发）
GET  /profile/ai/read            — 读取用户档案
"""
from fastapi import APIRouter, Depends
from app.schemas.profile_ai import ProfileUpdateRequest, ProfileUpdateResponse, ProfileReadResponse
from app.services.profile_writer import update_dynamic_profile, update_stable_profile, read_profiles
from app.extractors import DatabaseMessageSource
from app.middleware.user_identity import get_user_id
from app.utils.logger import logger

router = APIRouter(prefix="/profile/ai", tags=["AI档案编写"])

# 提取源 —— 当前使用数据库，以后可替换
_message_source = DatabaseMessageSource()


@router.post("/update-dynamic", response_model=ProfileUpdateResponse)
async def update_dynamic(req: ProfileUpdateRequest, user_id: str = Depends(get_user_id)):
    """
    从今日对话中提取信息，更新动态档案。

    前端在 Companion 页面 onHide 时调用此接口。
    只提取今天的对话，静默执行，失败不影响主流程。
    """
    logger.info(f"动态档案更新请求: user_id={user_id}")

    try:
        messages = await _message_source.fetch_today_messages(user_id)
    except Exception as e:
        logger.error(f"提取今日消息失败: {e}")
        return ProfileUpdateResponse(
            ok=False,
            profile_type="dynamic",
            path="",
            content_preview=f"提取消息失败: {str(e)}",
            messages_used=0,
        )

    result = await update_dynamic_profile(user_id, messages)
    return ProfileUpdateResponse(**result)


@router.post("/update-stable", response_model=ProfileUpdateResponse)
async def update_stable(req: ProfileUpdateRequest, user_id: str = Depends(get_user_id)):
    """
    从全部对话历史中提取固定信息，更新固定档案。

    前端在 Profile 页面手动触发。
    会读取所有历史消息（最近 200 条），全量重写固定档案。
    """
    logger.info(f"固定档案更新请求: user_id={user_id}")

    try:
        # 固定档案需要更长的历史，取最近 200 条
        messages = await _message_source.fetch_today_messages(user_id)
        # 如果今日消息太少，尝试从数据库取更多（暂时用今日的，后续可扩展）
    except Exception as e:
        logger.error(f"提取消息失败: {e}")
        return ProfileUpdateResponse(
            ok=False,
            profile_type="stable",
            path="",
            content_preview=f"提取消息失败: {str(e)}",
            messages_used=0,
        )

    result = await update_stable_profile(user_id, messages)
    return ProfileUpdateResponse(**result)


@router.get("/read", response_model=ProfileReadResponse)
async def read_profile(user_id: str = Depends(get_user_id)):
    """
    读取用户档案（固定 + 动态两份 Markdown）。
    """
    data = read_profiles(user_id)
    return ProfileReadResponse(**data)
