from sqlmodel import Session

from app.indexing.models import ChunkDraft, SearchHit


def prepare_chunks(content: str) -> list[ChunkDraft]:
    """切分 + 批量生成向量。不写库；Embedding 失败直接抛错。"""
    raise NotImplementedError


def save_chunks(session: Session, document_id: int, drafts: list[ChunkDraft]) -> int:
    """只 add，不 commit，提交由调用方决定。返回块数。"""
    raise NotImplementedError


def replace_chunks(session: Session, document_id: int, drafts: list[ChunkDraft]) -> int:
    """删旧块 + 插新块，同样不 commit。"""
    raise NotImplementedError


def search(
    session: Session, query: str, category_id: int | None, top_k: int = 5
) -> list[SearchHit]:
    """向量检索。category_id 为 None 表示全部资料。
    需要 documents 的 title、category_id 时用 SQL join 表名，不 import documents。"""
    raise NotImplementedError


def neighbors(session: Session, chunk_id: int, window: int = 1) -> list[SearchHit]:
    """同一文档内 chunk_index 在 ±window 范围的块。"""
    raise NotImplementedError
