"""向量存储抽象与实现。

- VectorStore：抽象基类（Protocol）
- InMemoryVectorStore：基于关键词匹配的内存实现
- PgVectorStore：pgvector 占位实现（不可用时降级）
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Protocol

logger = logging.getLogger(__name__)


class VectorStore(Protocol):
    """向量存储抽象协议。"""

    def add_documents(self, documents: list[dict]) -> None:
        """添加文档到向量存储。每个 document 是一个 dict，至少包含 'content' 字段。"""
        ...

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """根据查询检索 top_k 个最相关文档，返回包含 score 的文档列表。"""
        ...


def _tokenize(text: str) -> list[str]:
    """简单分词：英文按单词切分，中文按字符切分（字符级匹配）。

    中文分词较为复杂，这里采用字符级切分作为简化方案，
    使得 "京都红叶" 与 "京都的红叶很美" 能通过共享字符 "京都"/"红叶" 匹配。
    """
    if not text:
        return []
    tokens: list[str] = []
    # 先按非字母数字汉字字符切分原始片段
    segments = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z0-9]+", text.lower())
    for segment in segments:
        if re.fullmatch(r"[a-zA-Z0-9]+", segment):
            # 英文/数字：整体作为一个 token
            tokens.append(segment)
        else:
            # 中文：按单字切分，同时生成 bi-gram 提升短语匹配能力
            chars = list(segment)
            tokens.extend(chars)
            for i in range(len(chars) - 1):
                tokens.append(chars[i] + chars[i + 1])
    return tokens


def _compute_tfidf_scores(
    query_tokens: list[str],
    document_tokens: list[str],
    document_freq: Counter,
    total_documents: int,
) -> float:
    """计算 query 与 document 的 TF-IDF 相似度得分。"""
    if not query_tokens or not document_tokens:
        return 0.0

    doc_counter = Counter(document_tokens)
    doc_len = len(document_tokens)
    score = 0.0

    for term in set(query_tokens):
        if term not in doc_counter:
            continue
        # TF
        tf = doc_counter[term] / doc_len
        # IDF（加 1 平滑避免除零）
        df = document_freq.get(term, 0)
        idf = math.log((total_documents + 1) / (df + 1)) + 1
        score += tf * idf

    return score


class InMemoryVectorStore:
    """基于 TF-IDF 关键词匹配的内存向量存储。

    不依赖外部向量库，适合开发环境和小规模知识库。
    """

    def __init__(self) -> None:
        self._documents: list[dict] = []
        self._document_tokens: list[list[str]] = []
        self._document_freq: Counter = Counter()

    def add_documents(self, documents: list[dict]) -> None:
        """添加文档到内存存储。"""
        for doc in documents:
            content = str(doc.get("content", ""))
            tokens = _tokenize(content)
            self._documents.append(doc)
            self._document_tokens.append(tokens)
            for term in set(tokens):
                self._document_freq[term] += 1

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """根据 query 检索 top_k 个最相关文档。

        返回的每个文档 dict 会附加 'score' 字段表示相关度。
        """
        if not self._documents:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        total = len(self._documents)
        scored: list[tuple[float, dict]] = []
        for idx, doc_tokens in enumerate(self._document_tokens):
            score = _compute_tfidf_scores(
                query_tokens,
                doc_tokens,
                self._document_freq,
                total,
            )
            if score > 0:
                result = dict(self._documents[idx])
                result["score"] = round(score, 4)
                scored.append((score, result))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]


class PgVectorStore:
    """pgvector 实现的向量存储（占位骨架）。

    当前只提供骨架，不实现具体逻辑。
    实际使用时需要安装 pgvector 扩展并配置连接。
    """

    def __init__(self, database_url: str | None = None) -> None:
        self._database_url = database_url
        self._available = False
        logger.warning(
            "PgVectorStore is not yet implemented; operations will be no-ops. "
            "Consider using InMemoryVectorStore instead.",
        )

    def add_documents(self, documents: list[dict]) -> None:
        """占位实现：暂不存储文档。"""
        logger.debug("PgVectorStore.add_documents called with %d docs (no-op)", len(documents))

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """占位实现：返回空列表。"""
        logger.debug("PgVectorStore.search called (no-op, returning empty list)")
        return []


def get_vector_store(settings: object | None = None) -> VectorStore:
    """向量存储工厂函数。

    检查 pgvector 是否可用，不可用则降级到 InMemoryVectorStore。
    """
    # 尝试检测 pgvector 是否可用
    try:
        import psycopg  # noqa: F401

        has_psycopg = True
    except ImportError:
        has_psycopg = False

    if not has_psycopg:
        logger.warning(
            "pgvector/psycopg not available, falling back to InMemoryVectorStore",
        )
        return InMemoryVectorStore()

    # 即使 psycopg 可用，pgvector 扩展也需要数据库侧配置，
    # 当前阶段统一降级到内存实现，避免连接失败。
    logger.warning(
        "pgvector not fully configured, falling back to InMemoryVectorStore",
    )
    return InMemoryVectorStore()
