"""AgentState TypedDict for LangGraph state management."""

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict):
    """LangGraph state shared across all nodes.

    Attributes:
        messages: Conversation history (LangChain messages).
        emotion_state: Current emotion as dict (from EmotionState.to_dict()).
        memory_context: Memory orchestration result dict.
        tool_calls: Pending tool calls for this turn.
        current_step: Current graph step: plan / execute / respond.
        safety_flag: normal / warning / blocked.
    """

    messages: list
    emotion_state: dict
    memory_context: dict
    tool_calls: list
    current_step: str
    safety_flag: str


def create_agent_state() -> AgentState:
    """Create a new AgentState with sensible defaults."""
    return AgentState(
        messages=[],
        emotion_state={},
        memory_context={},
        tool_calls=[],
        current_step="plan",
        safety_flag="normal",
    )
