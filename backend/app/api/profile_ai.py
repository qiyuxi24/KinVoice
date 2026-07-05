"""
AI 档案编写接口

POST /profile/ai/extract      — 从对话中提取信息，更新用户档案（前端在聊天后调用）
GET  /profile/ai/read          — 读取用户档案

user_id 统一通过 X-User-Id Header 传递（Depends(get_user_id)）。
"""
from fastapi import APIRouter, Depends
from app.schemas.profile_ai import (
    ProfileExtractRequest, ProfileExtractResponse,
    ProfileReadResponse,
)
from app.services.profile_writer import update_dynamic_profile, update_stable_profile, read_profiles
from app.middleware.user_identity import get_user_id
from app.utils.logger import logger

router = APIRouter(prefix="/profile/ai", tags=["AI档案编写"])


@router.post("/extract", response_model=ProfileExtractResponse)
async def extract_from_chat(
    req: ProfileExtractRequest,
    user_id: str = Depends(get_user_id),
):
    """
    从对话消息中提取信息，更新用户档案。

    前端在 Companion 页面聊天后调用此接口，传入最近的对话消息。
    支持 stable（固定信息）和 dynamic（动态信息）两种类型。

    此接口独立于聊天流程，有自己独立的 AI prompt（profile_writer.STABLE_SYSTEM_PROMPT /
    DYNAMIC_SYSTEM_PROMPT），与 Cloudie 聊天 AI 完全解耦。
    """
    logger.info(f"档案提取请求: user_id={user_id}, type={req.profile_type}, msgs={len(req.messages)}")

    if not req.messages:
        return ProfileExtractResponse(
            ok=False,
            profile_type=req.profile_type,
            path="",
            content_preview="（无对话消息，跳过提取）",
            messages_used=0,
        )

    # 转换消息格式
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    try:
        if req.profile_type == "stable":
            result = await update_stable_profile(user_id, messages)
        else:
            result = await update_dynamic_profile(user_id, messages)
    except Exception as e:
        logger.error(f"档案提取失败: {e}")
        return ProfileExtractResponse(
            ok=False,
            profile_type=req.profile_type,
            path="",
            content_preview=f"提取失败: {str(e)}",
            messages_used=len(messages),
        )

    return ProfileExtractResponse(**result)


@router.get("/read", response_model=ProfileReadResponse)
async def read_profile(user_id: str = Depends(get_user_id)):
    """
    读取用户档案（固定 + 动态两份 Markdown）。

    user_id 通过 X-User-Id Header 传入，与项目其他接口保持一致。
    """
    data = read_profiles(user_id)
    return ProfileReadResponse(**data)
