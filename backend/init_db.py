"""
初始化数据库表 + 数据迁移 —— 独立脚本
用法：cd backend && python init_db.py
"""
import asyncio
import os
from sqlalchemy import select, text
from app.db.session import engine, Base, BASE_DIR, AsyncSessionLocal
from app.models.card import Card, Conversation, ChatMessage  # noqa: F401
from app.models.folder import Folder  # noqa: F401
from app.models.profile import UserDocument  # 用户个人文档
from app.models.profile import FamilyMember  # 家庭成员档案（si 保留）
from app.models.voice import CustomVoice  # 自定义音色（xia）
from app.models.family import User, FamilyGroup, FamilyMembership  # 家庭组（新增）


async def init_db():
    data_dir = os.path.join(BASE_DIR, "data")
    os.makedirs(data_dir, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"✓ 数据库表创建成功（{BASE_DIR}/data/kinvoice.db）")


async def migrate_category_to_folder():
    """
    迁移旧数据：将 cards.category 转换为 folders + folder_id
    - 每个非空的 category 值创建同名文件夹
    - 设置对应 card 的 folder_id
    """
    async with AsyncSessionLocal() as session:
        # 检查 folders 表是否已有数据
        from sqlalchemy import func as sa_func
        f_result = await session.execute(select(sa_func.count(Folder.id)))
        folder_count = f_result.scalar() or 0
        if folder_count > 0:
            print(f"✓ 文件夹已存在 {folder_count} 个，跳过迁移")
            return

        # 获取所有非空 category 的卡片
        result = await session.execute(
            select(Card).where(Card.category.isnot(None), Card.category != "")
        )
        cards = result.scalars().all()
        if not cards:
            print("✓ 无需迁移（没有含 category 的旧卡片）")
            return

        # 收集唯一分类
        categories = list(set(c.category for c in cards if c.category))
        folder_map: dict[str, Folder] = {}

        for cat in categories:
            folder = Folder(name=cat, family_id="1")
            session.add(folder)
            await session.flush()
            folder_map[cat] = folder
            print(f"  创建文件夹: {cat} (id={folder.id})")

        # 设置 folder_id
        for card in cards:
            if card.category in folder_map:
                card.folder_id = folder_map[card.category].id

        await session.commit()
        print(f"✓ 迁移完成: {len(categories)} 个分类 → 文件夹, {len(cards)} 张卡片已关联")


async def init_fts():
    """创建 FTS5 全文检索虚拟表 + 触发器（用于陪伴页上下文检索）"""
    # 卡片 FTS5
    cards_fts_sql = [
        # 虚拟表（外部内容模式，不存数据副本）
        """CREATE VIRTUAL TABLE IF NOT EXISTS cards_fts USING fts5(
            title, content, observation, feeling, need, request, author,
            content='cards', content_rowid='id'
        );""",
        # INSERT 触发器
        """CREATE TRIGGER IF NOT EXISTS cards_fts_ai AFTER INSERT ON cards BEGIN
            INSERT INTO cards_fts(rowid, title, content, observation, feeling, need, request, author)
            VALUES (new.id, new.title, new.content, new.observation, new.feeling, new.need, new.request, new.author);
        END;""",
        # DELETE 触发器
        """CREATE TRIGGER IF NOT EXISTS cards_fts_ad AFTER DELETE ON cards BEGIN
            INSERT INTO cards_fts(cards_fts, rowid, title, content, observation, feeling, need, request, author)
            VALUES ('delete', old.id, old.title, old.content, old.observation, old.feeling, old.need, old.request, old.author);
        END;""",
        # UPDATE 触发器（先删旧索引，再插新的）
        """CREATE TRIGGER IF NOT EXISTS cards_fts_au AFTER UPDATE ON cards BEGIN
            INSERT INTO cards_fts(cards_fts, rowid, title, content, observation, feeling, need, request, author)
            VALUES ('delete', old.id, old.title, old.content, old.observation, old.feeling, old.need, old.request, old.author);
            INSERT INTO cards_fts(rowid, title, content, observation, feeling, need, request, author)
            VALUES (new.id, new.title, new.content, new.observation, new.feeling, new.need, new.request, new.author);
        END;""",
    ]

    # 对话消息 FTS5
    msgs_fts_sql = [
        """CREATE VIRTUAL TABLE IF NOT EXISTS chat_messages_fts USING fts5(
            content, role,
            content='chat_messages', content_rowid='id'
        );""",
        """CREATE TRIGGER IF NOT EXISTS chat_msgs_fts_ai AFTER INSERT ON chat_messages BEGIN
            INSERT INTO chat_messages_fts(rowid, content, role)
            VALUES (new.id, new.content, new.role);
        END;""",
        """CREATE TRIGGER IF NOT EXISTS chat_msgs_fts_ad AFTER DELETE ON chat_messages BEGIN
            INSERT INTO chat_messages_fts(chat_messages_fts, rowid, content, role)
            VALUES ('delete', old.id, old.content, old.role);
        END;""",
        """CREATE TRIGGER IF NOT EXISTS chat_msgs_fts_au AFTER UPDATE ON chat_messages BEGIN
            INSERT INTO chat_messages_fts(chat_messages_fts, rowid, content, role)
            VALUES ('delete', old.id, old.content, old.role);
            INSERT INTO chat_messages_fts(rowid, content, role)
            VALUES (new.id, new.content, new.role);
        END;""",
    ]

    # 重建已有数据的索引
    rebuild_sql = [
        "INSERT INTO cards_fts(rowid, title, content, observation, feeling, need, request, author) SELECT id, title, content, observation, feeling, need, request, author FROM cards;",
        "INSERT INTO chat_messages_fts(rowid, content, role) SELECT id, content, role FROM chat_messages;",
    ]

    async with engine.begin() as conn:
        for sql in cards_fts_sql + msgs_fts_sql:
            await conn.execute(text(sql))
        # 重建索引（FTS5 外部内容表需手动填充已有数据）
        for sql in rebuild_sql:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass  # 表为空时忽略
    print("✓ FTS5 全文检索表创建完成")


async def main():
    await init_db()
    await migrate_category_to_folder()
    await init_fts()


if __name__ == "__main__":
    asyncio.run(main())
