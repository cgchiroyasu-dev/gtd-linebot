# LINE Bot → Notion タスク追加

LINEにタスク名を送ると、Notion DB_Task2026にDateが「今日」のタスクを自動登録するbot。

## 動作フロー

```
LINEでメッセージ送信
  └→ Render (FastAPI)
       ├─ 署名検証
       ├─ Notion DB_Task2026 にタスク作成
       │    Name: メッセージ内容
       │    Date: 今日(JST)
       │    actiontype: Next Action
       └─ LINE返信 "✅ タスク追加: {タスク名}"
```

---

## 事前準備

### 1. LINE Developers Console でチャネルを作成

1. https://developers.line.biz/ja/ にアクセス
2. **新規プロバイダー作成** → **Messaging API チャネル作成**
3. チャネル作成後、「Messaging API設定」タブを開く
4. **Channel Secret** をコピー（後で使用）
5. **チャネルアクセストークン（長期）** を発行してコピー
6. 「応答メッセージ」を **オフ** に設定
7. 「Webhook送信」を **オン** に設定

---

## ローカルでのテスト（ngrok使用）

```bash
cd automation/line_bot

# 依存関係インストール
pip install -r requirements.txt

# .env を作成して設定値を入力
cp .env.example .env
# .env を編集して実際のトークンを入力

# サーバー起動
uvicorn main:app --port 8000

# 別ターミナルでngrok起動
ngrok http 8000
```

ngrokが発行したHTTPS URLを LINE ConsoleのWebhook URLに設定：
```
https://xxxx.ngrok.io/webhook
```

「検証」ボタンをクリックして `{"status":"ok"}` が返れば成功。

---

## Render へのデプロイ

### 1. GitHubにpush

```bash
git add automation/line_bot/
git commit -m "feat: LINE bot for Notion task creation"
git push
```

### 2. Render Web Service を作成

1. https://render.com にアクセス → **New Web Service**
2. GitHubリポジトリを接続
3. 以下を設定：

| 項目 | 値 |
|------|-----|
| Root Directory | `automation/line_bot` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

### 3. 環境変数を設定

Renderダッシュボードの **Environment** タブで以下を追加：

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINEで発行したトークン |
| `LINE_CHANNEL_SECRET` | LINEのChannel Secret |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DB_TASK_2026_ID` | `2baa9f98-b152-815b-bc56-c0daa2ef9964` |

### 4. Webhook URL を更新

Renderが発行したURL（例: `https://line-bot-hiroyasu.onrender.com`）を LINE ConsoleのWebhook URLに設定：
```
https://line-bot-hiroyasu.onrender.com/webhook
```

---

## 動作確認

1. LINEで「テストタスク」と送信
2. Notion DB_Task2026 を確認：
   - Name: テストタスク
   - Date: 今日の日付
   - actiontype: Next Action
3. LINEに `✅ タスク追加: テストタスク` が返信されることを確認

---

## 注意事項

- **Renderの無料プランはスリープあり**: 15分無操作後にスリープし、復帰に最大30秒かかる。
  LINEのreply tokenは30秒で失効するため、最初のメッセージの返信が届かない場合がある（タスクは登録される）。
  → [UptimeRobot](https://uptimerobot.com/) で `/health` を5分間隔でpingすれば回避可能。

- **Notion Integration の権限**: Notion IntegrationにDB_Task2026への書き込み権限を付与すること。
  Notionで対象DBを開き、右上「...」→「コネクト」からIntegrationを追加。
