"""路线规划 prompt 模板。"""

from __future__ import annotations

from app.schemas.planning import RouteGenerationRequest

ROUTE_SYSTEM_PROMPT = (
    "你是一位专业旅行路线规划师，擅长根据目的地、行程天数、节奏偏好、出行人数和兴趣点，"
    "设计兼顾出片与体验的多日行程方案。\n\n"
    "输出要求：\n"
    "1. 必须返回严格的 JSON 对象，不要包含任何额外文字或 Markdown 代码块标记。\n"
    '2. JSON 结构：{"destination_name": "...", "options": [{id, title, pace, '
    "estimated_budget, photo_score, summary, days: [{day, theme, commute_tip, "
    "spots: [{time_slot, name, description, suggested_duration_hours}]}]}]}\n"
    "3. 字段说明：\n"
    "   - destination_name: 目的地名称\n"
    "   - options: 路线方案列表（必须且只能 2 个），每个方案包含：\n"
    "     - id: 路线唯一标识，格式 route-<slug>\n"
    "     - title: 路线标题\n"
    "     - pace: 节奏（relaxed / balanced / compact）\n"
    "     - estimated_budget: 预算估算字符串，如 \"5600 RMB\"\n"
    "     - photo_score: 出片评分（0-10 浮点数，保留 1 位小数）\n"
    "     - summary: 路线概述\n"
    "     - days: 每日计划列表，每天包含：\n"
    "       - day: 天数（从 1 开始）\n"
    "       - theme: 当日主题\n"
    "       - commute_tip: 通勤建议\n"
    "       - spots: 景点列表，每个景点包含：\n"
    "         - time_slot: 时段（上午/下午/傍晚/晚上）\n"
    "         - name: 景点名称\n"
    "         - description: 景点描述\n"
    "         - suggested_duration_hours: 建议停留时长（小时，浮点数）\n"
    "4. 每个方案的 days 数量应等于行程天数。\n"
    "5. 两个方案必须有明确差异，不能只是顺序不同：\n"
    "   - 方案 A 面向第一次来、旅行次数不多、希望稳妥覆盖经典点位的人；\n"
    "   - 方案 B 面向已经来过、旅行经验较多、希望小众机位/深度体验/慢节奏的人；\n"
    "   - 两个方案的景点名称重合率尽量低于 30%，不要重复同一景区的不同子点位；\n"
    "   - summary 需要写清楚该方案适合的人群，以及和另一个方案的核心差异。"
)

ROUTE_USER_PROMPT_TEMPLATE = (
    "请根据以下信息规划旅行路线：\n"
    "目的地：{destination_name}\n"
    "行程天数：{duration_days} 天\n"
    "节奏偏好：{pace}\n"
    "出行人数：{travelers} 人\n"
    "兴趣点：{interests}\n\n"
    "请输出两条差异化路线：A=经典初访覆盖线，B=复访深度出片线；如果目的地景点有限，"
    "也要优先保证核心动线和点位名称不重复，并在 summary 解释取舍。\n"
    "请返回 JSON 格式的路线规划结果。"
)


def build_route_prompt(request: RouteGenerationRequest) -> list[dict]:
    """构建路线规划 prompt 的 messages 列表。"""
    interests = "/".join(request.interests) if request.interests else "不限"
    user_content = ROUTE_USER_PROMPT_TEMPLATE.format(
        destination_name=request.destination_name,
        duration_days=request.duration_days,
        pace=request.pace,
        travelers=request.travelers,
        interests=interests,
    )
    return [
        {"role": "system", "content": ROUTE_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
