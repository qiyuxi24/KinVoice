"""
陪伴对话 —— 请求/响应模型
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """陪伴对话请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    history: list[dict] | None = Field(
        None, description="对话历史 [{role, content}, ...]"
    )
    emotion_state: str | None = Field(None, description="当前情绪状态")


class ChatResponse(BaseModel):
    """陪伴对话响应"""
    reply: str = Field(..., description="AI 回复")
    emotion: str | None = Field(None, description="识别到的用户情绪")
    need_hint: str | None = Field(None, description="推测的潜在需求（NVC 角度）")
