"""
经验卡片 —— CRUD 请求/响应模型
"""
from datetime import datetime
from pydantic import BaseModel, Field


class CardCreate(BaseModel):
    """创建卡片"""
    category: str = Field("通用", max_length=50)
    emotion: str = Field(default="感慨", max_length=100)
    observation: str = Field(default="")
    feeling: str = Field(default="")
    need: str = Field(default="")
    request: str | None = None
    # 前端额外携带的展示字段（存入对应 NVC 字段）
    title: str | None = Field(None, max_length=200)
    content: str | None = None
    author: str | None = Field(None, max_length=100)
    tag: str | None = Field(None, max_length=50)


class CardUpdate(BaseModel):
    """更新卡片（全字段可选）"""
    category: str | None = Field(None, max_length=50)
    emotion: str | None = Field(None, max_length=100)
    observation: str | None = None
    feeling: str | None = None
    need: str | None = None
    request: str | None = None
    title: str | None = Field(None, max_length=200)
    content: str | None = None
    author: str | None = Field(None, max_length=100)
    tag: str | None = Field(None, max_length=50)


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
