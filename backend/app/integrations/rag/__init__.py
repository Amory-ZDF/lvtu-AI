"""RAG（检索增强生成）框架模块。

提供向量存储抽象、内存实现、pgvector 占位实现、检索器和知识导入器。
"""

from app.integrations.rag.importer import KnowledgeImporter
from app.integrations.rag.retriever import RagRetriever
from app.integrations.rag.store import (
    DbBackedVectorStore,
    InMemoryVectorStore,
    PgVectorStore,
    VectorStore,
    build_vector_store_from_db,
    get_vector_store,
)

__all__ = [
    "DbBackedVectorStore",
    "InMemoryVectorStore",
    "KnowledgeImporter",
    "PgVectorStore",
    "RagRetriever",
    "VectorStore",
    "build_vector_store_from_db",
    "get_vector_store",
]
