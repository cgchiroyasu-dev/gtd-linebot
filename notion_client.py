"""
notion_client.py — DB_Task2026 にタスクを1件作成する専用モジュール

Usage:
    from notion_client import create_task
    from datetime import date
    create_task("英語の勉強", date.today())
"""

import hashlib
import os
import time
from datetime import date

import requests

NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {os.environ['NOTION_TOKEN']}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION,
    }


def _post_with_retry(url: str, payload: dict, max_retries: int = 3) -> requests.Response:
    response = None
    for attempt in range(max_retries):
        response = requests.post(url, headers=_headers(), json=payload, timeout=30)
        if response.status_code == 429:
            wait = 2 ** attempt
            print(f"[notion] rate limited, retrying in {wait}s (attempt {attempt + 1})")
            time.sleep(wait)
            continue
        return response
    return response  # type: ignore[return-value]


def create_task(title: str, task_date: date) -> dict:
    """
    DB_Task2026 に1件のタスクを作成する。

    Args:
        title: タスク名
        task_date: 実行日（YYYY-MM-DD形式でNotionに登録）

    Returns:
        作成されたNotionページのdict

    Raises:
        RuntimeError: Notion APIがエラーを返した場合
    """
    db_id = os.environ["NOTION_DB_TASK_2026_ID"]
    payload = {
        "parent": {"database_id": db_id},
        "properties": {
            "Name": {
                "title": [{"text": {"content": title}}]
            },
            "Date": {
                "date": {"start": task_date.isoformat()}
            },
            "Action Type": {
                "select": {"name": "Next Action"}
            },
        },
    }
    response = _post_with_retry(f"{NOTION_BASE_URL}/pages", payload)
    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Notion API error {response.status_code}: {response.text}"
        )
    return response.json()
