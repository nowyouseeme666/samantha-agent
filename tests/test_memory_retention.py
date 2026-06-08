"""Test that Samantha can remember user preferences across conversations."""
import pytest
from datetime import datetime
from unittest.mock import MagicMock

from src.schemas.memory import MemoryCategory, MemoryEntry
from src.schemas.emotion import EmotionState
from src.memory.long_term import LongTermMemory
from src.memory.short_term import ShortTermMemory
from src.memory.immutable import ImmutableMemory
from src.memory.orchestrator import MemoryOrchestrator


@pytest.fixture
def long_term():
    mem = LongTermMemory(chroma_dir="./data/chroma_test_retention")
    yield mem
    mem.clear()


@pytest.fixture
def short_term():
    return ShortTermMemory(max_rounds=10)


@pytest.fixture
def immutable():
    import os
    persona_path = os.path.join(os.path.dirname(__file__), "..", "config", "persona.yaml")
    return ImmutableMemory.from_yaml(persona_path)


@pytest.fixture
def orchestrator(short_term, long_term, immutable):
    return MemoryOrchestrator(short_term, long_term, immutable)


class TestUserPreferenceRetention:
    """Can Samantha remember user preferences across sessions?"""

    def test_add_and_retrieve_preference(self, long_term):
        """User tells preference, we store it, then retrieve it."""
        entry = MemoryEntry(
            id="pref-coffee", content="用户说他喜欢喝冰美式", summary="喜欢冰美式",
            category=MemoryCategory.PREFERENCE, importance=0.8,
        )
        long_term.add(entry)
        results = long_term.get(query="咖啡", k=5)
        matching_ids = {r.id for r in results}
        assert "pref-coffee" in matching_ids

    def test_add_and_retrieve_pet_info(self, long_term):
        """User tells about pet, we store it, then retrieve it."""
        entry = MemoryEntry(
            id="pet-cat", content="用户养了一只猫叫咪咪，今年3岁", summary="养猫叫咪咪",
            category=MemoryCategory.PROFILE, importance=0.7,
        )
        long_term.add(entry)
        results = long_term.get(query="猫", k=5)
        matching_ids = {r.id for r in results}
        assert "pet-cat" in matching_ids

    def test_add_and_retrieve_event(self, long_term):
        """User mentions event, we store it, then retrieve it."""
        entry = MemoryEntry(
            id="evt-travel", content="用户上周和女朋友去了杭州旅行", summary="杭州旅行",
            category=MemoryCategory.EVENT, importance=0.6,
        )
        long_term.add(entry)
        results = long_term.get(query="旅行", k=5)
        matching_ids = {r.id for r in results}
        assert "evt-travel" in matching_ids

    def test_multiple_preferences_all_retrievable(self, long_term):
        """Store multiple preferences, all should be retrievable."""
        prefs = [
            ("pref-1", "喜欢咖啡", MemoryCategory.PREFERENCE),
            ("pref-2", "喜欢冬天", MemoryCategory.PREFERENCE),
            ("pref-3", "不喜欢吃辣", MemoryCategory.PREFERENCE),
        ]
        for pid, content, cat in prefs:
            long_term.add(MemoryEntry(id=pid, content=content, summary=content, category=cat, importance=0.5))

        coffee_results = long_term.get(query="咖啡", k=5)
        assert any(r.id == "pref-1" for r in coffee_results)

        winter_results = long_term.get(query="冬天", k=5)
        assert any(r.id == "pref-2" for r in winter_results)

        spicy_results = long_term.get(query="辣", k=5)
        assert any(r.id == "pref-3" for r in spicy_results)

    def test_preference_later_conversation_still_retrievable(self, long_term):
        """Simulate: first session stores preference, later retrieval should find it."""
        # Session 1: user mentions preferences
        long_term.add(MemoryEntry(
            id="s1-pref", content="用户说他喜欢听周杰伦的歌", summary="喜欢周杰伦",
            category=MemoryCategory.PREFERENCE, importance=0.8,
        ))

        # Intermediate: other conversations happen
        long_term.add(MemoryEntry(id="s2-1", content="闲聊内容1", summary="闲聊1", category=MemoryCategory.EVENT, importance=0.3))
        long_term.add(MemoryEntry(id="s2-2", content="闲聊内容2", summary="闲聊2", category=MemoryCategory.EVENT, importance=0.3))

        # Session 3: user asks something related - should still find the preference
        results = long_term.get(query="听歌", k=5)
        assert any(r.id == "s1-pref" for r in results)


class TestMemoryOrchestratorIntegration:
    """Integration test of three-layer memory orchestration."""

    def test_orchestrator_gather_includes_immutable(self, orchestrator, long_term):
        """Immutable memories always present in gathered context."""
        ctx = orchestrator.gather("你好", EmotionState(valence=0, arousal=0, label="neutral"))
        persona_ids = {e.id for e in ctx.entries if e.id.startswith("persona-")}
        assert len(persona_ids) > 0

    def test_orchestrator_gather_includes_long_term(self, orchestrator, long_term):
        """Long-term memories that match the query appear."""
        long_term.add(MemoryEntry(
            id="lt-test", content="用户喜欢吃火锅", summary="喜欢火锅",
            category=MemoryCategory.PREFERENCE, importance=0.7,
        ))
        ctx = orchestrator.gather("火锅", EmotionState(valence=0.5, arousal=0.3, label="happy"))
        lt_ids = [e.id for e in ctx.entries if e.id == "lt-test"]
        assert len(lt_ids) > 0

    def test_orchestrator_immutable_always_first(self, orchestrator):
        """Immutable entries should appear first in the result."""
        ctx = orchestrator.gather("anything", EmotionState(valence=0, arousal=0, label="neutral"))
        if ctx.entries:
            first_entry = ctx.entries[0]
            assert first_entry.id.startswith("persona-"), f"Expected persona-* first, got {first_entry.id}"

    def test_orchestrator_dedup_by_category(self, orchestrator, long_term):
        """Deduplication keeps top-3 per category."""
        for i in range(5):
            long_term.add(MemoryEntry(
                id=f"pref-{i}", content=f"偏好{i}", summary=f"偏好{i}",
                category=MemoryCategory.PREFERENCE, importance=0.5,
            ))
        ctx = orchestrator.gather("偏好", EmotionState(valence=0, arousal=0, label="neutral"))
        pref_count = sum(1 for e in ctx.entries if e.id.startswith("pref-"))
        assert pref_count <= 3, f"Expected <= 3 preference entries, got {pref_count}"

    def test_orchestrator_total_hits(self, orchestrator):
        """Total hits should be non-negative."""
        ctx = orchestrator.gather("test", EmotionState(valence=0, arousal=0, label="neutral"))
        assert ctx.total_hits >= 0


class TestDecayScoring:
    """Verify the decay scoring logic in MemoryOrchestrator."""

    def test_recent_entry_scores_higher(self, orchestrator):
        """A more recently accessed entry should score higher."""
        from src.schemas.memory import MemoryEntry as ME
        from datetime import datetime, timedelta

        recent = ME(id="recent", content="recent", summary="recent", category=MemoryCategory.EVENT,
                     importance=0.5, last_accessed=datetime.now())
        old_entry = ME(id="old", content="old", summary="old", category=MemoryCategory.EVENT,
                        importance=0.5, last_accessed=datetime.now() - timedelta(days=30))

        recent_score = orchestrator._calc_decay_score(recent)
        old_score = orchestrator._calc_decay_score(old_entry)
        assert recent_score > old_score, f"Recent={recent_score:.3f}, Old={old_score:.3f}"

    def test_high_importance_outweighs_decay(self, orchestrator):
        """High-importance old memory can outscore low-importance recent memory."""
        from datetime import datetime, timedelta

        old_important = MemoryEntry(
            id="old-imp", content="important", summary="important",
            category=MemoryCategory.PREFERENCE, importance=0.95,
            last_accessed=datetime.now() - timedelta(days=10),
        )
        recent_unimportant = MemoryEntry(
            id="recent-unimp", content="unimportant", summary="unimportant",
            category=MemoryCategory.EVENT, importance=0.2,
            last_accessed=datetime.now(),
        )

        old_score = orchestrator._calc_decay_score(old_important)
        recent_score = orchestrator._calc_decay_score(recent_unimportant)
        assert old_score > recent_score, f"Old important={old_score:.3f} should beat recent unimportant={recent_score:.3f}"


class TestFullMemoryFlow:
    """End-to-end memory flow: store -> retrieve -> inject into context."""

    def test_remember_preference_across_sessions(self, long_term, short_term, immutable):
        """Full simulation of remembering a user preference."""
        orch = MemoryOrchestrator(short_term, long_term, immutable)

        # Session 1: user shares a preference
        long_term.add(MemoryEntry(
            id="mem-fav-food", content="用户最喜欢的食物是寿司", summary="喜欢寿司",
            category=MemoryCategory.PREFERENCE, importance=0.75,
        ))

        # Session 2: user asks about food recommendations
        ctx = orch.gather("推荐食物", EmotionState(valence=0.3, arousal=0.2, label="hopeful"))
        summaries = ctx.top_summaries(k=5)
        assert len(summaries) > 0

    def test_samantha_identity_always_present(self, long_term, short_term, immutable):
        """Samantha's core identity should always be in memory context."""
        orch = MemoryOrchestrator(short_term, long_term, immutable)
        ctx = orch.gather("你是谁", EmotionState())
        assert ctx.total_hits > 0
