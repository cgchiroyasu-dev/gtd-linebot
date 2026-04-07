# Secretary LINE Bot

Hiroyasuの秘書専用 LINE Bot。送ったメッセージを自動でディープリサーチ → NotebookLM Podcast 化する。

GTD ボット（`automation/line_bot/`）とは**別チャンネル**。

## 使い方

1. 秘書用 LINE Bot に**調べてほしいことを送る**
   - 例: `量子コンピュータの最新動向`
   - 例: `日本のDJシーンのマーケットリサーチ`
   - 例: `生成AIと音楽クリエイターの関係`
2. Bot が「📚 リサーチキューに追加しました」と返信
3. 毎日22時に自動処理（または Claude Code で `/research-podcast` を実行）
4. 完了すると LINE に NotebookLM Podcast のリンクが届く

Claude Code から即時実行する場合:
```
/research-podcast 量子コンピュータの最新動向
```

キューを一括処理する場合（LINE経由で溜まったもの）:
```
/research-podcast
```

## セットアップ

### 1. LINE Official Account を作成

1. https://developers.line.biz/ → 新規プロバイダー → 新規チャンネル（Messaging API）
2. チャンネル名: 「秘書」など
3. **Channel Access Token**（長期）を発行 → `.env` の `LINE_SECRETARY_CHANNEL_ACCESS_TOKEN` に設定
4. **Channel Secret** → `.env` の `LINE_SECRETARY_CHANNEL_SECRET` に設定

### 2. 環境変数を設定

```bash
cp .env.example .env
# .env を編集してトークンを設定
```

### 3. Notion DB のプロパティ設定

`knowledge/systems/research_pipeline.md` の「Notion DB_Research」セクションを参照。

### 4. Render にデプロイ

```
Root Directory: automation/secretary_linebot
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

デプロイ後、Render の URL を LINE Console の Webhook URL に設定:
```
https://your-app.onrender.com/webhook
```

### 5. launchd 登録（22:00 自動バッチ）

```bash
launchctl load ~/Library/LaunchAgents/com.hiroyasu.research_podcast.plist
```

詳細は `CLAUDE.md` を参照。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `main.py` | FastAPI Webhook エンドポイント |
| `config.py` | 環境変数の読み込み・定数定義 |
| `notion_queue.py` | Notion DB_Research CRUD |
| `check_queue.py` | pending 件数チェック（launchd 用） |
| `ping.py` | Render スリープ防止 |
| `run_research_batch.sh` | 22:00 バッチ起動スクリプト |

## 関連ファイル

- `/research-podcast` スキル: `.claude/commands/research-podcast.md`
- リサーチ保存先: `knowledge/research/topics/`
- launchd plist: `~/Library/LaunchAgents/com.hiroyasu.research_podcast.plist`
- システム定義: `knowledge/systems/research_pipeline.md`
