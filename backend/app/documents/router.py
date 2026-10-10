from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel
from sqlmodel import Session

from app import usecases
from app.documents import service
from app.documents.models import Document
from app.infrastructure.db import get_session

router = APIRouter(prefix="/documents", tags=["documents"])


class MetaIn(BaseModel):
    title: str | None = None
    category_id: int | None = None


class ContentIn(BaseModel):
    content: str


@router.post("", status_code=201)
def import_document(
    title: str = Form(),
    category_id: int | None = Form(None),
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    session: Session = Depends(get_session),
) -> Document:
    """文件和粘贴文本二选一。格式按文件后缀判断，粘贴文本当 txt。超过 1MB → 413。"""
    raise NotImplementedError


@router.get("")
def list_documents(
    category_id: int | None = None,
    page: int = 1,
    size: int = 20,
    session: Session = Depends(get_session),
) -> list[Document]:
    return service.list_documents(session, category_id, page, size)


@router.get("/{doc_id}")
def get_document(doc_id: int, session: Session = Depends(get_session)) -> Document:
    return service.get(session, doc_id)


@router.patch("/{doc_id}")
def update_meta(
    doc_id: int, body: MetaIn, session: Session = Depends(get_session)
) -> Document:
    changes = body.model_dump(exclude_unset=True)
    return usecases.update_meta(session, doc_id, changes)


@router.put("/{doc_id}/content")
def update_content(
    doc_id: int, body: ContentIn, session: Session = Depends(get_session)
) -> Document:
    return usecases.update_content(session, doc_id, body.content)


@router.delete("/{doc_id}", status_code=204)
def delete_document(doc_id: int, session: Session = Depends(get_session)) -> None:
    service.delete(session, doc_id)
    session.commit()
