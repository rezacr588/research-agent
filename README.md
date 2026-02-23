# 🧠 Research Agent Demo

This is a demonstration of a LangGraph-based ReAct agent capable of performing autonomous web research using the Tavily Search API and responding with structured factual claims. 

This agent connects to the **Groq API** but configures the language model to use the **Moonshot Kimi K2** (`moonshotai/kimi-k2-instruct`) identity.

## Prerequisites

Ensure you have the following environment variables configured:
*   `GROQ_API_KEY`: Required by `llm` to use the Groq hosted models.
*   `TAVILY_API_KEY`: Required by the `web_search` tool to fetch web results.

### Setup (Virtual Environment)
It's recommended to run this inside a Python virtual environment to prevent package collision with your system:

```bash
# 1. Create a virtual environment
python -m venv venv

# 2. Activate it (On macOS / Linux)
source venv/bin/activate
# Or on Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

## Running the Agent

Set your API keys, then launch the interactive CLI:

```bash
export GROQ_API_KEY="your_groq_api_key_here"
export TAVILY_API_KEY="your_tavily_api_key_here"

python main.py
```

This opens an interactive prompt where you can type research questions one after another. The agent will search the web, reason about the results, and give you a structured answer. Every run is traced and saved to `outputs/`.

**CLI commands:**
| Command | Action |
|---------|--------|
| `quit` / `exit` / `q` | Exit the agent |
| `clear` | Clear the screen |
| `Ctrl+C` | Exit gracefully |

## How it Works / Code Architecture

The codebase is split into modular components that form a complete LangGraph evaluation loop:

*   **`agent.py`**: This is the core brain of the application. It initializes the LLM connection via `langchain_groq.ChatGroq`. It then uses LangGraph's `create_react_agent` to bind a custom `SystemMessage` prompt and the web search tools to the model. The ReAct (Reason+Act) architecture allows the AI to form a plan, take action, observe results, and answer.
*   **`search.py`**: Defines the `@tool` `web_search`. This function acts as the interface to the outside world. It uses the `TavilyClient` to execute a search query, parse the top 6 responses, and return the titles, URLs, and text snippets to the LLM so it can read them.
*   **`trace.py`**: A debugging and execution utility. It takes the agent and streams its execution chunk-by-chunk using `agent.stream()`. Instead of hiding the intermediary processes, `run_with_trace` intercepts `AIMessage` and `ToolMessage` events to print precisely what tool the AI decided to call, what data it got back, and its final derived answer.
*   **`main.py`**: The main entrypoint. It performs simple environment validation to ensure keys are populated before cleanly invoking the trace.
*   **`test_agent.py`**: An end-to-end (E2E) testing suite that guarantees the logic functions without relying on external APIs. It uses Python's `unittest.mock.patch` to intercept requests to Tavily and return a controlled, dummy payload. This ensures the prompt structure and code syntax haven't broken.

## E2E Testing

You can run the mock E2E tests using Python's standard `unittest`:

```bash
python -m unittest test_agent.py
```
