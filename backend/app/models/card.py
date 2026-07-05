"""
定义"经验卡片"的数据库表结构 (ORM 映射) 以及 Conversation, ChatMessage
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.session import Base


class Conversation(Base):
    """对话会话"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=True, comment="会话标题（取第一条消息前50字）")
    family_id = Column(Integer, default=1)
    # 聊天室扩展字段（家庭组成员互聊，与 AI 对话解耦）
    type = Column(String(20), default="ai", comment="会话类型: ai(默认)/private(私聊)/group(群聊)")
    sender_id = Column(String(36), nullable=True, comment="私聊发起者 user_id")
    receiver_id = Column(String(36), nullable=True, comment="私聊接收者 user_id")
    is_favorited = Column(Boolean, default=False, comment="整个会话是否被收藏")
    created_at = Column(DateTime, server_default=func.now())

    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        order_by="ChatMessage.created_at"
    )


class ChatMessage(Base):
    """聊天消息"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    role = Column(String(36), nullable=False, comment="user/assistant 或聊天室 sender_id")
    content = Column(Text, nullable=False)
    is_favorited = Column(Boolean, default=False, comment="单条消息是否被收藏")
    created_at = Column(DateTime, server_default=func.now())

    conversation = relationship("Conversation", back_populates="messages")


class Card(Base):
    """
    经验卡片 —— 支持多种类型
    - type="nvc": NVC 四要素卡片（兼容旧数据）
    - type="chat_message": 收藏的单条对话消息
    - type="chat_conversation": 收藏的整个对话
    """
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 卡片类型
    type = Column(String(20), nullable=False, default="nvc",
                  comment="卡片类型: nvc / chat_message / chat_conversation")

    # NVC 专用字段（兼容旧数据，允许为空）
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

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type,
            "category": self.category,
            "emotion": self.emotion,
            "observation": self.observation,
            "feeling": self.feeling,
            "need": self.need,
            "request": self.request,
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "title": self.title,
            "content": self.content,
            "original_text": self.original_text,
            "family_id": self.family_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
