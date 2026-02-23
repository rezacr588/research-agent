"""
Execution tracer with rich console output.

Streams the agent's response step-by-step with styled panels,
spinners, and colour. Persists each run as a timestamped trace.

Set PLAIN_OUTPUT=1 to disable rich formatting (used in tests).
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage

from research_agent.agent import get_agent

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUTS_DIR = _PROJECT_ROOT / "outputs"


def _is_plain() -> bool:
    """Check if we should use plain output (for testing/piping)."""
    return bool(os.environ.get("PLAIN_OUTPUT"))


def run_with_trace(question: str) -> None:
    """Stream the agent's response and log each step."""
    agent = get_agent()
    plain = _is_plain()

    lines: list[str] = [
        f"Question: {question}",
        f"Timestamp: {datetime.now().isoformat()}",
        "-" * 60,
    ]

    if not plain:
        from rich.console import Console
        from rich.markdown import Markdown
        from rich.panel import Panel
        from rich.spinner import Spinner
        from rich.live import Live

        console = Console()
        console.print()

        with Live(
            Panel(Spinner("dots", text="Thinking..."), border_style="cyan", title="🧠 Agent"),
            console=console, refresh_per_second=12, transient=True,
        ):
            chunks = list(agent.stream(
                {"messages": [{"role": "user", "content": question}]},
                stream_mode="values",
            ))

        for chunk in chunks:
            msg = chunk["messages"][-1]
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                names = [tc["name"] for tc in msg.tool_calls]
                console.print(Panel(f"[bold]Calling:[/bold] {', '.join(names)}", title="🔧 Tool", border_style="yellow", padding=(0, 1)))
                lines.append(f"🧠 Tool call: {names}")
            elif isinstance(msg, ToolMessage):
                preview = str(msg.content)[:300]
                console.print(Panel(preview, title="📥 Search Results", border_style="blue", padding=(0, 1)))
                lines.append(f"🔧 Tool result: {preview}")
            elif isinstance(msg, AIMessage) and msg.content:
                console.print()
                console.print(Panel(Markdown(msg.content), title="✅ Answer", border_style="green", padding=(1, 2)))
                lines.append(f"✅ Final answer:\n{msg.content}")
    else:
        # Plain text mode (for tests and piped output)
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values",
        ):
            msg = chunk["messages"][-1]
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                line = "Tool call: " + str([tc["name"] for tc in msg.tool_calls])
                print(line)
                lines.append(line)
            elif isinstance(msg, ToolMessage):
                line = "Tool result: " + str(msg.content)[:250]
                print(line)
                lines.append(line)
            elif isinstance(msg, AIMessage) and msg.content:
                line = "Final answer:\n" + msg.content
                print(line)
                lines.append(line)

    _save_trace(lines, plain)


def _save_trace(lines: list[str], plain: bool = False) -> None:
    """Persist trace lines to a timestamped file under outputs/."""
    try:
        _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = _OUTPUTS_DIR / f"trace_{timestamp}.txt"
        filepath.write_text("\n".join(lines), encoding="utf-8")
        if plain:
            print(f"Trace saved to {filepath}")
        else:
            from rich.console import Console
            Console().print(f"\n[dim]📁 Trace saved to {filepath}[/dim]")
    except OSError as exc:
        logger.debug("Could not save trace file: %s", exc)
