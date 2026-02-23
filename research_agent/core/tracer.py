"""
Execution tracer with real-time token streaming.

Streams the agent's response token-by-token. Tool calls and
results appear as panels; the final answer streams live.
Traces accumulate per session and save on CLI exit.

Set PLAIN_OUTPUT=1 to disable rich formatting (used in tests).
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from research_agent.agent import get_agent

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
            Console().print(f"[dim]📁 Session trace saved to {filepath}[/dim]")
    except OSError as exc:
        logger.debug("Could not save session trace: %s", exc)


def _run_rich(agent, question: str) -> None:
    """Rich mode: panels for tools, live token streaming for answers."""
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text

    console = Console()
    console.print()

    answer_buffer = ""
    streaming_answer = False

    try:
        for chunk, metadata in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="messages",
        ):
            # --- AI message chunks (thinking / answer tokens) ---
            if isinstance(chunk, AIMessageChunk):
                # Tool call chunk — show panel when the name arrives
                if chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            # If we were streaming an answer, close it
                            if streaming_answer:
                                console.print()
                                streaming_answer = False
                            console.print(
                                Panel(
                                    f"[bold]Searching:[/bold] {tc['name']}",
                                    title="🔧 Tool",
                                    border_style="yellow",
                                    padding=(0, 1),
                                )
                            )
                            _session_lines.append(f"🧠 Tool call: {tc['name']}")

                # Content token — stream it live
                elif chunk.content:
                    if not streaming_answer:
                        # Start the answer stream with a header
                        console.print()
                        console.print("[bold green]✅ Answer[/bold green]")
                        console.print("[green]─" * 50 + "[/green]")
                        streaming_answer = True
                    sys.stdout.write(chunk.content)
                    sys.stdout.flush()
                    answer_buffer += chunk.content

            # --- Tool result messages ---
            elif isinstance(chunk, ToolMessage):
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

        # Close the answer stream
        if streaming_answer:
            console.print()
            console.print("[green]─" * 50 + "[/green]")

        if answer_buffer:
            _session_lines.append(f"✅ Final answer:\n{answer_buffer}")

    except Exception as exc:
        error_msg = str(exc)
        if streaming_answer:
            console.print()
        if "503" in error_msg or "over capacity" in error_msg:
            console.print(
                Panel(
                    "[bold]The model is temporarily over capacity.[/bold]\n"
                    "Please wait a moment and try again.",
                    title="⚠️  Service Busy",
                    border_style="yellow",
                    padding=(0, 1),
                )
            )
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
            console.print(f"[bold red]❌ Error: {error_msg}[/bold red]")
        _session_lines.append(f"❌ Error: {error_msg}")


def _run_plain(agent, question: str) -> None:
    """Plain mode: simple print output for tests and piped environments."""
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
