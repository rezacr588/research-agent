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
os.environ["PLAIN_OUTPUT"] = "1"  # Use plain text output in tests

from research_agent.core import run_with_trace  # noqa: E402
from research_agent.tools import reset_client  # noqa: E402


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

    def setUp(self) -> None:
        """Reset the cached Tavily client before each test."""
        reset_client()

    @patch("research_agent.tools.search._get_tavily_client")
    def test_agent_e2e_flow(self, mock_get_client: MagicMock) -> None:
        """Agent should call web_search and return a structured answer."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = MOCK_SEARCH_RESULTS

        output = self._run_and_capture("Who won the 2024 Super Bowl?")

        self.assertIn("web_search", output)
        self.assertIn("Final answer", output)
        self.assertIn("Kansas City Chiefs", output)
        mock_client.search.assert_called_once()

    @patch("research_agent.tools.search._get_tavily_client")
    def test_empty_search_results(self, mock_get_client: MagicMock) -> None:
        """Agent should not crash when search returns no results."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = {"results": []}

        output = self._run_and_capture("What happened at the 2099 Olympics?")

        # Agent should produce output without crashing
        self.assertIn("Final answer", output)

    @patch("research_agent.tools.search._get_tavily_client")
    def test_malformed_search_results(self, mock_get_client: MagicMock) -> None:
        """Agent should handle results with missing keys via defensive .get()."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {"url": "https://example.com"},  # missing title and content
                {"title": "Good Result", "url": "https://good.com", "content": "Valid data"},
            ]
        }

        output = self._run_and_capture("What is the capital of France?")

        # Should not crash even with partial data
        self.assertIn("Final answer", output)

    @patch("research_agent.tools.search._get_tavily_client")
    def test_search_api_failure(self, mock_get_client: MagicMock) -> None:
        """Agent should handle Tavily API errors without crashing."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.side_effect = ConnectionError("API timeout")

        output = self._run_and_capture("Who is the president of the US?")

        # The tool returns an error JSON, agent should still respond
        self.assertIn("Final answer", output)

    def _run_and_capture(self, question: str) -> str:
        """Helper: run the agent and return captured stdout."""
        print(f"\n--- Test: '{question}' ---")
        captured = io.StringIO()
        saved = sys.stdout
        sys.stdout = captured
        try:
            run_with_trace(question)
        finally:
            sys.stdout = saved
        output = captured.getvalue()
        print(output)
        return output


if __name__ == "__main__":
    unittest.main()
