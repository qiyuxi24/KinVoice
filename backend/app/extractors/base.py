"""
提取源接口定义 —— 所有消息来源必须实现此协议
"""
from typing import Protocol


class MessageSource(Protocol):
    """
    消息提取源接口。

    所有实现必须提供 fetch_today_messages 方法，
    返回今日的对话消息列表。
    """

    async def fetch_today_messages(self, user_id: str) -> list[dict]:
        """
        获取用户今日的对话消息。

        Args:
            user_id: 用户标识（当前为 "default"）

        Returns:
            [{role: "user"|"assistant", content: str, created_at: str}, ...]
            按时间正序排列
        """
        ...
