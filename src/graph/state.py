"""LangGraph AgentState re-export + factory.

This thin re-export file exists so the graph/ package can own the state
definition while schemas/ remains the canonical source of truth.
"""

from src.schemas.agent import AgentState, create_agent_state

__all__ = ["AgentState", "create_agent_state"]
