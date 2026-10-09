from fastapi.testclient import TestClient

from app.main import app


def test_health():
    # 不用 with TestClient(...)，lifespan 不执行，没有数据库也能跑
    assert TestClient(app).get("/health").json() == {"status": "ok"}
