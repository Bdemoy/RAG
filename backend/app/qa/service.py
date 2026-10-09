from sqlmodel import Session

from app.qa.models import AskResult, Verdict
from app.qa.ports import KnowledgeAccess, Passage

MAX_RETRIES = 2


def ask(question: str, knowledge: KnowledgeAccess) -> AskResult:
    """检索 → 空结果直接拒答 → judge → 最多补查 MAX_RETRIES 次 → 回答/部分回答/拒答。"""
    raise NotImplementedError


def judge(question: str, passages: list[Passage]) -> Verdict:
    """让模型判断证据：sufficient / partial / none，并说明缺什么。"""
    raise NotImplementedError


def answer(question: str, passages: list[Passage]) -> tuple[str, list[int]]:
    """按 [1]..[k] 编号生成回答，返回正文和引用到的编号；编号越界抛错。"""
    raise NotImplementedError
