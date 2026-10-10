"""配置：从 backend/.env 读取，没有就用默认值。"""
import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://postgres:postgres@localhost:5432/mydocagent",
)
