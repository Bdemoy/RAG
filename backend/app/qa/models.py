from typing import Literal

from pydantic import BaseModel

from app.qa.ports import Passage


class Verdict(BaseModel):
    status: Literal["sufficient", "partial", "none"]
    missing: str | None = None
    truncated_chunk_id: int | None = None


class AskRequest(BaseModel):
    question: str
    category_id: int | None = None


class AskResult(BaseModel):
    status: Literal["answered", "partial", "refused"]
    answer: str
    missing: str | None = None
    citations: list[Passage]
    trace: list[str] = []
