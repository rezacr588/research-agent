# 🧠 Research Agent CLI

A polished, interactive command-line research assistant powered by **Kimi K2** (via Groq) + **Tavily** web search + **LangGraph**.

Ask any research question and get a structured answer with TL;DR, key points, and sources — all displayed with rich, styled terminal output.

## Features

- 🔍 **Web-grounded answers** — every factual claim is backed by a live Tavily search
- 🧠 **ReAct agent loop** — the LLM reasons, decides to search, reads results, then answers
- ✨ **Rich terminal UI** — spinners while thinking, coloured panels for tool calls, search results, and answers rendered as Markdown
- 📁 **Automatic trace logging** — every run is saved to `outputs/` with full tool call history
- 🧪 **Robust test suite** — 4 E2E tests covering happy path, empty results, malformed data, and API failures

## Prerequisites

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | LLM inference via Groq |
| `TAVILY_API_KEY` | Web search via Tavily |

### Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
export GROQ_API_KEY="..."
export TAVILY_API_KEY="..."

python main.py
# or
python -m research_agent
```

The CLI displays a styled prompt where you can ask research questions interactively:

```
╭──────────────────────────────────────────╮
│  🧠 Research Agent                       │
│  Model: Kimi K2 (via Groq)  •  Search:  │
│  Tavily                                  │
│                                          │
│  Ask any research question. I'll search  │
│  the web and give you a structured       │
│  answer with sources.                    │
│                                          │
│  Commands: quit · clear                  │
╰──────────────────────────────────────────╯

> What are the latest AI breakthroughs?

╭─── 🔧 Tool ───╮        ← tool call (yellow)
│ Calling: web_search │
╰────────────────╯

╭─── 📥 Search Results ───╮  ← raw results (blue)
│ [{"title": "...", ...}]  │
╰──────────────────────────╯

╭──── ✅ Answer ────╮     ← final answer (green, Markdown)
│  TL;DR             │
│  • ...              │
│  Key points         │
│  • ...              │
│  Sources            │
│  • https://...      │
╰────────────────────╯
```

| Command | Action |
|---|---|
| `quit` / `exit` / `q` | Exit |
| `clear` | Clear screen |
| `Ctrl+C` | Exit gracefully |

## Project Structure

```
research-agent/
├── main.py                          # Entry point
├── requirements.txt
├── research_agent/
│   ├── __init__.py
│   ├── __main__.py                  # python -m research_agent
│   ├── agent.py                     # Lazy LLM factory + ReAct agent
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py                # Tavily tool (cached client, error handling)
│   ├── core/
│   │   ├── __init__.py
│   │   └── tracer.py                # Rich tracer (spinners, panels, file logging)
│   └── cli/
│       ├── __init__.py
│       └── app.py                   # Interactive REPL with rich prompt
└── tests/
    ├── __init__.py
    └── test_agent.py                # 4 E2E tests (mocked APIs)
```

### Architecture

| Layer | Responsibility | Key Decision |
|---|---|---|
| **CLI** (`cli/`) | User interaction | `rich` for styled I/O, lazy imports |
| **Core** (`core/`) | Tracing & logging | `PLAIN_OUTPUT` toggle for test compat |
| **Agent** (`agent.py`) | LLM + ReAct loop | `@lru_cache` factory, no import-time init |
| **Tools** (`tools/`) | External APIs | Cached client, defensive `.get()`, error JSON |

Dependencies flow inward: **CLI → Core → Agent → Tools**

## Testing

```bash
python -m unittest tests.test_agent -v
```

Tests set `PLAIN_OUTPUT=1` to bypass rich formatting and mock the Tavily API. No network or API keys needed.

| Test | What it verifies |
|---|---|
| `test_agent_e2e_flow` | Full loop: question → tool call → structured answer |
| `test_empty_search_results` | Agent handles zero results gracefully |
| `test_malformed_search_results` | Defensive `.get()` prevents `KeyError` |
| `test_search_api_failure` | API errors return error JSON instead of crashing |

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key for LLM inference |
| `TAVILY_API_KEY` | ✅ | Tavily API key for web search |
| `PLAIN_OUTPUT` | ❌ | Set to `1` for plain-text output (no rich styling) |
