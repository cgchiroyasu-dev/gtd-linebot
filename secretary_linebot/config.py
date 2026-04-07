"""
config.py — Secretary LINE Bot 設定

環境変数を .env から読み込み、全モジュールで共有する定数を定義する。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# .env は このファイルと同じディレクトリ
_ENV_PATH = Path(__file__).parent / ".env"
load_dotenv(_ENV_PATH)


def _require(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        raise ValueError(f"Missing required environment variable: {key}")
    return val


# ── LINE Secretary Bot（受信用 / 新チャンネル）────────────────────────────────────
LINE_SECRETARY_CHANNEL_ACCESS_TOKEN: str = _require("LINE_SECRETARY_CHANNEL_ACCESS_TOKEN")
LINE_SECRETARY_CHANNEL_SECRET: str = _require("LINE_SECRETARY_CHANNEL_SECRET")

# ── LINE Push通知（送信用 / 既存秘書チャンネルと同じ）─────────────────────────────
LINE_CHANNEL_ACCESS_TOKEN: str = _require("LINE_CHANNEL_ACCESS_TOKEN")
LINE_USER_ID: str = _require("LINE_USER_ID")

# ── Notion ───────────────────────────────────────────────────────────────────────
NOTION_TOKEN: str = _require("NOTION_TOKEN")
NOTION_DB_RESEARCH_ID: str = os.environ.get(
    "NOTION_DB_RESEARCH_ID",
    "33ba9f98-b152-8008-8f02-fd387341c4b4",
)
