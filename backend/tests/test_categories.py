from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from app.categories import service
from app.categories.models import Category
from app.documents.models import Document
from app.indexing.models import Chunk


def test_list_empty(session):
    assert service.list_all(session) == []


def test_create_and_list(session, db_engine):
    category = service.create(session, "高等数学")
    cat_id = category.id
    assert cat_id is not None
    assert category.created_at.tzinfo is not None
    session.commit()

    with Session(db_engine) as reader:
        categories = service.list_all(reader)
        assert [(item.id, item.name) for item in categories] == [(cat_id, "高等数学")]


def test_create_can_be_rolled_back(session, db_engine):
    service.create(session, "高等数学")
    session.rollback()

    with Session(db_engine) as reader:
        assert service.list_all(reader) == []


def test_duplicate_name_keeps_original(session, db_engine):
    category = service.create(session, "高等数学")
    cat_id = category.id
    session.commit()

    with pytest.raises(HTTPException) as error:
        service.create(session, "高等数学")
    assert error.value.status_code == 409
    session.rollback()

    with Session(db_engine) as reader:
        assert [(item.id, item.name) for item in service.list_all(reader)] == [
            (cat_id, "高等数学")
        ]


def test_rename_preserves_identity(session, db_engine):
    category = service.create(session, "高数")
    cat_id, created_at = category.id, category.created_at
    session.commit()

    renamed = service.rename(session, cat_id, "高等数学")
    assert renamed.id == cat_id
    assert renamed.created_at == created_at
    session.commit()

    with Session(db_engine) as reader:
        assert reader.get(Category, cat_id).name == "高等数学"


def test_rename_same_name(session):
    category = service.create(session, "高等数学")
    assert service.rename(session, category.id, "高等数学").name == "高等数学"


def test_rename_conflict_can_be_rolled_back(session, db_engine):
    first = service.create(session, "高等数学")
    second = service.create(session, "线性代数")
    first_id, second_id = first.id, second.id
    session.commit()

    with pytest.raises(HTTPException) as error:
        service.rename(session, first_id, "线性代数")
    assert error.value.status_code == 409
    session.rollback()

    with Session(db_engine) as reader:
        assert reader.get(Category, first_id).name == "高等数学"
        assert reader.get(Category, second_id).name == "线性代数"


def test_rename_can_be_rolled_back(session, db_engine):
    category = service.create(session, "高数")
    cat_id = category.id
    session.commit()

    service.rename(session, cat_id, "高等数学")
    session.rollback()

    with Session(db_engine) as reader:
        assert reader.get(Category, cat_id).name == "高数"


@pytest.mark.parametrize(
    "operation", [service.rename, service.delete, service.ensure_exists]
)
def test_missing_category_is_404(session, operation):
    args = (session, 999, "高等数学") if operation is service.rename else (session, 999)
    with pytest.raises(HTTPException) as error:
        operation(*args)
    assert error.value.status_code == 404


def test_ensure_exists_accepts_uncategorized(session):
    assert service.ensure_exists(session, None) is None


def test_ensure_exists_accepts_existing_category(session):
    category = service.create(session, "高等数学")
    assert service.ensure_exists(session, category.id) is None


@pytest.fixture
def linked_document(session):
    category = service.create(session, "高等数学")
    now = datetime.now(UTC)
    document = Document(
        title="笔记",
        content="正文",
        source_type="paste",
        content_format="txt",
        category_id=category.id,
        created_at=now,
        updated_at=now,
    )
    session.add(document)
    session.flush()
    chunk = Chunk(
        document_id=document.id,
        chunk_index=0,
        content="正文",
        start_offset=0,
        end_offset=2,
        created_at=now,
    )
    session.add(chunk)
    session.flush()
    ids = category.id, document.id, chunk.id
    session.commit()
    return ids


def test_delete_keeps_document_and_chunk(session, db_engine, linked_document):
    cat_id, doc_id, chunk_id = linked_document
    service.delete(session, cat_id)
    session.commit()

    with Session(db_engine) as reader:
        assert reader.get(Category, cat_id) is None
        document = reader.get(Document, doc_id)
        assert document.category_id is None
        assert document.content == "正文"
        assert reader.get(Chunk, chunk_id).document_id == doc_id


def test_delete_can_be_rolled_back(session, db_engine, linked_document):
    cat_id, doc_id, chunk_id = linked_document
    service.delete(session, cat_id)
    session.rollback()

    with Session(db_engine) as reader:
        assert reader.get(Category, cat_id).name == "高等数学"
        assert reader.get(Document, doc_id).category_id == cat_id
        assert reader.get(Chunk, chunk_id).document_id == doc_id
