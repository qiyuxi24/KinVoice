"""
初始化数据库表 —— 独立脚本
用法：cd backend && python init_db.py
"""
import asyncio
import os
<<<<<<< Updated upstream
from app.db.session import engine, Base
from app.models.card import Card  # noqa: F401 — 确保模型被注册

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
=======
from app.db.session import engine, Base, BASE_DIR, DATABASE_PATH
from app.models.card import Card  # 手动导入创建的"记忆卡片"Card
from app.models.profile import FamilyMember  # 家庭成员档案
>>>>>>> Stashed changes


async def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ 数据库表创建成功（data/kinvoice.db）")


if __name__ == "__main__":
    asyncio.run(init_db())
