from collections.abc import Callable

from fastapi import APIRouter, Depends

from app.qa import service
from app.qa.models import AskRequest, AskResult
from app.qa.ports import KnowledgeAccess

router = APIRouter(prefix="/qa", tags=["qa"])

KnowledgeFactory = Callable[[int | None], KnowledgeAccess]


def get_knowledge_factory() -> KnowledgeFactory:
    """占位，由 main.py 注入真正的实现。"""
    raise NotImplementedError


@router.post("/ask")
def ask(
    body: AskRequest, make: KnowledgeFactory = Depends(get_knowledge_factory)
) -> AskResult:
    knowledge = make(body.category_id)
    return service.ask(body.question, knowledge)
