"""
Chat 接口 —— 陪伴式 AI 对话
兼容 si 无状态模式 + xia 会话持久化模式 + 历史记录管理
"""
import asyncio
import re
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, delete
from app.services.llm_service import call_llm, chat_with_system
from app.services.cloudie_prompt import build_system_prompt
from app.services.profile_writer import read_profiles, update_stable_profile
from app.services.search_service import search_context
from app.schemas.chat import (
    ChatRequest, ChatResponse,
    ConversationListOut, ConversationOut,
    HistoryOut, MessageOut,
)
from app.models.card import Conversation, ChatMessage
from app.db.session import AsyncSessionLocal
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["陪伴对话"])

# 匹配 [MEMORY_UPDATE] 标记
MEMORY_TRIGGER = re.compile(r'\[MEMORY_UPDATE\]')


# ── xia 分支辅助函数 ──

async def get_or_create_conversation(session, conv_id: int | None, first_message: str) -> Conversation:
    """获取或创建会话（仅限 AI 对话类型）"""
    if conv_id:
        result = await session.execute(
            select(Conversation).where(
                Conversation.id == conv_id,
                Conversation.type == "ai",
            )
        )
        conv = result.scalar_one_or_none()
        if conv:
            return conv
        raise HTTPException(status_code=404, detail="会话不存在或不是 AI 对话")
    title = first_message[:50] if first_message else "新对话"
    conv = Conversation(title=title, type="ai")
    session.add(conv)
    await session.flush()
    return conv


async def build_history(session, conv_id: int) -> list[dict]:
    """从数据库构建对话历史"""
    result = await session.execute(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv_id)
        .order_by(ChatMessage.created_at.asc())
    )
    return [{"role": m.role, "content": m.content} for m in result.scalars()]


# ── POST /chat ──

@router.post("", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    陪伴式 AI 对话 —— 统一使用 xia 模式（会话持久化）
    - 首次对话：不传 conversation_id（或传 null）→ 自动新建会话，返回新 conversation_id
    - 续接对话：传上次返回的 conversation_id → 加载历史，追加新消息
    - 兼容 si：传 history 时仍走无状态模式（旧前端过渡期保留）
    """
    logger.info(f"收到对话: user_id={user_id}, msg_len={len(req.message)}, conv_id={req.conversation_id}, family_id={req.family_id}")

    # ① 加载用户画像（始终注入）
    user_profile = read_profiles(user_id)

    # ② FTS5 检索家庭卡片 + 对话历史
    ctx = ""
    if req.family_id:
        try:
            async with AsyncSessionLocal() as search_session:
                ctx = await search_context(search_session, req.message, user_id, req.family_id)
        except Exception as e:
            logger.warning(f"FTS 检索异常（降级忽略）: {e}")

    # ③ 拼接 system prompt（画像 + 检索上下文）
    system_prompt = build_system_prompt(user_profile, ctx)

    # si 兼容：如果显式传了 history 且没有 conversation_id，走无状态模式
    if req.history and req.conversation_id is None:
        reply = await chat_with_system(
            user_message=req.message,
            history=req.history,
            system_prompt=system_prompt,
        )
        # si 模式不支持记忆提取（无会话持久化）
        return ChatResponse(
            reply=reply,
            emotion=req.emotion_state,
            need_hint=None,
            conversation_id=None,
            message_id=None,
            tokens_used=0,
        )

    # ── xia 模式：会话持久化（默认路径） ──
    try:
        async with AsyncSessionLocal() as session:
            conv = await get_or_create_conversation(session, req.conversation_id, req.message)

            # 保存用户消息
            user_msg = ChatMessage(conversation_id=conv.id, role="user", content=req.message)
            session.add(user_msg)
            await session.flush()

            # 构建历史（含系统提示词 + 用户画像 + 检索上下文）
            history = await build_history(session, conv.id)
            full_messages = [{"role": "system", "content": system_prompt}] + history

            try:
                reply_text = await call_llm(full_messages)
            except Exception as e:
                logger.error(f"LLM 调用失败: {e}")
                reply_text = "我暂时无法回复，请稍后再试。"

            # 检测记忆更新标记
            should_extract = bool(MEMORY_TRIGGER.search(reply_text))
            # 去掉标记，用户看不到
            clean_reply = MEMORY_TRIGGER.sub("", reply_text).strip()

            # 保存 AI 回复（干净版本）
            asst_msg = ChatMessage(conversation_id=conv.id, role="assistant", content=clean_reply)
            session.add(asst_msg)
            await session.commit()
            await session.refresh(asst_msg)

            # 异步触发记忆提取（不阻塞回复）
            if should_extract:
                asyncio.create_task(_run_memory_extraction(conv.id, history, user_id))

            return ChatResponse(
                reply=clean_reply,
                conversation_id=conv.id,
                message_id=asst_msg.id,
                tokens_used=0,
            )
    except Exception as e:
        logger.error(f"聊天接口异常: {str(e)}")
        raise


# ── GET /chat/conversations ──

@router.get("/conversations", response_model=ConversationListOut)
async def list_conversations():
    """列出所有会话（按创建时间倒序）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation).order_by(Conversation.created_at.desc())
        )
        convs = result.scalars().all()
        return ConversationListOut(
            conversations=[
                ConversationOut(id=c.id, title=c.title, created_at=c.created_at)
                for c in convs
            ]
        )


# ── GET /chat/history ──

@router.get("/history", response_model=HistoryOut)
async def get_history(conversation_id: int):
    """拉取某个会话的全部消息历史"""
    async with AsyncSessionLocal() as session:
        # 验证会话存在且为 AI 对话类型（隔离聊天室会话）
        conv_result = await session.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.type == "ai",
            )
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="会话不存在或不是 AI 对话")

        # 按时间正序拉取消息
        msg_result = await session.execute(
            select(ChatMessage)
            .where(ChatMessage.conversation_id == conversation_id)
            .order_by(ChatMessage.created_at.asc())
        )
        messages = msg_result.scalars().all()

        return HistoryOut(
            conversation_id=conversation_id,
            messages=[
                MessageOut(id=m.id, role=m.role, content=m.content, created_at=m.created_at)
                for m in messages
            ]
        )


# ── DELETE /chat/conversations/{conv_id} ──

@router.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: int):
    """删除会话及其所有关联消息（硬删除）"""
    async with AsyncSessionLocal() as session:
        conv_result = await session.execute(
            select(Conversation).where(Conversation.id == conv_id)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            raise HTTPException(status_code=404, detail="会话不存在")

        # 先删消息，再删会话（外键约束）
        await session.execute(
            delete(ChatMessage).where(ChatMessage.conversation_id == conv_id)
        )
        await session.delete(conv)
        await session.commit()

        logger.info(f"已删除会话 {conv_id} 及其消息")
        return {"ok": True, "deleted_id": conv_id}


# ── 后台记忆提取 ──

async def _run_memory_extraction(conv_id: int, history: list[dict], user_id: str):
    """后台任务：从当前对话提取记忆，更新固定档案"""
    try:
        logger.info(f"开始记忆提取: conv_id={conv_id}, user_id={user_id}")
        result = await update_stable_profile(user_id, history)
        if result.get("ok"):
            logger.info(f"记忆提取完成: user_id={user_id}, preview={result.get('content_preview', '')[:100]}")
        else:
            logger.warning(f"记忆提取未成功: user_id={user_id}, preview={result.get('content_preview', '')}")
    except Exception as e:
        logger.error(f"记忆提取后台任务异常: conv_id={conv_id}, {e}")
