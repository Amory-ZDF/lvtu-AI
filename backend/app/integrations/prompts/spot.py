"""机位推荐 prompt 模板。"""

from __future__ import annotations

SPOT_SYSTEM_PROMPT = (
    "你是一位旅行摄影机位专家，擅长根据目的地、具体地点和拍摄时段，"
    "推荐最佳构图、拍摄时间和出片技巧。\n\n"
    "输出要求：\n"
    "1. 必须返回严格的 JSON 对象，不要包含任何额外文字或 Markdown 代码块标记。\n"
    '2. JSON 结构：{"name": "...", "composition": "...", "best_time": "...", '
    '"photo_score": 9.0, "tips": "..."}\n'
    "3. 字段说明：\n"
    "   - name: 机位名称\n"
    "   - composition: 构图建议\n"
    "   - best_time: 最佳拍摄时间\n"
    "   - photo_score: 出片评分（0-10 浮点数，保留 1 位小数）\n"
    "   - tips: 拍摄小贴士"
)

SPOT_USER_PROMPT_TEMPLATE = (
    "请根据以下信息推荐摄影机位：\n"
    "目的地：{destination}\n"
    "地点：{location_name}\n"
    "{time_line}\n"
    "请返回 JSON 格式的机位推荐结果。"
)


def build_spot_prompt(
    destination: str,
    location_name: str,
    time_of_day: str | None = None,
) -> list[dict]:
    """构建机位推荐 prompt 的 messages 列表。"""
    time_line = f"拍摄时段：{time_of_day}" if time_of_day else "拍摄时段：不限"
    user_content = SPOT_USER_PROMPT_TEMPLATE.format(
        destination=destination,
        location_name=location_name,
        time_line=time_line,
    )
    return [
        {"role": "system", "content": SPOT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
