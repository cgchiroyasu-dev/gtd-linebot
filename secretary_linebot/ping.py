"""
ping.py — Render スリープ防止 keep-alive

Render Cron Job から 5分おきに呼ばれ、/health をセルフ ping する。
"""

import os
import sys

import requests

BASE_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:8000")

if __name__ == "__main__":
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        print(f"[ping] {r.status_code} {r.json()}")
    except Exception as e:
        print(f"[ping] error: {e}", file=sys.stderr)
        sys.exit(1)
