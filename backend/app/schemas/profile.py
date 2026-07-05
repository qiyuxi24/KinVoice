"""
<<<<<<< HEAD
家庭成员档案 Pydantic Schema
=======
用户个人文档 Pydantic Schema
>>>>>>> si
"""
from pydantic import BaseModel, Field
from datetime import datetime


# ── 创建 ──
class ProfileCreate(BaseModel):
<<<<<<< HEAD
    name: str = Field(..., min_length=1, max_length=100, description="姓名")
    relation: str = Field(default="家人", max_length=50, description="关系")
    birth_date: str | None = Field(default=None, max_length=20, description="生日 YYYY-MM-DD")
    avatar_url: str | None = Field(default=None, max_length=500, description="头像链接")
=======
    name: str = Field(..., min_length=1, max_length=100, description="文档标题")
    tags: str = Field(default="", max_length=200, description="标签，逗号分隔")
>>>>>>> si
    content_md: str = Field(default="", description="Markdown 正文")


# ── 更新（全可选）──
class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
<<<<<<< HEAD
    relation: str | None = Field(default=None, max_length=50)
    birth_date: str | None = Field(default=None, max_length=20)
    avatar_url: str | None = Field(default=None, max_length=500)
=======
    tags: str | None = Field(default=None, max_length=200)
>>>>>>> si
    content_md: str | None = Field(default=None)


# ── 输出 ──
class ProfileOut(BaseModel):
    id: int
<<<<<<< HEAD
    name: str
    relation: str
    birth_date: str | None
    avatar_url: str | None
=======
    user_id: str
    name: str
    tags: str
>>>>>>> si
    content_md: str
    created_at: datetime | None
    updated_at: datetime | None

    model_config = {"from_attributes": True}


class ProfileListOut(BaseModel):
    profiles: list[ProfileOut]
    total: int
