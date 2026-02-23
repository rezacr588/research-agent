"""Allow running as `python -m research_agent`."""

from dotenv import load_dotenv
load_dotenv()

from research_agent.cli import main

main()
