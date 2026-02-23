"""
Agent configuration with model fallback.

Provides a factory function that lazily initialises the LLM
and creates a LangGraph ReAct agent. If the primary model
(Kimi K2) is unavailable, falls back to GPT OSS 120B.
The agent is cached per session to avoid repeated API probes.
"""

import logging
from datetime import datetime

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from research_agent.tools import web_search

logger = logging.getLogger(__name__)

MODELS = [
    "moonshotai/kimi-k2-instruct",
    "openai/gpt-oss-120b",
]

SYSTEM_PROMPT_TEMPLATE = """\
You are Research Agent — a sharp, thorough, and friendly AI research assistant.

## Current Time
Today is {current_date}. The current time is {current_time}. \
Always use this as your reference for "today", "this year", "recently", etc. \
Do NOT assume an older date based on your training data.

## Personality
- You are curious, precise, and conversational.
- You explain things clearly and cite your sources.
- When uncertain, you say so honestly rather than guessing.
- You add helpful context the user might not have asked for but would appreciate.

## Behaviour
- ALWAYS use web_search for factual claims, current events, or anything time-sensitive.
- If the first search doesn't give enough info, search again with a refined query.
- Never fabricate URLs or statistics.

## Output Format
Structure every answer as:
1) **TL;DR** (2 concise bullets)
2) **Key Points** (up to 5 detailed bullets)
3) **Sources** (URLs from your search results)
"""

# Cached agent and model name (set once per session)
_cached_agent = None
_active_model: str = ""


def _build_system_prompt() -> SystemMessage:
    """Build the system prompt with the current date/time injected."""
    now = datetime.now()
    return SystemMessage(content=SYSTEM_PROMPT_TEMPLATE.format(
        current_date=now.strftime("%A, %B %d, %Y"),
        current_time=now.strftime("%H:%M %Z").strip(),
    ))


def get_agent():
    """Return the cached agent, or create one (with fallback) on first call."""
    global _cached_agent, _active_model
    if _cached_agent is not None:
        return _cached_agent

    for model_id in MODELS:
        try:
            llm = ChatGroq(model=model_id, temperature=0)
            # Quick probe to verify the model is reachable
            llm.invoke("ping")
            logger.info("Using model: %s", model_id)
            _active_model = model_id
            _print_model_info(model_id)
            _cached_agent = create_react_agent(
                llm,
                tools=[web_search],
                prompt=_build_system_prompt(),
            )
            return _cached_agent
        except Exception as exc:
            logger.warning("Model %s unavailable (%s), trying next...", model_id, exc)
            _print_fallback_warning(model_id, exc)
            continue

    raise RuntimeError(
        f"All models are unavailable: {MODELS}. "
        "Check https://groqstatus.com for incidents."
    )


def get_active_model() -> str:
    """Return the model ID currently in use."""
    return _active_model


def reset_agent() -> None:
    """Force re-creation of the agent (e.g., after a 503 mid-session)."""
    global _cached_agent
    _cached_agent = None


def _print_model_info(model_id: str) -> None:
    """Show which model was selected."""
    try:
        from rich.console import Console
        Console().print(f"[dim]🤖 Model: {model_id}[/dim]")
    except ImportError:
        print(f"Model: {model_id}")


def _print_fallback_warning(model_id: str, exc: Exception) -> None:
    """Warn the user about a model fallback."""
    try:
        from rich.console import Console
        Console().print(f"[yellow]⚠️  {model_id} unavailable, trying fallback...[/yellow]")
    except ImportError:
        print(f"Warning: {model_id} unavailable ({exc}), trying fallback...")
