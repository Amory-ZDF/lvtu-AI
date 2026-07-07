from __future__ import annotations

from typing import Any

import httpx


class OutfitImageGenerationError(Exception):
    pass


def _item_names(items: list[dict[str, Any]]) -> list[str]:
    names: list[str] = []
    for item in items:
        name = str(item.get("name") or "").strip()
        if name:
            names.append(name)
    return names


def _infer_gender(scene: str, style: str, items: list[dict[str, Any]]) -> str:
    explicit_genders = {
        str(item.get("gender") or "").strip().lower()
        for item in items
        if item.get("gender")
    }
    if "female" in explicit_genders and "male" not in explicit_genders:
        return "女生"
    if "male" in explicit_genders and "female" not in explicit_genders:
        return "男生"

    text = f"{scene} {style} {' '.join(str(item.get('gender') or '') for item in items)}"
    lower_text = text.lower()
    words = {
        word.strip(".,;:/|·-_()[]{}")
        for word in lower_text.split()
    }
    if (
        any(token in text for token in ("女生", "女士", "女性", "女装"))
        or "female" in words
        or "womenswear" in lower_text
    ):
        return "女生"
    if (
        any(token in text for token in ("男生", "男士", "男性", "男装"))
        or "male" in words
        or "menswear" in lower_text
    ):
        return "男生"
    return "旅行者"


def build_outfit_preview_prompt(
    *,
    destination_name: str,
    scene: str,
    season: str,
    style: str,
    items: list[dict[str, Any]],
) -> str:
    gender = _infer_gender(scene, style, items)
    gender_guard = ""
    if gender == "女生":
        gender_guard = "画面主体必须是成年女性/女装旅行穿搭，不要生成男性或男装。"
    elif gender == "男生":
        gender_guard = "画面主体必须是成年男性/男装旅行穿搭，不要生成女性或女装。"
    item_text = "、".join(_item_names(items)) or "舒适旅行穿搭"
    return (
        f"生成一张真实感旅行穿搭预览图：主体是一位成年{gender}，目的地是{destination_name}，"
        f"场景为{scene}，季节/天气参考为{season}。穿搭风格：{style}。"
        f"{gender_guard}核心单品：{item_text}。画面比例固定为 3:4 竖图，要求全身或接近全身构图，"
        "不要裁切头部、脚部或关键单品，能清楚看到上装、下装、鞋履和层次，"
        "姿态自然，符合真实旅行步行、拍照和户外移动需求；背景是与目的地和场景相符的旅行环境，"
        "自然光，真实摄影质感，lookbook 构图。不要出现文字、Logo、品牌标识、夸张秀场造型、"
        "畸形手指、多余肢体或儿童形象。"
    )


class VolcengineOutfitImageClient:
    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        size: str = "2K",
        watermark: bool = True,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.size = size
        self.watermark = watermark

    def generate(self, prompt: str) -> str:
        body = {
            "model": self.model,
            "prompt": prompt,
            "sequential_image_generation": "disabled",
            "response_format": "url",
            "size": self.size,
            "stream": False,
            "watermark": self.watermark,
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(self.base_url, headers=headers, json=body)
                response.raise_for_status()
                payload = response.json()
        except httpx.HTTPStatusError as exc:
            raise OutfitImageGenerationError(
                f"图片生成服务返回错误状态：{exc.response.status_code}",
            ) from exc
        except (httpx.RequestError, ValueError) as exc:
            raise OutfitImageGenerationError("图片生成服务暂时不可用") from exc

        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, list) or not data:
            raise OutfitImageGenerationError("图片生成服务未返回图片")
        first = data[0]
        if not isinstance(first, dict):
            raise OutfitImageGenerationError("图片生成服务返回结构异常")
        url = str(first.get("url") or "").strip()
        if not url:
            raise OutfitImageGenerationError("图片生成服务未返回图片 URL")
        return url
