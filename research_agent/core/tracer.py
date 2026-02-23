"""
Execution tracer.

Streams the agent's response step-by-step and persists each
run as a timestamped trace file under outputs/.
"""

import logging
import os
from datetime import datetime

from langchain_core.messages import AIMessage, ToolMessage

from research_agent.agent import agent

logger = logging.getLogger(__name__)


def run_with_trace(question: str) -> None:
    """Stream the agent's response and log each step to console and file."""
    lines: list[str] = [
        f"Question: {question}",
        f"Timestamp: {datetime.now().isoformat()}",
        "-" * 60,
    ]

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        msg = chunk["messages"][-1]

        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            line = "🧠 Tool call: " + str([tc["name"] for tc in msg.tool_calls])
            print(line)
            lines.append(line)
        elif isinstance(msg, ToolMessage):
            line = "🔧 Tool result (preview): " + str(msg.content)[:250] + " ..."
            print(line)
            lines.append(line)
        elif isinstance(msg, AIMessage) and msg.content:
            line = "✅ Final answer:\n" + msg.content
            print(line)
            lines.append(line)

    _save_trace(lines)


def _save_trace(lines: list[str]) -> None:
    """Persist trace lines to a timestamped file under outputs/."""
    try:
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = os.path.join("outputs", f"trace_{timestamp}.txt")
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"\n📁 Trace saved to {filepath}")
    except OSError as exc:
        logger.debug("Could not save trace file: %s", exc)
