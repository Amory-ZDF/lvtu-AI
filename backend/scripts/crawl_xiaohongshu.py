#!/usr/bin/env python3
"""小红书旅行笔记采集脚本。

通过 OpenCLI 采集小红书笔记，保存原始 JSON 数据。
本脚本不依赖 app 模块，可独立运行（仅需 Python 标准库）。

用法：
    cd backend && source .venv/bin/activate
    python -m scripts.crawl_xiaohongshu                              # 采集全部关键词
    python -m scripts.crawl_xiaohongshu --keywords 京都攻略,云南攻略   # 指定关键词
    python -m scripts.crawl_xiaohongshu --limit 10                    # 每个关键词采集 10 条

注意：实际采集需要浏览器扩展支持，本脚本只负责调用 OpenCLI 并保存原始数据。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
from datetime import datetime
from pathlib import Path

OPENCLI_CWD = "/Users/amory/Desktop/lvtu-/opencli-sandbox"
DEFAULT_KEYWORDS = [
    "京都攻略",
    "日本旅行",
    "云南攻略",
    "西藏攻略",
    "成都美食",
    "拍照机位",
    "旅行穿搭",
]
RAW_NOTES_DIR = Path(__file__).resolve().parent.parent / "app" / "data" / "raw_notes"
KEYWORD_DELAY_SECONDS = 2
COMMAND_TIMEOUT = 60


def run_opencli(args: list[str], timeout: int = COMMAND_TIMEOUT) -> list | dict | None:
    """运行 opencli 命令并解析 JSON 输出。失败返回 None。"""
    cmd = ["npx", "opencli", *args]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=OPENCLI_CWD,
        )
    except subprocess.TimeoutExpired:
        print(f"  [超时] 命令执行超时: {' '.join(args[:3])}")
        return None
    except Exception as e:  # noqa: BLE001
        print(f"  [错误] 命令执行异常: {e}")
        return None

    if result.returncode != 0:
        stderr = result.stderr.strip()
        print(f"  [失败] 命令返回非零状态: {stderr[:200]}")
        return None

    stdout = result.stdout.strip()
    if not stdout:
        print("  [空] 命令无输出")
        return None

    try:
        return json.loads(stdout)
    except json.JSONDecodeError as e:
        print(f"  [解析错误] JSON 解析失败: {e}")
        return None


def search_notes(keyword: str, limit: int) -> list[dict]:
    """搜索小红书笔记列表。返回搜索结果数组。"""
    print(f"  搜索: {keyword} (limit={limit})")
    data = run_opencli(
        ["xiaohongshu", "search", keyword, "--limit", str(limit), "-f", "json"]
    )
    if not data:
        return []
    if not isinstance(data, list):
        print(f"  [警告] 搜索结果格式异常: {type(data).__name__}")
        return []
    return data


def get_note_detail(note_url: str) -> dict | None:
    """获取笔记详情。note_url 是搜索结果中的完整 URL（含 xsec_token）。"""
    data = run_opencli(["xiaohongshu", "note", note_url, "-f", "json"])
    if not data:
        return None
    # note 命令输出为 [{field, value}, ...]，转换为字典
    if isinstance(data, list):
        detail: dict = {}
        for row in data:
            if isinstance(row, dict) and "field" in row and "value" in row:
                detail[row["field"]] = row["value"]
        return detail if detail else None
    if isinstance(data, dict):
        return data
    return None


def extract_note_id(url: str) -> str | None:
    """从笔记 URL 中提取 note_id（24 位十六进制）。"""
    match = re.search(
        r"/(?:search_result|explore|note)/([0-9a-f]{24})(?=[?#/]|$)", url, re.I
    )
    return match.group(1) if match else None


def crawl_keyword(keyword: str, limit: int) -> list[dict]:
    """采集单个关键词的所有笔记（含详情）。"""
    search_results = search_notes(keyword, limit)
    if not search_results:
        print(f"  未找到结果: {keyword}")
        return []

    notes: list[dict] = []
    total = len(search_results)
    for idx, item in enumerate(search_results, 1):
        url = item.get("url", "")
        title = item.get("title", "")
        if not url:
            print(f"  [{idx}/{total}] 跳过：无 URL")
            continue

        print(f"  [{idx}/{total}] 采集详情: {title[:30]}")
        detail = get_note_detail(url)
        if detail is None:
            print("    [跳过] 详情获取失败")
            continue

        note_id = extract_note_id(url)
        notes.append(
            {
                "source_id": note_id,
                "source_url": url,
                "search_result": item,
                "detail": detail,
            }
        )

    return notes


def save_raw_notes(keyword: str, notes: list[dict]) -> Path:
    """保存原始数据到 JSON 文件。"""
    RAW_NOTES_DIR.mkdir(parents=True, exist_ok=True)
    # 文件名安全处理：只保留中文、字母、数字、下划线
    safe_keyword = re.sub(r"[^\w\u4e00-\u9fa5]", "_", keyword)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = RAW_NOTES_DIR / f"{safe_keyword}_{timestamp}.json"

    payload = {
        "keyword": keyword,
        "crawled_at": datetime.now().isoformat(),
        "count": len(notes),
        "notes": notes,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return filepath


def main() -> None:
    parser = argparse.ArgumentParser(description="采集小红书旅行笔记（通过 OpenCLI）")
    parser.add_argument(
        "--keywords",
        type=str,
        default=None,
        help="逗号分隔的关键词列表，不指定则使用默认 7 个关键词",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="每个关键词采集数量（默认 20）",
    )
    args = parser.parse_args()

    if args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    else:
        keywords = DEFAULT_KEYWORDS

    print("=" * 60)
    print("小红书旅行笔记采集")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"关键词: {keywords}")
    print(f"每个关键词限制: {args.limit}")
    print(f"输出目录: {RAW_NOTES_DIR}")
    print("=" * 60)

    keyword_stats: list[dict] = []
    total_detail = 0

    for i, keyword in enumerate(keywords):
        print(f"\n[{i + 1}/{len(keywords)}] 关键词: {keyword}")
        notes = crawl_keyword(keyword, args.limit)
        filepath = save_raw_notes(keyword, notes)
        print(f"  保存 {len(notes)} 条到: {filepath.name}")

        keyword_stats.append({"keyword": keyword, "count": len(notes)})
        total_detail += len(notes)

        # 关键词之间间隔 2 秒（最后一个不等待）
        if i < len(keywords) - 1:
            print(f"  等待 {KEYWORD_DELAY_SECONDS} 秒...")
            time.sleep(KEYWORD_DELAY_SECONDS)

    # 统计
    print("\n" + "=" * 60)
    print("采集完成统计")
    print("=" * 60)
    for item in keyword_stats:
        print(f"  {item['keyword']}: {item['count']} 条")
    print(f"  总计: {total_detail} 条")
    print("=" * 60)


if __name__ == "__main__":
    main()
