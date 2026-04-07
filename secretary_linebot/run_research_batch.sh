#!/bin/bash
# run_research_batch.sh — ディープリサーチ 22:00 自動バッチ
# launchd (com.hiroyasu.research_podcast.plist) から呼ばれる
#
# 注意: このスクリプトは `claude -p` を使用するため API クレジットを消費します。
#       （claude.ai サブスクリプションではなく Anthropic API クレジット）

set -euo pipefail

LOG="/tmp/research_podcast_batch.log"
exec >> "$LOG" 2>&1
echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== Research Podcast Batch Start ====="

REPO="$HOME/ClaudeCodeH"
BOT_DIR="$REPO/automation/secretary_linebot"

# ── PATH 設定（nodenv / nvm 対応）──────────────────────────────────────────────
export PATH="$HOME/.nodenv/shims:$HOME/.nodenv/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
if [ -d "$HOME/.nvm" ]; then
    export NVM_DIR="$HOME/.nvm"
    NVM_NODE=$(ls "$NVM_DIR/versions/node" 2>/dev/null | sort -V | tail -1)
    if [ -n "$NVM_NODE" ]; then
        export PATH="$NVM_DIR/versions/node/$NVM_NODE/bin:$PATH"
    fi
fi

# ── 環境変数ロード（Notion トークン等）──────────────────────────────────────────
if [ -f "$BOT_DIR/.env" ]; then
    set -a
    source "$BOT_DIR/.env"
    set +a
fi

# ── pending 件数チェック ──────────────────────────────────────────────────────
cd "$BOT_DIR"
PENDING_COUNT=$(python3 check_queue.py 2>/dev/null || echo "0")
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pending items: $PENDING_COUNT"

if [ "$PENDING_COUNT" -eq "0" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] No pending items. Exiting."
    exit 0
fi

# ── claude -p でリサーチパイプラインを実行 ────────────────────────────────────
PROMPT="$REPO/.claude/commands/research-podcast.md"
if [ ! -f "$PROMPT" ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: research-podcast.md not found"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Running research pipeline for $PENDING_COUNT topics..."
cd "$REPO"

# /research-podcast をキュー処理モード（引数なし）で実行
claude -p "$(cat "$PROMPT")

---
実行指示: 引数なしモード（キュー処理）として実行してください。
Notion DB_Research の pending アイテムを全て処理してください。" 2>&1

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ===== Research Podcast Batch Complete ====="
