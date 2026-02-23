"""
Agent configuration.

Provides a factory function that lazily initialises the LLM
(Kimi K2 via Groq) and creates a LangGraph ReAct agent.
"""

from functools import lru_cache

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from research_agent.tools import web_search

SYSTEM_PROMPT = (
    "You are a research agent. Always use web_search for factual claims.\n"
    "Output:\n"
    "1) TL;DR (2 bullets)\n"
    "2) Key points (5 bullets)\n"
    "3) Sources (URLs)\n"
)


@lru_cache(maxsize=1)
def get_agent():
    """Lazily create and cache the ReAct agent (avoids cold-start at import)."""
    llm = ChatGroq(
        model="moonshotai/kimi-k2-instruct",
        temperature=0,
    )
    return create_react_agent(
        llm,
        tools=[web_search],
        prompt=SystemMessage(content=SYSTEM_PROMPT),
    )
