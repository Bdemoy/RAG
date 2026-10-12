from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str  # 解析规整后的完整正文，索引输入与文本块 offset 的基准
    source_type: str
    content_format: str
    category_id: int | None = Field(
        default=None, foreign_key="categories.id", ondelete="SET NULL"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
