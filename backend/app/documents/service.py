from datetime import UTC, datetime
from io import BytesIO

from fastapi import HTTPException
from pypdf import PdfReader
from pypdf.errors import PyPdfError
from sqlmodel import Session, select

from app.documents.models import Document


def parse(source: bytes | str, content_format: str) -> str:
    """统一成完整正文并规整换行；Markdown 保留源码，PDF 提取文本。"""
    try:
        if content_format in {"txt", "markdown"}:
            content = source.decode("utf-8-sig") if isinstance(source, bytes) else source
        elif content_format == "pdf":
            reader = PdfReader(BytesIO(source))
            content = "\n\n".join(page.extract_text() for page in reader.pages)
        else:
            raise HTTPException(status_code=400, detail="资料格式需为 txt、markdown 或 pdf")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="文本需使用 UTF-8 编码") from exc
    except PyPdfError as exc:
        raise HTTPException(status_code=400, detail="PDF 解析失败") from exc

    content = content.replace("\r\n", "\n").replace("\r", "\n")
    if not content.strip():
        raise HTTPException(status_code=400, detail="资料中没有可提取的正文")
    return content


def insert(
    session: Session,
    title: str,
    content: str,
    source_type: str,
    content_format: str,
    category_id: int | None,
) -> Document:
    """add + flush 拿到 id，不提交。content 已由 parse 规整。"""
    document = Document(
        title=title,
        content=content,
        source_type=source_type,
        content_format=content_format,
        category_id=category_id,
    )
    session.add(document)
    session.flush()
    return document


def get(session: Session, doc_id: int) -> Document:
    """不存在 → 404。"""
    document = session.get(Document, doc_id)
    if document is None:
        raise HTTPException(status_code=404, detail="资料不存在")
    return document


def list_documents(
    session: Session, category_id: int | None = None, page: int = 1, size: int = 20
) -> list[Document]:
    """按更新时间倒序分页；None 表示全部资料，同时间按 id 倒序。"""
    statement = select(Document)
    if category_id is not None:
        statement = statement.where(Document.category_id == category_id)
    statement = (
        statement.order_by(Document.updated_at.desc(), Document.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    return list(session.exec(statement).all())


def set_content(session: Session, doc_id: int, content: str) -> Document:
    """更新规整后的正文和更新时间，不处理文本块，不提交。"""
    document = get(session, doc_id)
    document.content = content
    document.updated_at = datetime.now(UTC)
    session.flush()
    return document


def set_meta(session: Session, doc_id: int, changes: dict) -> Document:
    """只更新明确提供的 title/category_id；分类为 None 时清空。不提交。"""
    document = get(session, doc_id)
    if not changes:
        return document
    if "title" in changes:
        document.title = changes["title"]
    if "category_id" in changes:
        document.category_id = changes["category_id"]
    document.updated_at = datetime.now(UTC)
    session.flush()
    return document


def delete(session: Session, doc_id: int) -> None:
    """文本块由外键 CASCADE 一起删。不提交。"""
    session.delete(get(session, doc_id))
    session.flush()
