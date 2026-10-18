from sqlmodel import Session
from openai import OpenAI
from app.infrastructure import config
from app.indexing.models import ChunkDraft, SearchHit
import re

CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
BATCH_SIZE = 16

def split_content(
    content: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[tuple[str | None, str, int, int]]:
    """按 Markdown 标题和长度切分，返回 (heading, text, start_offset, end_offset) 列表。"""
    if not content or not content.strip():
        return []

    # 1. 找出所有 Markdown 标题的位置，把文章分成一个个章节 (heading, sec_start, sec_end)
    matches = list(_HEADING_RE.finditer(content))
    sections: list[tuple[str | None, int, int]] = []

    if not matches:
        # 没有任何 Markdown 标题（比如普通 txt），整篇文章就是一个章节，heading 为 None
        sections.append((None, 0, len(content)))
    else:
        # 如果第一个标题前还有前言文字，先把前言当成一个 heading=None 的章节
        if matches[0].start() > 0:
            sections.append((None, 0, matches[0].start()))
        # 每个标题管辖从自己开始、到下一个标题之前（或文章末尾）的范围
        for i, match in enumerate(matches):
            heading_text = match.group(2).strip()
            sec_start = match.start()
            sec_end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            sections.append((heading_text, sec_start, sec_end))

    # 2. 在每个章节内部按 chunk_size (600) 和 overlap (100) 切块
    chunks: list[tuple[str | None, str, int, int]] = []
    for heading, sec_start, sec_end in sections:
        pos = sec_start
        while pos < sec_end:
            # 先跳过开头的空白字符，避免切出纯空格开头的块
            while pos < sec_end and content[pos].isspace():
                pos += 1
            if pos >= sec_end:
                break

            # 如果剩下的内容不到 600 字，直接一口气收到章节末尾
            if sec_end - pos <= chunk_size:
                end = sec_end
            else:
                end = pos + chunk_size
                # 优先在后半段找段落换行 "\n\n" 或单行换行 "\n" 落刀，避免劈断句子
                half = pos + chunk_size // 2
                newline_pos = content.rfind("\n", half, end)
                if newline_pos != -1:
                    end = newline_pos + 1

            # 去掉块末尾多余的空白字符（通过左移 end 游标，不破坏 offset！）
            real_end = end
            while real_end > pos and content[real_end - 1].isspace():
                real_end -= 1

            if real_end > pos:
                chunks.append((heading, content[pos:real_end], pos, real_end))

            if end >= sec_end:
                break
            # 下一块的起点：往回退 overlap (100) 个字符，但必须保证比当前 pos 往前走
            pos = max(pos + 1, end - overlap)

    return chunks

def embed_texts(texts: list[str]) -> list[list[float]]:
    """分批调用硅基流动 Embedding 接口，每批最多 16 条。"""
    client = OpenAI(
        api_key=config.EMBEDDING_API_KEY,
        base_url=config.EMBEDDING_URL,   # "https://api.siliconflow.cn/v1"
        timeout=15.0,
    )
    vectors: list[list[float]] = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i : i + BATCH_SIZE]
        resp = client.embeddings.create(model=config.EMBEDDING_MODEL, input=batch)
        vectors.extend(item.embedding for item in resp.data)
    return vectors

def prepare_chunks(content: str) -> list[ChunkDraft]:
    """切分 + 批量生成向量。不写库；Embedding 失败直接抛错。"""
    parts=split_content(content)
    if not parts:
        return []

    texts=[text for _ , text , _ , in parts]
    embeddings=embed_texts(texts)

    drafts:list[ChunkDraft]=[]
    for i,(part,embedding) in enumerate(zip(parts,embeddings,strict=True)):
        heading,text,start,end=part
        drafts.append(
            ChunkDraft(
                index=i,
                heading=heading,
                content=text,
                start_offset=start,
                end_offset=end,
                embedding=embedding
            )
        )
    return drafts


def save_chunks(session: Session, document_id: int, drafts: list[ChunkDraft]) -> int:
    """只 add，不 commit，提交由调用方决定。返回块数。"""
    raise NotImplementedError


def replace_chunks(session: Session, document_id: int, drafts: list[ChunkDraft]) -> int:
    """删旧块 + 插新块，同样不 commit。"""
    raise NotImplementedError


def search(
    session: Session, query: str, category_id: int | None, top_k: int = 5
) -> list[SearchHit]:
    """向量检索。category_id 为 None 表示全部资料。
    需要 documents 的 title、category_id 时用 SQL join 表名，不 import documents。"""
    raise NotImplementedError


def neighbors(session: Session, chunk_id: int, window: int = 1) -> list[SearchHit]:
    """同一文档内 chunk_index 在 ±window 范围的块。"""
    raise NotImplementedError
