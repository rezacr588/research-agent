# 🧠 Research Agent CLI

A polished, interactive command-line research assistant that searches the web and delivers structured, source-backed answers — powered by **Kimi K2** (via Groq), **Tavily** web search, and **LangGraph**.

## What It Does

You ask a question in plain English. The agent autonomously decides whether it needs to search the web, executes one or more searches, reads the results, reasons about them, and returns a structured answer with:

- **TL;DR** — 2-bullet summary
- **Key Points** — 5 detailed bullets
- **Sources** — clickable URLs for every claim

All of this happens in real time with animated spinners and color-coded panels in your terminal.

## How It Works

### The ReAct Pattern

This agent uses the **ReAct** (Reason + Act) pattern, a well-known approach in AI agent design. Instead of answering in one shot, the LLM operates in a loop:

```
User Question
     ↓
┌─────────────────────────┐
│  🧠 REASON              │  ← LLM thinks about what it knows
│  "I need current data"  │     and what it still needs
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  🔧 ACT                 │  ← LLM calls a tool (web_search)
│  web_search("query")    │     with a self-chosen query
└──────────┬──────────────┘
           ↓
┌─────────────────────────┐
│  📥 OBSERVE             │  ← LLM reads the search results
│  [{title, url, snippet}]│     and decides: enough info?
└──────────┬──────────────┘
           ↓
     Enough info? ──No──→ Loop back to REASON
           │
          Yes
           ↓
┌─────────────────────────┐
│  ✅ ANSWER              │  ← LLM synthesizes a final
│  TL;DR + Key Points     │     structured response
│  + Sources              │
└─────────────────────────┘
```

This loop is managed by **LangGraph**, which orchestrates the state machine and handles message passing between the LLM and tools.

### Key Design Decisions

| Decision | Why |
|---|---|
| **Kimi K2 via Groq** | Kimi K2 is a strong reasoning model; Groq provides fast inference via their LPU hardware |
| **Tavily for search** | Purpose-built for AI agents — returns clean, structured results (not raw HTML) |
| **LangGraph ReAct** | Battle-tested agent loop with built-in state management and streaming |
| **Rich terminal UI** | Spinners, panels, and Markdown rendering make the experience feel professional |
| **Lazy agent init** | Agent is created on first use (`@lru_cache`), not at import time — avoids slow startup |
| **Trace logging** | Every run is saved to `outputs/` so you can audit what the agent did |

### Component Flow

```
main.py
  └→ dotenv loads .env (API keys)
  └→ cli/app.py
       └→ Shows banner, starts REPL
       └→ core/tracer.py
            └→ agent.py (lazy init)
            │    └→ ChatGroq (Kimi K2)
            │    └→ tools/search.py (Tavily)
            └→ Streams chunks from agent
            └→ Displays rich panels
            └→ Saves trace to outputs/
```

## Features

- 🔍 **Web-grounded answers** — every factual claim is backed by a live search
- 🧠 **Autonomous reasoning** — the LLM decides when and what to search
- ✨ **Rich terminal UI** — spinners, coloured panels, Markdown-rendered answers
- 📁 **Automatic trace logging** — every run is saved with timestamps
- 🛡️ **Error resilience** — API failures return error JSON instead of crashing
- 🧪 **4 E2E tests** — happy path, empty results, malformed data, API failure

## Quick Start

### 1. Install

```bash
git clone git@github.com:rezacr588/research-agent.git
cd research-agent
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure

Create a `.env` file in the project root (auto-loaded, no need to export):

```env
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```

Get your keys:
- **Groq**: [console.groq.com](https://console.groq.com)
- **Tavily**: [tavily.com](https://tavily.com) (free tier available)

### 3. Run

```bash
python main.py
# or
python -m research_agent
```

### 4. Ask Questions

```
> What are the latest breakthroughs in quantum computing?
> Who won the Nobel Prize in Physics 2024?
> Compare React vs Vue for building web apps
```

| Command | Action |
|---|---|
| `quit` / `exit` / `q` | Exit |
| `clear` | Clear screen |
| `Ctrl+C` | Exit gracefully |

## Project Structure

```
research-agent/
├── main.py                          # Entry point (loads .env)
├── .env                             # API keys (git-ignored)
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
├── tests/
│   ├── __init__.py
│   └── test_agent.py                # 4 E2E tests (mocked APIs)
└── outputs/                         # Auto-generated trace files
```

### Architecture Layers

| Layer | Responsibility | Key Design |
|---|---|---|
| **CLI** (`cli/`) | User interaction, env checks | `rich` panels, lazy imports |
| **Core** (`core/`) | Tracing, streaming, file logging | `PLAIN_OUTPUT` toggle for tests |
| **Agent** (`agent.py`) | LLM + ReAct loop config | `@lru_cache` factory avoids cold start |
| **Tools** (`tools/`) | External API calls | Cached client, defensive `.get()`, error JSON |

Dependencies flow inward: **CLI → Core → Agent → Tools**

## Testing

```bash
python -m unittest tests.test_agent -v
```

Tests set `PLAIN_OUTPUT=1` to bypass rich formatting and mock the Tavily API — no network or keys needed.

| Test | Verifies |
|---|---|
| `test_agent_e2e_flow` | Full loop: question → search → structured answer |
| `test_empty_search_results` | Agent handles zero results without crashing |
| `test_malformed_search_results` | Missing fields don't cause `KeyError` |
| `test_search_api_failure` | API errors return error JSON, agent still responds |

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key for Kimi K2 inference |
| `TAVILY_API_KEY` | ✅ | Tavily API key for web search |
| `PLAIN_OUTPUT` | ❌ | Set to `1` for plain-text output (used in tests) |
