from langchain_core.messages import AIMessage, ToolMessage
from agent import agent
from datetime import datetime
import os

def run_with_trace(question: str):
    lines = []
    lines.append(f"Question: {question}")
    lines.append(f"Timestamp: {datetime.now().isoformat()}")
    lines.append("-" * 60)

    for chunk in agent.stream(
        {"messages": [{"role": "user", "content": question}]},
        stream_mode="values",
    ):
        msg = chunk["messages"][-1]
        if isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            line = "🧠 Tool call: " + str([tc["name"] for tc in msg.tool_calls])
            print(line)
            lines.append(line)
        elif isinstance(msg, ToolMessage):
            line = "🔧 Tool result (preview): " + str(msg.content)[:250] + " ..."
            print(line)
            lines.append(line)
        elif isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
            line = "✅ Final answer:\n" + msg.content
            print(line)
            lines.append(line)

    # Save trace to file
    try:
        os.makedirs("outputs", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filepath = os.path.join("outputs", f"trace_{timestamp}.txt")
        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        print(f"\n📁 Trace saved to {filepath}")
    except OSError:
        pass  # Skip saving if filesystem is restricted