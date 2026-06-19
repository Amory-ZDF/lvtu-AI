"""穿搭推荐 prompt 模板。"""

from __future__ import annotations

OUTFIT_SYSTEM_PROMPT = (
    "你是一位旅行穿搭顾问，擅长根据目的地、季节、场景和风格偏好，"
    "推荐兼顾实用与出片的穿搭方案。\n\n"
    "输出要求：\n"
    "1. 必须返回严格的 JSON 对象，不要包含任何额外文字或 Markdown 代码块标记。\n"
    '2. JSON 结构：{"items": [{name, category, color, image_description}], "tips": "..."}\n'
    "3. 字段说明：\n"
    "   - items: 穿搭单品列表（4-6 件），每件包含：\n"
    "     - name: 单品名称\n"
    "     - category: 类别（top / bottom / outerwear / shoes / accessory）\n"
    "     - color: 推荐颜色\n"
    "     - image_description: 单品画面描述（用于后续图像生成）\n"
    "   - tips: 穿搭小贴士字符串"
)

OUTFIT_USER_PROMPT_TEMPLATE = (
    "请根据以下信息推荐旅行穿搭：\n"
    "目的地：{destination}\n"
    "季节：{season}\n"
    "场景：{scene}\n"
    "风格：{style}\n"
    "{gender_line}\n"
    "请返回 JSON 格式的穿搭推荐结果。"
)


def build_outfit_prompt(
    destination: str,
    season: str,
    scene: str,
    style: str,
    gender: str | None = None,
) -> list[dict]:
    """构建穿搭推荐 prompt 的 messages 列表。"""
    gender_line = f"性别：{gender}" if gender else "性别：不限"
    user_content = OUTFIT_USER_PROMPT_TEMPLATE.format(
        destination=destination,
        season=season,
        scene=scene,
        style=style,
        gender_line=gender_line,
    )
    return [
        {"role": "system", "content": OUTFIT_SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
