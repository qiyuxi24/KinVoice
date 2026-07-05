"""
AI 档案编写 —— 请求/响应模型
"""
from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    """AI 档案更新请求（user_id 由 X-User-Id Header 传递，不在此模型中）"""
    pass


class ProfileUpdateResponse(BaseModel):
    """AI 档案更新响应"""
    ok: bool
    profile_type: str = Field(description="stable 或 dynamic")
    path: str = Field(description="写入的文件路径")
    content_preview: str = Field(default="", description="新内容前 200 字预览")
    messages_used: int = Field(default=0, description="用于提取的消息条数")


class ProfileReadResponse(BaseModel):
    """读取档案响应"""
    user_id: str
    stable: str = Field(default="", description="固定档案 Markdown 内容")
    dynamic: str = Field(default="", description="动态档案 Markdown 内容")
