"""缓存装饰器。

基于 app/db/redis.py 的 cache_get/cache_set/cache_delete 实现，
支持 JSON 序列化函数返回值，支持 cache bypass。
"""

from __future__ import annotations

import functools
import hashlib
import json
from collections.abc import Callable
from typing import Any

from app.db.redis import cache_delete, cache_get, cache_set


def _make_cache_key(key_prefix: str, args: tuple, kwargs: dict) -> str:
    """根据函数参数生成缓存 key。"""
    # 排除 self/cls 参数
    sig_args = args[1:] if args and hasattr(args[0], "__class__") else args
    payload = {"args": list(_normalize(arg) for arg in sig_args), "kwargs": kwargs}
    serialized = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{key_prefix}:{digest}"


def _normalize(value: Any) -> Any:
    """将参数转换为可 JSON 序列化的形式。"""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    return str(value)


def cached(
    key_prefix: str,
    ttl: int = 3600,
    *,
    bypass_param: str | None = None,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """缓存装饰器。

    Args:
        key_prefix: 缓存 key 前缀
        ttl: 缓存过期时间（秒）
        bypass_param: 若指定，当 kwargs 中该参数为 True 时跳过缓存

    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 支持 cache bypass
            if bypass_param is not None and kwargs.pop(bypass_param, False):
                return func(*args, **kwargs)

            cache_key = _make_cache_key(key_prefix, args, kwargs)
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                try:
                    return json.loads(cached_value)
                except (json.JSONDecodeError, TypeError):
                    pass

            result = func(*args, **kwargs)
            try:
                cache_set(cache_key, json.dumps(result, ensure_ascii=False, default=str), ttl=ttl)
            except (TypeError, ValueError):
                pass
            return result

        wrapper.cache_delete = cache_delete  # type: ignore[attr-defined]
        return wrapper

    return decorator
