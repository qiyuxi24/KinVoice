"""
经验卡片 —— CRUD 请求/响应模型
"""
from datetime import datetime
from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    """创建卡片"""
    category: str = Field("通用", max_length=50)
    emotion: str = Field(..., max_length=100)
    observation: str = Field(...)
    feeling: str = Field(...)
    need: str = Field(...)
    request: str | None = None


class CardUpdate(BaseModel):
    """更新卡片（全字段可选）"""
    category: str | None = Field(None, max_length=50)
    emotion: str | None = Field(None, max_length=100)
    observation: str | None = None
    feeling: str | None = None
    need: str | None = None
    request: str | None = None


class CardOut(BaseModel):
    """卡片响应"""
    id: int
    category: str
    emotion: str
    observation: str
    feeling: str
    need: str
    request: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CardListOut(BaseModel):
    """卡片列表响应"""
    cards: list[CardOut]
    total: int
