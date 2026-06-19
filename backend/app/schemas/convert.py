"""
NVC 破冰转换服务 —— 请求/响应规范化
"""
# 用于规范 NVC 转换接口的入参和出参


from pydantic import BaseModel, Field

class ConvertRequest(BaseModel):
    # 请求
    text: str = Field(..., min_length=1, max_length=500, description="需要转换的原始文本")


class ConvertResponse(BaseModel):
    # 响应
    original: str
    converted: str
    tokens_used: int = 0
    processing_time: float = 0.0
