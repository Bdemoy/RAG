from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine

from app.infrastructure import db
from app.main import app


@pytest.fixture
def db_engine():
    schema = "categories_test_" + uuid4().hex
    with db.engine.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    test_engine = create_engine(
        db.engine.url, connect_args={"options": f"-csearch_path={schema}"}
    )
    try:
        SQLModel.metadata.create_all(test_engine)
        yield test_engine
    finally:
        test_engine.dispose()
        with db.engine.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


@pytest.fixture
def session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture
def client(db_engine, monkeypatch):
    monkeypatch.setattr(db, "engine", db_engine)
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
