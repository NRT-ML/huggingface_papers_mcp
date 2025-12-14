"""Hugging Faceの論文情報を配信するMCPサーバー。"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from mcp.server.fastmcp import FastMCP

import sys,os
from pathlib import Path
sys.path.append(str(Path(__file__).absolute().parent))

from tools.create_hf_papers_json_feed import create_hf_papers_json_feed


HF_TRENDING_URL = "https://huggingface.co/papers/trending"
HF_MONTHLY_URL_TEMPLATE = "https://huggingface.co/papers/month/{year_month}"

mcp = FastMCP("hf_papers")


def _convert_feed_items(feed: Dict, limit: int) -> List[Dict[str, str]]:
    """JSON FeedをMCPレスポンス用に整形する。

    Args:
        feed (dict): create_hf_papers_json_feedが返す辞書。
        limit (int): 返却する最大件数。

    Returns:
        list[dict[str, str]]: タイトルや概要を格納した辞書リスト。
    """

    items = feed.get("items", [])
    selected = items[:limit]
    response = []
    for item in selected:
        response.append(
            {
                "title": item.get("title", ""),
                "summary": item.get("content_text", ""),
                "paper_url": item.get("url", ""),
                "published_at": item.get("date_published"),
            }
        )
    return response


def _validate_limit(n_paper: int) -> int:
    """件数指定を検証して返す。

    Args:
        n_paper (int): 取得したい件数。

    Returns:
        int: 正常化された件数。

    Raises:
        ValueError: n_paperが正の整数ではない場合。
    """

    if n_paper <= 0:
        raise ValueError("n_paperは1以上を指定してください。")
    return n_paper


def _validate_year_month(year_month: str) -> str:
    """YYYY-MM形式の年月文字列を検証する。

    Args:
        year_month (str): 取得対象の年月。

    Returns:
        str: 検証済みの年月文字列。

    Raises:
        ValueError: フォーマットが不正な場合。
    """

    try:
        datetime.strptime(year_month, "%Y-%m")
    except ValueError as exc:
        raise ValueError("dateはYYYY-MM形式で指定してください。") from exc
    return year_month


@mcp.tool()
async def search_trend_papers(n_paper: int = 10) -> List[Dict[str, str]]:
    """トレンド上位の論文を取得する。

    Args:
        n_paper (int, optional): 返却する件数。デフォルトは10。

    Returns:
        list[dict[str, str]]: タイトル、概要、URLなどをまとめたリスト。
    """

    limit = _validate_limit(n_paper)
    feed = create_hf_papers_json_feed(HF_TRENDING_URL, length=limit)
    return _convert_feed_items(feed, limit)


@mcp.tool()
async def search_papers_monthly(date: str, n_paper: int = 5) -> List[Dict[str, str]]:
    """指定月の人気論文を取得する。

    Args:
        date (str): YYYY-MM形式の年月。
        n_paper (int, optional): 返却する件数。デフォルトは5。

    Returns:
        list[dict[str, str]]: 指定月の人気論文情報。
    """

    limit = _validate_limit(n_paper)
    validated_date = _validate_year_month(date)
    url = HF_MONTHLY_URL_TEMPLATE.format(year_month=validated_date)
    feed = create_hf_papers_json_feed(url, length=limit)
    return _convert_feed_items(feed, limit)


if __name__ == "__main__":
    mcp.run()