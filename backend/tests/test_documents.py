from datetime import UTC, datetime
from io import BytesIO

import pytest
from fastapi import HTTPException
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlmodel import Session

from app.categories.models import Category
from app.documents import service
from app.documents.models import Document
from app.indexing.models import Chunk


def make_pdf(*texts, encrypted=False):
    writer = PdfWriter()
    for value in texts:
        page = writer.add_blank_page(width=200, height=200)
        if value:
            font = DictionaryObject({
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            })
            page[NameObject("/Resources")] = DictionaryObject({
                NameObject("/Font"): DictionaryObject({
                    NameObject("/F1"): writer._add_object(font),
                }),
            })
            stream = DecodedStreamObject()
            stream.set_data(f"BT /F1 12 Tf 10 10 Td ({value}) Tj ET".encode("ascii"))
            page[NameObject("/Contents")] = writer._add_object(stream)
    if encrypted:
        writer.encrypt("test-password")
    output = BytesIO()
    writer.write(output)
    return output.getvalue()


@pytest.mark.parametrize("content_format", ["txt", "markdown"])
@pytest.mark.parametrize("as_bytes", [False, True])
def test_parse_normalizes_newlines_and_keeps_source(content_format, as_bytes):
    source = "# 标题\r\n\r\n  正文 **原样保留**  \r下一行\n"
    if as_bytes:
        source = source.encode("utf-8-sig")
    assert service.parse(source, content_format) == (
        "# 标题\n\n  正文 **原样保留**  \n下一行\n"
    )


def test_parse_pdf_extracts_all_pages():
    assert service.parse(make_pdf("First page", "Second page"), "pdf") == (
        "First page\n\nSecond page"
    )


@pytest.mark.parametrize("source, content_format", [
    (b"\xff", "txt"),
    (b"broken PDF", "pdf"),
    ("body", "docx"),
    ("", "txt"),
    (" \r\n\t", "markdown"),
])
def test_parse_input_errors_are_400(source, content_format):
    with pytest.raises(HTTPException) as error:
        service.parse(source, content_format)
    assert error.value.status_code == 400


@pytest.mark.parametrize("encrypted", [False, True])
def test_parse_unreadable_pdf_is_400(encrypted):
    with pytest.raises(HTTPException) as error:
        service.parse(make_pdf("" if not encrypted else "body", encrypted=encrypted), "pdf")
    assert error.value.status_code == 400


@pytest.fixture
def existing_document(session):
    first = Category(name="高等数学")
    second = Category(name="线性代数")
    session.add_all([first, second])
    session.flush()
    document = service.insert(session, "笔记", "旧正文", "paste", "txt", first.id)
    document.created_at = document.updated_at = datetime(2000, 1, 1, tzinfo=UTC)
    chunk = Chunk(
        document_id=document.id, chunk_index=0, content="旧正文",
        start_offset=0, end_offset=3, created_at=datetime.now(UTC),
    )
    session.add(chunk)
    session.flush()
    ids = document.id, first.id, second.id, chunk.id
    session.commit()
    return ids


def test_insert_get_and_caller_commit(session, db_engine):
    document = service.insert(session, "笔记", "完整正文", "upload", "markdown", None)
    doc_id = document.id
    assert doc_id is not None
    assert service.get(session, doc_id) is document
    with Session(db_engine) as reader:
        assert reader.get(Document, doc_id) is None
    session.commit()
    with Session(db_engine) as reader:
        saved = service.get(reader, doc_id)
        assert (saved.title, saved.content, saved.source_type, saved.content_format) == (
            "笔记", "完整正文", "upload", "markdown",
        )
        assert saved.category_id is None


def test_insert_can_be_rolled_back(session, db_engine):
    document = service.insert(session, "笔记", "完整正文", "paste", "txt", None)
    doc_id = document.id
    session.rollback()
    with Session(db_engine) as reader:
        assert reader.get(Document, doc_id) is None


def test_list_filters_then_paginates_in_stable_order(session):
    assert service.list_documents(session) == []
    category = Category(name="高等数学")
    session.add(category)
    session.flush()
    ids = []
    for category_id in [category.id, None, category.id]:
        document = service.insert(session, "笔记", "正文", "paste", "txt", category_id)
        document.updated_at = datetime(2000, 1, 1, tzinfo=UTC)
        ids.append(document.id)
    session.flush()
    assert [d.id for d in service.list_documents(session)] == ids[::-1]
    assert [d.id for d in service.list_documents(session, category.id, page=2, size=1)] == [ids[0]]
    assert service.list_documents(session, category.id, page=3, size=1) == []
    assert service.list_documents(session, category.id + 1) == []
    session.get(Document, ids[0]).updated_at = datetime(2001, 1, 1, tzinfo=UTC)
    session.flush()
    assert service.list_documents(session, size=1)[0].id == ids[0]


@pytest.mark.parametrize("operation, extra", [
    (service.get, ()),
    (service.set_content, ("新正文",)),
    (service.set_meta, ({"title": "新标题"},)),
    (service.delete, ()),
])
def test_missing_document_is_404(session, operation, extra):
    with pytest.raises(HTTPException) as error:
        operation(session, 999, *extra)
    assert error.value.status_code == 404


def test_set_content_preserves_document_identity_and_source(session, db_engine, existing_document):
    doc_id, category_id, _, chunk_id = existing_document
    updated = service.set_content(session, doc_id, "新正文")
    assert updated.updated_at > updated.created_at
    session.commit()
    with Session(db_engine) as reader:
        document = service.get(reader, doc_id)
        assert document.content == "新正文"
        assert (document.title, document.category_id, document.source_type, document.content_format) == (
            "笔记", category_id, "paste", "txt",
        )
        assert document.created_at == datetime(2000, 1, 1, tzinfo=UTC)
        assert reader.get(Chunk, chunk_id).content == "旧正文"


@pytest.mark.parametrize("change", ["title", "clear_category", "move_category", "empty"])
def test_set_meta_patch_semantics(session, db_engine, existing_document, change):
    doc_id, first_id, second_id, chunk_id = existing_document
    changes = {
        "title": {"title": "新标题"},
        "clear_category": {"category_id": None},
        "move_category": {"category_id": second_id},
        "empty": {},
    }[change]
    updated = service.set_meta(session, doc_id, changes)
    assert (updated.updated_at == updated.created_at) is (change == "empty")
    session.commit()
    with Session(db_engine) as reader:
        document = service.get(reader, doc_id)
        assert document.title == changes.get("title", "笔记")
        assert document.category_id == changes.get("category_id", first_id)
        assert document.content == "旧正文"
        assert document.created_at == datetime(2000, 1, 1, tzinfo=UTC)
        assert reader.get(Chunk, chunk_id).content == "旧正文"


@pytest.mark.parametrize("operation", ["content", "meta", "delete"])
def test_writes_remain_uncommitted_and_can_be_rolled_back(session, db_engine, existing_document, operation):
    doc_id, category_id, _, chunk_id = existing_document
    if operation == "content":
        service.set_content(session, doc_id, "新正文")
    elif operation == "meta":
        service.set_meta(session, doc_id, {"title": "新标题", "category_id": None})
    else:
        service.delete(session, doc_id)
    with Session(db_engine) as reader:
        old = service.get(reader, doc_id)
        assert (old.title, old.content, old.category_id) == ("笔记", "旧正文", category_id)
        assert reader.get(Chunk, chunk_id) is not None
    session.rollback()
    with Session(db_engine) as reader:
        old = service.get(reader, doc_id)
        assert (old.title, old.content, old.category_id) == ("笔记", "旧正文", category_id)
        assert old.updated_at == datetime(2000, 1, 1, tzinfo=UTC)
        assert reader.get(Chunk, chunk_id) is not None


def test_delete_cascades_chunks_and_keeps_category(session, db_engine, existing_document):
    doc_id, category_id, _, chunk_id = existing_document
    service.delete(session, doc_id)
    session.commit()
    with Session(db_engine) as reader:
        assert reader.get(Document, doc_id) is None
        assert reader.get(Chunk, chunk_id) is None
        assert reader.get(Category, category_id) is not None
