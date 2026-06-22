"""
Chat 接口的 Pydantic 模型 —— 数据校验
兼容 si 旧字段 + xia 新字段
"""
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """对话请求（兼容两种模式）"""
    message: str = Field(..., min_length=1, description="用户消息")
    # si 旧字段（兼容）
    history: list[dict] | None = Field(None, description="对话历史 [{role, content}, ...]")
    emotion_state: str | None = Field(None, description="当前情绪状态")
    # xia 新字段
    conversation_id: int | None = Field(None, description="会话 ID, 不传则新建会话")


class ChatResponse(BaseModel):
    """对话响应"""
    reply: str = Field(..., description="AI 回复")
    # si 旧字段（兼容）
    emotion: str | None = Field(None, description="识别到的用户情绪")
    need_hint: str | None = Field(None, description="推测的潜在需求（NVC 角度）")
    # xia 新字段
    conversation_id: int | None = None
    message_id: int | None = None
    tokens_used: int = 0
