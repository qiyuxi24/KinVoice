"""
NVC 破冰转换 —— 请求/响应模型
兼容 si JSON 四要素 + xia 口语化输出
"""
from pydantic import BaseModel, Field


class ConvertRequest(BaseModel):
    """NVC 破冰转换请求（兼容 si text / xia raw_text 两种字段名）"""
    text: str | None = Field(None, max_length=2000, description="需要转换的原始文本（新前端）")
    # si 旧字段
    raw_text: str | None = Field(None, max_length=2000, description="原始发言文本（兼容旧前端）")
    emotion_hint: str | None = Field(None, description="情绪提示（可选）")
    # xia 模式选择
    mode: str = Field(default="json", description="输出模式: json（四要素）| spoken（口语化）")


class ConvertResponse(BaseModel):
    """NVC 破冰转换响应（兼容两种模式）"""
    # si JSON 模式字段
    observation: str | None = None
    feeling: str | None = None
    need: str | None = None
    request: str | None = None
    emotion: str | None = None
    # xia 口语化模式字段
    original: str | None = None
    converted: str | None = None
    tokens_used: int = 0
    processing_time: float = 0.0
