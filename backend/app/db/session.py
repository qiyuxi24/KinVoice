"""
数据库连接管理 —— 异步式调用数据库 & 数据库会话实现
"""

# api/memory.py先将该请求经过schemas/memory.py的格式校验，然后调用models/card.py创建卡片，最终利用db/session.py手动存储到创建好的card中(即存入数据库)


import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATABASE_PATH = os.path.join(BASE_DIR, "data", "kinvoice.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DATABASE_PATH}"

# 1.异步式调用数据库
# echo=True 会打印所有SQL语句，开发时用于调试，正式上线改成 False
engine = create_async_engine(DATABASE_URL, echo=False)

# 2.会话(session)实现
# 每一次调用async_sessionmaker来请求数据库都会创建一个新的异步会话
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # 提交后不使数据过期，方便在别的地方继续使用
)

class Base(DeclarativeBase):
    pass
