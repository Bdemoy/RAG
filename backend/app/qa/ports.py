from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Passage:
    chunk_id: int
    document_id: int
    document_title: str
    heading: str | None
    content: str
    start_offset: int
    end_offset: int


class KnowledgeAccess(Protocol):
    """qa 需要的能力，由 adapters 实现。范围在创建适配器时绑定，接口里不带范围参数。"""

    def search(self, query: str) -> list[Passage]: ...
    def read_context(self, chunk_id: int) -> list[Passage]: ...
