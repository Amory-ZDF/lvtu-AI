#!/usr/bin/env python3
"""清洗并导入小红书笔记到 travel_notes 表。

读取 raw_notes/ 目录下的原始 JSON，去重、过滤广告/低质量内容、
自动打标签（目的地/季节/风格/分类）后入库到 travel_notes 表。

用法：
    cd backend && source .venv/bin/activate
    python -m scripts.clean_and_import              # 清洗并入库
    python -m scripts.clean_and_import --dry-run    # 只打印不入库
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# 确保能导入 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.destination import Destination
from app.models.travel_note import TravelNote

RAW_NOTES_DIR = Path(__file__).resolve().parent.parent / "app" / "data" / "raw_notes"

# 广告/低质量内容黑名单关键词
AD_BLACKLIST = [
    "加微",
    "微信",
    "代理",
    "代购",
    "私聊",
    "咨询",
    "优惠",
    "折扣",
    "促销",
    "领取",
    "下单",
]
MIN_CONTENT_LENGTH = 50

# 季节关键词映射
SEASON_KEYWORDS = {
    "spring": ["春季", "春天", "spring", "樱花季", "三月", "四月", "五月"],
    "summer": ["夏季", "夏天", "summer", "暑假", "六月", "七月", "八月"],
    "autumn": ["秋季", "秋天", "autumn", "红叶季", "枫叶", "九月", "十月", "十一月"],
    "winter": ["冬季", "冬天", "winter", "雪景", "十二月", "一月", "二月"],
}

# 旅行风格关键词映射
STYLE_KEYWORDS = {
    "摄影": ["摄影", "拍照", "机位", "出片", "镜头", "单反"],
    "美食": ["美食", "小吃", "餐厅", "打卡", "探店", "吃货"],
    "购物": ["购物", "免税", "商场", "血拼"],
    "徒步": ["徒步", "hiking", "登山", "户外", "露营"],
    "休闲": ["休闲", "度假", "放松", "温泉", "spa"],
    "文化": ["文化", "历史", "古迹", "博物馆", "寺庙", "神社"],
    "冒险": ["冒险", "探险", "极限", "潜水", "跳伞"],
}

# 分类关键词映射
CATEGORY_KEYWORDS = {
    "destination": ["攻略", "旅行", "行程", "自由行", "跟团"],
    "spot": ["景点", "机位", "打卡", "拍照"],
    "outfit": ["穿搭", "ootd", "服装", "搭配", "穿衣"],
}

# HTML 标签正则
HTML_TAG_RE = re.compile(r"<[^>]+>")
# 多余空白
MULTI_SPACE_RE = re.compile(r"\s+")
# Emoji 范围
EMOJI_RE = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002700-\U000027BF"
    "\U0001F900-\U0001F9FF"
    "\U00002600-\U000026FF"
    "]+",
    flags=re.UNICODE,
)


def clean_text(text: str) -> str:
    """清洗文本：去除 HTML 标签、emoji、多余空白。"""
    if not text:
        return ""
    text = HTML_TAG_RE.sub("", text)
    text = EMOJI_RE.sub("", text)
    text = MULTI_SPACE_RE.sub(" ", text).strip()
    return text


def parse_int(value) -> int:
    """解析数字字符串，提取前导数字。"""
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    match = re.match(r"\d+", str(value))
    return int(match.group()) if match else 0


def is_ad_content(content: str, title: str = "") -> bool:
    """判断是否为广告/低质量内容。"""
    combined = f"{title} {content}"
    for keyword in AD_BLACKLIST:
        if keyword in combined:
            return True
    if len(content) < MIN_CONTENT_LENGTH:
        return True
    return False


def match_season(content: str) -> str | None:
    """匹配季节。返回 spring/summer/autumn/winter 或 None。"""
    content_lower = content.lower()
    for season, keywords in SEASON_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in content_lower:
                return season
    return None


def match_travel_styles(content: str) -> list[str]:
    """匹配旅行风格。返回风格列表。"""
    content_lower = content.lower()
    styles: list[str] = []
    for style, keywords in STYLE_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in content_lower:
                styles.append(style)
                break
    return styles


def match_destination(content: str, destination_names: list[str]) -> str | None:
    """匹配目的地。返回第一个匹配的目的地名称。"""
    for name in destination_names:
        if name and name in content:
            return name
    return None


def classify_category(content: str, title: str = "") -> str:
    """根据内容分类：destination/spot/outfit/general。"""
    combined = f"{title} {content}".lower()
    scores = {"destination": 0, "spot": 0, "outfit": 0}
    for category, keywords in CATEGORY_KEYWORDS.items():
        for kw in keywords:
            if kw.lower() in combined:
                scores[category] += 1
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general"
    return best


def extract_note_id(url: str) -> str | None:
    """从笔记 URL 中提取 note_id（24 位十六进制）。"""
    match = re.search(
        r"/(?:search_result|explore|note)/([0-9a-f]{24})(?=[?#/]|$)", url, re.I
    )
    return match.group(1) if match else None


def parse_published_at(value: str) -> datetime | None:
    """解析发布日期字符串。"""
    if not value:
        return None
    # 尝试 YYYY-MM-DD 格式
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        pass
    # 尝试 ISO 格式
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass
    return None


def load_raw_notes() -> list[dict]:
    """读取 raw_notes 目录下所有 JSON 文件，返回笔记列表。"""
    all_notes: list[dict] = []
    if not RAW_NOTES_DIR.exists():
        print(f"目录不存在: {RAW_NOTES_DIR}")
        return all_notes

    json_files = sorted(RAW_NOTES_DIR.glob("*.json"))
    if not json_files:
        print(f"未找到 JSON 文件: {RAW_NOTES_DIR}")
        return all_notes

    print(f"发现 {len(json_files)} 个原始 JSON 文件")
    for filepath in json_files:
        try:
            with open(filepath, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"  [跳过] 读取失败 {filepath.name}: {e}")
            continue

        notes = data.get("notes", []) if isinstance(data, dict) else []
        for note in notes:
            note["_source_file"] = filepath.name
        all_notes.extend(notes)

    return all_notes


def build_travel_note(
    note: dict, destination_names: list[str]
) -> TravelNote | None:
    """将原始笔记字典转换为 TravelNote 对象。

    返回 None 表示该笔记应被过滤（广告/低质量）。
    """
    search_result = note.get("search_result", {}) or {}
    detail = note.get("detail", {}) or {}

    # source_id 优先从顶层取，其次从 URL 提取
    source_id = note.get("source_id") or extract_note_id(
        search_result.get("url", "")
    )
    source_url = note.get("source_url") or search_result.get("url", "")

    title = detail.get("title") or search_result.get("title") or "无标题"
    raw_content = detail.get("content", "")
    cleaned_content = clean_text(raw_content)

    # 过滤广告/低质量内容
    if is_ad_content(cleaned_content, title):
        return None

    # 标签：detail 中的 tags 是逗号分隔字符串
    tags_raw = detail.get("tags", "")
    if isinstance(tags_raw, str):
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    elif isinstance(tags_raw, list):
        tags = [str(t).strip() for t in tags_raw if t]
    else:
        tags = []

    # 自动打标签
    destination_name = match_destination(cleaned_content, destination_names)
    season = match_season(cleaned_content)
    travel_style = match_travel_styles(cleaned_content)
    category = classify_category(cleaned_content, title)

    # 互动数据
    like_count = parse_int(detail.get("likes") or search_result.get("likes"))
    collect_count = parse_int(detail.get("collects"))
    comment_count = parse_int(detail.get("comments"))

    author_name = detail.get("author") or search_result.get("author")
    published_at = parse_published_at(search_result.get("published_at", ""))

    return TravelNote(
        title=title[:255],
        source="xiaohongshu",
        source_url=source_url[:512] if source_url else None,
        source_id=source_id,
        destination_name=destination_name,
        content=cleaned_content,
        raw_content=raw_content,
        tags=tags,
        category=category,
        season=season,
        travel_style=travel_style,
        cover_image_url=None,
        images=[],
        like_count=like_count,
        collect_count=collect_count,
        comment_count=comment_count,
        author_name=author_name[:128] if author_name else None,
        published_at=published_at,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="清洗并导入小红书笔记到 travel_notes 表"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印不入库",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("小红书笔记清洗入库")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"原始数据目录: {RAW_NOTES_DIR}")
    print(f"模式: {'dry-run（不入库）' if args.dry_run else '入库'}")
    print("=" * 60)

    # 读取原始数据
    raw_notes = load_raw_notes()
    total = len(raw_notes)
    print(f"\n读取原始笔记: {total} 条")

    if total == 0:
        print("无数据可处理，退出")
        return

    session = SessionLocal()
    try:
        # 查询所有目的地名称用于匹配
        destination_names = list(session.scalars(select(Destination.name)).all())
        print(f"数据库目的地数量: {len(destination_names)}")

        # 查询已存在的 source_id（用于去重）
        existing_ids = set(
            session.scalars(
                select(TravelNote.source_id).where(TravelNote.source_id.isnot(None))
            ).all()
        )

        # 去重（按 source_id）
        seen_ids: set[str] = set()
        deduped: list[dict] = []
        dedup_count = 0
        for note in raw_notes:
            search_result = note.get("search_result", {}) or {}
            url = note.get("source_url") or search_result.get("url", "")
            sid = note.get("source_id") or extract_note_id(url)
            if sid:
                if sid in seen_ids or sid in existing_ids:
                    dedup_count += 1
                    continue
                seen_ids.add(sid)
            deduped.append(note)

        print(f"去重: {dedup_count} 条（剩余 {len(deduped)} 条）")

        # 清洗 + 过滤 + 入库
        filtered_count = 0
        imported_count = 0
        for note in deduped:
            travel_note = build_travel_note(note, destination_names)
            if travel_note is None:
                filtered_count += 1
                continue
            if args.dry_run:
                print(f"  [dry-run] 将入库: {travel_note.title[:40]}")
            else:
                session.add(travel_note)
            imported_count += 1

        if not args.dry_run:
            session.commit()

        # 统计
        print("\n" + "=" * 60)
        print("清洗入库统计")
        print("=" * 60)
        print(f"  原始总数: {total}")
        print(f"  去重数:   {dedup_count}")
        print(f"  过滤数:   {filtered_count}（广告/低质量）")
        print(f"  入库数:   {imported_count}")
        print("=" * 60)
    finally:
        session.close()


if __name__ == "__main__":
    main()
