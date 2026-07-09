"""Add a passwordless data-center admin from the backend.

Usage:
    cd backend
    python -m scripts.add_data_center_admin --email admin@example.com

The admin can then open /data-center and log in with email only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal
from app.services.analytics_admin_service import add_analytics_admin


def main() -> None:
    parser = argparse.ArgumentParser(description="Add a passwordless data-center admin.")
    parser.add_argument("--email", required=True, help="Admin login email.")
    parser.add_argument("--display-name", help="Optional display name.")
    args = parser.parse_args()

    with SessionLocal() as session:
        admin = add_analytics_admin(session, args.email, args.display_name)

    print(f"数据中台免密账号已添加：{admin.email}")


if __name__ == "__main__":
    main()
