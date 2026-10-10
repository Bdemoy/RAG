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
    """解析 → 校验分类 → 写库前准备文本块和向量 → 写库 → 提交。
    解析或向量生成失败时不写库，写入失败时回滚，不留下半份资料。
    """
    raise NotImplementedError


def update_content(session: Session, doc_id: int, new_content: str) -> Document:
    """先确认资料存在，再用 parse(new_content, "txt") 规整编辑文本。
    以规整后的正文准备文本块和向量，成功后在同一事务中保存该正文并替换旧块。
    写入失败时回滚，保留旧正文和文本块；解析或向量生成失败时不写库。
    """
    raise NotImplementedError


def update_meta(session: Session, doc_id: int, changes: dict) -> Document:
    """未传字段保留；分类 None 表示清空，非空分类先校验存在。
    调用 set_meta 后提交，不重建文本块。changes 仅包含 title/category_id。
    """
    raise NotImplementedError
