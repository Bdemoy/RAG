from datetime import datetime

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    __tablename__ = "documents"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    content: str
    source_type: str
    content_format: str
    category_id: int | None = Field(
        default=None, foreign_key="categories.id", ondelete="SET NULL"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
