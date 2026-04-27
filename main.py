"""
main.py — LINE Messaging API webhook → Notion DB_Task2026 タスク追加

起動:
    uvicorn main:app --host 0.0.0.0 --port 8000

環境変数 (必須):
    LINE_CHANNEL_ACCESS_TOKEN
    LINE_CHANNEL_SECRET
    NOTION_TOKEN
    NOTION_DB_TASK_2026_ID
"""

import base64
import hashlib
import hmac
import json
import os
import time

import requests
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from notion_client import create_task, check_notion_connection

load_dotenv()

# ── 起動時にenv vars全チェック ──────────────────────────────────────────────────
REQUIRED_ENV = [
    "LINE_CHANNEL_ACCESS_TOKEN",
    "LINE_CHANNEL_SECRET",
    "NOTION_TOKEN",
    "NOTION_DB_TASK_2026_ID",
]

_missing = [k for k in REQUIRED_ENV if not os.environ.get(k)]
if _missing:
    raise ValueError(f"Missing required environment variables: {', '.join(_missing)}")

_boot_time = time.time()
print(f"[boot] Service started at {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(_boot_time))}")

app = FastAPI()


# ── ヘルスチェック ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    uptime_sec = int(time.time() - _boot_time)
    return {"status": "ok", "uptime_seconds": uptime_sec}


# ── セルフテスト（Notion疎通確認）──────────────────────────────────────────────
@app.get("/self-test")
async def self_test():
    uptime_sec = int(time.time() - _boot_time)
    notion_ok, notion_detail = check_notion_connection()
    if notion_ok:
        return {"status": "ok", "notion": "connected", "uptime_seconds": uptime_sec}
    return {"status": "error", "notion": notion_detail, "uptime_seconds": uptime_sec}


# ── LINE署名検証 ────────────────────────────────────────────────────────────────
def _verify_signature(body: bytes, signature: str) -> bool:
    secret = os.environ["LINE_CHANNEL_SECRET"].encode("utf-8")
    digest = hmac.new(secret, body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)


# ── LINE Reply API ──────────────────────────────────────────────────────────────
def _reply_line(reply_token: str, text: str) -> None:
    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['LINE_CHANNEL_ACCESS_TOKEN']}",
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        print(f"[LINE reply error] {r.status_code}: {r.text}")


# ── LINE Push API（reply token失効時の代替）──────────────────────────────────────
def _push_line(user_id: str, text: str) -> None:
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.environ['LINE_CHANNEL_ACCESS_TOKEN']}",
    }
    payload = {
        "to": user_id,
        "messages": [{"type": "text", "text": text}],
    }
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    if r.status_code != 200:
        print(f"[LINE push error] {r.status_code}: {r.text}")


# ── タスク作成ハンドラ（バックグラウンド実行）──────────────────────────────────────
def _handle_task(task_name: str, reply_token: str, user_id: str, received_at: float) -> None:
    print(f"[task] start: {task_name!r}")
    try:
        create_task(task_name)
        print(f"[task] done: {task_name!r}")
        elapsed = time.time() - received_at
        msg = f"✅ タスク追加: {task_name}"
        if elapsed > 25:
            # Reply token likely expired (30s TTL), use push instead
            print(f"[task] reply token likely expired ({elapsed:.1f}s), using push API")
            _push_line(user_id, msg)
        else:
            _reply_line(reply_token, msg)
    except RuntimeError as e:
        print(f"[task] Notion error: {e}")
        error_msg = "⚠️ タスクの追加に失敗しました。もう一度お試しください。"
        elapsed = time.time() - received_at
        if elapsed > 25:
            _push_line(user_id, error_msg)
        else:
            _reply_line(reply_token, error_msg)


# ── webhook エンドポイント ────────────────────────────────────────────────────────
@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    received_at = time.time()
    body_bytes = await request.body()

    # 署名検証 (LINE Messaging API 必須)
    signature = request.headers.get("X-Line-Signature", "")
    if not _verify_signature(body_bytes, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    body = json.loads(body_bytes)
    for event in body.get("events", []):
        if event.get("type") != "message":
            continue
        message = event.get("message", {})
        if message.get("type") != "text":
            continue
        task_name = message.get("text", "").strip()
        if not task_name:
            continue
        reply_token = event.get("replyToken", "")
        user_id = event.get("source", {}).get("userId", "")
        print(f"[webhook] received: {task_name!r}")
        background_tasks.add_task(_handle_task, task_name, reply_token, user_id, received_at)

    return {"status": "ok"}
