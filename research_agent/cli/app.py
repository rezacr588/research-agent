"""
Interactive CLI application.

Provides a polished REPL-style interface for asking research
questions, inspired by modern CLI agents.
"""

import subprocess
import sys

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.theme import Theme

_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

console = Console(theme=_theme)

REQUIRED_KEYS = ("GROQ_API_KEY", "TAVILY_API_KEY")


def _check_env() -> None:
    """Verify that all required environment variables are set."""
    import os

    missing = [key for key in REQUIRED_KEYS if not os.environ.get(key)]
    if missing:
        console.print("\n[error]❌ Missing environment variables:[/error]")
        for var in missing:
            console.print(f'   [dim]export {var}="your_key_here"[/dim]')
        console.print()
        sys.exit(1)


def _print_banner() -> None:
    """Display the welcome banner with the active model name."""
    # Try to get the actual model name; fall back to generic if not ready
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
    """Clear the terminal screen safely."""
    import os

    try:
        cmd = "cls" if os.name == "nt" else "clear"
        subprocess.call([cmd], shell=False)  # noqa: S603
    except FileNotFoundError:
        # clear/cls not available (e.g., Docker)
        console.print("\n" * 50)


def main() -> None:
    """Run the interactive CLI loop."""
    _check_env()

    # Lazy import so env check runs first
    from research_agent.core import run_with_trace, save_session_trace

    # Trigger agent init (with model probe) before showing the banner
    try:
        from research_agent.agent import get_agent
        get_agent()
    except RuntimeError as e:
        console.print(f"[error]❌ {e}[/error]")
        sys.exit(1)

    _print_banner()

    while True:
        try:
            question = Prompt.ask("[bold cyan]>[/bold cyan]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]👋 Goodbye![/dim]")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            console.print("[dim]👋 Goodbye![/dim]")
            break
        if question.lower() == "clear":
            _clear_screen()
            _print_banner()
            continue

        try:
            run_with_trace(question)
        except (ValueError, RuntimeError, ConnectionError) as e:
            console.print(f"[error]❌ {e}[/error]")
        except KeyboardInterrupt:
            console.print("\n[warning]⚠️  Interrupted. Type 'quit' to exit.[/warning]")
        console.print()

    # Save entire session trace on exit
    save_session_trace()
