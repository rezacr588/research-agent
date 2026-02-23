"""
Web search tool.

Wraps the Tavily Search API as a LangChain tool for use
by the research agent.
"""

import json
import logging
import os

from langchain_core.tools import tool
from tavily import TavilyClient

logger = logging.getLogger(__name__)

_tavily_client: TavilyClient | None = None


def _get_tavily_client() -> TavilyClient:
    """Return a cached TavilyClient, creating one on first use."""
    global _tavily_client
    if _tavily_client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY environment variable is not set. "
                "Please set it to use the web_search tool."
            )
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


def reset_client() -> None:
    """Reset the cached client. Used for test isolation."""
    global _tavily_client
    _tavily_client = None


@tool
def web_search(query: str, max_results: int = 6) -> str:
    """Search the web and return top results with titles, URLs, and snippets."""
    client = _get_tavily_client()
    try:
        resp = client.search(query=query, search_depth="basic", max_results=max_results)
    except Exception as exc:
        logger.error("Tavily API error: %s", exc)
        return json.dumps({"error": f"Search failed: {exc}"})

    results = []
    for r in resp.get("results", []):
        try:
            results.append({
                "title": r.get("title", "Untitled"),
                "url": r.get("url", ""),
                "snippet": r.get("content", ""),
            })
        except (TypeError, AttributeError) as exc:
            logger.warning("Skipping malformed result: %s", exc)
            continue

    return json.dumps(results, ensure_ascii=False)
