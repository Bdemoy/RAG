from datetime import datetime

import pytest
from sqlmodel import Session


def test_create_returns_complete_category_and_persists(client):
    response = client.post("/categories", json={"name": "高等数学"})

    assert response.status_code == 201
    category = response.json()
    assert isinstance(category["id"], int)
    assert category["name"] == "高等数学"
    assert datetime.fromisoformat(category["created_at"]).tzinfo is not None
    listed = client.get("/categories")
    assert listed.status_code == 200
    assert listed.json() == [category]


def test_rename_returns_complete_category_and_persists(client):
    created = client.post("/categories", json={"name": "高数"})
    assert created.status_code == 201
    category = created.json()

    response = client.patch(
        f"/categories/{category['id']}", json={"name": "高等数学"}
    )

    assert response.status_code == 200
    expected = category | {"name": "高等数学"}
    assert response.json() == expected
    assert client.get("/categories").json() == [expected]


def test_delete_returns_no_content_and_persists(client):
    created = client.post("/categories", json={"name": "高等数学"})
    assert created.status_code == 201

    response = client.delete(f"/categories/{created.json()['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get("/categories").json() == []


def test_duplicate_create_returns_409_and_keeps_original(client):
    created = client.post("/categories", json={"name": "高等数学"})
    assert created.status_code == 201

    response = client.post("/categories", json={"name": "高等数学"})

    assert response.status_code == 409
    assert response.json()["detail"]
    assert client.get("/categories").json() == [created.json()]


def test_rename_conflict_returns_409_and_keeps_originals(client):
    first = client.post("/categories", json={"name": "高等数学"})
    second = client.post("/categories", json={"name": "线性代数"})
    assert first.status_code == second.status_code == 201

    response = client.patch(
        f"/categories/{first.json()['id']}", json={"name": "线性代数"}
    )

    assert response.status_code == 409
    assert response.json()["detail"]
    assert client.get("/categories").json() == [first.json(), second.json()]


@pytest.mark.parametrize("method", ["patch", "delete"])
def test_missing_category_returns_404(client, method):
    kwargs = {"json": {"name": "高等数学"}} if method == "patch" else {}

    response = client.request(method, "/categories/999", **kwargs)

    assert response.status_code == 404
    assert response.json()["detail"]


@pytest.mark.parametrize("method", ["post", "patch", "delete"])
def test_commit_failure_rolls_back_request(client, monkeypatch, method):
    created = client.post("/categories", json={"name": "高等数学"})
    assert created.status_code == 201
    category = created.json()
    url = "/categories" if method == "post" else f"/categories/{category['id']}"
    kwargs = {} if method == "delete" else {"json": {"name": "线性代数"}}

    def failed_commit(self):
        raise RuntimeError("测试提交失败")

    with monkeypatch.context() as patch:
        patch.setattr(Session, "commit", failed_commit)
        response = client.request(method, url, **kwargs)
        assert response.status_code == 500

    assert client.get("/categories").json() == [category]
