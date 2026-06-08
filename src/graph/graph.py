"""LangGraph StateGraph — the core agent orchestration graph.

Follows the architecture from the design doc:

    START → agent_node → has tool_calls?
              │ yes            │ no
              ▼                ▼
          tool_node      safety_guard
              │                │
              └→ agent_node    ├─ normal ──→ respond_node → END
                               └─ blocked ──→ END
"""

from __future__ import annotations

from typing import Any, Literal

from langgraph.graph import END, StateGraph

from src.graph.state import AgentState, create_agent_state


# ======================================================================
# Node functions
# ======================================================================

def agent_node(state: AgentState) -> dict[str, Any]:
    """Entry node — analyse intent, decide if tool calls are needed.

    In Phase 1 this is a placeholder that passes through.
    When the full LLM integration is wired in, this node will:
    1. Build prompt with PromptBuilder
    2. Call LLMClient.chat()
    3. Parse any tool_call directives
    """
    return {
        "current_step": "execute",
        "messages": list(state.get("messages", [])),
        "tool_calls": list(state.get("tool_calls", [])),
    }


def tool_node(state: AgentState) -> dict[str, Any]:
    """Execute pending tool calls and feed results back to agent_node.

    Phase 1: placeholder — returns state unchanged with tool_calls cleared.
    """
    return {
        "tool_calls": [],
        "messages": list(state.get("messages", [])),
        "current_step": "plan",
    }


def safety_guard(state: AgentState) -> dict[str, Any]:
    """Check output for safety violations before responding.

    Returns:
        safety_flag: "normal" (pass) or "warning" / "blocked".
    """
    # Phase 1: default pass-through; will integrate SafetyGuard in Task 7
    return {
        "safety_flag": "normal",
        "current_step": "respond",
        "messages": list(state.get("messages", [])),
    }


def respond_node(state: AgentState) -> dict[str, Any]:
    """Final node — prepare the response for the user."""
    return {
        "current_step": "respond",
        "messages": list(state.get("messages", [])),
    }


# ======================================================================
# Conditional routing
# ======================================================================

def should_call_tools(state: AgentState) -> Literal["tool_node", "respond_node"]:
    """Route to tool_node if there are tool calls, else to respond_node.

    Note: in the full graph flow, agent_node routes here **before** safety_guard.
    After tool_node executes, the graph loops back to agent_node for re-evaluation.
    """
    tool_calls = state.get("tool_calls", [])
    if tool_calls:
        return "tool_node"
    return "respond_node"


def after_safety_check(state: AgentState) -> Literal["respond_node", "__end__"]:
    """After safety_guard, allow through or end immediately."""
    flag = state.get("safety_flag", "normal")
    if flag == "blocked":
        return END
    return "respond_node"


# ======================================================================
# Graph builder
# ======================================================================

def build_graph() -> Any:
    """Build and compile the Samantha agent StateGraph.

    Returns a compiled graph with .invoke(state) entry point.
    """
    graph = StateGraph(AgentState)

    # -- Add nodes --
    graph.add_node("agent_node", agent_node)
    graph.add_node("tool_node", tool_node)
    graph.add_node("safety_guard", safety_guard)
    graph.add_node("respond_node", respond_node)

    # -- Edges --
    graph.set_entry_point("agent_node")

    # agent_node → tool_node (if tool calls) or safety_guard (if not)
    graph.add_conditional_edges(
        "agent_node",
        should_call_tools,
        {"tool_node": "tool_node", "respond_node": "safety_guard"},
    )

    # tool_node → back to agent_node (re-evaluate after tool execution)
    graph.add_edge("tool_node", "agent_node")

    # safety_guard → respond_node or END
    graph.add_conditional_edges(
        "safety_guard",
        after_safety_check,
        {"respond_node": "respond_node", "__end__": END},
    )

    # respond_node → END
    graph.add_edge("respond_node", END)

    return graph.compile()
