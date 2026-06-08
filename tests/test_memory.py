"""Tests for the three-layer memory system."""
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from src.schemas.memory import MemoryCategory, MemoryEntry


# ======================================================================
# BaseMemory — abstract contract
# ======================================================================

class TestBaseMemory:
    def test_cannot_instantiate_abstract(self):
        """BaseMemory should not be directly instantiable."""
        from src.memory.base import BaseMemory

        with pytest.raises(TypeError):
            BaseMemory()  # type: ignore[abstract]

    def test_concrete_must_implement_add(self):
        """Subclass without add() should be uninstantiable."""
        from src.memory.base import BaseMemory

        class BrokenMemory(BaseMemory):
            def get(self, query, k):
                return []
            def clear(self):
                pass

        with pytest.raises(TypeError):
            BrokenMemory()  # type: ignore[abstract]

    def test_concrete_must_implement_get(self):
        """Subclass without get() should be uninstantiable."""
        from src.memory.base import BaseMemory

        class BrokenMemory(BaseMemory):
            def add(self, entry):
                pass
            def clear(self):
                pass

        with pytest.raises(TypeError):
            BrokenMemory()  # type: ignore[abstract]


# ======================================================================
# ShortTermMemory — sliding window
# ======================================================================

class TestShortTermMemory:
    @pytest.fixture
    def mem(self):
        from src.memory.short_term import ShortTermMemory
        return ShortTermMemory(max_rounds=5)

    def test_add_and_get(self, mem):
        """Adding entries should be retrievable via get()."""
        entry = MemoryEntry(
            id="s1", content="你好", summary="打招呼",
            category=MemoryCategory.EVENT,
        )
        mem.add(entry)
        results = mem.get(query="", k=10)

        assert len(results) == 1
        assert results[0].id == "s1"

    def test_window_eviction(self, mem):
        """When exceeding max_rounds, oldest entries should be evicted."""
        for i in range(10):
            mem.add(MemoryEntry(
                id=f"s{i}", content=f"msg{i}", summary=f"msg{i}",
                category=MemoryCategory.ROUTINE,
            ))

        results = mem.get(query="", k=20)
        assert len(results) == 5  # max_rounds
        # Oldest 5 evicted, youngest 5 retained
        ids = {r.id for r in results}
        assert "s0" not in ids
        assert "s9" in ids

    def test_clear(self, mem):
        """clear() should remove all entries."""
        mem.add(MemoryEntry(
            id="s1", content="test", summary="test",
            category=MemoryCategory.EVENT,
        ))
        mem.clear()
        assert len(mem.get(query="", k=10)) == 0

    def test_get_returns_most_recent_first(self, mem):
        """get() should return most recently added first."""
        for i in range(3):
            mem.add(MemoryEntry(
                id=f"s{i}", content=f"msg{i}", summary=f"msg{i}",
                category=MemoryCategory.ROUTINE,
            ))
        results = mem.get(query="", k=10)
        assert results[0].id == "s2"  # newest first
        assert results[2].id == "s0"  # oldest last


# ======================================================================
# LongTermMemory — ChromaDB placeholder
# ======================================================================

class TestLongTermMemory:
    def test_instantiation_no_chroma(self):
        """LongTermMemory should instantiate without crashing even without ChromaDB data."""
        from src.memory.long_term import LongTermMemory

        mem = LongTermMemory(chroma_dir="./data/chroma_test")
        assert mem is not None

    def test_add_placeholder(self):
        """In Phase 1, add() should store in an in-memory list fallback."""
        from src.memory.long_term import LongTermMemory

        mem = LongTermMemory(chroma_dir="./data/chroma_test")
        entry = MemoryEntry(
            id="l1", content="用户喜欢冬天", summary="喜欢冬天",
            category=MemoryCategory.PREFERENCE,
        )
        mem.add(entry)
        results = mem.get(query="冬天", k=5)
        assert any(r.id == "l1" for r in results)

    def test_get_empty_returns_empty(self):
        """get() on a fresh, empty LongTermMemory should return empty list."""
        import shutil, tempfile
        from src.memory.long_term import LongTermMemory

        tmp = tempfile.mkdtemp(prefix="chroma_empty_")
        try:
            mem = LongTermMemory(chroma_dir=tmp)
            assert mem.get(query="anything", k=5) == []
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


# ======================================================================
# ImmutableMemory — persona injection
# ======================================================================

class TestImmutableMemory:
    @pytest.fixture
    def persona_path(self):
        return Path(__file__).parent.parent / "config" / "persona.yaml"

    def test_load_from_yaml(self, persona_path):
        """ImmutableMemory should load persona from YAML file."""
        from src.memory.immutable import ImmutableMemory

        mem = ImmutableMemory.from_yaml(persona_path)
        entries = mem.get(query="", k=50)

        assert len(entries) > 0
        # Each trait/boundary/value becomes a MemoryEntry
        contents = " ".join(e.content for e in entries)
        assert "温柔体贴" in contents

    def test_get_always_returns_all(self, persona_path):
        """get() should always return all entries regardless of query."""
        from src.memory.immutable import ImmutableMemory

        mem = ImmutableMemory.from_yaml(persona_path)
        all_entries = mem.get(query="", k=50)
        filtered = mem.get(query="unrelated", k=50)

        assert len(filtered) == len(all_entries)

    def test_add_raises_not_implemented(self, persona_path):
        """ImmutableMemory.add() should raise — it's read-only."""
        from src.memory.immutable import ImmutableMemory

        mem = ImmutableMemory.from_yaml(persona_path)
        entry = MemoryEntry(
            id="x", content="test", summary="test",
            category=MemoryCategory.PROFILE,
        )
        with pytest.raises(NotImplementedError):
            mem.add(entry)
