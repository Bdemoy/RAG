from fastapi import HTTPException
from psycopg.errors import UniqueViolation
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.categories.models import Category


def _flush(session: Session) -> None:
    try:
        session.flush()
    except IntegrityError as exc:
        if isinstance(exc.orig, UniqueViolation):
            raise HTTPException(status_code=409, detail="分类名称已存在") from exc
        raise


def create(session: Session, name: str) -> Category:
    """重名 → 409。"""
    category = Category(name=name)
    session.add(category)
    _flush(session)
    return category


def list_all(session: Session) -> list[Category]:
    return list(session.exec(select(Category).order_by(Category.id)).all())


def rename(session: Session, cat_id: int, name: str) -> Category:
    """不存在 → 404；重名 → 409。"""
    category = session.get(Category, cat_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    category.name = name
    _flush(session)
    return category


def delete(session: Session, cat_id: int) -> None:
    """资料不删，靠外键 ON DELETE SET NULL 变为未分类。"""
    category = session.get(Category, cat_id)
    if category is None:
        raise HTTPException(status_code=404, detail="分类不存在")
    session.delete(category)
    session.flush()


def ensure_exists(session: Session, cat_id: int | None) -> None:
    """None 表示未分类，直接通过；不存在 → 404。"""
    if cat_id is None:
        return
    if session.get(Category, cat_id) is None:
        raise HTTPException(status_code=404, detail="分类不存在")
