# 🧠 Research Agent CLI

A CLI research assistant powered by **Kimi K2** (via Groq) + **Tavily** web search + **LangGraph**.

Ask any research question and get a structured answer with TL;DR, key points, and sources.

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
```

```
╔══════════════════════════════════════════════╗
║   🧠  Research Agent CLI                     ║
║   Model: Kimi K2 (via Groq)                  ║
║   Search: Tavily                              ║
╚══════════════════════════════════════════════╝

🔍 Ask: What are the latest AI breakthroughs?
```

| Command | Action |
|---|---|
| `quit` / `exit` / `q` | Exit |
| `clear` | Clear screen |
| `Ctrl+C` | Exit gracefully |

Every answer is traced and saved to `outputs/`.

## Project Structure

```
research-agent/
├── main.py                          # Entry point
├── requirements.txt
├── research_agent/
│   ├── __init__.py
│   ├── agent.py                     # LLM + ReAct agent config
│   ├── tools/
│   │   ├── __init__.py
│   │   └── search.py                # Tavily web search tool
│   ├── core/
│   │   ├── __init__.py
│   │   └── tracer.py                # Execution tracing + file logging
│   └── cli/
│       ├── __init__.py
│       └── app.py                   # Interactive REPL
└── tests/
    ├── __init__.py
    └── test_agent.py                # E2E tests (mocked APIs)
```

### Architecture

| Layer | Responsibility | Files |
|---|---|---|
| **CLI** | User interaction, env checks | `cli/app.py` |
| **Core** | Tracing, logging, orchestration | `core/tracer.py` |
| **Agent** | LLM config, ReAct loop | `agent.py` |
| **Tools** | External integrations | `tools/search.py` |

Dependencies flow inward: CLI → Core → Agent → Tools.

## Testing

```bash
python -m unittest tests.test_agent -v
```

Tests mock the Tavily API so no network or API keys are needed.
