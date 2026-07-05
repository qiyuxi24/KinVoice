"""
建立初始化数据库表
用法: cd backend && python init_db.py
"""
import asyncio
import os
from app.db.session import engine, Base, BASE_DIR
import app.models

async def init_db():
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"数据库初始化完成！{BASE_DIR}/data/kinvoice.db")

if __name__ == "__main__":
    asyncio.run(init_db())    # 入口


"""
1.执行命令: 进入backend目录, 运行 python init_db.py
2.自动创建data存储库
3.加载所有 ORM 模型 (先指明所建表的结构) (当前只有Card卡片表)
4.连接 SQLite 数据库并自动生成Card空数据表
5.提示初始化成功
"""