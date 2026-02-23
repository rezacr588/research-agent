"""
End-to-end tests for the research agent.

Mocks the Tavily search API so tests run without network
access or API keys.
"""

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Ensure env vars are set before importing agent modules
os.environ.setdefault("TAVILY_API_KEY", "dummy_tavily_key")
os.environ.setdefault("GROQ_API_KEY", "dummy_groq_key")

from research_agent.core import run_with_trace  # noqa: E402


MOCK_SEARCH_RESULTS = {
    "results": [
        {
            "title": "2024 Super Bowl Highlights",
            "url": "https://dummy-sports-news.com/superbowl-2024",
            "content": (
                "The Kansas City Chiefs claimed victory in the 2024 "
                "Super Bowl (Super Bowl LVIII), defeating the "
                "San Francisco 49ers 25-22 in overtime."
            ),
        }
    ]
}


class TestResearchAgent(unittest.TestCase):
    """Verify the full agent loop: question → tool call → answer."""

    @patch("research_agent.tools.search._get_tavily_client")
    def test_agent_e2e_flow(self, mock_get_client: MagicMock) -> None:
        """Agent should call web_search and return a structured answer."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = MOCK_SEARCH_RESULTS

        question = "Who won the 2024 Super Bowl?"
        print(f"\n--- E2E test: '{question}' ---")

        # Capture stdout
        captured = io.StringIO()
        saved = sys.stdout
        sys.stdout = captured

        try:
            run_with_trace(question)
        finally:
            sys.stdout = saved

        output = captured.getvalue()
        print(output)

        # Verify key agent behaviours
        self.assertIn("web_search", output)
        self.assertIn("Final answer", output)
        self.assertIn("Kansas City Chiefs", output)

        # Verify tool was actually invoked
        mock_client.search.assert_called_once()


if __name__ == "__main__":
    unittest.main()
