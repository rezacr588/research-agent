#!/usr/bin/env python3
"""Entry point for the Research Agent CLI."""

from dotenv import load_dotenv
load_dotenv()

from research_agent.cli import main

if __name__ == "__main__":
    main()
