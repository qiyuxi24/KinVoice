"""
Chat 接口的 Pydantic 模型--数据校验
"""
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1,description="用户消息")
    conversation_id: int | None = Field(None, description="会话 ID, 不传则新建会话")

class ChatResponse(BaseModel):
    reply: str
    conversation_id: int
    message_id: int | None = None       # 本次助手回复的消息 ID
    tokens_used: int = 0