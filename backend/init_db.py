"""
初始化数据库表 —— 独立脚本
用法：cd backend && python init_db.py
"""
import asyncio
import os
from app.db.session import engine, Base
from app.models.card import Card  # noqa: F401 — 确保模型被注册

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


async def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ 数据库表创建成功（data/kinvoice.db）")


if __name__ == "__main__":
    asyncio.run(init_db())
