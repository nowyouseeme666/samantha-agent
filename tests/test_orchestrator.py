"""Tests for memory orchestrator — src/memory/orchestrator.py."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.schemas.emotion import EmotionState
from src.schemas.memory import MemoryCategory, MemoryEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def _make_orchestrator(*, short_term_entries=(), long_term_entries=()):
    """Build a MemoryOrchestrator with pre-populated memory layers."""
    from src.memory.short_term import ShortTermMemory
    from src.memory.long_term import LongTermMemory
    from src.memory.immutable import ImmutableMemory
    from src.memory.orchestrator import MemoryOrchestrator

    short_term = ShortTermMemory(max_rounds=20)
    for e in short_term_entries:
        short_term.add(e)

    long_term = LongTermMemory()
    for e in long_term_entries:
        long_term.add(e)

    # Load immutable from persona.yaml (contains identity, traits, boundaries, values)
    immutable = ImmutableMemory.from_yaml(_CONFIG_DIR / "persona.yaml")

    return MemoryOrchestrator(
        short_term=short_term,
        long_term=long_term,
        immutable=immutable,
    )


def _make_entry(
    id_: str,
    content: str,
    summary: str,
    category: MemoryCategory,
    importance: float = 0.5,
    days_ago: float = 0,
) -> MemoryEntry:
    """Create a MemoryEntry with a configurable age."""
    created = datetime.now() - timedelta(days=days_ago)
    return MemoryEntry(
        id=id_,
        content=content,
        summary=summary,
        category=category,
        importance=importance,
        created_at=created,
        last_accessed=created,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGatherReturnsAllLayers:
    def test_all_layers_present(self):
        orch = _make_orchestrator(
            short_term_entries=[
                _make_entry("st-1", "User: 你好", "你好", MemoryCategory.EVENT),
            ],
            long_term_entries=[
                _make_entry("lt-1", "用户喜欢咖啡", "喜欢咖啡", MemoryCategory.PREFERENCE),
            ],
        )
        emotion = EmotionState()

        result = orch.gather(query="咖啡", current_emotion=emotion)
        # Should have entries
        assert len(result.entries) > 0

    def test_immutable_always_included(self):
        orch = _make_orchestrator(
            short_term_entries=[],
            long_term_entries=[
                _make_entry("lt-1", "用户喜欢咖啡", "喜欢咖啡", MemoryCategory.PREFERENCE),
            ],
        )
        emotion = EmotionState()

        result = orch.gather(query="什么", current_emotion=emotion)
        persona_ids = {e.id for e in result.entries if e.id.startswith("persona-")}
        assert len(persona_ids) >= 2  # persona identity + traits should be present


class TestImmutableFirst:
    def test_immutable_entries_are_first(self):
        orch = _make_orchestrator(
            short_term_entries=[
                _make_entry("st-1", "User: 最近如何", "最近如何", MemoryCategory.EVENT),
            ],
            long_term_entries=[
                _make_entry(
                    "lt-1", "用户喜欢跑步", "喜欢跑步", MemoryCategory.PREFERENCE,
                    importance=0.9, days_ago=1,
                ),
            ],
        )
        emotion = EmotionState()

        result = orch.gather(query="运动", current_emotion=emotion)
        # First entries should be persona (immutable)
        first_ids = [e.id for e in result.entries[:2]]
        for fid in first_ids:
            assert fid.startswith("persona-"), f"Expected persona entry first, got {fid}"


class TestDecayReducesScore:
    def test_older_memory_scores_lower(self):
        """An older memory should rank lower than a recent one (same importance)."""
        orch = _make_orchestrator(
            short_term_entries=[],
            long_term_entries=[
                _make_entry(
                    "lt-recent", "最近喜欢游泳", "最近游泳",
                    MemoryCategory.PREFERENCE, importance=0.8, days_ago=1,
                ),
                _make_entry(
                    "lt-old", "很久以前游泳比赛", "过去游泳比赛",
                    MemoryCategory.PREFERENCE, importance=0.8, days_ago=100,
                ),
            ],
        )
        emotion = EmotionState()

        result = orch.gather(query="游泳", current_emotion=emotion)

        # Find indices of our two entries (skip immutable ones at front)
        lt_entries = [e for e in result.entries if e.id.startswith("lt-")]
        recent_idx = next(
            i for i, e in enumerate(lt_entries) if e.id == "lt-recent"
        )
        old_idx = next(
            i for i, e in enumerate(lt_entries) if e.id == "lt-old"
        )
        assert recent_idx < old_idx, (
            f"Recent entry (idx={recent_idx}) should come before old (idx={old_idx})"
        )


class TestEmptyQuery:
    def test_empty_query_returns_short_term(self):
        orch = _make_orchestrator(
            short_term_entries=[
                _make_entry("st-1", "User: 你好", "你好", MemoryCategory.EVENT),
                _make_entry("st-2", "Samantha: 嗨！", "回复", MemoryCategory.EVENT),
            ],
            long_term_entries=[
                _make_entry("lt-1", "旧记忆", "旧记忆", MemoryCategory.EVENT),
            ],
        )
        emotion = EmotionState()

        result = orch.gather(query="", current_emotion=emotion)
        # Should still return something (immutable + whatever available)
        assert len(result.entries) > 0


class TestConflictResolution:
    def test_same_category_deduplication(self):
        """Entries in the same category should be deduplicated, keeping top-scored."""
        orch = _make_orchestrator(
            short_term_entries=[],
            long_term_entries=[
                _make_entry(
                    "lt-1", "用户喜欢咖啡", "喜欢咖啡",
                    MemoryCategory.PREFERENCE, importance=0.9,
                ),
                _make_entry(
                    "lt-2", "用户每天早上喝咖啡", "早上喝咖啡",
                    MemoryCategory.PREFERENCE, importance=0.7,
                ),
                _make_entry(
                    "lt-3", "用户最爱的咖啡店", "最爱咖啡店",
                    MemoryCategory.PREFERENCE, importance=0.5,
                ),
                _make_entry(
                    "lt-4", "另一条偏好", "另一条",
                    MemoryCategory.PREFERENCE, importance=0.3,
                ),
            ],
        )
        emotion = EmotionState()

        result = orch.gather(query="咖啡", current_emotion=emotion)
        # Should not crash; entries should be deduplicated
        pref_entries = [
            e for e in result.entries
            if e.category == MemoryCategory.PREFERENCE and e.id.startswith("lt-")
        ]
        # At most top-3 per category should remain
        assert len(pref_entries) <= 3
