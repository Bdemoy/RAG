from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from sqlmodel import Session

from app.adapters.knowledge_access import IndexingKnowledgeAccess
from app.categories.router import router as categories_router
from app.documents.router import router as documents_router
from app.infrastructure.db import get_session, init_db
from app.qa import router as qa


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="MyDocAgent", lifespan=lifespan)

app.include_router(categories_router)
app.include_router(documents_router)
app.include_router(qa.router)


def knowledge_factory(session: Session = Depends(get_session)) -> qa.KnowledgeFactory:
    return lambda category_id: IndexingKnowledgeAccess(session, category_id)


app.dependency_overrides[qa.get_knowledge_factory] = knowledge_factory


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
