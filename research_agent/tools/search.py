"""
Web search tool — the agent's connection to the internet.

This module wraps the Tavily Search API as a LangChain-compatible tool.
When the agent decides it needs information, it calls this tool with
a search query and gets back structured results (title, URL, snippet).

Why Tavily instead of Google/Bing?
  - Tavily is PURPOSE-BUILT for AI agents
  - It returns clean, structured JSON (not raw HTML pages)
  - No scraping or parsing needed — just query and get results
  - Free tier available for development

The tool is registered with the @tool decorator, which tells LangChain:
  "Hey, the LLM can call this function when it needs to search the web."
"""

import json
import logging
import os

# @tool decorator: converts a regular Python function into a
# LangChain Tool that the agent can call autonomously
from langchain_core.tools import tool

# TavilyClient: official Python client for the Tavily Search API
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# ─── Client Cache ────────────────────────────────────────────────
# We cache the TavilyClient so we don't create a new one per search.
# This avoids unnecessary overhead and API key validation on every call.
_tavily_client: TavilyClient | None = None


def _get_tavily_client() -> TavilyClient:
    """
    Return a cached TavilyClient, creating one on first use.

    The client is created lazily (not at import time) because:
      1. The API key might not be set yet when this module is imported
      2. Tests can mock this function to avoid real API calls
    """
    global _tavily_client
    if _tavily_client is None:
        # Read the API key from environment variables
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY environment variable is not set. "
                "Please set it to use the web_search tool."
            )
        _tavily_client = TavilyClient(api_key=api_key)
    return _tavily_client


def reset_client() -> None:
    """
    Reset the cached client.

    Used in tests to ensure each test gets a fresh mock client.
    Without this, mocks from one test could leak into the next.
    """
    global _tavily_client
    _tavily_client = None


# ─── The Tool Itself ─────────────────────────────────────────────
# The @tool decorator registers this function so the LLM can call it.
# The docstring becomes the tool's description — the LLM reads this
# to decide WHEN and HOW to use the tool.
@tool
def web_search(query: str, max_results: int = 6) -> str:
    """Search the web and return top results with titles, URLs, and snippets."""
    client = _get_tavily_client()

    # ── Step 1: Call the Tavily API ──
    try:
        resp = client.search(
            query=query,
            search_depth="basic",       # "basic" is fast; "advanced" is slower but deeper
            max_results=max_results,    # How many results to return (default: 6)
        )
    except Exception as exc:
        # If the API call fails (network error, rate limit, etc.),
        # return an error as JSON instead of crashing.
        # The agent will see this error and can still generate a response.
        logger.error("Tavily API error: %s", exc)
        return json.dumps({"error": f"Search failed: {exc}"})

    # ── Step 2: Extract and normalize results ──
    # Tavily returns a dict with a "results" key containing a list.
    # We extract just the fields we need: title, url, snippet.
    results = []
    for r in resp.get("results", []):  # .get() avoids KeyError if "results" is missing
        try:
            results.append({
                "title": r.get("title", "Untitled"),   # Defensive: default if missing
                "url": r.get("url", ""),                # Defensive: empty string if missing
                "snippet": r.get("content", ""),        # Tavily calls it "content", we call it "snippet"
            })
        except (TypeError, AttributeError) as exc:
            # Skip any result that's malformed (e.g., None instead of dict)
            logger.warning("Skipping malformed result: %s", exc)
            continue

    # ── Step 3: Return as JSON string ──
    # The agent receives this string and uses it to formulate its answer.
    # ensure_ascii=False preserves special characters (accents, emoji, etc.)
    return json.dumps(results, ensure_ascii=False)
