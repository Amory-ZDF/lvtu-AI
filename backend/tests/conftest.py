"""Pytest 全局配置。

在导入 app.main 之前禁用限流，避免现有测试因共享单例 app 的内存限流计数器而互相干扰。
限流功能由 tests/test_rate_limit.py 通过独立 app 实例验证。
"""

import os

os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
