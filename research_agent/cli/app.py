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
    """Display the welcome banner."""
    banner = (
        "[bold cyan]🧠 Research Agent[/bold cyan]\n"
        "[dim]Model: Kimi K2 (via Groq)  •  Search: Tavily[/dim]\n\n"
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

    cmd = "cls" if os.name == "nt" else "clear"
    subprocess.call([cmd], shell=False)  # noqa: S603


def main() -> None:
    """Run the interactive CLI loop."""
    _check_env()
    _print_banner()

    # Lazy import so env check runs first
    from research_agent.core import run_with_trace

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
