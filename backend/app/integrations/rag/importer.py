"""知识导入器：将目的地、机位、穿搭知识导入向量存储。

框架代码，具体数据导入逻辑待后续实现。
"""

from __future__ import annotations

import logging

from app.integrations.rag.store import VectorStore

logger = logging.getLogger(__name__)


class KnowledgeImporter:
    """知识库导入器，负责将结构化知识导入向量存储。"""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def import_destinations(self, data: list[dict]) -> None:
        """导入目的地知识。

        每个 dict 应包含目的地名称、描述、最佳季节、预算等信息，
        导入时会拼接为 content 文本并保留原始字段作为 metadata。
        """
        documents: list[dict] = []
        for item in data:
            name = item.get("name", "")
            country = item.get("country_or_region", "")
            best_season = item.get("best_season", "")
            budget = item.get("budget_range", "")
            vibe_tags = item.get("vibe_tags", [])
            reasons = item.get("reasons", [])

            content_parts = [f"目的地：{name}", f"国家/地区：{country}"]
            if best_season:
                content_parts.append(f"最佳季节：{best_season}")
            if budget:
                content_parts.append(f"预算：{budget}")
            if vibe_tags:
                content_parts.append(f"氛围标签：{', '.join(vibe_tags)}")
            if reasons:
                content_parts.append(f"推荐理由：{'; '.join(reasons)}")

            documents.append(
                {
                    "content": "\n".join(content_parts),
                    "source": "destinations",
                    "metadata": item,
                },
            )

        self._store.add_documents(documents)
        logger.info("Imported %d destination documents", len(documents))

    def import_spots(self, data: list[dict]) -> None:
        """导入机位知识。

        每个 dict 应包含机位名称、目的地、构图建议、最佳时间等信息。
        """
        documents: list[dict] = []
        for item in data:
            name = item.get("name", "")
            destination = item.get("destination", "")
            composition = item.get("composition", "")
            best_time = item.get("best_time", "")
            tips = item.get("tips", "")

            content_parts = [f"机位：{name}"]
            if destination:
                content_parts.append(f"目的地：{destination}")
            if composition:
                content_parts.append(f"构图：{composition}")
            if best_time:
                content_parts.append(f"最佳时间：{best_time}")
            if tips:
                content_parts.append(f"拍摄技巧：{tips}")

            documents.append(
                {
                    "content": "\n".join(content_parts),
                    "source": "spots",
                    "metadata": item,
                },
            )

        self._store.add_documents(documents)
        logger.info("Imported %d spot documents", len(documents))

    def import_outfits(self, data: list[dict]) -> None:
        """导入穿搭知识。

        每个 dict 应包含穿搭单品、目的地、季节、场景等信息。
        """
        documents: list[dict] = []
        for item in data:
            destination = item.get("destination", "")
            season = item.get("season", "")
            scene = item.get("scene", "")
            style = item.get("style", "")
            items = item.get("items", [])
            tips = item.get("tips", "")

            content_parts: list[str] = []
            if destination:
                content_parts.append(f"目的地：{destination}")
            if season:
                content_parts.append(f"季节：{season}")
            if scene:
                content_parts.append(f"场景：{scene}")
            if style:
                content_parts.append(f"风格：{style}")
            if items:
                item_names = [
                    i.get("name", "") if isinstance(i, dict) else str(i) for i in items
                ]
                content_parts.append(f"单品：{', '.join(item_names)}")
            if tips:
                content_parts.append(f"穿搭贴士：{tips}")

            documents.append(
                {
                    "content": "\n".join(content_parts),
                    "source": "outfits",
                    "metadata": item,
                },
            )

        self._store.add_documents(documents)
        logger.info("Imported %d outfit documents", len(documents))
