"""
DatabaseMessageSource —— 从 SQLite 数据库提取指定用户的对话消息

通过 JOIN conversations 表按 user_id 过滤，确保只提取当前用户的 AI 对话消息。
聊天室消息（conversations.user_id IS NULL）不会被提取到个人档案中。
"""
from datetime import date
from sqlalchemy import select
from app.models.card import ChatMessage, Conversation
from app.db.session import AsyncSessionLocal
from app.utils.logger import logger


class DatabaseMessageSource:
    """
    从数据库 chat_messages 表提取指定用户今日的消息。

    使用方式：
        source = DatabaseMessageSource()
        messages = await source.fetch_today_messages("user-xxx")
    """

    async def fetch_today_messages(self, user_id: str) -> list[dict]:
        """
        获取今日属于该用户的 AI 对话消息，按时间正序。

        Args:
            user_id: 用户标识

        Returns:
            [{role, content, created_at}, ...]
        """
        today = date.today()
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(ChatMessage)
                .join(Conversation, ChatMessage.conversation_id == Conversation.id)
                .where(
                    Conversation.user_id == user_id,
                    Conversation.type == "ai",
                    ChatMessage.created_at >= today,
                )
                .order_by(ChatMessage.created_at.asc())
            )
            messages = result.scalars().all()

        logger.info(f"提取用户 {user_id} 今日消息: {len(messages)} 条")
        return [
            {
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ]
