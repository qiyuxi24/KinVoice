"""
经验卡片 —— CRUD 请求/响应模型
兼容 si 旧格式 + xia 多类型卡片
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    """创建卡片（兼容 NVC + 对话收藏）"""
    # NVC 字段
    category: str = Field(default="通用", max_length=50)
    emotion: str = Field(default="感慨", max_length=100)
    observation: str = Field(default="")
    feeling: str = Field(default="")
    need: str = Field(default="")
    request: Optional[str] = None
    # 前端额外携带的展示字段（si 兼容）
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100)
    tag: Optional[str] = Field(None, max_length=50)
    # xia 新增
    type: str = Field(default="nvc", description="卡片类型: nvc/chat_message/chat_conversation")
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    original_text: Optional[str] = None
    family_id: str = Field(default="1")


class CardUpdate(BaseModel):
    """更新卡片（全字段可选）"""
    category: Optional[str] = Field(None, max_length=50)
    emotion: Optional[str] = Field(None, max_length=100)
    observation: Optional[str] = None
    feeling: Optional[str] = None
    need: Optional[str] = None
    request: Optional[str] = None
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    author: Optional[str] = Field(None, max_length=100)
    tag: Optional[str] = Field(None, max_length=50)
    type: Optional[str] = None


class CardOut(BaseModel):
    """卡片响应（si 兼容）"""
    id: int
    type: str = "nvc"
    category: Optional[str] = None
    emotion: Optional[str] = None
    observation: Optional[str] = None
    feeling: Optional[str] = None
    need: Optional[str] = None
    request: Optional[str] = None
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    original_text: Optional[str] = None
    family_id: str = "1"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CardListOut(BaseModel):
    """卡片列表响应"""
    cards: list[CardOut]
    total: int


class DeleteResponse(BaseModel):
    """删除响应"""
    success: bool
