"""目的地推荐 prompt 模板。"""

from __future__ import annotations

from app.schemas.planning import DestinationRecommendationRequest

DESTINATION_SYSTEM_PROMPT = (
    "你是一位资深旅行专家，擅长根据用户的出发地、行程天数、季节偏好、旅行风格、"
    "兴趣点和预算等级，推荐契合度高的目的地。你需要结合目的地的出片潜力、"
    "交通友好度、季节适配性和整体氛围给出客观建议。\n\n"
    "输出要求：\n"
    "1. 必须返回严格的 JSON 对象，不要包含任何额外文字或 Markdown 代码块标记。\n"
    '2. JSON 结构：{"destinations": [{id, name, country_or_region, match_score, '
    "budget_range, best_season, vibe_tags, reasons, hero_image_description, "
    "gallery_descriptions}]}\n"
    "3. 字段说明：\n"
    "   - id: 目的地唯一标识，格式 dest-<slug>\n"
    "   - name: 目的地名称\n"
    "   - country_or_region: 所属国家或地区\n"
    "   - match_score: 匹配度评分（0-100 整数）\n"
    "   - budget_range: 预算区间字符串，如 \"4200-5800 RMB\"\n"
    "   - best_season: 最佳出行季节描述\n"
    "   - vibe_tags: 氛围标签字符串列表（3-5 个）\n"
    "   - reasons: 推荐理由字符串列表（2-4 条）\n"
    "   - hero_image_description: 主图画面描述（用于后续图像生成）\n"
    "   - gallery_descriptions: 画廊画面描述字符串列表（2 条）\n"
    "4. 推荐数量为 3 个，按 match_score 降序排列。"
)

DESTINATION_USER_PROMPT_TEMPLATE = (
    "请根据以下信息推荐旅行目的地：\n"
    "出发城市：{departure_city}\n"
    "行程天数：{duration_days} 天\n"
    "季节偏好：{season}\n"
    "旅行风格：{travel_style}\n"
    "兴趣点：{interests}\n"
    "预算等级：{budget_level}\n\n"
    "请返回 JSON 格式的推荐结果。"
)


def build_destination_prompt(
    request: DestinationRecommendationRequest,
) -> list[dict]:
    """构建目的地推荐 prompt 的 messages 列表。

    返回 OpenAI Chat Completions 兼容格式：
    [{"role": "system", "content": ...}, {"role": "user", "content": ...}]
    """
    departure_city = request.departure_city or "未指定"
    season = request.season or "不限"
    travel_style = "/".join(request.travel_style) if request.travel_style else "不限"
    interests = "/".join(request.interests) if request.interests else "不限"
    if request.budget_min is not None and request.budget_max is not None:
        budget_level = f"{request.budget_min}-{request.budget_max} RMB"
    elif request.budget_max is not None:
        budget_level = f"≤{request.budget_max} RMB"
    else:
        budget_level = "不限"

    user_content = DESTINATION_USER_PROMPT_TEMPLATE.format(
        departure_city=departure_city,
        duration_days=request.duration_days,
        season=season,
        travel_style=travel_style,
        interests=interests,
        budget_level=budget_level,
    )
    return [
        {"role": "system", "content": DESTINATION_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
