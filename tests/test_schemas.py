"""Tests for data schemas: MemoryEntry, EmotionState, AgentState."""
import json
from datetime import datetime
from enum import Enum

import pytest


# ======================================================================
# MemoryEntry
# ======================================================================

class TestMemoryEntry:
    def test_create_minimal(self):
        """MemoryEntry should be creatable with minimal required fields."""
        from src.schemas.memory import MemoryEntry, MemoryCategory

        entry = MemoryEntry(
            id="mem-001",
            content="用户喜欢喝咖啡",
            summary="用户喜欢咖啡",
            category=MemoryCategory.PREFERENCE,
        )

        assert entry.id == "mem-001"
        assert entry.content == "用户喜欢喝咖啡"
        assert entry.category == MemoryCategory.PREFERENCE

    def test_default_values(self):
        """MemoryEntry should have sensible defaults for optional fields."""
        from src.schemas.memory import MemoryEntry, MemoryCategory

        entry = MemoryEntry(
            id="mem-002",
            content="用户昨天去了公园",
            summary="用户去过公园",
            category=MemoryCategory.EVENT,
        )

        assert entry.importance == 0.5
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.last_accessed, datetime)
        assert entry.decay_rate == 0.01

    def test_to_dict_and_back(self):
        """MemoryEntry should round-trip through dict serialization."""
        from src.schemas.memory import MemoryEntry, MemoryCategory

        original = MemoryEntry(
            id="mem-003",
            content="用户今天很开心",
            summary="用户开心",
            category=MemoryCategory.EMOTION,
            importance=0.8,
        )
        data = original.to_dict()
        restored = MemoryEntry.from_dict(data)

        assert restored.id == original.id
        assert restored.content == original.content
        assert restored.summary == original.summary
        assert restored.category == original.category
        assert restored.importance == original.importance

    def test_importance_clamped(self):
        """importance should be clamped to 0.0–1.0 on construction."""
        from src.schemas.memory import MemoryEntry, MemoryCategory

        too_high = MemoryEntry(
            id="mem-004",
            content="test",
            summary="test",
            category=MemoryCategory.PROFILE,
            importance=5.0,
        )
        assert 0.0 <= too_high.importance <= 1.0

        too_low = MemoryEntry(
            id="mem-005",
            content="test",
            summary="test",
            category=MemoryCategory.ROUTINE,
            importance=-3.0,
        )
        assert 0.0 <= too_low.importance <= 1.0


# ======================================================================
# MemoryCategory Enum
# ======================================================================

class TestMemoryCategory:
    def test_all_categories_present(self):
        """MemoryCategory should contain all 5 categories from the design."""
        from src.schemas.memory import MemoryCategory

        members = {m.value for m in MemoryCategory}
        assert members == {"preference", "event", "emotion", "profile", "routine"}


# ======================================================================
# EmotionState
# ======================================================================

class TestEmotionState:
    def test_create_neutral(self):
        """Default EmotionState should be neutral/calm."""
        from src.schemas.emotion import EmotionState

        state = EmotionState()

        assert state.valence == 0.0
        assert state.arousal == 0.0
        assert state.label == "平静"

    def test_create_happy(self):
        """EmotionState should support happy/excited settings."""
        from src.schemas.emotion import EmotionState

        state = EmotionState(valence=0.9, arousal=0.7, label="开心")

        assert state.valence == 0.9
        assert state.arousal == 0.7
        assert state.label == "开心"

    def test_valence_clamped(self):
        """valence should be clamped to -1.0..1.0."""
        from src.schemas.emotion import EmotionState

        s = EmotionState(valence=2.5)
        assert -1.0 <= s.valence <= 1.0

        s2 = EmotionState(valence=-2.0)
        assert -1.0 <= s2.valence <= 1.0

    def test_arousal_clamped(self):
        """arousal should be clamped to 0.0..1.0."""
        from src.schemas.emotion import EmotionState

        s = EmotionState(arousal=1.5)
        assert 0.0 <= s.arousal <= 1.0

        s2 = EmotionState(arousal=-0.5)
        assert 0.0 <= s2.arousal <= 1.0

    def test_to_dict(self):
        """to_dict should produce a plain dict for LangGraph state."""
        from src.schemas.emotion import EmotionState

        s = EmotionState(valence=0.5, arousal=0.3, label="愉悦")
        d = s.to_dict()

        assert d == {"valence": 0.5, "arousal": 0.3, "label": "愉悦", "confidence": 0.5}

    def test_from_dict(self):
        """from_dict should reconstruct EmotionState from a dict."""
        from src.schemas.emotion import EmotionState

        d = {"valence": -0.3, "arousal": 0.6, "label": "焦虑", "confidence": 0.8}
        s = EmotionState.from_dict(d)

        assert s.valence == -0.3
        assert s.arousal == 0.6
        assert s.label == "焦虑"
        assert s.confidence == 0.8


# ======================================================================
# AgentState (LangGraph TypedDict)
# ======================================================================

class TestAgentState:
    def test_agent_state_fields(self):
        """AgentState TypedDict should have all required keys."""
        from src.schemas.agent import AgentState

        # TypedDict fields are accessible via __required_keys__
        required_keys = AgentState.__required_keys__
        assert "messages" in required_keys
        assert "emotion_state" in required_keys
        assert "memory_context" in required_keys
        assert "tool_calls" in required_keys
        assert "current_step" in required_keys
        assert "safety_flag" in required_keys

    def test_agent_state_default_factory(self):
        """AgentState should be instantiable with a factory that sets defaults."""
        from src.schemas.agent import create_agent_state

        state = create_agent_state()

        assert state["messages"] == []
        assert state["emotion_state"] == {}
        assert state["memory_context"] == {}
        assert state["tool_calls"] == []
        assert state["current_step"] == "plan"
        assert state["safety_flag"] == "normal"

    def test_agent_state_mutable(self):
        """AgentState should be a mutable dict-like object."""
        from src.schemas.agent import create_agent_state

        state = create_agent_state()
        state["current_step"] = "execute"
        state["safety_flag"] = "warning"

        assert state["current_step"] == "execute"
        assert state["safety_flag"] == "warning"
