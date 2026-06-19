"""Prompt 模板工程模块。

按业务域拆分 prompt 模板，每个模块提供：
- 系统提示常量（*_SYSTEM_PROMPT）
- 用户提示模板常量（*_USER_PROMPT_TEMPLATE）
- build_*_prompt 函数：返回 OpenAI Chat Completions 兼容的 messages 列表
"""

from app.integrations.prompts.adjustment import (
    ADJUSTMENT_SYSTEM_PROMPT,
    ADJUSTMENT_USER_PROMPT_TEMPLATE,
    build_adjustment_prompt,
)
from app.integrations.prompts.destination import (
    DESTINATION_SYSTEM_PROMPT,
    DESTINATION_USER_PROMPT_TEMPLATE,
    build_destination_prompt,
)
from app.integrations.prompts.outfit import (
    OUTFIT_SYSTEM_PROMPT,
    OUTFIT_USER_PROMPT_TEMPLATE,
    build_outfit_prompt,
)
from app.integrations.prompts.route import (
    ROUTE_SYSTEM_PROMPT,
    ROUTE_USER_PROMPT_TEMPLATE,
    build_route_prompt,
)
from app.integrations.prompts.spot import (
    SPOT_SYSTEM_PROMPT,
    SPOT_USER_PROMPT_TEMPLATE,
    build_spot_prompt,
)

__all__ = [
    "ADJUSTMENT_SYSTEM_PROMPT",
    "ADJUSTMENT_USER_PROMPT_TEMPLATE",
    "build_adjustment_prompt",
    "DESTINATION_SYSTEM_PROMPT",
    "DESTINATION_USER_PROMPT_TEMPLATE",
    "build_destination_prompt",
    "OUTFIT_SYSTEM_PROMPT",
    "OUTFIT_USER_PROMPT_TEMPLATE",
    "build_outfit_prompt",
    "ROUTE_SYSTEM_PROMPT",
    "ROUTE_USER_PROMPT_TEMPLATE",
    "build_route_prompt",
    "SPOT_SYSTEM_PROMPT",
    "SPOT_USER_PROMPT_TEMPLATE",
    "build_spot_prompt",
]
