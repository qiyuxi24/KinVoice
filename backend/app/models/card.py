"""
<<<<<<< Updated upstream
经验卡片 ORM 模型
=======
可存入数据库的"经验卡片" ORM 模型
字段与 Pydantic Schema (schemas/memory.py) 一一对齐：
  id / category / emotion / observation / feeling / need / request / created_at / updated_at
>>>>>>> Stashed changes
"""
from datetime import datetime
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


class Card(Base):
    __tablename__ = "cards"

<<<<<<< Updated upstream
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    category: Mapped[str] = mapped_column(String(50), default="通用", comment="分类（感受/需要/行动/通用）")
    emotion: Mapped[str] = mapped_column(String(100), nullable=False, comment="情绪关键词")
    observation: Mapped[str] = mapped_column(Text, nullable=False, comment="观察（事实描述）")
    feeling: Mapped[str] = mapped_column(Text, nullable=False, comment="感受")
    need: Mapped[str] = mapped_column(Text, nullable=False, comment="需要")
    request: Mapped[str | None] = mapped_column(Text, nullable=True, comment="请求")

    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "emotion": self.emotion,
            "observation": self.observation,
            "feeling": self.feeling,
            "need": self.need,
            "request": self.request,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
=======
    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), nullable=False, default="通用")
    emotion = Column(String(100), nullable=False, default="")
    observation = Column(Text, nullable=False, default="")
    feeling = Column(Text, nullable=False, default="")
    need = Column(Text, nullable=False, default="")
    request = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Card(id={self.id}, category='{self.category}', emotion='{self.emotion}')>"
>>>>>>> Stashed changes
