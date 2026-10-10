"""数据库连接。"""
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from app.infrastructure.config import DATABASE_URL

engine = create_engine(DATABASE_URL)


def get_session() -> Iterator[Session]:
    """FastAPI 依赖：每个请求一个 Session，请求结束自动关闭。"""
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """启动时调用：按模型建表（表已存在则跳过）。

    调用前必须先 import 所有 models，否则 SQLModel 不知道有哪些表。
    pgvector 装好后，在这里补 CREATE EXTENSION IF NOT EXISTS vector。
    """
    # 本机还没装 pgvector，先注释掉；装好后取消注释
    # with engine.begin() as conn:
    #     conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    SQLModel.metadata.create_all(engine)
