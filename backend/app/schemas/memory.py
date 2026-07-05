"""
经验卡片 + 文件夹 —— 请求/响应模型
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════
# 文件夹
# ═══════════════════════════════════════════════════

class FolderCreate(BaseModel):
    """创建文件夹"""
    name: str = Field(..., min_length=1, max_length=50, description="文件夹名称")

class FolderOut(BaseModel):
    """文件夹响应"""
    id: int
    name: str
    family_id: str = "1"
    note_count: int = 0
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

class FolderListOut(BaseModel):
    """文件夹列表"""
    folders: list[FolderOut]

# ═══════════════════════════════════════════════════
# 卡片
# ═══════════════════════════════════════════════════

class CardCreate(BaseModel):
    """创建卡片"""
    type: str = Field(default="simple", description="卡片类型: simple/chat_message/chat_conversation")
    title: str = Field(default="", max_length=200, description="标题")
    content: str = Field(default="", description="正文")
    category: str = Field(default="", max_length=50, description="分类标签（兼容旧数据）")
    emotion: str = Field(default="感慨", max_length=100, description="情绪标签")
    author: str = Field(default="我", max_length=100, description="作者/讲述人")
    folder_id: Optional[int] = Field(None, description="所属文件夹 ID")
    # 兼容旧字段
    observation: Optional[str] = None
    feeling: Optional[str] = None
    need: Optional[str] = None
    request: Optional[str] = None
    tag: Optional[str] = Field(None, max_length=50)
    # 对话收藏
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    original_text: Optional[str] = None
    family_id: int = Field(default=1)


class CardUpdate(BaseModel):
    """更新卡片（全字段可选）"""
    type: Optional[str] = None
    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    emotion: Optional[str] = Field(None, max_length=100)
    author: Optional[str] = Field(None, max_length=100)
    folder_id: Optional[int] = None
    # 兼容旧字段
    observation: Optional[str] = None
    feeling: Optional[str] = None
    need: Optional[str] = None
    request: Optional[str] = None
    tag: Optional[str] = Field(None, max_length=50)


class CardOut(BaseModel):
    """卡片响应"""
    id: int
    type: str = "simple"
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    emotion: Optional[str] = None
    author: Optional[str] = None
    folder_id: Optional[int] = None
    # NVC 兼容
    observation: Optional[str] = None
    feeling: Optional[str] = None
    need: Optional[str] = None
    request: Optional[str] = None
    # 对话收藏
    conversation_id: Optional[int] = None
    message_id: Optional[int] = None
    original_text: Optional[str] = None
    family_id: int = 1
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
