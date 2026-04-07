"""
check_queue.py — Notion DB_Research の pending 件数を標準出力に出力する

launchd バッチスクリプト（run_research_batch.sh）から呼ばれ、
pending が0件のときは claude -p を実行しないようにする。
"""

import sys
from pathlib import Path

# このスクリプトのディレクトリを sys.path に追加
sys.path.insert(0, str(Path(__file__).parent))

from notion_queue import count_pending

if __name__ == "__main__":
    try:
        count = count_pending()
        print(count)
    except Exception as e:
        print(f"[check_queue] error: {e}", file=sys.stderr)
        print(0)
