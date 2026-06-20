"""
对话总结接口 —— POST /chat/summarize
前端在离开 Companion 页面时调用，传入完整对话历史
后端用 LLM 总结 + SQLite LIKE 匹配已有卡片 → 新建或更新
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_session
from app.models.card import Card
from app.services.card_summarizer import summarize_and_sync
from app.schemas.memory import CardOut
from app.utils.logger import logger

router = APIRouter(prefix="/chat", tags=["对话总结"])

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    """总结请求"""
    history: list[dict] = Field(..., min_length=1, description="对话历史 [{role, content}, ...]")


class SummarizeResult(BaseModel):
    """单条操作结果"""
    action: str               # "create" | "update"
    card_id: int | None = None
    card: CardOut | None = None
    message: str = ""


class SummarizeResponse(BaseModel):
    """总结响应"""
    results: list[SummarizeResult]
    total_created: int
    total_updated: int


@router.post("/summarize", response_model=SummarizeResponse)
async def summarize_chat(
    request: SummarizeRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    总结多轮对话，自动生成/更新经验卡片。

    流程：
    1. 从对话中提取关键词
    2. 用 LIKE 查询现有卡片标题，缩小候选集
    3. LLM 判断新建还是更新
    4. 执行数据库操作
    """
    history = request.history
    logger.info(f"收到总结请求，对话轮数: {len(history)}")

    # ── 1. 提取关键词用于 SQLite LIKE 查询 ──
    keywords = _extract_keywords(history)
    logger.info(f"提取关键词: {keywords}")

    # ── 2. 查询候选卡片 ──
    existing_cards = await _query_candidates(session, keywords)
    logger.info(f"候选卡片数: {len(existing_cards)}")

    # ── 3. LLM 总结 ──
    ops = await summarize_and_sync(history, existing_cards)

    if not ops:
        return SummarizeResponse(results=[], total_created=0, total_updated=0)

    # ── 4. 执行数据库操作 ──
    results = []
    created = 0
    updated = 0

    for op in ops:
        try:
            action = op.get("action", "create")
            card_id = op.get("card_id")

            if action == "update" and card_id:
                # 更新已有卡片
                card = await session.get(Card, card_id)
                if card:
                    card.observation = op.get("observation", card.observation)
                    card.feeling = op.get("feeling", card.feeling)
                    card.need = op.get("need", card.need)
                    card.request = op.get("request", card.request)
                    if op.get("category"):
                        card.category = op["category"]
                    if op.get("emotion"):
                        card.emotion = op["emotion"]
                    await session.flush()
                    await session.refresh(card)
                    results.append(SummarizeResult(
                        action="update",
                        card_id=card.id,
                        card=CardOut.model_validate(card),
                        message="卡片已更新"
                    ))
                    updated += 1
                    logger.info(f"更新卡片 id={card.id}, observation={card.observation}")
                else:
                    # card_id 不存在，降级为 create
                    logger.warning(f"更新目标卡片 id={card_id} 不存在，降级为新建")
                    new_card = await _create_card(session, op)
                    results.append(SummarizeResult(
                        action="create",
                        card_id=new_card.id,
                        card=CardOut.model_validate(new_card),
                        message="目标卡片不存在，已新建"
                    ))
                    created += 1
            else:
                # 新建卡片
                new_card = await _create_card(session, op)
                results.append(SummarizeResult(
                    action="create",
                    card_id=new_card.id,
                    card=CardOut.model_validate(new_card),
                    message="卡片已创建"
                ))
                created += 1

        except Exception as e:
            logger.error(f"处理卡片操作失败: {e}, op={op}")
            results.append(SummarizeResult(
                action=op.get("action", "unknown"),
                message=f"操作失败: {str(e)}"
            ))

    return SummarizeResponse(
        results=results,
        total_created=created,
        total_updated=updated,
    )


# ── 辅助函数 ────────────────────────────────────────────

def _extract_keywords(history: list[dict]) -> list[str]:
    """从对话中提取关键词，用于 SQLite LIKE 查询"""
    # 简单策略：取用户消息中出现频率最高的有意义词汇
    import re
    # 常见停用词
    stop_words = {
        "我", "你", "的", "了", "是", "在", "不", "有", "和", "就", "都",
        "也", "这", "那", "吗", "呢", "吧", "啊", "哦", "嗯", "么", "着",
        "过", "说", "看", "去", "来", "会", "要", "能", "好", "很", "还",
        "没", "上", "下", "个", "对", "把", "被", "从", "到", "让", "给",
        "跟", "与", "为", "以", "所以", "因为", "但是", "可以", "如果",
        "觉得", "知道", "什么", "怎么", "为什么", "怎么样", "多少", "一个",
        "真的", "一点", "一下", "一些", "那种", "这个", "那个", "我们",
        "他们", "自己", "大家", "别人", "人家", "然后", "就是", "的话",
    }
    words = []
    for m in history:
        if m.get("role") == "user":
            content = m.get("content", "")
            # 提取中文词汇（2-4字）
            chinese_words = re.findall(r'[\u4e00-\u9fff]{2,4}', content)
            words.extend([w for w in chinese_words if w not in stop_words])

    # 去重，取前 5 个
    seen = set()
    unique = []
    for w in words:
        if w not in seen:
            seen.add(w)
            unique.append(w)
        if len(unique) >= 5:
            break
    return unique


async def _query_candidates(session: AsyncSession, keywords: list[str]) -> list[dict]:
    """用 LIKE 查询候选卡片，返回精简字段列表"""
    if not keywords:
        # 无关键词时返回最近 5 张卡片
        stmt = select(Card).order_by(Card.updated_at.desc()).limit(5)
    else:
        # 对每个关键词做 OR LIKE 匹配 observation 字段
        conditions = []
        for kw in keywords:
            conditions.append(Card.observation.like(f"%{kw}%"))
        stmt = select(Card).where(or_(*conditions)).limit(10)

    result = await session.execute(stmt)
    cards = result.scalars().all()
    return [
        {
            "id": c.id,
            "category": c.category,
            "observation": c.observation,
            "feeling": c.feeling or "",
        }
        for c in cards
    ]


async def _create_card(session: AsyncSession, data: dict) -> Card:
    """从 LLM 返回数据创建新卡片"""
    orm_fields = {c.name for c in Card.__table__.columns}
    payload = {k: v for k, v in data.items() if k in orm_fields and v is not None}
    card = Card(**payload)
    session.add(card)
    await session.flush()
    await session.refresh(card)
    logger.info(f"创建卡片: id={card.id}, category={card.category}, observation={card.observation}")
    return card
