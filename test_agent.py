import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import io

# Set a dummy TAVILY_API_KEY so initialization doesn't fail
os.environ["TAVILY_API_KEY"] = "dummy_tavily_key"

from trace import run_with_trace
from agent import agent
import search


class TestResearchAgent(unittest.TestCase):
    @patch("search._get_tavily_client")
    def test_agent_e2e_flow(self, mock_get_client):
        """Full E2E test: agent receives a question, calls web_search, returns structured answer."""
        # Setup mock TavilyClient
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Provide dummy search results
        mock_client.search.return_value = {
            "results": [
                {
                    "title": "2024 Super Bowl Highlights",
                    "url": "https://dummy-sports-news.com/superbowl-2024",
                    "content": "The Kansas City Chiefs claimed victory in the 2024 Super Bowl (Super Bowl LVIII), defeating the San Francisco 49ers 25-22 in overtime."
                }
            ]
        }

        question = "Who won the 2024 Super Bowl?"
        print(f"\n--- Running Agent for question: '{question}' ---")

        # Redirect stdout to capture print statements
        captured_output = io.StringIO()
        saved_stdout = sys.stdout
        sys.stdout = captured_output

        try:
            run_with_trace(question)
        finally:
            sys.stdout = saved_stdout

        output = captured_output.getvalue()
        print(output)

        # Assertions — check key behaviors, not exact formatting
        self.assertIn("web_search", output)
        self.assertIn("Final answer", output)
        self.assertIn("Kansas City Chiefs", output)

        # Ensure the web_search tool was actually called
        mock_client.search.assert_called_once()


if __name__ == "__main__":
    unittest.main()
