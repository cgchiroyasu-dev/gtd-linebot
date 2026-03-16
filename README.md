# LINE Bot → Notion タスク追加

LINEにタスク名を送ると、Notion DB_Task2026にDateが「今日」のタスクを自動登録するbot。

## 動作フロー

```
LINEでメッセージ送信
  └→ Render (FastAPI)
       ├─ 署名検証 (HMAC-SHA256)
       ├─ Notion DB_Task2026 にタスク作成
       │    Name: メッセージ内容
       │    Date: 今日(JST)
       │    Action Type: Next Action
       └─ LINE返信 "✅ タスク追加: {タスク名}"
```

**GitHub**: https://github.com/Capel1801/gtd-linebot
**本番URL**: https://gtd-linebot.onrender.com

---

## 事前準備

### 1. LINE Developers Console でチャネルを作成

1. https://developers.line.biz/ja/ にアクセス
2. **新規プロバイダー作成** → **Messaging API チャネル作成**
3. チャネル作成後、「Messaging API設定」タブを開く
4. **Channel Secret**（「チャネル基本設定」タブ）をコピー
5. **チャネルアクセストークン（長期）** を発行してコピー
   - ⚠️ 正規トークンは170文字以上の長い文字列。短い文字列はUser IDなど別の値なので注意
6. 「応答メッセージ」を **オフ** に設定
7. 「Webhook送信」を **オン** に設定

### 2. Notion Integrationの権限付与

NotionでDB_Task2026を開き、右上「...」→「コネクト」からIntegrationを追加。
**これをしないとNotionへの書き込みが403で失敗する。**

---

## ローカルでのテスト

```bash
pip install -r requirements.txt
cp .env.example .env
# .env を編集して実際のトークンを入力

uvicorn main:app --port 8000
```

### トンネリング（ngrokの代替）

ngrokはアカウント登録が必要になったため **cloudflared** を使う（認証不要）：

```bash
brew install cloudflare/cloudflare/cloudflared
cloudflared tunnel --url http://localhost:8000
# → https://xxxx.trycloudflare.com が発行される
```

LINE ConsoleのWebhook URLに設定：
```
https://xxxx.trycloudflare.com/webhook
```

「検証」ボタンで `{"status":"ok"}` が返れば成功。

---

## Render へのデプロイ

### 1. Render Web Service を作成

1. https://render.com → **New Web Service**
2. GitHubリポジトリ `Capel1801/gtd-linebot` を接続
3. 以下を設定：

| 項目 | 値 |
|------|-----|
| Root Directory | （空白） |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |

### 2. 環境変数を設定

| Key | Value |
|-----|-------|
| `LINE_CHANNEL_ACCESS_TOKEN` | LINEで発行したトークン（長期、170文字以上） |
| `LINE_CHANNEL_SECRET` | LINEのChannel Secret（32文字のhex） |
| `NOTION_TOKEN` | Notion Integration Token |
| `NOTION_DB_TASK_2026_ID` | `2baa9f98-b152-815b-bc56-c0daa2ef9964` |

### 3. Webhook URL を設定

```
https://gtd-linebot.onrender.com/webhook
```

---

## 動作確認

1. LINEで「テストタスク」と送信
2. Notion DB_Task2026 を確認：
   - Name: テストタスク
   - Date: 今日の日付
   - Action Type: Next Action
3. LINEに `✅ タスク追加: テストタスク` が返信されることを確認

---

## トラブルシューティング

### ⚠️ タスクの追加に失敗しました、と返ってくる

**原因1: Notionプロパティ名の不一致**
コードと実際のDBのプロパティ名が違う。以下で実際の名前を確認する：
```python
import os, requests
r = requests.get(
    'https://api.notion.com/v1/databases/2baa9f98-b152-815b-bc56-c0daa2ef9964',
    headers={'Authorization': f'Bearer {NOTION_TOKEN}', 'Notion-Version': '2022-06-28'}
)
for k, v in r.json()['properties'].items():
    print(f'{k!r}: {v["type"]}')
```
→ `notion_client.py` のプロパティ名を実際のDBに合わせて修正する。

**原因2: NotionのIntegration権限不足**
DB_Task2026の「コネクト」からIntegrationを追加する（上記「事前準備」参照）。

**原因3: NOTION_TOKENが間違っている**
uvicornのログで `401` が出ていないか確認する。

### LINEから返信が届かない（タスクは登録される）

**原因: Renderのコールドスタート**
無料プランは15分無操作でスリープ。復帰に最大30秒かかりreply token（30秒で失効）が切れる。

**対策**: [UptimeRobot](https://uptimerobot.com/) で `/health` を5分間隔でpingする（無料）。
```
https://gtd-linebot.onrender.com/health
```

### 署名検証エラー（400 Invalid signature）

LINE ConsoleのChannel Secretが `.env` のものと一致しているか確認する。
