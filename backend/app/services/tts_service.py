"""
语音合成服务 —— 占位，后期集成 Azure TTS
"""
from app.utils.logger import logger


async def synthesize_speech(text: str, voice: str = "zh-CN-XiaoxiaoNeural") -> bytes | None:
    """
    将文本转换为语音（后期实现）
    Args:
        text: 要合成的文本
        voice: 语音名称
    Returns:
        音频字节流，暂返回 None
    """
    logger.info(f"TTS 请求（占位）: voice={voice}, text_len={len(text)}")
    return None
