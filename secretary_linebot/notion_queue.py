"""
notion_queue.py — Notion DB_Research への CRUD 操作

リサーチリクエストのキュー管理（追加・取得・更新）。
"""

import time
from datetime import datetime, timezone

import requests

from config import NOTION_TOKEN, NOTION_DB_RESEARCH_ID


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json",
    }


def _with_retry(fn, retries: int = 3):
    """429レートリミット対応のリトライラッパー"""
    for attempt in range(retries):
        result = fn()
        if result.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        result.raise_for_status()
        return result.json()
    raise RuntimeError(f"Notion API failed after {retries} retries")


def add_research_request(topic: str, source: str = "LINE") -> dict:
    """リサーチリクエストをNotionキューに追加する。

    Args:
        topic: リサーチトピックのテキスト
        source: 入力元（"LINE" or "Claude"）

    Returns:
        作成されたNotionページのdict
    """
    def call():
        return requests.post(
            "https://api.notion.com/v1/pages",
            headers=_headers(),
            json={
                "parent": {
                    "type": "database_id",
                    "database_id": NOTION_DB_RESEARCH_ID,
                },
                "properties": {
                    "Topic": {
                        "title": [{"text": {"content": topic[:2000]}}]
                    },
                    "Status": {"select": {"name": "pending"}},
                    "Source": {"select": {"name": source}},
                },
            },
            timeout=10,
        )

    return _with_retry(call)


def get_pending_requests() -> list[dict]:
    """Status が pending のリサーチリクエストを全件取得する。

    Returns:
        [{"id": page_id, "topic": str}, ...]
    """
    def call():
        return requests.post(
            f"https://api.notion.com/v1/databases/{NOTION_DB_RESEARCH_ID}/query",
            headers=_headers(),
            json={
                "filter": {
                    "property": "Status",
                    "select": {"equals": "pending"},
                }
            },
            timeout=10,
        )

    data = _with_retry(call)
    results = []
    for page in data.get("results", []):
        title_list = page.get("properties", {}).get("Topic", {}).get("title", [])
        topic = title_list[0]["plain_text"] if title_list else ""
        if topic:
            results.append({"id": page["id"], "topic": topic})
    return results


def count_pending() -> int:
    """pending なリクエスト件数を返す（launchd バッチ判定用）"""
    return len(get_pending_requests())


def update_request_done(
    page_id: str,
    local_md_path: str,
    summary: str,
    tags: list[str],
    complexity: str,
    notebooklm_url: str = "",
) -> dict:
    """処理完了後に Notion ページを更新する。

    Args:
        page_id: 対象 Notion ページ ID
        local_md_path: knowledge/research/topics/ からの相対パス
        summary: 日本語150文字サマリー
        tags: タグリスト
        complexity: "standard" or "deep"
        notebooklm_url: NotebookLM ノートブック URL
    """
    now_jst = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+09:00")

    props: dict = {
        "Status": {"select": {"name": "done"}},
        "ProcessedAt": {"date": {"start": now_jst}},
        "LocalMDPath": {
            "rich_text": [{"text": {"content": local_md_path[:2000]}}]
        },
        "Summary": {
            "rich_text": [{"text": {"content": summary[:2000]}}]
        },
        "Tags": {
            "multi_select": [{"name": t[:100]} for t in tags[:10]]
        },
        "Complexity": {"select": {"name": complexity}},
    }
    if notebooklm_url:
        props["NotebookLMURL"] = {"url": notebooklm_url}

    def call():
        return requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=_headers(),
            json={"properties": props},
            timeout=10,
        )

    return _with_retry(call)


def update_notebooklm_url(page_id: str, url: str) -> dict:
    """NotebookLM URL のみを後から更新する（Podcast生成後に呼ぶ）"""
    def call():
        return requests.patch(
            f"https://api.notion.com/v1/pages/{page_id}",
            headers=_headers(),
            json={"properties": {"NotebookLMURL": {"url": url}}},
            timeout=10,
        )

    return _with_retry(call)
