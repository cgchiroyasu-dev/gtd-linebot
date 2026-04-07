"""
main.py — Secretary LINE Bot Webhook

秘書用 LINE Official Account（GTDボットとは別チャンネル）の Webhook エンドポイント。
送られてきた全メッセージをリサーチリクエストとして Notion DB_Research キューに追加する。

起動:
    uvicorn main:app --host 0.0.0.0 --port 8000

環境変数 (必須):
    LINE_SECRETARY_CHANNEL_ACCESS_TOKEN
    LINE_SECRETARY_CHANNEL_SECRET
    LINE_CHANNEL_ACCESS_TOKEN  (Push通知用・既存秘書チャンネルと同じ)
    LINE_USER_ID
    NOTION_TOKEN
    NOTION_DB_RESEARCH_ID      (デフォルト: 33ba9f98-b152-8008-8f02-fd387341c4b4)
"""

import base64
import hashlib
import hmac
import json

import requests
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request

from config import (
    LINE_SECRETARY_CHANNEL_ACCESS_TOKEN,
    LINE_SECRETARY_CHANNEL_SECRET,
)
from notion_queue import add_research_request

app = FastAPI()


# ── ヘルスチェック ──────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok"}


# ── LINE 署名検証 ────────────────────────────────────────────────────────────────
def _verify_signature(body: bytes, signature: str) -> bool:
    secret = LINE_SECRETARY_CHANNEL_SECRET.encode("utf-8")
    digest = hmac.new(secret, body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected, signature)


# ── LINE Reply API ──────────────────────────────────────────────────────────────
def _reply_line(reply_token: str, text: str) -> None:
    r = requests.post(
        "https://api.line.me/v2/bot/message/reply",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_SECRETARY_CHANNEL_ACCESS_TOKEN}",
        },
        json={
            "replyToken": reply_token,
            "messages": [{"type": "text", "text": text}],
        },
        timeout=10,
    )
    if r.status_code != 200:
        print(f"[LINE reply error] {r.status_code}: {r.text}")


# ── リサーチキュー登録ハンドラ（バックグラウンド実行）────────────────────────────
def _handle_research(topic: str, reply_token: str) -> None:
    print(f"[research] queuing: {topic!r}")
    try:
        add_research_request(topic, source="LINE")
        print(f"[research] queued: {topic!r}")
        _reply_line(reply_token, f"📚 リサーチキューに追加しました\n\n「{topic}」\n\n毎日22時に自動処理、またはClaude Codeで `/research-podcast` を実行すると即時Podcast化されます。")
    except Exception as e:
        print(f"[research] Notion error: {e}")
        _reply_line(reply_token, "⚠️ キューへの追加に失敗しました。もう一度お試しください。")


# ── Webhook エンドポイント ────────────────────────────────────────────────────────
@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    body_bytes = await request.body()

    # 署名検証（LINE Messaging API 必須）
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
        topic = message.get("text", "").strip()
        if not topic:
            continue
        reply_token = event.get("replyToken", "")
        print(f"[webhook] received: {topic!r}")
        # Notion処理はバックグラウンドで実行し、LINEへ即座に200を返す
        background_tasks.add_task(_handle_research, topic, reply_token)

    return {"status": "ok"}
