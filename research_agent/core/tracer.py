"""
Execution tracer with real-time token streaming.

This is the ENGINE of the application. When a user asks a question,
this module:
  1. Sends the question to the agent
  2. Streams the response in real-time (token by token)
  3. Displays tool calls and results as styled panels
  4. Logs everything to a trace file for auditing

Two display modes:
  - Rich mode (default): Beautiful panels, spinners, live Markdown
  - Plain mode (PLAIN_OUTPUT=1): Simple print() for tests

Why stream token by token?
  Instead of waiting for the full response (could be 10+ seconds),
  we show each token as it arrives — like ChatGPT does.
  This uses Rich's `Live` display for real-time Markdown rendering.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

# LangChain message types — we check these to know what kind of
# chunk we received (AI thinking, tool call, or tool result)
from langchain_core.messages import AIMessage, AIMessageChunk, ToolMessage

from research_agent.agent import get_agent, reset_agent

logger = logging.getLogger(__name__)

# ─── File Paths ──────────────────────────────────────────────────
# Calculate the project root so we can find the outputs/ directory
# regardless of where the script is run from
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # core/ → research_agent/ → project root
_OUTPUTS_DIR = _PROJECT_ROOT / "outputs"

# ─── Session Trace ───────────────────────────────────────────────
# Accumulates log lines throughout the entire CLI session.
# We save them all at once when the user exits (see save_session_trace).
_session_lines: list[str] = []


def _is_plain() -> bool:
    """Check if we should use plain text output (for tests)."""
    return bool(os.environ.get("PLAIN_OUTPUT"))


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

def run_with_trace(question: str) -> None:
    """
    Stream the agent's response in real-time.

    This is the main function called by the CLI for every question.
    It:
      1. Gets the agent (cached after first call)
      2. Adds a header to the session trace
      3. Routes to either Rich or Plain display mode
    """
    agent = get_agent()
    plain = _is_plain()

    # Add a trace header for this question
    _session_lines.append(f"\n{'='*60}")
    _session_lines.append(f"Question: {question}")
    _session_lines.append(f"Timestamp: {datetime.now().isoformat()}")
    _session_lines.append("-" * 60)

    # Choose display mode based on PLAIN_OUTPUT env var
    if plain:
        _run_plain(agent, question)
    else:
        _run_rich(agent, question)


def save_session_trace() -> None:
    """
    Save the accumulated session trace to a file.

    Called once when the CLI exits (not after every question).
    This creates a file like: outputs/session_20260224_163000_123456.txt
    containing all questions, tool calls, and answers from the session.

    Why save traces?
      - Debugging: see exactly what the agent searched and received
      - Auditing: verify the agent cited real sources
      - Learning: understand the agent's reasoning process
    """
    if not _session_lines:
        return  # Nothing to save

    plain = _is_plain()
    try:
        _OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = _OUTPUTS_DIR / f"session_{timestamp}.txt"
        filepath.write_text("\n".join(_session_lines), encoding="utf-8")

        # Notify the user that the trace was saved
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


# ═══════════════════════════════════════════════════════════════════
# RICH MODE — Beautiful terminal output with panels and streaming
# ═══════════════════════════════════════════════════════════════════

def _run_rich(agent, question: str) -> None:
    """
    Rich mode: panels for tools, live-rendered Markdown for answers.

    How streaming works:
      - We use `agent.stream()` with `stream_mode="messages"` to get
        individual message chunks as they arrive
      - Each chunk can be:
        a) AIMessageChunk with tool_call_chunks → agent is calling a tool
        b) AIMessageChunk with content → agent is writing its answer
        c) ToolMessage → search results came back

      - For answer tokens, we accumulate them in `answer_buffer` and
        re-render the entire buffer as Markdown on each token.
        Rich's `Live` display handles redrawing without flickering.
    """
    from rich.console import Console
    from rich.live import Live
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.text import Text
    from rich.theme import Theme

    # Custom theme for consistent styling across panels
    theme = Theme({
        "tool": "bold yellow",     # Tool call panels
        "result": "bold blue",     # Search result panels
        "answer": "bold green",    # Answer panel
        "error": "bold red",       # Error messages
    })
    console = Console(theme=theme)
    console.print()  # Blank line for spacing

    # answer_buffer accumulates the answer token by token
    # live_display is the Rich Live context for real-time rendering
    answer_buffer = ""
    live_display: Live | None = None

    try:
        # ── Stream chunks from the agent ──
        # Each iteration gives us one chunk (a token, tool call, or tool result)
        for chunk, metadata in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="messages",
        ):
            # ── Case 1: AI is making a tool call ──
            if isinstance(chunk, AIMessageChunk):
                if chunk.tool_call_chunks:
                    for tc in chunk.tool_call_chunks:
                        if tc.get("name"):
                            # Stop any active answer display before showing tool panel
                            if live_display:
                                live_display.stop()
                                live_display = None

                            # Show a yellow panel: "🔧 Tool: Searching: web_search"
                            console.print(
                                Panel(
                                    f"[bold]Searching:[/bold] {tc['name']}",
                                    title="🔧 Tool",
                                    border_style="yellow",
                                    padding=(0, 1),
                                )
                            )
                            _session_lines.append(f"🧠 Tool call: {tc['name']}")

                # ── Case 2: AI is streaming answer tokens ──
                elif chunk.content:
                    # Add this token to the growing answer
                    answer_buffer += chunk.content

                    # Try to render the buffer as Markdown
                    # (might fail mid-stream if Markdown is incomplete)
                    try:
                        rendered = Panel(
                            Markdown(answer_buffer),
                            title="✅ Answer",
                            border_style="green",
                            padding=(1, 2),
                        )
                    except Exception:
                        # Fallback: render as plain text if Markdown parsing fails
                        rendered = Panel(
                            Text(answer_buffer),
                            title="✅ Answer",
                            border_style="green",
                            padding=(1, 2),
                        )

                    # Start or update the Live display
                    if live_display is None:
                        console.print()
                        # Live display redraws in place without scrolling
                        live_display = Live(
                            rendered,
                            console=console,
                            refresh_per_second=12,           # Smooth updates
                            vertical_overflow="visible",     # Don't clip long answers
                        )
                        live_display.start()
                    else:
                        # Update the existing display with the new content
                        live_display.update(rendered)

            # ── Case 3: Search results came back ──
            elif isinstance(chunk, ToolMessage):
                # Stop answer display if active
                if live_display:
                    live_display.stop()
                    live_display = None

                # Show a blue panel with a preview of the search results
                preview = str(chunk.content)[:400]  # Truncate for readability
                console.print(
                    Panel(
                        preview,
                        title="📥 Search Results",
                        border_style="blue",
                        padding=(0, 1),
                    )
                )
                _session_lines.append(f"🔧 Tool result: {preview}")

    # ── Error Handling ──
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Interrupted.[/yellow]")
        _session_lines.append("⚠️  Interrupted by user.")

    except Exception as exc:
        error_msg = str(exc)

        # 503 = model overloaded → reset agent to try fallback next time
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
            reset_agent()  # Force agent re-creation with fallback model

        # 429 = rate limited → tell user to wait
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
        # ALWAYS clean up the Live display to prevent terminal corruption
        # If we don't stop it, the terminal can get into a broken state
        if live_display:
            try:
                live_display.stop()
            except Exception:
                pass

    # Save the final answer to the session trace
    if answer_buffer:
        _session_lines.append(f"✅ Final answer:\n{answer_buffer}")


# ═══════════════════════════════════════════════════════════════════
# PLAIN MODE — Simple output for tests
# ═══════════════════════════════════════════════════════════════════

def _run_plain(agent, question: str) -> None:
    """
    Plain mode: simple print output for tests.

    Uses stream_mode="values" (full messages) instead of "messages"
    (individual chunks) because we don't need token-level streaming
    in tests — we just need to verify the output content.
    """
    try:
        for chunk in agent.stream(
            {"messages": [{"role": "user", "content": question}]},
            stream_mode="values",  # Returns full messages, not individual tokens
        ):
            msg = chunk["messages"][-1]  # Get the latest message

            # AI message with tool calls → agent decided to use a tool
            if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
                if msg.content:
                    line = "Thinking: " + msg.content
                    print(line)
                    _session_lines.append(line)
                line = "Tool call: " + str([tc["name"] for tc in msg.tool_calls])
                print(line)
                _session_lines.append(line)

            # Tool message → search results came back
            elif isinstance(msg, ToolMessage):
                line = "Tool result: " + str(msg.content)[:250]
                print(line)
                _session_lines.append(line)

            # AI message with content (no tool calls) → final answer
            elif isinstance(msg, AIMessage) and msg.content:
                line = "Final answer:\n" + msg.content
                print(line)
                _session_lines.append(line)

    except Exception as exc:
        print(f"Error: {exc}")
        _session_lines.append(f"Error: {exc}")
