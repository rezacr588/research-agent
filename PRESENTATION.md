# 🧠 Research Agent CLI — Video Presentation Script

> **Estimated length:** 8–10 minutes  
> **Format:** Screen recording with voiceover  
> **Audience:** Developers, AI enthusiasts, hiring managers

---

## 🎬 INTRO (0:00 – 0:45)

**[Show: Terminal with the banner visible]**

> "Hey everyone! Today I'm going to walk you through a project I built called **Research Agent** — an interactive command-line AI assistant that can search the web and give you structured, source-backed answers in real time.
>
> Think of it as having a research analyst inside your terminal. You ask a question in plain English, and it autonomously decides what to search for, reads the results, reasons about them, and comes back with a clean answer — all with sources.
>
> Let me show you how it works and, more importantly, **how I built it**."

---

## 🔍 LIVE DEMO (0:45 – 2:30)

**[Show: Running `python main.py` in the terminal]**

> "Let's start with a demo. I'll run the app..."

**[Type a question like: `What are the latest breakthroughs in quantum computing?`]**

> "I'll ask it about quantum computing breakthroughs. Watch what happens — you can see it in real time:
>
> 1. First, it picks up my question.
> 2. Then it **autonomously decides** to search the web — you can see the tool call panel.
> 3. The search results come back — those blue panels show what Tavily returned.
> 4. And then the model **streams its final answer** token by token, rendered as Markdown right in the terminal.
>
> Notice the output format: a **TL;DR**, **Key Points**, and **Sources** with real URLs. Everything is grounded in an actual web search — no hallucinated links."

**[Try a second question, maybe: `Who won the 2024 Nobel Prize in Physics?`]**

> "Let me try another one — something time-sensitive. The agent knows today's date, so it can handle 'recent' or 'latest' questions correctly."

---

## 🏗️ ARCHITECTURE DEEP DIVE (2:30 – 5:00)

### The ReAct Pattern

**[Show: The ASCII diagram from the README, or draw it on screen]**

> "Under the hood, this uses the **ReAct pattern** — that stands for Reason plus Act. Instead of answering in one shot, the LLM operates in a loop:
>
> 1. **Reason** — it thinks about what it knows and what it still needs.
> 2. **Act** — it calls a tool, in our case `web_search`, with a query it chose itself.
> 3. **Observe** — it reads the results and decides: do I have enough information?
>
> If not, it loops back and searches again with a refined query. When it's satisfied, it synthesizes a final answer. This is the same pattern used in state-of-the-art AI agents."

### Tech Stack

**[Show: `requirements.txt` or a slide with the stack]**

> "Here's the stack:
>
> - **Kimi K2** via **Groq** for the LLM — Kimi K2 is a strong reasoning model, and Groq gives us incredibly fast inference through their LPU hardware. I also built in automatic **model fallback**: if Kimi K2 is down, it seamlessly switches to GPT OSS 120B without the user even noticing.
>
> - **Tavily** for web search — it's purpose-built for AI agents, so it returns clean, structured JSON instead of raw HTML. No need to scrape or parse anything.
>
> - **LangGraph** to orchestrate the agent loop — it provides the state machine, message passing, and streaming out of the box.
>
> - **Rich** for the terminal UI — that's what gives us the spinners, colored panels, and live Markdown rendering."

### Project Walkthrough

**[Show: The file tree in the terminal or editor]**

> "The project has a clean four-layer architecture:
>
> - **`main.py`** — just the entry point. It loads the `.env` file and hands off to the CLI.
> - **`cli/app.py`** — the interactive REPL loop. It shows the banner, checks for API keys, and handles user input.
> - **`core/tracer.py`** — the execution engine. It streams the agent's output in real time and logs everything to a trace file.
> - **`agent.py`** — the brain. It configures the LLM with a system prompt (including today's date!), wires up the tools, and creates the ReAct agent. The agent is **lazily cached**: it's only created once per session.
> - **`tools/search.py`** — the only tool: a thin wrapper around Tavily with defensive error handling."

---

## 💡 KEY DESIGN DECISIONS (5:00 – 6:30)

**[Show relevant code snippets as you talk]**

> "There are a few design decisions I'm proud of:
>
> **1. Lazy Agent Initialization**  
> The agent isn't created at import time — it's built on first use and then cached. This means the CLI starts instantly, and we avoid unnecessary API calls.
>
> **2. Model Fallback with Probing**  
> When the agent initializes, it sends a quick 'ping' to verify the model is reachable. If it gets an error, it automatically tries the next model in the list. The user sees a warning, but the experience isn't interrupted.
>
> **3. Token-by-Token Streaming**  
> The answer doesn't appear all at once. It streams token by token using Rich's `Live` display, so you see the response being built in real time — just like ChatGPT.
>
> **4. Trace Logging**  
> Every session is logged to the `outputs/` folder with timestamps. You can audit exactly what the agent searched for, what it received, and what it answered. This is useful for debugging and for understanding the agent's reasoning.
>
> **5. Defensive Error Handling**  
> API failures don't crash the app. If Tavily returns an error, the search tool returns it as JSON, and the agent still generates a response. Rate limits and 503 errors get their own user-friendly panels."

---

## 🧪 TESTING (6:30 – 7:30)

**[Show: Running `python -m unittest tests.test_agent -v`]**

> "I've also written end-to-end tests. Let me run them..."

**[Run the tests and show the output]**

> "There are four tests, all using mocked APIs — no network or keys needed:
>
> 1. **Happy path** — full loop from question to search to structured answer.
> 2. **Empty results** — the agent handles zero search results gracefully.
> 3. **Malformed data** — missing fields don't cause crashes thanks to defensive `.get()` calls.
> 4. **API failure** — a `ConnectionError` returns error JSON, and the agent still produces a response.
>
> The tests use `PLAIN_OUTPUT=1` to bypass the Rich formatting, so we can capture and assert on plain text."

---

## 🚀 CLOSING (7:30 – 8:30)

**[Show: The terminal with the agent running]**

> "To wrap up — this project demonstrates several important concepts:
>
> - How to build an **agentic AI system** using the ReAct pattern
> - How to use **LangGraph** for orchestrating multi-step LLM workflows
> - How to integrate **external tools** (web search) cleanly and defensively
> - How to build a **polished developer experience** with streaming, error handling, and a beautiful terminal UI
> - And how to write **testable agent code** with mocked dependencies
>
> The code is open-source on GitHub. If you found this interesting, give it a star — and feel free to ask me any questions.
>
> Thanks for watching!"

---

## 📋 Recording Checklist

Before recording, make sure you have:

- [ ] API keys set in `.env` (Groq + Tavily)
- [ ] Terminal with a clean, dark background (increase font size for readability)
- [ ] Screen recording software ready (OBS, QuickTime, or Loom)
- [ ] Close other notifications / Do Not Disturb mode on
- [ ] Run the demo once before recording to warm up the agent cache
- [ ] Have 2–3 interesting questions ready that show different capabilities
- [ ] Run the tests once to make sure they all pass

## 🎯 Suggested Demo Questions

| Question | Why It's Good |
|---|---|
| "What are the latest breakthroughs in quantum computing?" | Shows real-time web research with multiple search results |
| "Who won the 2024 Nobel Prize in Physics?" | Demonstrates time-awareness (agent knows today's date) |
| "Compare React vs Vue for building web apps" | Shows the agent's ability to synthesize and structure opinions |
| "What is the current population of Tokyo?" | Quick factual lookup — shows speed |
