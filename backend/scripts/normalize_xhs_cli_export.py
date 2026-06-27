#!/usr/bin/env python3
"""Normalize authorized Xiaohongshu CLI exports into private travel note candidates.

This script does not crawl Xiaohongshu. It only reads JSON files that the user has
already exported through an authorized/manual workflow and writes cleaned summaries
to the private data folder.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PRIVATE_DIR = REPO_ROOT.parent / f"{REPO_ROOT.name}_private_data"
DEFAULT_INPUT_DIR = DEFAULT_PRIVATE_DIR / "raw" / "xiaohongshu"
DEFAULT_OUTPUT_DIR = DEFAULT_PRIVATE_DIR / "processed" / "xiaohongshu"

HTML_TAG_RE = re.compile(r"<[^>]+>")
MULTI_SPACE_RE = re.compile(r"\s+")
URL_NOTE_ID_RE = re.compile(r"/(?:search_result|explore|note)/([0-9a-f]{24})(?=[?#/]|$)", re.I)

SEASON_KEYWORDS = {
    "spring": ["春季", "春天", "樱花", "三月", "四月", "五月"],
    "summer": ["夏季", "夏天", "暑假", "六月", "七月", "八月", "避暑"],
    "autumn": ["秋季", "秋天", "红叶", "枫叶", "九月", "十月", "十一月"],
    "winter": ["冬季", "冬天", "雪景", "十二月", "一月", "二月"],
}
STYLE_KEYWORDS = {
    "photogenic": ["拍照", "机位", "出片", "打卡", "构图", "镜头"],
    "food": ["美食", "小吃", "餐厅", "咖啡", "探店"],
    "citywalk": ["citywalk", "城市漫步", "街区", "步行"],
    "culture": ["历史", "博物馆", "寺庙", "古迹", "展览", "建筑"],
    "nature": ["徒步", "露营", "草原", "海边", "雪山", "森林", "湖"],
    "outfit": ["穿搭", "ootd", "裙", "风衣", "外套", "妆造"],
}


def clean_text(value: Any) -> str:
    text = "" if value is None else str(value)
    text = HTML_TAG_RE.sub("", text)
    text = MULTI_SPACE_RE.sub(" ", text)
    return text.strip()


def extract_note_id(url: str) -> str | None:
    match = URL_NOTE_ID_RE.search(url)
    return match.group(1) if match else None


def first_present(data: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def flatten_note(raw: dict[str, Any]) -> dict[str, Any]:
    detail = raw.get("detail") if isinstance(raw.get("detail"), dict) else {}
    search_result = raw.get("search_result") if isinstance(raw.get("search_result"), dict) else {}
    merged = {**search_result, **detail, **raw}
    url = clean_text(first_present(merged, ["source_url", "url", "note_url", "link"]))
    title = clean_text(first_present(merged, ["title", "标题", "note_title"]))
    content = clean_text(
        first_present(merged, ["content", "正文", "desc", "description", "note_content"])
    )
    if not content:
        content = clean_text(first_present(merged, ["text", "summary"]))
    return {
        "source_id": clean_text(first_present(merged, ["source_id", "id", "note_id"]))
        or extract_note_id(url),
        "source_url": url or None,
        "title": title,
        "content": content,
        "raw_tags": first_present(merged, ["tags", "标签"]) or [],
        "like_count": first_present(merged, ["like_count", "likes", "点赞"]) or 0,
        "collect_count": first_present(merged, ["collect_count", "收藏"]) or 0,
        "comment_count": first_present(merged, ["comment_count", "comments", "评论"]) or 0,
    }


def classify(note: dict[str, Any], destination_names: list[str]) -> dict[str, Any]:
    combined = f"{note.get('title') or ''} {note.get('content') or ''}".lower()
    destination = None
    for name in destination_names:
        if name and name.lower() in combined:
            destination = name
            break

    season = None
    for value, keywords in SEASON_KEYWORDS.items():
        if any(keyword.lower() in combined for keyword in keywords):
            season = value
            break

    styles = [
        style
        for style, keywords in STYLE_KEYWORDS.items()
        if any(keyword.lower() in combined for keyword in keywords)
    ]
    category = "general"
    if "outfit" in styles:
        category = "outfit"
    elif "photogenic" in styles:
        category = "spot"
    elif destination:
        category = "destination"

    note["destination_name"] = destination
    note["season"] = season
    note["travel_style"] = styles
    note["category"] = category
    note["summary"] = (note.get("content") or "")[:500]
    return note


def iter_json_files(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(input_dir.glob("*.json"))


def load_notes(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in ["notes", "items", "data", "results"]:
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
        return [data]
    return []


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize authorized XHS CLI JSON exports.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--destinations",
        default="北京,上海,杭州,苏州,厦门,大理,成都,重庆",
        help="Comma-separated destination names for lightweight tagging.",
    )
    args = parser.parse_args()

    input_dir = args.input_dir.expanduser()
    output_dir = args.output_dir.expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    destination_names = [item.strip() for item in args.destinations.split(",") if item.strip()]

    raw_files = iter_json_files(input_dir)
    all_notes: list[dict[str, Any]] = []
    for path in raw_files:
        for raw in load_notes(path):
            note = classify(flatten_note(raw), destination_names)
            note["source"] = "xiaohongshu_cli_export"
            note["source_file"] = path.name
            note["processed_at"] = datetime.now().isoformat()
            if note.get("title") or note.get("content"):
                all_notes.append(note)

    deduped: dict[str, dict[str, Any]] = {}
    for note in all_notes:
        key = (
            note.get("source_id")
            or note.get("source_url")
            or f"{note.get('title')}|{note.get('summary')}"
        )
        deduped[str(key)] = note

    payload = {
        "source": "xiaohongshu_cli_export",
        "processed_at": datetime.now().isoformat(),
        "input_dir": str(input_dir),
        "file_count": len(raw_files),
        "raw_count": len(all_notes),
        "deduped_count": len(deduped),
        "items": list(deduped.values()),
    }
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"travel_notes_candidates_{timestamp}.json"
    latest_file = output_dir / "travel_notes_candidates_latest.json"
    for path in [output_file, latest_file]:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"input_files={len(raw_files)}")
    print(f"deduped_count={len(deduped)}")
    print(f"output={output_file}")
    print(f"latest={latest_file}")


if __name__ == "__main__":
    main()
