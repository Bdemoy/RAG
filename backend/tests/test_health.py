from fastapi.testclient import TestClient
from sqlalchemy import inspect
from app.infrastructure.db import engine
from app.main import app


def test_health():
    with TestClient(app) as client:
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


def test_startup_creates_tables():
    with TestClient(app):
        tables = inspect(engine).get_table_names()

        assert "categories" in tables
        assert "documents" in tables
        assert "chunks" in tables


def test_docs():
    with TestClient(app) as client:
        response = client.get("/docs")

        assert response.status_code == 200
