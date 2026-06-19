"""行程调整 prompt 模板。"""

from __future__ import annotations

ADJUSTMENT_SYSTEM_PROMPT = (
    "你是一位旅行行程调整助手，擅长根据用户的自然语言指令和当前行程，"
    "生成结构化的行程变更方案。\n\n"
    "输出要求：\n"
    "1. 必须返回严格的 JSON 对象，不要包含任何额外文字或 Markdown 代码块标记。\n"
    '2. JSON 结构：{"changes": [{type, day_id, point_id, changes}], "summary": "..."}\n'
    "3. 字段说明：\n"
    "   - changes: 变更列表，每条变更包含：\n"
    "     - type: 变更类型（modify / delete / add）\n"
    "     - day_id: 受影响的天 ID\n"
    "     - point_id: 受影响的点位 ID（add 类型可为 null）\n"
    "     - changes: 变更内容描述\n"
    "   - summary: 变更摘要字符串"
)

ADJUSTMENT_USER_PROMPT_TEMPLATE = (
    "请根据以下信息调整行程：\n"
    "调整指令：{instruction}\n"
    "当前行程：{current_itinerary}\n"
    "{target_day_line}\n"
    "请返回 JSON 格式的行程调整结果。"
)


def build_adjustment_prompt(
    instruction: str,
    current_itinerary: str,
    target_day: str | None = None,
) -> list[dict]:
    """构建行程调整 prompt 的 messages 列表。"""
    target_day_line = f"目标日期：{target_day}" if target_day else "目标日期：不限"
    user_content = ADJUSTMENT_USER_PROMPT_TEMPLATE.format(
        instruction=instruction,
        current_itinerary=current_itinerary,
        target_day_line=target_day_line,
    )
    return [
        {"role": "system", "content": ADJUSTMENT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
