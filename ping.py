"""
ping.py — Render Cron Job 用 self-ping スクリプト

Render の Cron Job サービスからこのスクリプトを実行することで、
Web サービスのスリープを防止する。

Render Cron Job 設定:
    Command:  python ping.py
    Schedule: */5 * * * *   (5分ごと)

環境変数:
    SELF_URL: pingするURL（省略時は https://gtd-linebot.onrender.com/health）
"""

import os
import sys

import requests

URL = os.environ.get("SELF_URL", "https://gtd-linebot.onrender.com/health")

try:
    r = requests.get(URL, timeout=30)
    print(f"[ping] {URL} -> {r.status_code}")
    sys.exit(0)
except Exception as e:
    print(f"[ping] error: {e}")
    sys.exit(1)
