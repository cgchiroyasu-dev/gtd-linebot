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

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request

from notion_client import create_task

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

app = FastAPI()


# ── ヘルスチェック ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


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
        # タスクは既に保存済みのためログのみ
        print(f"[LINE reply error] {r.status_code}: {r.text}")


# ── タスク作成ハンドラ ───────────────────────────────────────────────────────────
async def _handle_task(task_name: str, reply_token: str) -> None:
    try:
        create_task(task_name)
        _reply_line(reply_token, f"✅ タスク追加: {task_name}")
    except RuntimeError as e:
        print(f"[Notion error] {e}")
        _reply_line(reply_token, "⚠️ タスクの追加に失敗しました。もう一度お試しください。")


# ── webhook エンドポイント ────────────────────────────────────────────────────────
@app.post("/webhook")
async def webhook(request: Request):
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
        await _handle_task(task_name, reply_token)

    return {"status": "ok"}
