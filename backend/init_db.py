"""
初始化数据库表 —— 独立脚本
用法：cd backend && python init_db.py
"""
import asyncio
import os
from app.db.session import engine, Base, BASE_DIR
from app.models.card import Card, Conversation, ChatMessage  # noqa: F401
from app.models.profile import FamilyMember  # 家庭成员档案（si 保留）
from app.models.voice import CustomVoice  # 自定义音色（xia）


async def init_db():
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✓ 数据库表创建成功（{BASE_DIR}/data/kinvoice.db）")


if __name__ == "__main__":
    asyncio.run(init_db())
