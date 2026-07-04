"""
提取源抽象层 —— 从不同来源提取对话历史
当前实现：DatabaseMessageSource（从 SQLite messages 表读取）
未来可扩展：APIMessageSource、FileMessageSource 等
"""
from app.extractors.base import MessageSource
from app.extractors.database import DatabaseMessageSource

__all__ = ["MessageSource", "DatabaseMessageSource"]
