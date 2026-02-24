# 🧠 Research Agent — Code Walkthrough

> Use this document while scrolling through the code on camera.  
> Each section matches a file. Read the **talking points** aloud and **show the highlighted lines**.

---

## 1️⃣ `main.py` — The Entry Point (30 seconds)

**Open the file on screen.**

> "Everything starts here. Two lines do all the work:
> - `load_dotenv()` reads our API keys from a `.env` file.
> - Then we import and call `main()` from the CLI module.
>
> Notice the ORDER matters — dotenv **must** run before any other import tries to read the keys."

**Highlight:** Lines 4–7 (load_dotenv before imports).

---

## 2️⃣ `agent.py` — The Brain (2 minutes)

**Open the file and scroll to the MODELS list.**

> "This file builds the AI agent. Let me walk through it:"

### A. Model Fallback (line ~40)
> "We define a list of models to try. Right now it's Kimi K2 first, then GPT OSS 120B as a fallback. If the first model is down, we automatically switch."

**Highlight:** `MODELS` list.

### B. System Prompt (line ~50)
> "This is the prompt that shapes the agent's personality. Notice how we inject today's date at runtime — `{current_date}` and `{current_time}`. This is critical: without it, the LLM would think it's still in its training period and couldn't answer questions about recent events."

**Highlight:** `SYSTEM_PROMPT_TEMPLATE` and `_build_system_prompt()`.

### C. Agent Factory (line ~85)
> "Here's where the magic happens. `get_agent()` tries each model, sends a quick 'ping' to check if it's online, and then creates the ReAct agent with `create_react_agent`. The agent is cached so we only do this once per session."

**Highlight:** The `for model_id in MODELS` loop and `create_react_agent()` call.

---

## 3️⃣ `tools/search.py` — The Web Search Tool (1.5 minutes)

**Open the file.**

> "This is the only tool the agent has — web search via Tavily."

### A. The @tool Decorator (line ~70)
> "The `@tool` decorator is key — it registers this function so the LLM knows it exists and can call it autonomously. The docstring becomes the tool description that the LLM reads."

**Highlight:** `@tool` and the function signature.

### B. Defensive Error Handling (line ~75–90)
> "I've made this bulletproof. If the API fails, we return an error as JSON instead of crashing. And for each result, we use `.get()` with defaults — so missing fields don't cause `KeyError` exceptions."

**Highlight:** The `try/except` around `client.search()` and the `.get("title", "Untitled")` calls.

---

## 4️⃣ `core/tracer.py` — Real-Time Streaming (2 minutes)

**Open the file and scroll to `_run_rich()`.**

> "This is the most complex file — it handles streaming the answer token by token."

### A. Three Types of Chunks (line ~100)
> "When we stream from the agent, we get three kinds of messages:
> 1. **Tool call chunks** — 'I'm about to search for X' → yellow panel  
> 2. **Content chunks** — individual tokens of the answer → live Markdown  
> 3. **Tool messages** — search results came back → blue panel"

**Highlight:** The three `if/elif` branches inside the streaming loop.

### B. Live Markdown Rendering (line ~120)
> "Instead of waiting for the full answer, we render it as Markdown in real-time using Rich's `Live` display. Each new token gets appended to a buffer, and we re-render the whole thing. If the Markdown is incomplete mid-stream, we fall back to plain text."

**Highlight:** `answer_buffer += chunk.content` and the `Live()` setup.

### C. Error Resilience (line ~170)
> "We handle three error types gracefully: 503 (overloaded) triggers a model fallback, 429 (rate limit) tells the user to wait, and everything else shows a clean error message."

**Highlight:** The `except Exception` block with the three branches.

---

## 5️⃣ `cli/app.py` — The REPL Loop (1 minute)

**Open the file and scroll to `main()`.**

> "This is the user-facing loop. The flow is:
> 1. Check environment variables — fail fast with helpful instructions  
> 2. Initialize the agent — probe models, set up fallback  
> 3. Show the banner — now with the correct model name  
> 4. Enter the loop — read input, run agent, handle errors  
> 5. On exit — save the full session trace"

**Highlight:** The numbered steps in the `main()` function.

---

## 6️⃣ `tests/test_agent.py` — Testing (1 minute)

**Open the file.**

> "I've written four end-to-end tests, all with mocked APIs — no network needed:
> 1. **Happy path**: question → search → structured answer  
> 2. **Empty results**: zero search results don't crash  
> 3. **Malformed data**: missing fields handled by `.get()`  
> 4. **API failure**: `ConnectionError` returns error JSON, agent still responds  
>
> The key technique is `PLAIN_OUTPUT=1` — it disables Rich formatting so we can capture plain text with `io.StringIO` and run assertions on it."

**Highlight:** `@patch("research_agent.tools.search._get_tavily_client")` and `PLAIN_OUTPUT=1`.

---

## 🎯 Key Concepts to Emphasize

| Concept | Where to Show | One-Liner |
|---|---|---|
| **ReAct pattern** | `agent.py` → `create_react_agent()` | "Reason + Act in a loop until satisfied" |
| **Model fallback** | `agent.py` → `get_agent()` | "Try primary, fall back automatically" |
| **Lazy initialization** | `agent.py` → `_cached_agent` | "Only created once, reused forever" |
| **Token streaming** | `tracer.py` → `_run_rich()` | "Like ChatGPT — tokens appear one by one" |
| **Defensive tools** | `search.py` → `.get()` / `try/except` | "Never crash, always return something" |
| **Trace logging** | `tracer.py` → `save_session_trace()` | "Audit everything the agent did" |
