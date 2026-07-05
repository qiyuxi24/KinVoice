"""
用户个人文档 Pydantic Schema
"""
from pydantic import BaseModel, Field
from datetime import datetime


# ── 创建 ──
class ProfileCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="文档标题")
    tags: str = Field(default="", max_length=200, description="标签，逗号分隔")
    content_md: str = Field(default="", description="Markdown 正文")


# ── 更新（全可选）──
class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    tags: str | None = Field(default=None, max_length=200)
    content_md: str | None = Field(default=None)


# ── 输出 ──
class ProfileOut(BaseModel):
    id: int
    user_id: str
    name: str
    tags: str
    content_md: str
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ProfileListOut(BaseModel):
    profiles: list[ProfileOut]
    total: int
