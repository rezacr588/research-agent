"""
Interactive CLI application.

This module provides the user-facing REPL (Read-Eval-Print Loop):
  1. Checks that required API keys are set
  2. Initializes the agent (triggers model probe + fallback)
  3. Shows a welcome banner
  4. Enters an infinite loop: read question → run agent → display answer
  5. On exit, saves the session trace to disk

The CLI uses Rich for a polished terminal experience:
  - Styled prompt with colors
  - Panels for the banner and errors
  - Graceful handling of Ctrl+C
"""

import subprocess
import sys

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

# Custom theme for consistent color coding throughout the app
_theme = Theme({
    "info": "cyan",           # Informational messages
    "warning": "yellow",      # Warnings (rate limits, interruptions)
    "error": "bold red",      # Errors (missing keys, crashes)
    "success": "bold green",  # Success messages
})

console = Console(theme=_theme)

# Both API keys are REQUIRED — the app won't start without them
REQUIRED_KEYS = ("GROQ_API_KEY", "TAVILY_API_KEY")


def _check_env() -> None:
    """
    Verify that all required environment variables are set.

    Called BEFORE the agent is created. If any keys are missing,
    we print helpful instructions and exit immediately.
    This prevents confusing errors later in the pipeline.
    """
    import os

    missing = [key for key in REQUIRED_KEYS if not os.environ.get(key)]
    if missing:
        console.print("\n[error]❌ Missing environment variables:[/error]")
        for var in missing:
            console.print(f'   [dim]export {var}="your_key_here"[/dim]')
        console.print()
        sys.exit(1)


def _print_banner() -> None:
    """
    Display the welcome banner with the active model name.

    The banner shows:
      - App name and branding
      - Which LLM model is active (e.g., "kimi-k2-instruct")
      - Available commands (quit, clear)

    If the model hasn't been initialized yet, shows "initializing..."
    """
    try:
        from research_agent.agent import get_active_model
        model = get_active_model() or "initializing..."
    except Exception:
        model = "initializing..."

    banner = (
        "[bold cyan]🧠 Research Agent[/bold cyan]\n"
        f"[dim]Model: {model}  •  Search: Tavily[/dim]\n\n"
        "Ask any research question. I'll search the web and\n"
        "give you a structured answer with sources.\n\n"
        "[dim]Commands: quit · clear[/dim]"
    )
    console.print()
    console.print(Panel(banner, border_style="cyan", padding=(1, 3)))
    console.print()


def _clear_screen() -> None:
    """
    Clear the terminal screen safely.

    Uses the system's `clear` command (or `cls` on Windows).
    Falls back to printing 50 blank lines if the command isn't available
    (e.g., inside a Docker container with minimal shell).
    """
    import os

    try:
        cmd = "cls" if os.name == "nt" else "clear"
        subprocess.call([cmd], shell=False)
    except FileNotFoundError:
        # clear/cls not available — just print blank lines
        console.print("\n" * 50)


# ═══════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT — The REPL loop
# ═══════════════════════════════════════════════════════════════════

def main() -> None:
    """
    Run the interactive CLI loop.

    Flow:
      1. Check environment variables (exit if missing)
      2. Initialize the agent (lazy — probes models, sets up fallback)
      3. Show the welcome banner (now with correct model name)
      4. Enter the REPL loop:
         - Read user input
         - Handle commands (quit, clear)
         - Run the agent for questions
         - Handle errors gracefully
      5. On exit, save the full session trace to outputs/
    """
    # Step 1: Verify API keys are set
    _check_env()

    # Step 2: Lazy import so env check runs first
    # If we imported at the top, the modules might try to read env vars
    # before load_dotenv() ran in main.py
    from research_agent.core import run_with_trace, save_session_trace

    # Step 3: Trigger agent initialization (model probe + possible fallback)
    # We do this BEFORE showing the banner so the banner can display
    # the correct model name
    try:
        from research_agent.agent import get_agent
        get_agent()  # This probes the model and caches the agent
    except RuntimeError as e:
        console.print(f"[error]❌ {e}[/error]")
        sys.exit(1)

    # Step 4: Show the welcome banner (model name is now available)
    _print_banner()

    # Step 5: The REPL (Read-Eval-Print Loop)
    while True:
        try:
            # Show a styled "> " prompt and read user input
            question = Prompt.ask("[bold cyan]>[/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            # Ctrl+C or Ctrl+D → exit gracefully
            console.print("\n[dim]👋 Goodbye![/dim]")
            break

        # Skip empty input (user just pressed Enter)
        if not question:
            continue

        # Handle exit commands
        if question.lower() in ("quit", "exit", "q"):
            console.print("[dim]👋 Goodbye![/dim]")
            break

        # Handle clear screen command
        if question.lower() == "clear":
            _clear_screen()
            _print_banner()  # Re-show banner after clearing
            continue

        # Run the agent for this question
        try:
            run_with_trace(question)  # This streams the answer in real-time
        except (ValueError, RuntimeError, ConnectionError) as e:
            console.print(f"[error]❌ {e}[/error]")
        except KeyboardInterrupt:
            # Ctrl+C during a question → don't exit, just cancel this question
            console.print("\n[warning]⚠️  Interrupted. Type 'quit' to exit.[/warning]")

        console.print()  # Blank line between questions

    # Step 6: Save the entire session trace on exit
    save_session_trace()
