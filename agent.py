from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import SystemMessage
from search import web_search

system = SystemMessage(content=
  "You are a research agent. Always use web_search for factual claims.\n"
  "Output:\n1) TL;DR (2 bullets)\n2) Key points (5 bullets)\n3) Sources (URLs)\n"
)

llm = ChatGroq(
    model="moonshotai/kimi-k2-instruct",
    temperature=0,
)

agent = create_react_agent(
    llm,
    tools=[web_search],
    prompt=system,
)