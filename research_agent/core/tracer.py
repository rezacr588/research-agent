"""
Execution tracer with real-time token streaming.

Streams the agent's answer token-by-token with rich Markdown
rendering via Live display. Tool calls and results appear
as styled panels. Traces accumulate per session.

Set PLAIN_OUTPUT=1 to disable rich formatting (used in tests).
"""

import logging
import os
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from research_agent.agent import get_agent, reset_agent

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_OUTPUTS_DIR = _PROJECT_ROOT / "outputs"

_session_lines: list[str] = []


def _is_plain() -> bool:
    return bool(os.environ.get("PLAIN_OUTPUT"))


def run_with_trace(question: str) -> None:
    """Stream the agent's response in real-time."""
    agent = get_agent()
    plain = _is_plain()

    _session_lines.append(f"\n{'='*60}")
    _session_lines.append(f"Question: {question}")
    _session_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    _session_lines.append("-" * 60)

    if plain:
        _run_plain(agent, question)
    else:
        _run_rich(agent, question)


def save_session_trace() -> None:
    """Save the accumulated session trace to a file. Called on CLI exit."""
    if not _session_lines:
        return
    plain = _is_plain()
    try:
        _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = _OUTPUTS_DIR / f"session_{timestamp}.txt"
        filepath.write_text("\n".join(_session_lines), encoding="utf-8")
        if plain:
            print(f"Session trace saved to {filepath}")
        else:
            from rich.console import Console
            Console().print(f"[dim]📁 Trace saved to {filepath}[/dim]")
    except OSError as exc:
        logger.debug("Could not save session trace: %s", exc)


def clear_session() -> None:
    """Reset the session lines (for test isolation)."""
    _session_lines.clear()


def _run_rich(agent, question: str) -> None:
    """Rich mode: panels for tools, live-rendered Markdown for answers."""
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text
    from rich.theme import Theme

    theme = Theme({
        "tool": "bold yellow",
        "result": "bold blue",
        "answer": "bold green",
        "error": "bold red",
    })
    console = Console(theme=theme)
    console.print()

    answer_buffer = ""
    live_display: Live | None = None

    try:
        for chunk, metadata in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="messages",
        ):
            # --- AI message chunks ---
            if isinstance(chunk, AIMessageChunk):
                # Tool call
                if chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            if live_display:
                                live_display.stop()
                                live_display = None
                            console.print(
                                Panel(
                                    f"[bold]Searching:[/bold] {tc['name']}",
                                    title="🔧 Tool",
                                    border_style="yellow",
                                    padding=(0, 1),
                                )
                            )
                            _session_lines.append(f"🧠 Tool call: {tc['name']}")

                # Content token — stream as live-rendered Markdown
                elif chunk.content:
                    answer_buffer += chunk.content
                    # Wrap in try since partial Markdown can cause parse errors
                    try:
                        rendered = Panel(
                            Markdown(answer_buffer),
                            title="✅ Answer",
                            border_style="green",
                            padding=(1, 2),
                        )
                    except Exception:
                        # Fallback to plain text if Markdown parsing fails mid-stream
                        rendered = Panel(
                            Text(answer_buffer),
                            title="✅ Answer",
                            border_style="green",
                            padding=(1, 2),
                        )

                    if live_display is None:
                        console.print()
                        live_display = Live(
                            rendered,
                            console=console,
                            refresh_per_second=12,
                            vertical_overflow="visible",
                        )
                        live_display.start()
                    else:
                        live_display.update(rendered)

            # --- Tool result messages ---
            elif isinstance(chunk, ToolMessage):
                if live_display:
                    live_display.stop()
                    live_display = None
                preview = str(chunk.content)[:400]
                console.print(
                    Panel(
                        preview,
                        title="📥 Search Results",
                        border_style="blue",
                        padding=(0, 1),
                    )
                )
                _session_lines.append(f"🔧 Tool result: {preview}")

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted.[/yellow]")
        _session_lines.append("⚠️  Interrupted by user.")
    except Exception as exc:
        error_msg = str(exc)
        if "503" in error_msg or "over capacity" in error_msg:
            console.print(
                Panel(
                    "[bold]Model is temporarily over capacity.[/bold]\n"
                    "Retrying with fallback model...",
                    title="⚠️  Service Busy",
                    border_style="yellow",
                    padding=(0, 1),
                )
            )
            # Force agent re-creation so fallback kicks in next question
            reset_agent()
        elif "429" in error_msg or "rate" in error_msg.lower():
            console.print(
                Panel(
                    "[bold]Rate limit reached.[/bold]\n"
                    "Please wait a few seconds and try again.",
                    title="⚠️  Rate Limited",
                    border_style="yellow",
                    padding=(0, 1),
                )
            )
        else:
            console.print(f"[error]❌ Error: {error_msg}[/error]")
        _session_lines.append(f"❌ Error: {error_msg}")
    finally:
        # Always clean up the Live display to prevent terminal corruption
        if live_display:
            try:
                live_display.stop()
            except Exception:
                pass

    if answer_buffer:
        _session_lines.append(f"✅ Final answer:\n{answer_buffer}")


def _run_plain(agent, question: str) -> None:
    """Plain mode: simple print output for tests."""
    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values",
        ):
            msg = chunk["messages"][-1]

            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                if msg.content:
                    line = "Thinking: " + msg.content
                    print(line)
                    _session_lines.append(line)
                line = "Tool call: " + str([tc["name"] for tc in msg.tool_calls])
                print(line)
                _session_lines.append(line)
            elif isinstance(msg, ToolMessage):
                line = "Tool result: " + str(msg.content)[:250]
                print(line)
                _session_lines.append(line)
            elif isinstance(msg, AIMessage) and msg.content:
                line = "Final answer:\n" + msg.content
                print(line)
                _session_lines.append(line)
    except Exception as exc:
        print(f"Error: {exc}")
        _session_lines.append(f"Error: {exc}")
