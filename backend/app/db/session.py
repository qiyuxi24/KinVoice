"""
数据库连接管理 —— 异步 SQLite + SQLAlchemy 2.0
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    pass


<<<<<<< Updated upstream
async def get_session() -> AsyncSession:
    """FastAPI 依赖注入：获取异步数据库会话"""
    async with async_session_factory() as session:
=======
# 3.FastAPI 依赖注入 —— 每次请求自动创建/提交/关闭 session
async def get_session():
    async with AsyncSessionLocal() as session:
>>>>>>> Stashed changes
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
<<<<<<< Updated upstream
        finally:
            await session.close()
=======
>>>>>>> Stashed changes
