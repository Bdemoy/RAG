from sqlmodel import Session

from app.categories.models import Category


def create(session: Session, name: str) -> Category:
    raise NotImplementedError


def list_all(session: Session) -> list[Category]:
    raise NotImplementedError


def rename(session: Session, cat_id: int, name: str) -> Category:
    raise NotImplementedError


def delete(session: Session, cat_id: int) -> None:
    raise NotImplementedError


def ensure_exists(session: Session, cat_id: int | None) -> None:
    raise NotImplementedError