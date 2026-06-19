"""AI 输出安全与内容过滤工具。

提供敏感词过滤、AI 输出字段校验和 XSS 清理能力。
"""

from __future__ import annotations

import html
import logging
import re

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)

# 基础敏感词列表（可按需扩展）
SENSITIVE_WORDS: list[str] = [
    "fuck",
    "shit",
    "bitch",
    "asshole",
    "dick",
    "cunt",
    "porn",
    "nude",
    "sex",
    "nigger",
    "faggot",
    "slut",
    "whore",
    "damn",
    "hell",
]

# 预编译敏感词正则（不区分大小写，词边界匹配）
_SENSITIVE_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(w) for w in SENSITIVE_WORDS) + r")\b",
    re.IGNORECASE,
)

# 潜在 XSS / 脚本注入模式
_XSS_PATTERNS = [
    re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*object[^>]*>.*?<\s*/\s*object\s*>", re.IGNORECASE | re.DOTALL),
    re.compile(r"<\s*embed[^>]*>", re.IGNORECASE),
    re.compile(r"javascript\s*:", re.IGNORECASE),
    re.compile(r"on\w+\s*=\s*['\"][^'\"]*['\"]", re.IGNORECASE),
    re.compile(r"<\s*img[^>]*onerror[^>]*>", re.IGNORECASE),
]


def filter_sensitive_words(text: str) -> str:
    """将文本中的敏感词替换为 ***。"""
    if not text:
        return text
    return _SENSITIVE_PATTERN.sub("***", text)


def sanitize_content(content: str) -> str:
    """清理内容，去除潜在 XSS 并转义 HTML，再过滤敏感词。

    处理顺序：
    1. 移除脚本/事件注入标签
    2. HTML 转义剩余特殊字符
    3. 过滤敏感词
    """
    if not content:
        return content
    cleaned = content
    for pattern in _XSS_PATTERNS:
        cleaned = pattern.sub("", cleaned)
    cleaned = html.escape(cleaned, quote=True)
    cleaned = filter_sensitive_words(cleaned)
    return cleaned


def validate_ai_output(output: dict, required_fields: list[str]) -> dict:
    """校验 AI 输出是否包含必需字段。

    缺失字段时抛出 AppException(502, ai_response_invalid)。
    """
    if not isinstance(output, dict):
        raise AppException(
            status_code=502,
            code="ai_response_invalid",
            message="AI 输出不是 JSON 对象",
        )
    missing = [field for field in required_fields if field not in output]
    if missing:
        logger.warning("AI output missing required fields: %s", missing)
        raise AppException(
            status_code=502,
            code="ai_response_invalid",
            message=f"AI 输出缺少必需字段：{', '.join(missing)}",
        )
    return output
