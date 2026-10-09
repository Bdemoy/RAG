from sqlmodel import Session

from app.categories.models import Category


def create(session: Session, name: str) -> Category:
    """重名 → 409。"""
    raise NotImplementedError


def list_all(session: Session) -> list[Category]:
    raise NotImplementedError


def rename(session: Session, cat_id: int, name: str) -> Category:
    """不存在 → 404；重名 → 409。"""
    raise NotImplementedError


def delete(session: Session, cat_id: int) -> None:
    """资料不删，靠外键 ON DELETE SET NULL 变为未分类。"""
    raise NotImplementedError


def ensure_exists(session: Session, cat_id: int | None) -> None:
    """给 documents 用。None 表示未分类，直接通过；不存在 → 404。"""
    raise NotImplementedError
