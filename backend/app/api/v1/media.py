# ruff: noqa: E501
from __future__ import annotations

import hashlib
import html

from fastapi import APIRouter, Query, Response

router = APIRouter()

PALETTES = [
    ("#2563eb", "#14b8a6", "#eff6ff"),
    ("#0f766e", "#84cc16", "#f0fdfa"),
    ("#7c3aed", "#ec4899", "#faf5ff"),
    ("#ea580c", "#facc15", "#fff7ed"),
    ("#0369a1", "#38bdf8", "#f0f9ff"),
]


def _trim(value: str, max_len: int) -> str:
    value = " ".join(value.split())
    return value if len(value) <= max_len else f"{value[: max_len - 1]}…"


def _palette(seed: str) -> tuple[str, str, str]:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()
    return PALETTES[int(digest[:2], 16) % len(PALETTES)]


@router.get("/place-card.svg", tags=["media"])
def place_card_svg(
    title: str = Query(..., max_length=80),
    subtitle: str = Query(default="", max_length=180),
    category: str = Query(default="destination", max_length=40),
    tags: str = Query(default="", max_length=120),
    lat: str | None = Query(default=None, max_length=32),
    lng: str | None = Query(default=None, max_length=32),
) -> Response:
    """生成可缓存的本地点位图卡，避免前端继续显示无信息占位图。"""
    primary, secondary, bg = _palette(f"{title}-{subtitle}-{category}")
    safe_title = html.escape(_trim(title, 24))
    safe_subtitle = html.escape(_trim(subtitle, 42))
    safe_category = html.escape(_trim(category, 18))
    safe_tags = html.escape(_trim(tags, 36))
    coord = html.escape(f"{lat}, {lng}") if lat and lng else "Lv Travel Knowledge"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="960" height="540" viewBox="0 0 960 540" role="img" aria-label="{safe_title}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{primary}"/>
      <stop offset="100%" stop-color="{secondary}"/>
    </linearGradient>
    <radialGradient id="light" cx="72%" cy="24%" r="58%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.45"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="18" stdDeviation="18" flood-color="#0f172a" flood-opacity="0.22"/>
    </filter>
  </defs>
  <rect width="960" height="540" fill="url(#bg)"/>
  <rect width="960" height="540" fill="url(#light)"/>
  <circle cx="770" cy="102" r="148" fill="#ffffff" opacity="0.16"/>
  <circle cx="150" cy="462" r="210" fill="#ffffff" opacity="0.12"/>
  <g filter="url(#shadow)">
    <rect x="76" y="74" width="808" height="392" rx="36" fill="{bg}" opacity="0.94"/>
  </g>
  <text x="116" y="138" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="24" font-weight="700" fill="{primary}" letter-spacing="2">{safe_category.upper()}</text>
  <text x="116" y="226" font-family="-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif" font-size="68" font-weight="800" fill="#0f172a">{safe_title}</text>
  <text x="116" y="292" font-family="-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif" font-size="30" font-weight="600" fill="#334155">{safe_subtitle}</text>
  <text x="116" y="360" font-family="-apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif" font-size="24" fill="#475569">{safe_tags}</text>
  <text x="116" y="420" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="22" fill="#64748b">📍 {coord}</text>
  <text x="760" y="420" text-anchor="end" font-family="-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif" font-size="22" font-weight="700" fill="{secondary}">旅图 LV</text>
</svg>"""
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )
