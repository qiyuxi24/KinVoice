"""
定义"经验卡片"的数据库表结构card(利用 ORM 映射) 以及 Conversation, ChatMessage
"""

# 目前实现的是对于nvc记录的手动存储与对于conversation和chatmessage这两个数据库表(定义于models/chat.py)的关联


from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=True)          # 将第一条消息作为标题
    family_id = Column(Integer, default=1)
    is_favorited = Column(Boolean, default=False, comment="整个会话是否被收藏")
    created_at = Column(DateTime, server_default=func.now())

    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)           # "user" 或 "assistant"
    content = Column(Text, nullable=False)
    is_favorited = Column(Boolean, default=False, comment="单条消息是否被收藏")
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")


class Card(Base):
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 卡片类型
    type = Column(String(20), nullable=False, default="nvc",
                  comment="卡片类型: nvc / chat_message / chat_conversation")

    # NVC 专用字段
    category = Column(String(50), nullable=True, comment="分类（感受/需要/行动/通用）")
    emotion = Column(String(100), nullable=True, comment="情绪关键词")
    observation = Column(Text, nullable=True, comment="观察（事实描述）")
    feeling = Column(Text, nullable=True, comment="感受")
    need = Column(Text, nullable=True, comment="需要")
    request = Column(Text, nullable=True, comment="请求")

    # 对话收藏专用字段
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id"), nullable=True)
    title = Column(String(200), nullable=True, comment="卡片标题")
    content = Column(Text, nullable=True, comment="卡片正文（自动拼接或单条消息）")
    original_text = Column(Text, nullable=True, comment="原始用户文本（可选）")

    # 通用
    family_id = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    message = relationship("ChatMessage", foreign_keys=[message_id])