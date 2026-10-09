from sqlmodel import Session

from app.categories import service as categories
from app.documents import service as documents
from app.documents.models import Document
from app.indexing import service as indexing


def import_document(
    session: Session,
    title: str,
    source: bytes | str,
    content_format: str,
    source_type: str,
    category_id: int | None = None,
) -> Document:
    """解析 → 校验分类 → 事务外准备文本块 → 写库 → 提交。失败不留下半份资料。"""
    raise NotImplementedError


def update_content(session: Session, doc_id: int, new_content: str) -> Document:
    """先准备新文本块，成功后替换正文和旧文本块；失败旧版本不变。"""
    raise NotImplementedError


def update_meta(
    session: Session,
    doc_id: int,
    title: str | None = None,
    category_id: int | None = None,
) -> Document:
    """校验分类 → 改标题或分类 → 提交。不重建文本块。"""
    raise NotImplementedError
