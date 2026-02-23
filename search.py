from tavily import TavilyClient
from langchain_core.tools import tool
import os, json

_tavily_client = None

def _get_tavily_client():
    """Lazily initialize and cache the TavilyClient."""
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

@tool
def web_search(query: str, max_results: int = 6) -> str:
    """Search the web and return top results with titles + URLs + snippets."""
    client = _get_tavily_client()
    resp = client.search(query=query, search_depth="basic", max_results=max_results)
    results = [{"title": r["title"], "url": r["url"], "snippet": r.get("content", "")}
               for r in resp.get("results", [])]
    return json.dumps(results, ensure_ascii=False)