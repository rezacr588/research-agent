"""
Agent configuration.

Provides a factory function that lazily initialises the LLM
(Kimi K2 via Groq) and creates a LangGraph ReAct agent.
The system prompt includes the current date/time so the agent
is aware of the real-world timeline.
"""

from datetime import datetime

from langchain_core.messages import SystemMessage
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent

from research_agent.tools import web_search

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


def _build_system_prompt() -> SystemMessage:
    """Build the system prompt with the current date/time injected."""
    now = datetime.now()
    return SystemMessage(content=SYSTEM_PROMPT_TEMPLATE.format(
        current_date=now.strftime("%A, %B %d, %Y"),
        current_time=now.strftime("%H:%M %Z").strip(),
    ))


def get_agent():
    """Create a fresh ReAct agent with the current timestamp in the prompt."""
    llm = ChatGroq(
        model="moonshotai/kimi-k2-instruct",
        temperature=0,
    )
    return create_react_agent(
        llm,
        tools=[web_search],
        prompt=_build_system_prompt(),
    )
