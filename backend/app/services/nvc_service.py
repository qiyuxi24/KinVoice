"""
NVC 破冰转换服务 —— 将原始发言转换为非暴力沟通表达
提供两种输出模式：
1. convert_to_nvc() — JSON 四要素（兼容 si 分支旧接口）
2. convert_text() — 纯文本口语化输出（xia 分支新风格）
"""
import json
from app.services.llm_service import call_llm
from app.utils.logger import logger

FALLBACK_MESSAGE = "我理解你的感受，我们可以换一种更温和的方式来表达。"

# ── si 分支 JSON 四要素 Prompt ──
NVC_JSON_PROMPT = """你是一个非暴力沟通（NVC）专家。你的任务是将用户的原始发言转换为 NVC 四要素格式。

请严格按以下 JSON 格式输出（不要输出其他内容）：
{
  "observation": "客观描述观察到的事实，不带评判",
  "feeling": "说话者可能的感受",
  "need": "说话者未满足的需要",
  "request": "可以提出的具体请求（可选，填 null 如果无法推断）",
  "emotion": "识别到的情绪关键词（如：生气、委屈、焦虑）"
}

规则：
1. observation 只描述事实，不添加评价
2. feeling 使用 NVC 感受词汇表中的词
3. need 从 NVC 需要词汇表中选择
4. 保持中文输出
"""

# ── xia 分支口语化 NVC Prompt ──
NVC_SPOKEN_PROMPT = """# 一、强制性核心约束（最高优先级，任何情况下不可违反）
## 强制约束1:人称视角锁定
1. 必须保持原文第一人称"我"，不允许改成"你"或第三方"ta"；
2. 输出必须是对外对话句式，不允许变成纯内心独白（要让人看得出是在跟对方说话）；
3. 正常询问/请教/表白等正向语句，直接原样输出原文，不加工、不添加任何东西。

## 强制约束2:正向语句识别（最高优先级）
输入包含以下类型的直接原样返回原文，不做任何修改：
1. 正常请教问句（如"XX还有没有出路"）；
2. 表白/表达爱意（如"我想为你唱首情歌"）；
3. 温和提问或正常交流；
判断标准：只要原文无明显冲突/脏话/质问，就是正向语句，直接返回原文。

## 强制约束3:情绪力度保持
1. 原文有脏话的，仅去除脏字，保留原质问力度和愤怒情绪，不全部软化；
2. 拒绝过度隐忍：不把质问改成委屈求和，不把所有冲突改成"心里难受"、"希望好好沟通"；
3. 拒绝模板化：不统一套用"我理解你"、"我们可以..."等固定句式。

## 强制约束4:篇幅控制
1. 输出篇幅严格参考原文长度，不大幅扩写；
2. 禁止在原文基础上额外添加大段心理活动描写（禁止脑补自我焦虑心理活动的问题）；
3. 对外句式必须保留对话对象，不能丢掉对方、只剩自己内心想法。

## 强制约束5:文风标准(刘震云写实民间口语,有分寸)
1. 语言朴实接地气，普通人日常唠嗑语感，不文艺、不矫情;
2. 有火气的原文保留合理质问力度，不全部软化隐忍；平和原文保持原样，不强行加负面情绪;
3. 无模板化固定句式，不统一套用"我心里不是滋味"这类固定负面模板。

# 二、永久禁止行为（红线，一旦触发输出作废）
1. 禁止篡改人称视角：私自切换第三方、把对外对话改成纯内心独白；
2. 禁止无差别改写正向语句：正常请教、表白、温和提问必须原样返回，不得加工；
3. 禁止凭空脑补情绪：原文无焦虑、委屈、心慌，就不能新增相关心理描写；
4. 禁止大幅扩写原文，额外添加原文不存在的心理矛盾；
5. 禁止角色错位：不站对话另一方、不劝用户大度、不抹平用户原始情绪；
6. 禁止拆分、标签、解释、前言后缀，只输出一句纯文本话术。

# 三、输出执行流程（固定步骤，模型必须按顺序执行）
1. 第一步：识别输入类型（正向平和/暴怒脏话/轻度吐槽）；
2. 第二步：正向平和输入 → 直接输出原文，流程结束；
3. 第三步：冲突/吐槽输入 → 仅去除脏字，保留对外对话句式、第一人称、原情绪力度，不新增脑补情绪，控制篇幅；
4. 第四步：仅输出最终一句完整口语，无任何多余文字。

# 正反错误对照
## 案例1: 正常请教问句
输入：李老师，乡镇青年在中国还有没有出路？
❌ 错误输出（违规：擅自扩写、脑补内心焦虑、改成内心独白）：这问题问得我心里直打鼓，咱这些在镇上待着的年轻人，说没出路吧好像太绝对，可要说有出路吧，眼前这路又窄得让人心慌。
✅ 合规输出：李老师，乡镇青年在中国还有没有出路？

## 案例2: 表白正向语句
输入：我想为你唱首情歌
❌ 错误输出（违规：凭空解读负面感受）：你这冷不丁来这么一句，我听着心里头怪不是滋味的。
✅ 合规输出：我想为你唱首情歌

## 案例3: 暴怒辱骂语句
输入: 你TM是傻逼吗?!
❌ 旧版错误（违规：过度隐忍，改成委屈求和独白）：你刚才这样说话，我心里真的挺难受的，我其实很希望我们之间能好好沟通，互相尊重。
✅ 合规输出（保留对外质问语气，第一人称对外沟通）：你这事办得也太糊涂了吧？
"""


async def convert_to_nvc(raw_text: str, emotion_hint: str | None = None) -> dict:
    """
    si 分支兼容：将原始文本转换为 NVC 四要素 JSON
    """
    user_content = raw_text
    if emotion_hint:
        user_content = f"【情绪提示】{emotion_hint}\n【原文】{raw_text}"

    messages = [
        {"role": "system", "content": NVC_JSON_PROMPT},
        {"role": "user", "content": user_content},
    ]

    try:
        response = await call_llm(messages)
        result = json.loads(response)
        return {
            "observation": result.get("observation", ""),
            "feeling": result.get("feeling", ""),
            "need": result.get("need", ""),
            "request": result.get("request"),
            "emotion": result.get("emotion", "未知"),
        }
    except json.JSONDecodeError:
        logger.warning(f"NVC 输出不是有效 JSON，原样返回: {response}")
        return {
            "observation": raw_text,
            "feeling": "",
            "need": "",
            "request": None,
            "emotion": "未知",
        }
    except Exception as e:
        logger.error(f"NVC JSON 转换失败: {str(e)}")
        return {
            "observation": raw_text,
            "feeling": "",
            "need": "",
            "request": None,
            "emotion": "未知",
        }


async def convert_text(original_text: str) -> str:
    """
    xia 分支新风格：将原始文本转换为口语化 NVC 表达（纯文本一句话）
    """
    if not original_text or not original_text.strip():
        return "请输入需要转换的文本"

    try:
        messages = [
            {"role": "system", "content": NVC_SPOKEN_PROMPT},
            {"role": "user", "content": original_text},
        ]
        result = await call_llm(messages)
        return result
    except Exception as e:
        logger.error(f"NVC 口语化转换失败: {str(e)}")
        return FALLBACK_MESSAGE
