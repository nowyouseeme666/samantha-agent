"""Tests for LangGraph state and graph construction."""
from unittest.mock import MagicMock, patch

import pytest


# ======================================================================
# AgentState (re-exported in graph/state.py)
# ======================================================================

class TestGraphState:
    def test_create_agent_state(self):
        """create_agent_state should return a properly initialized AgentState."""
        from src.graph.state import create_agent_state

        state = create_agent_state()

        assert state["messages"] == []
        assert state["emotion_state"] == {}
        assert state["memory_context"] == {}
        assert state["tool_calls"] == []
        assert state["current_step"] == "plan"
        assert state["safety_flag"] == "normal"

    def test_agent_state_mutation(self):
        """AgentState should be mutable for LangGraph updates."""
        from src.graph.state import create_agent_state

        state = create_agent_state()
        state["messages"].append("test message")
        state["current_step"] = "respond"

        assert len(state["messages"]) == 1
        assert state["current_step"] == "respond"


# ======================================================================
# Graph construction
# ======================================================================

class TestGraphConstruction:
    def test_build_graph_returns_compiled_graph(self):
        """build_graph should return a compiled StateGraph."""
        from src.graph.graph import build_graph

        graph = build_graph()

        assert graph is not None
        # A compiled graph should have a 'invoke' method
        assert hasattr(graph, "invoke")

    def test_graph_has_required_nodes(self):
        """The compiled graph should contain all four required nodes."""
        from src.graph.graph import build_graph

        graph = build_graph()

        # Compiled graphs expose their nodes via get_graph()
        compiled_nodes = {n for n in graph.get_graph().nodes}
        expected = {"agent_node", "tool_node", "safety_guard", "respond_node"}
        assert expected.issubset(compiled_nodes)

    def test_graph_invoke_basic_flow(self):
        """A basic invoke should flow from agent_node through to respond_node."""
        from src.graph.graph import build_graph
        from src.graph.state import create_agent_state

        graph = build_graph()
        state = create_agent_state()

        result = graph.invoke(state)

        # Should have progressed through the graph
        assert result is not None
        assert "current_step" in result
        # Without tools, should reach respond_node via safety_guard
        assert result["current_step"] in ("respond", "plan")

    def test_graph_invoke_empty_state(self):
        """Invoking with valid minimal state should not error."""
        from src.graph.graph import build_graph
        from src.graph.state import create_agent_state

        graph = build_graph()
        result = graph.invoke(create_agent_state())

        assert result is not None


# ======================================================================
# Node function signatures
# ======================================================================

class TestNodes:
    def test_agent_node_function(self):
        """agent_node should accept and return an AgentState dict."""
        from src.graph.graph import agent_node
        from src.graph.state import create_agent_state

        state = create_agent_state()
        result = agent_node(state)

        assert isinstance(result, dict)
        assert "messages" in result
        assert "current_step" in result

    def test_tool_node_placeholder(self):
        """tool_node should return state unchanged (placeholder in Phase 1)."""
        from src.graph.graph import tool_node
        from src.graph.state import create_agent_state

        state = create_agent_state()
        result = tool_node(state)

        assert result["tool_calls"] == state["tool_calls"]

    def test_safety_guard_node(self):
        """safety_guard should return 'normal' by default."""
        from src.graph.graph import safety_guard
        from src.graph.state import create_agent_state

        state = create_agent_state()
        result = safety_guard(state)

        assert result["safety_flag"] in ("normal", "warning")

    def test_respond_node(self):
        """respond_node should set step to 'respond'."""
        from src.graph.graph import respond_node
        from src.graph.state import create_agent_state

        state = create_agent_state()
        result = respond_node(state)

        assert result["current_step"] == "respond"


# ======================================================================
# Conditional routing
# ======================================================================

class TestRouting:
    def test_should_call_tools_no_calls(self):
        """should_call_tools should return 'respond' when no tool_calls."""
        from src.graph.graph import should_call_tools
        from src.graph.state import create_agent_state

        state = create_agent_state()
        state["tool_calls"] = []

        route = should_call_tools(state)
        assert route == "respond_node"

    def test_should_call_tools_with_calls(self):
        """should_call_tools should return 'tool_node' when tool_calls exists."""
        from src.graph.graph import should_call_tools
        from src.graph.state import create_agent_state

        state = create_agent_state()
        state["tool_calls"] = [{"name": "memory_search", "args": {"query": "test"}}]

        route = should_call_tools(state)
        assert route == "tool_node"
