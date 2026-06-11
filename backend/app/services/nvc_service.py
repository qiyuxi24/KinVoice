"""
NVC 破冰转换服务 —— 将原始发言转换为非暴力语言( NVC: Nonviolent Communication)
"""
# 接收来自api\convert.py传入的用户端的原始文本，进行调用模型llm_service.py进行处理


from app.services.llm_service import chat, FALLBACK_MESSAGE
from app.utils.logger import logger

NVC_SYSTEM_PROMPT = """你是一位专业的非暴力沟通(NVC)语言转换专家。

你的任务是把用户输入的、可能带有攻击性或负面情绪的话语, 转换成温和、尊重、建设性的表达;
一定要注意你是"替身"，你只是在帮用户完成他所说的话的非暴力转换，从而让对话更加和谐融洽易于建立有效沟通.

转换规则：
1. 使用"观察-感受-需要-请求"四步法
2. 保留原意，但用更温和的方式表达
3. 不要添加原句没有的内容
4. 不要评价或批评用户的原始表达
5. 直接返回转换后的文本，不要加任何解释或前缀
"""


async def convert_text(original_text: str) -> str:
    if not original_text or not original_text.strip():
        return "请输入需要转换的文本"

    try:
        result = await chat(prompt=original_text, system_prompt=NVC_SYSTEM_PROMPT)
        return result
    except Exception as e:
        logger.error(f"NVC 转换失败: {str(e)}")
        return FALLBACK_MESSAGE