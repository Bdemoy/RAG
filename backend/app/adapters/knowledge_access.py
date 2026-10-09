from sqlmodel import Session

from app.indexing import service as indexing
from app.qa.ports import Passage


class IndexingKnowledgeAccess:
    """把 qa 的 KnowledgeAccess 接到 indexing 上。不用继承，方法签名对上就算实现。"""

    def __init__(self, session: Session, category_id: int | None, top_k: int = 5):
        self._session = session
        self._category_id = category_id
        self._top_k = top_k

    def search(self, query: str) -> list[Passage]:
        """indexing.search(...) 的 SearchHit 转成 Passage。"""
        raise NotImplementedError

    def read_context(self, chunk_id: int) -> list[Passage]:
        raise NotImplementedError
