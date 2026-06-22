"""
NVC 破冰转换接口 —— POST /convert
支持两种模式：json（四要素）/ spoken（口语化）
"""
import time
from fastapi import APIRouter
from app.schemas.convert import ConvertRequest, ConvertResponse
from app.services.nvc_service import convert_to_nvc, convert_text
from app.utils.logger import logger

router = APIRouter(prefix="/convert", tags=["破冰转换"])


@router.post("", response_model=ConvertResponse)
async def convert(request: ConvertRequest):
    """
    将原始文本转换为 NVC 表达：
    - mode=json（默认）：返回 observation/feeling/need/request 四要素
    - mode=spoken：返回一句话口语化表达
    """
    # 兼容旧前端 raw_text 字段
    text = request.raw_text or request.text
    start_time = time.time()
    logger.info(f"收到转换请求: text_len={len(text)}, mode={request.mode}")

    if request.mode == "spoken":
        # xia 风格：口语化输出
        try:
            converted = await convert_text(text)
            elapsed = round(time.time() - start_time, 2)
            return ConvertResponse(
                original=text,
                converted=converted,
                tokens_used=0,
                processing_time=elapsed,
            )
        except Exception as e:
            logger.error(f"口语化转换失败: {str(e)}")
            return ConvertResponse(
                original=text,
                converted="我理解你的感受，我们可以换一种更温和的方式来表达。",
                tokens_used=0,
                processing_time=0.0,
            )
    else:
        # si 风格：JSON 四要素（默认）
        try:
            result = await convert_to_nvc(text, request.emotion_hint)
            elapsed = round(time.time() - start_time, 2)
            # 拼接完整表达供前端展示
            full_expr_parts = [result.get("observation", "")]
            if result.get("feeling"):
                full_expr_parts.append(f"我感到{result['feeling']}")
            if result.get("need"):
                full_expr_parts.append(f"因为我需要{result['need']}")
            if result.get("request"):
                full_expr_parts.append(result["request"])
            full_expression = "，".join(filter(None, full_expr_parts))

            return ConvertResponse(
                observation=result.get("observation", ""),
                feeling=result.get("feeling", ""),
                need=result.get("need", ""),
                request=result.get("request"),
                emotion=result.get("emotion", "未知"),
                original=text,
                converted=full_expression,
                tokens_used=0,
                processing_time=elapsed,
            )
        except Exception as e:
            logger.error(f"JSON 转换失败: {str(e)}")
            return ConvertResponse(
                observation=text,
                feeling="",
                need="",
                request=None,
                emotion="未知",
                original=text,
                converted="",
                tokens_used=0,
                processing_time=0.0,
            )
