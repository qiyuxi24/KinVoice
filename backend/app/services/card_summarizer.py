"""
对话总结 → 经验卡片 服务
从多轮对话中提取 NVC 经验，与知识库比对后决定新建或追加
"""
import json
from app.services.llm_service import call_llm
from app.utils.logger import logger

# ── LLM Prompt ────────────────────────────────────────────
SUMMARIZE_SYSTEM_PROMPT = """你是一个家庭记忆整理师。你的任务是从家庭对话中提取有价值的经验，整理成知识卡片。

## 卡片格式（NVC 四要素）
每张卡片包含：
- observation（观察/事实）：这条经验是什么，用一句话概括标题
- feeling（感受）：当时的情绪体验
- need（需要）：背后的核心需求
- request（请求/建议）：可以怎么做的具体建议（可选）

## 分类判断
根据内容自动选择 category：
- 人生阅历：工作、选择、人生道理
- 家庭菜谱：烹饪、食物、配方
- 成长故事：个人成长、学习、旅行
- 相处感悟：人际关系、沟通、情感

## 与已有卡片比对
我会给你已有卡片的标题列表。你需要判断：
- 如果新经验和某张已有卡片主题高度相关（同一件事的不同角度），用 "update" 并指定 card_id
- 如果是全新经验，用 "create"，card_id 填 null
- update 时，observation/feeling/need/request 应该是**融合后的完整内容**（保留原有精华+补充新内容），而不是只写增量

## 输出格式
返回纯 JSON 数组，不要加任何解释：
[{"action":"create","card_id":null,"category":"人生阅历","observation":"关于选择的经验","feeling":"当时很纠结但最终释然","need":"需要被理解和支持","request":"下次可以多听听家人的意见"}, ...]

## 规则
- 如果对话没有实质性经验内容（纯寒暄），返回空数组 []
- 一次最多返回 3 张卡片
- observation 控制在 20 字以内
- feeling/need/request 各控制在 100 字以内
"""


async def summarize_and_sync(history: list[dict], existing_cards: list[dict]) -> list[dict]:
    """
    输入：
        history: 对话历史 [{role, content}, ...]
        existing_cards: 知识库中候选卡片 [{id, category, observation, feeling}, ...]
    输出：
        list[dict]: LLM 返回的卡片操作指令
            [{action:"create"|"update", card_id:null|int, category, observation, feeling, need, request}, ...]
    """
    # 构建对话文本
    dialogue = "\n".join(
        [f"{'用户' if m['role']=='user' else 'AI'}: {m['content']}" for m in history]
    )

    # 构建已有卡片摘要（精简版，控制 token）
    if existing_cards:
        card_summary = "\n".join(
            [f"[id={c['id']}] {c['category']} | {c['observation']} | {c['feeling'][:60]}" for c in existing_cards]
        )
    else:
        card_summary = "（知识库为空，所有经验都是新的）"

    user_prompt = f"""## 对话记录
{dialogue}

## 已有卡片
{card_summary}

请从以上对话中提取经验卡片。"""

    try:
        messages = [
            {"role": "system", "content": SUMMARIZE_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        raw = await call_llm(messages)
        logger.info(f"卡片总结 LLM 返回: {raw[:200]}...")

        # 清洗：去掉可能的 markdown 代码块包裹
        raw = raw.strip()
        if raw.startswith("```"):
            # 去掉 ```json 和结尾 ```
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        result = json.loads(raw)
        if not isinstance(result, list):
            logger.warning(f"LLM 返回格式异常，期望数组，实际: {type(result)}")
            return []
        return result

    except json.JSONDecodeError as e:
        logger.error(f"LLM 返回 JSON 解析失败: {e}, raw={raw[:500]}")
        return []
    except Exception as e:
        logger.error(f"卡片总结失败: {e}")
        return []
