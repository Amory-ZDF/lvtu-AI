"""Redis 客户端封装（可选导入）。

尝试导入 redis-py，失败则降级到内存实现。
不添加 redis 到 pyproject.toml 依赖，用户无需安装 Redis 即可运行。
"""

from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

try:
    import redis as _redis  # type: ignore[import-not-found]

    _REDIS_AVAILABLE = True
except ImportError:
    _redis = None  # type: ignore[assignment]
    _REDIS_AVAILABLE = False


class _InMemoryBackend:
    """内存降级实现：使用 dict + 过期时间。"""

    def __init__(self) -> None:
        # {key: (value, expire_timestamp | None)}
        self._store: dict[str, tuple[str, float | None]] = {}

    def _is_expired(self, expire_at: float | None) -> bool:
        return expire_at is not None and time.time() > expire_at

    def get(self, key: str) -> str | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if self._is_expired(expire_at):
            self._store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: str, ttl: int | None = None) -> None:
        expire_at = time.time() + ttl if ttl else None
        self._store[key] = (value, expire_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def exists(self, key: str) -> bool:
        return self.get(key) is not None

    def flushdb(self) -> None:
        self._store.clear()


# 全局单例
_redis_client: Any = None
_inmemory_backend: _InMemoryBackend | None = None


def get_redis() -> Any:
    """返回 Redis 客户端或 None。

    如果 redis-py 可用且配置了 REDIS_URL，返回 Redis 客户端。
    否则返回 None（调用方应使用 cache_get/cache_set 等封装函数，
    它们会自动降级到内存实现）。
    """
    global _redis_client, _inmemory_backend

    if _REDIS_AVAILABLE:
        if _redis_client is not None:
            return _redis_client
        try:
            from app.core.config import get_settings

            settings = get_settings()
            redis_url = getattr(settings, "effective_redis_url", None)
            if redis_url:
                _redis_client = _redis.from_url(redis_url, decode_responses=True)
                logger.info("Redis client connected: %s", redis_url)
                return _redis_client
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to connect to Redis, falling back to memory: %s", exc)

    # 降级到内存实现
    if _inmemory_backend is None:
        _inmemory_backend = _InMemoryBackend()
        logger.info("Redis unavailable, using in-memory cache backend")
    return None


def get_redis_client() -> Any:
    """返回 Redis 客户端或 None（用于健康检查等场景）。

    与 get_redis 相同语义：Redis 可用且配置了连接信息时返回客户端，否则返回 None。
    """
    return get_redis()


def _get_backend() -> _InMemoryBackend:
    """获取内存后端（仅在 Redis 不可用时使用）。"""
    global _inmemory_backend
    if _inmemory_backend is None:
        _inmemory_backend = _InMemoryBackend()
    return _inmemory_backend


def cache_get(key: str) -> str | None:
    """获取缓存值，不存在返回 None。"""
    client = get_redis()
    if client is not None:
        try:
            return client.get(key)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis get failed, using memory: %s", exc)
    return _get_backend().get(key)


def cache_set(key: str, value: str, ttl: int = 3600) -> None:
    """写入缓存，ttl 单位为秒。"""
    client = get_redis()
    if client is not None:
        try:
            client.set(key, value, ex=ttl)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis set failed, using memory: %s", exc)
    _get_backend().set(key, value, ttl=ttl)


def cache_delete(key: str) -> None:
    """删除缓存键。"""
    client = get_redis()
    if client is not None:
        try:
            client.delete(key)
            return
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis delete failed, using memory: %s", exc)
    _get_backend().delete(key)
