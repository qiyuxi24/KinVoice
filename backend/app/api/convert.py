"""
NVC 破冰转换服务接口 —— POST /convert
"""
# 负责将用户输入的原始文本传入nvc_service.py进行处理，同时负责将处理后的文本返回给前端用户


import time
from fastapi import APIRouter
from app.schemas.convert import ConvertRequest, ConvertResponse
from app.services.nvc_service import convert_text
from app.utils.logger import logger

router = APIRouter(tags=["破冰转换"])


@router.post("/convert", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    start_time = time.time()
    logger.info(f"收到转换请求: {request.text}")
    try:
        converted = await convert_text(request.text)
        elapsed = round(time.time() - start_time, 2)
        return ConvertResponse(
            original=request.text,
            converted=converted,
            tokens_used=0,
            processing_time=elapsed,
        )
    except Exception as e:
        logger.error(f"转换失败，使用降级预设: {str(e)}")
        return ConvertResponse(
            original=request.text,
            converted="我理解你的感受，我们可以换一种更温和的方式来表达。",
            tokens_used=0,
            processing_time=0.0,
        )