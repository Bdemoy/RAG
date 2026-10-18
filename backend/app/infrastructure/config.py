"""配置：从 backend/.env 读取，没有就用默认值。"""
import os

from dotenv import load_dotenv

load_dotenv()

EMBEDDING_API_KEY = os.getenv("EMBEDDING_API_KEY", "")
EMBEDDING_URL = os.getenv(
    "EMBEDDING_URL",
    "https://api.siliconflow.cn/v1/embeddings",
)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/mydocagent",
)
