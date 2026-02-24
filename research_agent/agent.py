"""
Agent configuration with model fallback.

This module is the BRAIN of the application. It:
  1. Defines which LLM models to try (primary + fallback)
  2. Crafts a detailed system prompt that shapes the agent's personality
  3. Creates a LangGraph ReAct agent that can call tools (web_search)
  4. Caches the agent so we only pay the initialization cost once

Key Concept — ReAct (Reason + Act):
  The agent doesn't answer in one shot. Instead, it runs in a loop:
    REASON → "I need to search for X"
    ACT    → calls web_search("X")
    OBSERVE→ reads the results
    REASON → "Now I have enough info" or "I need more"
    ...repeat until satisfied...
    ANSWER → synthesizes a final response

  LangGraph's `create_react_agent` handles this loop automatically.
"""

import logging
from datetime import datetime

# LangChain's message types — used to build the system prompt
from langchain_core.messages import SystemMessage

# ChatGroq is the LangChain wrapper for Groq's API
# Groq provides ultra-fast inference using their LPU (Language Processing Unit)
from langchain_groq import ChatGroq

# create_react_agent is a prebuilt LangGraph function that creates
# a full ReAct loop: LLM → tool calls → observation → repeat
from langgraph.prebuilt import create_react_agent

# Import our custom web search tool (the only tool the agent has)
from research_agent.tools import web_search

logger = logging.getLogger(__name__)

# ─── Model Configuration ────────────────────────────────────────
# Models are tried IN ORDER. If the first one fails (e.g., 503),
# we automatically fall back to the next one.
MODELS = [
    "moonshotai/kimi-k2-instruct",  # Primary: Kimi K2 — strong reasoning
    "openai/gpt-oss-120b",          # Fallback: GPT OSS 120B
]

# ─── System Prompt ───────────────────────────────────────────────
# This template is injected as the FIRST message in every conversation.
# It defines WHO the agent is, HOW it should behave, and the OUTPUT FORMAT.
# {current_date} and {current_time} are filled at runtime so the agent
# always knows "today" — critical for time-sensitive questions.
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

# ─── Agent Cache ─────────────────────────────────────────────────
# We cache the agent instance so it's only created once per session.
# This avoids repeated "ping" calls to verify model availability.
_cached_agent = None
_active_model: str = ""


def _build_system_prompt() -> SystemMessage:
    """
    Build the system prompt with the current date/time injected.

    Why inject the date?
      LLMs have a training cutoff — they don't know "today's" date.
      By injecting it, the agent can correctly answer questions like
      "What happened this week?" or "Who is the current president?"
    """
    now = datetime.now()
    return SystemMessage(content=SYSTEM_PROMPT_TEMPLATE.format(
        current_date=now.strftime("%A, %B %d, %Y"),   # e.g., "Monday, February 24, 2026"
        current_time=now.strftime("%H:%M %Z").strip(),  # e.g., "16:30 AST"
    ))


def get_agent():
    """
    Return the cached agent, or create one (with fallback) on first call.

    How it works:
      1. If the agent was already created, return it immediately (cached).
      2. Otherwise, try each model in MODELS list:
         a. Create a ChatGroq LLM with that model
         b. Send a quick "ping" to verify it's reachable
         c. If it works → create the ReAct agent and cache it
         d. If it fails → log a warning and try the next model
      3. If ALL models fail → raise a RuntimeError

    The agent is wired with:
      - The LLM (for reasoning)
      - The tools list (just [web_search] for now)
      - The system prompt (personality + output format)
    """
    global _cached_agent, _active_model

    # Return cached agent if already initialized
    if _cached_agent is not None:
        return _cached_agent

    # Try each model until one works
    for model_id in MODELS:
        try:
            # Create the LLM client — temperature=0 for deterministic answers
            llm = ChatGroq(model=model_id, temperature=0)

            # Quick probe: send "ping" to verify the model is online
            # This catches 503/unavailable errors BEFORE the user asks a question
            llm.invoke("ping")

            logger.info("Using model: %s", model_id)
            _active_model = model_id
            _print_model_info(model_id)

            # Create the ReAct agent using LangGraph
            # This wires together: LLM + tools + system prompt
            # The agent can now autonomously decide when to call web_search
            _cached_agent = create_react_agent(
                llm,
                tools=[web_search],       # List of tools the agent can use
                prompt=_build_system_prompt(),  # System prompt with personality
            )
            return _cached_agent

        except Exception as exc:
            # Model unavailable → warn and try the next one
            logger.warning("Model %s unavailable (%s), trying next...", model_id, exc)
            _print_fallback_warning(model_id, exc)
            continue

    # All models failed — nothing we can do
    raise RuntimeError(
        f"All models are unavailable: {MODELS}. "
        "Check https://groqstatus.com for incidents."
    )


def get_active_model() -> str:
    """Return the model ID currently in use (e.g., 'moonshotai/kimi-k2-instruct')."""
    return _active_model


def reset_agent() -> None:
    """
    Force re-creation of the agent on the next call.

    Used when we get a 503 mid-session — the current model might
    have gone down, so we want to re-probe and potentially fall back.
    """
    global _cached_agent
    _cached_agent = None


# ─── UI Helpers ──────────────────────────────────────────────────

def _print_model_info(model_id: str) -> None:
    """Show which model was selected (uses Rich if available)."""
    try:
        from rich.console import Console
        Console().print(f"[dim]🤖 Model: {model_id}[/dim]")
    except ImportError:
        print(f"Model: {model_id}")


def _print_fallback_warning(model_id: str, exc: Exception) -> None:
    """Warn the user that a model was unavailable and we're trying the next one."""
    try:
        from rich.console import Console
        Console().print(f"[yellow]⚠️  {model_id} unavailable, trying fallback...[/yellow]")
    except ImportError:
        print(f"Warning: {model_id} unavailable ({exc}), trying fallback...")
