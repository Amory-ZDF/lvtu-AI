"""AI 响应缓存。

内存实现（dict + 过期时间），后续可替换为 Redis。
"""

from __future__ import annotations

import hashlib
import json
import logging
import time

logger = logging.getLogger(__name__)


class ResponseCache:
    """基于内存 dict 的响应缓存，支持 TTL。"""

    def __init__(self) -> None:
        # {key: (value, expire_timestamp)}
        self._store: dict[str, tuple[dict, float]] = {}

    def get(self, key: str) -> dict | None:
        """获取缓存值，过期或不存在返回 None。"""
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if time.time() > expire_at:
            # 惰性过期
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: dict, ttl: int = 3600) -> None:
        """写入缓存，ttl 单位为秒。"""
        expire_at = time.time() + ttl
        self._store[key] = (value, expire_at)

    @staticmethod
    def make_key(request_data: dict) -> str:
        """根据请求数据生成缓存 key（SHA256 hash）。

        将 request_data 序列化为稳定 JSON 字符串后取 hash，
        确保相同请求参数生成相同 key。
        """
        serialized = json.dumps(request_data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def cleanup_expired(self) -> int:
        """清理所有已过期的缓存项，返回清理数量。"""
        now = time.time()
        expired_keys = [k for k, (_, expire_at) in self._store.items() if now > expire_at]
        for key in expired_keys:
            self._store.pop(key, None)
        if expired_keys:
            logger.debug("Cleaned up %d expired cache entries", len(expired_keys))
        return len(expired_keys)

    def clear(self) -> None:
        """清空所有缓存。"""
        self._store.clear()
