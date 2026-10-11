from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from app.categories import service
from app.categories.models import Category
from app.infrastructure.db import get_session

router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryIn(BaseModel):
    name: str


@router.post("", status_code=201)
def create_category(
    body: CategoryIn, session: Session = Depends(get_session)
) -> Category:
    category = service.create(session, body.name)
    session.commit()
    session.refresh(category)
    return category


@router.get("")
def list_categories(session: Session = Depends(get_session)) -> list[Category]:
    return service.list_all(session)


@router.patch("/{cat_id}")
def rename_category(
    cat_id: int, body: CategoryIn, session: Session = Depends(get_session)
) -> Category:
    category = service.rename(session, cat_id, body.name)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/{cat_id}", status_code=204)
def delete_category(cat_id: int, session: Session = Depends(get_session)) -> None:
    service.delete(session, cat_id)

    session.commit()
