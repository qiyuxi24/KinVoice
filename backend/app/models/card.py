"""
可存入数据库的"经验卡片" ORM 模型
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.session import Base


class Card(Base):  # 创建卡片的页格式(继承自基类Base)
    __tablename__ = "cards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    original_text = Column(Text, nullable=True)
    family_id = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Card(id={self.id}, title='{self.title}')>"