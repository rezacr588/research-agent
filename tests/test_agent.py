"""
End-to-end tests for the research agent.

These tests verify the FULL agent loop: question → tool call → answer.
They mock the Tavily API so they run WITHOUT network access or API keys.

Key testing techniques used:
  1. @patch — replaces the real Tavily client with a mock
  2. PLAIN_OUTPUT=1 — disables Rich formatting for plain text assertions
  3. io.StringIO — captures stdout so we can assert on the output

What we test:
  - Happy path: agent searches, receives results, returns structured answer
  - Empty results: agent handles zero results without crashing
  - Malformed data: missing keys don't cause KeyError
  - API failure: ConnectionError returns error JSON, agent still responds
"""

import io
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# ─── Test Environment Setup ─────────────────────────────────────
# Set dummy API keys BEFORE importing agent modules.
# The modules check for these keys at import time, so they must exist.
# Using setdefault() means real keys (if present) won't be overwritten.
os.environ.setdefault("TAVILY_API_KEY", "dummy_tavily_key")
os.environ.setdefault("GROQ_API_KEY", "dummy_groq_key")

# PLAIN_OUTPUT=1 tells the tracer to use print() instead of Rich.
# This lets us capture output with io.StringIO and run assertions.
os.environ["PLAIN_OUTPUT"] = "1"

from research_agent.core import run_with_trace  # noqa: E402
from research_agent.tools import reset_client  # noqa: E402

# ─── Mock Data ───────────────────────────────────────────────────
# This simulates what Tavily's API would return for a real search.
# The structure matches Tavily's actual response format.
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
        """
        Reset the cached Tavily client before each test.

        Without this, mocks from one test could leak into the next,
        causing false positives or mysterious failures.
        """
        reset_client()

    # ── Test 1: Happy Path ───────────────────────────────────────
    @patch("research_agent.tools.search._get_tavily_client")
    def test_agent_e2e_flow(self, mock_get_client: MagicMock) -> None:
        """
        Agent should call web_search and return a structured answer.

        This is the "golden path" test — everything works as expected.
        We verify that:
          - The agent called web_search (appears in output)
          - The agent produced a final answer
          - The answer contains data from the mock search results
          - The search was actually called once
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = MOCK_SEARCH_RESULTS

        output = self._run_and_capture("Who won the 2024 Super Bowl?")

        self.assertIn("web_search", output)
        self.assertIn("Final answer", output)
        self.assertIn("Kansas City Chiefs", output)
        mock_client.search.assert_called_once()

    # ── Test 2: Empty Results ────────────────────────────────────
    @patch("research_agent.tools.search._get_tavily_client")
    def test_empty_search_results(self, mock_get_client: MagicMock) -> None:
        """
        Agent should not crash when search returns no results.

        Real-world scenario: the query is too niche or the API
        returns nothing. The agent should still produce an answer
        (even if it says "I couldn't find anything").
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = {"results": []}  # Empty!

        output = self._run_and_capture("What happened at the 2099 Olympics?")

        self.assertIn("Final answer", output)

    # ── Test 3: Malformed Data ───────────────────────────────────
    @patch("research_agent.tools.search._get_tavily_client")
    def test_malformed_search_results(self, mock_get_client: MagicMock) -> None:
        """
        Agent should handle results with missing keys gracefully.

        This tests our defensive .get() calls in search.py.
        The first result is missing "title" and "content" — our code
        should use defaults ("Untitled", "") without crashing.
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.return_value = {
            "results": [
                {"url": "https://example.com"},  # Missing title and content!
                {"title": "Good Result", "url": "https://good.com", "content": "Valid data"},
            ]
        }

        output = self._run_and_capture("What is the capital of France?")

        self.assertIn("Final answer", output)

    # ── Test 4: API Failure ──────────────────────────────────────
    @patch("research_agent.tools.search._get_tavily_client")
    def test_search_api_failure(self, mock_get_client: MagicMock) -> None:
        """
        Agent should handle Tavily API errors without crashing.

        When the search tool catches an exception, it returns
        {"error": "Search failed: ..."} as JSON. The agent sees this
        and should still produce a response (explaining it couldn't search).
        """
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.search.side_effect = ConnectionError("API timeout")

        output = self._run_and_capture("Who is the president of the US?")

        self.assertIn("Final answer", output)

    # ── Helper ───────────────────────────────────────────────────
    def _run_and_capture(self, question: str) -> str:
        """
        Helper: run the agent and return captured stdout.

        We redirect sys.stdout to an io.StringIO buffer,
        run the agent, then restore stdout and return the captured text.
        This lets us assert on what the agent printed.
        """
        print(f"\n--- Test: '{question}' ---")
        captured = io.StringIO()
        saved = sys.stdout
        sys.stdout = captured
        try:
            run_with_trace(question)
        finally:
            sys.stdout = saved  # Always restore stdout!
        output = captured.getvalue()
        print(output)  # Print to real stdout for visibility
        return output


if __name__ == "__main__":
    unittest.main()
