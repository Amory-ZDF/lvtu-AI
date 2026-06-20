"""高德地图 API 集成：POI 搜索、地理编码、周边搜索。

文档：https://lbs.amap.com/api/webservice/guide/api/search
需要在 .env 中配置 AMAP_API_KEY。
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class AmapClient:
    """高德地图开放平台 API 客户端。"""

    def __init__(self, api_key: str | None, base_url: str = "https://restapi.amap.com/v3") -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._available = bool(api_key)

    @property
    def available(self) -> bool:
        return self._available

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        if not self._available:
            raise RuntimeError("AMAP_API_KEY 未配置，无法调用高德 API")
        params = {**params, "key": self._api_key, "output": "json"}
        url = f"{self._base_url}/{path}"
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        if data.get("status") != "1":
            err = data.get("info", "unknown error")
            logger.warning("高德 API 返回错误: %s (infocode=%s)", err, data.get("infocode"))
            return {"pois": [], "count": "0", "error": err}
        return data

    def search_pois(
        self,
        keywords: str,
        city: str | None = None,
        types: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """POI 关键词搜索。

        Args:
            keywords: 搜索关键词，如 "故宫"
            city: 城市名/编码，如 "北京"
            types: POI 类型码，如 "110000"（风景名胜）
            page: 页码，从 1 开始
            page_size: 每页数量（最大 25）

        Returns:
            POI 列表，每个含 name/address/location/type/tel 等字段
        """
        params: dict[str, Any] = {
            "keywords": keywords,
            "offset": min(page_size, 25),
            "page": page,
            "extensions": "all",
        }
        if city:
            params["city"] = city
        if types:
            params["types"] = types
        data = self._get("place/text", params)
        return data.get("pois", [])

    def search_around(
        self,
        location: str,
        keywords: str | None = None,
        types: str | None = None,
        radius: int = 3000,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        """周边搜索。

        Args:
            location: 中心点坐标 "经度,纬度"，如 "116.397428,39.90923"
            keywords: 搜索关键词（可选）
            types: POI 类型码（可选）
            radius: 搜索半径（米），最大 50000
            page_size: 每页数量

        Returns:
            POI 列表
        """
        params: dict[str, Any] = {
            "location": location,
            "radius": min(radius, 50000),
            "offset": min(page_size, 25),
            "sortrule": "distance",
            "extensions": "all",
        }
        if keywords:
            params["keywords"] = keywords
        if types:
            params["types"] = types
        data = self._get("place/around", params)
        return data.get("pois", [])

    def geocode(self, address: str, city: str | None = None) -> dict[str, Any] | None:
        """地理编码：地址 → 坐标。

        Returns:
            {"location": "经度,纬度", "formatted_address": "...", "level": "..."} 或 None
        """
        params: dict[str, Any] = {"address": address}
        if city:
            params["city"] = city
        data = self._get("geocode/geo", params)
        geocodes = data.get("geocodes", [])
        return geocodes[0] if geocodes else None


_amap_client: AmapClient | None = None


def get_amap_client() -> AmapClient:
    """获取高德 API 客户端单例。"""
    global _amap_client
    if _amap_client is None:
        settings = get_settings()
        _amap_client = AmapClient(
            api_key=settings.amap_api_key,
            base_url=settings.amap_base_url,
        )
    return _amap_client
