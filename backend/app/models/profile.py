"""
用户个人文档 ORM 模型
字段：id / user_id / name / tags / content_md / created_at / updated_at

设计决策：
- 去掉了 relation（家庭成员关系）和 birth_date（生日），改为 tags（标签）
- 新增 user_id 实现数据隔离，每个用户只能看到自己的文档
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.db.session import Base


class UserDocument(Base):
    __tablename__ = "user_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False, index=True, default="")   # 所属用户 ID
    name = Column(String(100), nullable=False, default="")                  # 文档标题
    tags = Column(String(200), nullable=False, default="")                  # 标签，逗号分隔，如 "工作,健康"
    content_md = Column(Text, nullable=False, default="")                   # Markdown 正文
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserDocument(id={self.id}, user_id='{self.user_id}', name='{self.name}')>"
