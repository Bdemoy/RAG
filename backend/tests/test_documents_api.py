from datetime import UTC, datetime

import pytest
from sqlmodel import Session

from app.documents import service
from app.documents.models import Document
from app.indexing.models import Chunk


@pytest.fixture
def saved_document(db_engine):
    with Session(db_engine) as session:
        document = service.insert(session, "笔记", "完整正文", "paste", "txt", None)
        chunk = Chunk(
            document_id=document.id, chunk_index=0, content="完整正文",
            start_offset=0, end_offset=4, created_at=datetime.now(UTC),
        )
        session.add(chunk)
        session.flush()
        ids = document.id, chunk.id
        session.commit()
        return ids


def test_get_and_list_return_complete_document(client, saved_document):
    doc_id, _ = saved_document
    response = client.get(f"/documents/{doc_id}")
    assert response.status_code == 200
    document = response.json()
    assert (document["id"], document["title"], document["content"]) == (doc_id, "笔记", "完整正文")
    assert document["category_id"] is None
    assert document["source_type"] == "paste"
    assert document["content_format"] == "txt"
    assert document["created_at"] and document["updated_at"]
    assert client.get("/documents?page=1&size=1").json() == [document]
    assert client.get("/documents?page=2&size=1").json() == []


@pytest.mark.parametrize("method", ["get", "delete"])
def test_missing_document_returns_404(client, method):
    assert client.request(method, "/documents/999").status_code == 404


def test_delete_returns_204_and_cascades_chunks(client, db_engine, saved_document):
    doc_id, chunk_id = saved_document
    response = client.delete(f"/documents/{doc_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/documents").json() == []
    with Session(db_engine) as reader:
        assert reader.get(Document, doc_id) is None
        assert reader.get(Chunk, chunk_id) is None


def test_delete_commit_failure_keeps_document_and_chunk(client, db_engine, saved_document, monkeypatch):
    doc_id, chunk_id = saved_document

    def failed_commit(self):
        raise RuntimeError("测试提交失败")

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", failed_commit)
        assert client.delete(f"/documents/{doc_id}").status_code == 500
    assert client.get(f"/documents/{doc_id}").status_code == 200
    with Session(db_engine) as reader:
        assert reader.get(Chunk, chunk_id) is not None
