"""
Memory 接口的 Pydantic 模型
"""
"""
记忆卡片 / 收藏相关 Schema
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CardCreate(BaseModel):
    """手动创建 NVC 卡片"""
    category: str = Field(default="通用", description="分类")
    emotion: str = Field(..., description="情绪关键词")
    observation: str = Field(..., description="观察")
    feeling: str = Field(..., description="感受")
    need: str = Field(..., description="需要")
    request: Optional[str] = Field(None, description="请求")
    family_id: int = Field(default=1)


class CardResponse(BaseModel):
    id: int
    type: str

    # NVC 字段
    category: Optional[str] = None
    emotion: Optional[str] = None
    observation: Optional[str] = None
    feeling: Optional[str] = None
    need: Optional[str] = None
    request: Optional[str] = None

    # 对话收藏字段
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    title: Optional[str] = None
    content: Optional[str] = None
    original_text: Optional[str] = None

    family_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DeleteResponse(BaseModel):
    success: bool