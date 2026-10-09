from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Chunk(SQLModel, table=True):
    __tablename__ = "chunks"
    __table_args__ = (UniqueConstraint("document_id", "chunk_index"),)

    id: int | None = Field(default=None, primary_key=True)
    document_id: int = Field(foreign_key="documents.id", ondelete="CASCADE")
    chunk_index: int
    heading: str | None = None
    content: str
    start_offset: int
    end_offset: int
    created_at: datetime = Field(default_factory=datetime.now)


@dataclass(frozen=True)
class ChunkDraft:
    index: int
    heading: str | None
    content: str
    start_offset: int
    end_offset: int
    embedding: list[float]


@dataclass(frozen=True)
class SearchHit:
    chunk_id: int
    document_id: int
    document_title: str
    heading: str | None
    content: str
    start_offset: int
    end_offset: int
    chunk_index: int
    score: float
