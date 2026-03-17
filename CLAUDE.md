# LINE Bot → Notion タスク追加 — Claude 作業メモ

## ローカル起動

```bash
cd automation/line_bot

pip install -r requirements.txt
cp .env.example .env  # 初回のみ
# .env を編集してトークンを設定

uvicorn main:app --host 0.0.0.0 --port 8000
```

## ローカルテスト用トンネル（ngrok代替）

```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:8000
# → https://xxxx.trycloudflare.com を LINE Console の Webhook URL に設定
```

## デプロイ（Render）

- **本番URL**: https://gtd-linebot.onrender.com
- **GitHub**: https://github.com/Capel1801/gtd-linebot
- Render の Web Service に GitHub リポジトリを接続してデプロイ
- 環境変数は Render の Environment から設定（`.env` はデプロイしない）

## 必須環境変数

| 変数名 | 説明 |
|---|---|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API 長期トークン（170文字以上） |
| `LINE_CHANNEL_SECRET` | LINE チャネルシークレット |
| `NOTION_TOKEN` | Notion Integration トークン |
| `NOTION_DB_TASK_2026_ID` | DB_Task2026 のデータベースID |

## アーキテクチャ

| ファイル | 役割 |
|---|---|
| `main.py` | FastAPI エントリーポイント・署名検証・webhook処理 |
| `notion_client.py` | Notion API でタスク作成（Name / Date / Action Type） |

## 動作フロー

```
LINE メッセージ送信
  └→ POST /webhook (FastAPI)
       ├─ HMAC-SHA256 署名検証
       ├─ notion_client.create_task()
       │    Name: メッセージ内容
       │    Date: (設定しない)
       │    Action Type: (設定しない)
       └─ LINE 返信「✅ タスク追加: {タスク名}」
```

## Gotchas

- LINE チャネルアクセストークンは **170文字以上** が正規。短い文字列は別の値なので注意
- Notion Integration を DB_Task2026 に「コネクト」していないと 403 で失敗する
- Render は無料プランだとスリープあり → 初回リクエストに数十秒かかる場合がある
