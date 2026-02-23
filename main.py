#!/usr/bin/env python3
"""
🧠 Research Agent CLI
An interactive command-line research assistant powered by
Moonshot Kimi K2 (via Groq) + Tavily Web Search + LangGraph.
"""

import os
import sys

def check_env():
    """Check that required environment variables are set."""
    missing = []
    if not os.environ.get("GROQ_API_KEY"):
        missing.append("GROQ_API_KEY")
    if not os.environ.get("TAVILY_API_KEY"):
        missing.append("TAVILY_API_KEY")
    if missing:
        print("❌ Missing environment variables:")
        for var in missing:
            print(f"   export {var}=\"your_key_here\"")
        sys.exit(1)

def print_banner():
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

def main():
    check_env()
    print_banner()

    # Import after env check so missing keys don't crash on import
    from trace import run_with_trace

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

if __name__ == "__main__":
    main()
