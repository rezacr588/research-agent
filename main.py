#!/usr/bin/env python3
"""
Entry point for the Research Agent CLI.

This is the first file that runs when you execute `python main.py`.
Its only job is to:
  1. Load environment variables from a .env file (API keys)
  2. Hand off control to the CLI module

Why load .env here?
  - We use `python-dotenv` to read GROQ_API_KEY and TAVILY_API_KEY
    from a `.env` file in the project root.
  - load_dotenv() MUST run before any module tries to read os.environ,
    which is why it's at the very top, before importing the CLI.
"""

from dotenv import load_dotenv

# Load API keys from .env file into os.environ
# This must happen BEFORE any other imports that read env vars
load_dotenv()

# Now it's safe to import the CLI — it will check for the keys
from research_agent.cli import main

if __name__ == "__main__":
    # Standard Python idiom: only runs when executed directly,
    # not when imported as a module
    main()
