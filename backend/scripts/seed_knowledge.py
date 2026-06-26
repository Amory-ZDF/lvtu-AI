"""种子数据导入脚本：将私有数据目录下的 JSON 灌入知识库表。

用法：
    cd backend
    python -m scripts.seed_knowledge              # 导入全部
    python -m scripts.seed_knowledge --reset      # 先清空再导入
    python -m scripts.seed_knowledge --only destinations  # 只导入目的地
    LV_SEED_DATA_DIR=/path/to/seed_data python -m scripts.seed_knowledge --reset
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# 确保能导入 app 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.destination import Destination
from app.models.outfit import Outfit
from app.models.photo_spot import PhotoSpot

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "app" / "data"
DATA_DIR = Path(os.getenv("LV_SEED_DATA_DIR", DEFAULT_DATA_DIR)).expanduser()


def _load_json(filename: str) -> list[dict]:
    filepath = DATA_DIR / filename
    if not filepath.exists():
        print(f"  [跳过] 文件不存在: {filepath}")
        return []
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


def _import_destinations(session: Session, reset: bool) -> int:
    if reset:
        deleted = session.query(Destination).delete()
        print(f"  清空 destinations: {deleted} 条")

    data = _load_json("destinations.json")
    if not data:
        return 0

    for item in data:
        session.add(Destination(**item))
    session.commit()
    return len(data)


def _import_photo_spots(session: Session, reset: bool) -> int:
    if reset:
        deleted = session.query(PhotoSpot).delete()
        print(f"  清空 photo_spots: {deleted} 条")

    data = _load_json("photo_spots.json")
    if not data:
        return 0

    for item in data:
        session.add(PhotoSpot(**item))
    session.commit()
    return len(data)


def _import_outfits(session: Session, reset: bool) -> int:
    if reset:
        deleted = session.query(Outfit).delete()
        print(f"  清空 outfits: {deleted} 条")

    data = _load_json("outfits.json")
    if not data:
        return 0

    for item in data:
        session.add(Outfit(**item))
    session.commit()
    return len(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="导入旅行知识库种子数据")
    parser.add_argument("--reset", action="store_true", help="导入前先清空表")
    parser.add_argument(
        "--only",
        choices=["destinations", "photo_spots", "outfits"],
        help="只导入指定类型",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="种子数据目录；也可用 LV_SEED_DATA_DIR 指定",
    )
    args = parser.parse_args()

    global DATA_DIR
    if args.data_dir is not None:
        DATA_DIR = args.data_dir.expanduser()

    print("=" * 50)
    print("旅行知识库种子数据导入")
    print(f"数据目录: {DATA_DIR}")
    print(f"模式: {'清空后导入' if args.reset else '追加导入'}")
    print("=" * 50)

    session = SessionLocal()
    try:
        tasks: list[tuple[str, callable]] = []
        if args.only == "destinations" or args.only is None:
            tasks.append(("destinations", _import_destinations))
        if args.only == "photo_spots" or args.only is None:
            tasks.append(("photo_spots", _import_photo_spots))
        if args.only == "outfits" or args.only is None:
            tasks.append(("outfits", _import_outfits))

        for label, func in tasks:
            print(f"\n[{label}] 导入中...")
            count = func(session, args.reset)
            print(f"[{label}] 完成: {count} 条")

        # 统计
        print("\n" + "=" * 50)
        print("导入完成，当前数据库统计:")
        print(f"  destinations: {session.query(Destination).count()} 条")
        print(f"  photo_spots:  {session.query(PhotoSpot).count()} 条")
        print(f"  outfits:      {session.query(Outfit).count()} 条")
        print("=" * 50)
    finally:
        session.close()


if __name__ == "__main__":
    main()
