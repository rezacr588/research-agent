"""
Interactive CLI application.

Provides a REPL-style interface for asking research questions.
"""

import os
import sys

REQUIRED_KEYS = ("GROQ_API_KEY", "TAVILY_API_KEY")


def check_env() -> None:
    """Verify that all required environment variables are set."""
    missing = [key for key in REQUIRED_KEYS if not os.environ.get(key)]
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f'   export {var}="your_key_here"')
        sys.exit(1)


def print_banner() -> None:
    """Display the welcome banner."""
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║   🧠  Research Agent CLI                     ║")
    print("║   Model: Kimi K2 (via Groq)                  ║")
    print("║   Search: Tavily                              ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    print("  Type your research question and press Enter.")
    print("  Commands:  quit / exit / q  →  exit the agent")
    print("             clear            →  clear screen")
    print()


def main() -> None:
    """Run the interactive CLI loop."""
    check_env()
    print_banner()

    # Lazy import so env check runs first
    from research_agent.core import run_with_trace

    while True:
        try:
            question = input("🔍 Ask: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break

        if not question:
            continue
        if question.lower() in ("quit", "exit", "q"):
            print("👋 Goodbye!")
            break
        if question.lower() == "clear":
            os.system("clear" if os.name != "nt" else "cls")
            print_banner()
            continue

        print()
        try:
            run_with_trace(question)
        except Exception as e:
            print(f"❌ Error: {e}")
        print()
