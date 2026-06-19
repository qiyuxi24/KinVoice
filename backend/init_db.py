"""
建立初始化数据库表
用法: cd backend && python init_db.py
"""
import asyncio
import os
from app.db.session import engine, Base, BASE_DIR, DATABASE_PATH
from app.models.card import Card  # 手动导入创建的"记忆卡片"Card


async def init_db():
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)

    # 异步获取数据库连接,自动创建项目中所有定义好类型的数据库数据表(仅新建不存在的表，不会改动已有表)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  
    # Base 是 SQLAlchemy(一种ORM框架) 提供的基类, models里面所有表模型都继承自它

    print(f"数据库初始化完成！{DATABASE_PATH}")


if __name__ == "__main__":
    asyncio.run(init_db())    # 入口


"""
1.执行命令: 进入backend目录, 运行 python init_db.py
2.自动创建data存储库
3.加载所有 ORM 模型 (先指明所建表的结构) (当前只有Card卡片表)
4.连接 SQLite 数据库并自动生成Card空数据表
5.提示初始化成功
"""