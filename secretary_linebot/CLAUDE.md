# Secretary LINE Bot — Claude 作業メモ

## 概要

GTD ボット（`automation/line_bot/`）とは**別チャンネル**の秘書専用 LINE Bot。
送られてきた全メッセージをリサーチリクエストとして Notion DB_Research キューに追加する。

GTD ボットとの違い:
| | GTD Bot | Secretary Bot |
|---|---|---|
| チャンネル | 別 | 別 |
| 受信したメッセージ | Notion DB_Task2026 にタスク作成 | Notion DB_Research にリサーチキュー追加 |
| 返信 | ✅ タスク追加: {名前} | 📚 リサーチキューに追加: {トピック} |

---

## ローカル起動

```bash
cd automation/secretary_linebot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # 初回のみ、トークンを設定
uvicorn main:app --host 0.0.0.0 --port 8001  # GTDボット(8000)と別ポート
```

## ローカルテスト用トンネル

```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:8001
# → https://xxxx.trycloudflare.com を LINE Console の Webhook URL に設定
```

## デプロイ（Render）

- **新規 Web Service** を作成（GTD ボットとは別サービス）
- **Repository**: `Capel1801/gtd-linebot` または新規リポジトリ
- **Root Directory**: `automation/secretary_linebot`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- 環境変数は Render の Environment から設定

## 必須環境変数

| 変数名 | 説明 |
|---|---|
| `LINE_SECRETARY_CHANNEL_ACCESS_TOKEN` | 秘書用 LINE Official Account のトークン（170文字以上） |
| `LINE_SECRETARY_CHANNEL_SECRET` | 秘書用チャネルシークレット |
| `LINE_CHANNEL_ACCESS_TOKEN` | 既存のPush通知用トークン（secretary/.envと同じ） |
| `LINE_USER_ID` | Hiroyasuの LINE User ID |
| `NOTION_TOKEN` | Notion Integration トークン |
| `NOTION_DB_RESEARCH_ID` | DB_Research のDB ID（デフォルト: 33ba9f98-b152-8008-8f02-fd387341c4b4） |

## Notion DB セットアップ

1. https://www.notion.so/hiroyasuseki/33ba9f98b15280088f02fd387341c4b4 を開く
2. 右上「...」→「Connections」→「Claude Code」を追加
3. 同じ手順で Secretary Bot の Notion Integration も追加
4. DB プロパティを以下の通り作成:

| プロパティ名 | 型 | 選択肢 |
|---|---|---|
| `Status` | Select | pending / processing / done / error |
| `Source` | Select | LINE / Claude |
| `ProcessedAt` | Date | — |
| `LocalMDPath` | Text | — |
| `NotebookLMURL` | URL | — |
| `Summary` | Text | — |
| `Tags` | Multi-select | — |
| `Complexity` | Select | standard / deep |

## launchd セットアップ（22:00 自動バッチ）

```bash
# plist を登録
launchctl load ~/Library/LaunchAgents/com.hiroyasu.research_podcast.plist

# 手動テスト実行
launchctl start com.hiroyasu.research_podcast

# ログ確認
tail -f /tmp/research_podcast_batch.log

# 無効化
launchctl unload ~/Library/LaunchAgents/com.hiroyasu.research_podcast.plist
```

> **注意**: `run_research_batch.sh` は `claude -p` を使用するため **API クレジット**を消費します。
> pending が 0 件のときは自動的にスキップされます。

## スリープ防止（Render 無料プラン）

GTD ボットと同様に2重構成:
- **UptimeRobot**: `/health` を5分おきに ping
- **Render Cron Job**: `python ping.py` を `*/5 * * * *` で実行

## アーキテクチャ

```
LINE メッセージ（どんな内容でもOK）
  └→ POST /webhook (FastAPI)
       ├─ HMAC-SHA256 署名検証
       ├─ HTTP 200 を即時返却
       └─ BackgroundTask
            ├─ notion_queue.add_research_request(topic, source="LINE")
            └─ LINE 返信「📚 リサーチキューに追加: {トピック}」
```

## Gotchas

- `LINE_SECRETARY_CHANNEL_ACCESS_TOKEN` と `LINE_CHANNEL_ACCESS_TOKEN` は**別変数**
  - Secretary: 受信 + 返信用（新チャンネル）
  - Channel: Push通知送信用（既存秘書チャンネル）
- Notion DB に Integration を「コネクト」しないと 403 エラー
- `_verify_signature` の secret は `LINE_SECRETARY_CHANNEL_SECRET` を使うこと（GTDボットと混同しない）
- BackgroundTask の関数は `async def` ではなく **sync `def`** にすること
