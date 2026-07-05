"""
家庭成员档案 ORM 模型
字段：id / name / relation / birth_date / avatar_url / content_md / created_at / updated_at
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.session import Base


class FamilyMember(Base):
    __tablename__ = "family_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, default="")
    relation = Column(String(50), nullable=False, default="家人")       # 关系：父亲/母亲/配偶/子女/...
    birth_date = Column(String(20), nullable=True)                    # 生日：YYYY-MM-DD
    avatar_url = Column(String(500), nullable=True)                   # 头像链接（可选）
    content_md = Column(Text, nullable=False, default="")             # Markdown 正文（档案详细内容）
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<FamilyMember(id={self.id}, name='{self.name}', relation='{self.relation}')>"
