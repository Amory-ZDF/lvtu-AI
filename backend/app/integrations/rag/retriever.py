"""RAG 检索器：将检索结果注入 prompt。"""

from __future__ import annotations

import logging

from app.integrations.rag.store import VectorStore

logger = logging.getLogger(__name__)


class RagRetriever:
    """RAG 检索器，封装向量存储并提供 prompt 增强。"""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def retrieve(self, query: str, top_k: int = 5) -> list[dict]:
        """检索与 query 相关的 top_k 个文档。"""
        return self._store.search(query, top_k=top_k)

    def augment_prompt(
        self,
        query: str,
        base_prompt: list[dict],
        top_k: int = 3,
    ) -> list[dict]:
        """将检索结果注入 prompt。

        在 system prompt 之后插入一条包含 retrieved context 的 system 消息，
        保留原始 messages 顺序。

        Args:
            query: 检索查询
            base_prompt: 原始 messages 列表
            top_k: 检索文档数量

        Returns:
            增强后的 messages 列表
        """
        retrieved = self.retrieve(query, top_k=top_k)
        if not retrieved:
            return list(base_prompt)

        context_parts: list[str] = []
        for idx, doc in enumerate(retrieved, start=1):
            content = doc.get("content", "")
            source = doc.get("source", "knowledge_base")
            context_parts.append(f"[{idx}] (来源: {source})\n{content}")

        context_block = (
            "以下是从知识库检索到的相关背景信息，请参考这些信息回答用户问题：\n\n"
            + "\n\n".join(context_parts)
        )

        augmented: list[dict] = []
        inserted = False
        for message in base_prompt:
            augmented.append(message)
            # 在第一条 system 消息后插入 retrieved context
            if not inserted and message.get("role") == "system":
                augmented.append({"role": "system", "content": context_block})
                inserted = True

        # 如果没有 system 消息，则在开头插入
        if not inserted:
            augmented.insert(0, {"role": "system", "content": context_block})

        return augmented
