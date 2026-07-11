import os
from typing import Annotated, TypedDict

from langchain_core.messages import SystemMessage, AIMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END, add_messages
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from langgraph_agent.tools import ALL_TOOLS
from langgraph_agent.prompts import AGENT_SYSTEM_PROMPT

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


# gemma2-9b-it drives the conversational tool-calling loop: fast + cheap,
# good enough for routing "log this / edit that / look this HCP up".
llm = ChatGroq(
   model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.2,
)
llm_with_tools = llm.bind_tools(ALL_TOOLS)


def call_model(state: AgentState):
    messages = state["messages"]
    if not any(isinstance(m, SystemMessage) for m in messages):
        messages = [SystemMessage(content=AGENT_SYSTEM_PROMPT)] + messages
    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


def should_continue(state: AgentState):
    last_message = state["messages"][-1]
    if getattr(last_message, "tool_calls", None):
        return "tools"
    return END


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(ALL_TOOLS))

    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")

    # In-memory checkpointer keyed by thread/session id, so each rep's chat
    # keeps its own running context (which HCP they're logging, etc.).
    # Swap for a Postgres/Redis checkpointer in production.
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)


agent_graph = build_graph()


def run_agent(session_id: str, user_message: str) -> str:
    config = {"configurable": {"thread_id": session_id}}
    result = agent_graph.invoke(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config,
    )
    last = result["messages"][-1]
    return last.content if isinstance(last, AIMessage) else str(last.content)