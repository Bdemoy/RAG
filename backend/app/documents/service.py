from sqlmodel import Session

from app.documents.models import Document


def parse(source: bytes | str, content_format: str) -> str:
    """统一成正文。换行规整等处理都在这里做完，之后正文不再改。无法解析 → 400。"""
    raise NotImplementedError


def insert(
    session: Session,
    title: str,
    content: str,
    source_type: str,
    content_format: str,
    category_id: int | None,
) -> Document:
    """add + flush 拿到 id，不提交。"""
    raise NotImplementedError


def get(session: Session, doc_id: int) -> Document:
    """不存在 → 404。"""
    raise NotImplementedError


def list_documents(
    session: Session, category_id: int | None = None, page: int = 1, size: int = 20
) -> list[Document]:
    raise NotImplementedError


def set_content(session: Session, doc_id: int, content: str) -> Document:
    raise NotImplementedError


def set_meta(session: Session, doc_id: int, changes: dict) -> Document:
    """只更新明确提供的 title/category_id；分类为 None 时清空。不提交。"""
    raise NotImplementedError


def delete(session: Session, doc_id: int) -> None:
    """文本块由外键 CASCADE 一起删。不提交。"""
    raise NotImplementedError
