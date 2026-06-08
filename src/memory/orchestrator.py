"""MemoryOrchestrator — fuses three-layer memory with decay scoring.

Priority ordering:
    1. Immutable memory (always first, importance=1.0, never decays)
    2. Recent long-term (≤ 7 days, scored by importance × decay)
    3. Older long-term (> 7 days)
    4. Short-term (fills gaps when long-term is insufficient)

Within the same category, only the top-3 entries by score are kept.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.schemas.emotion import EmotionState
    from src.schemas.memory import MemoryEntry
    from src.memory.short_term import ShortTermMemory
    from src.memory.long_term import LongTermMemory
    from src.memory.immutable import ImmutableMemory


@dataclass
class MemoryContext:
    """The assembled memory context for a single prompt turn."""

    entries: list["MemoryEntry"] = field(default_factory=list)
    total_hits: int = 0

    def top_summaries(self, k: int = 5) -> list[str]:
        """Return summaries of the top-k entries for prompt injection."""
        return [e.summary for e in self.entries[:k]]


class MemoryOrchestrator:
    """Fuses short-term, long-term, and immutable memory layers.

    Uses exponential decay scoring for long-term memories:
        score = importance × exp(-decay_rate × days_since_access)
    """

    RECENT_DAYS = 7  # entries within 7 days are "recent"

    def __init__(
        self,
        short_term: "ShortTermMemory",
        long_term: "LongTermMemory",
        immutable: "ImmutableMemory",
    ) -> None:
        self.short_term = short_term
        self.long_term = long_term
        self.immutable = immutable

    # ------------------------------------------------------------------
    def gather(
        self,
        query: str,
        current_emotion: "EmotionState",
    ) -> MemoryContext:
        """Collect and rank memories from all three layers.

        Returns a MemoryContext with entries sorted by priority.
        """
        # 1. Collect from each layer
        immutable_entries = self.immutable.get(query)  # always returns all
        long_term_entries = self.long_term.get(query, k=10)
        short_term_entries = self.short_term.get(query, k=6)

        # 2. Score long-term entries with decay
        scored_lt: list[tuple[float, "MemoryEntry"]] = []
        for entry in long_term_entries:
            score = self._calc_decay_score(entry)
            scored_lt.append((score, entry))

        # 3. Split into recent and old
        now = datetime.now()
        recent_cutoff = now - timedelta(days=self.RECENT_DAYS)

        recent_lt: list[tuple[float, "MemoryEntry"]] = []
        old_lt: list[tuple[float, "MemoryEntry"]] = []
        for score, entry in scored_lt:
            if entry.last_accessed >= recent_cutoff:
                recent_lt.append((score, entry))
            else:
                old_lt.append((score, entry))

        # Sort each group by score descending
        recent_lt.sort(key=lambda x: x[0], reverse=True)
        old_lt.sort(key=lambda x: x[0], reverse=True)

        # 4. Assemble in priority order
        result_entries: list["MemoryEntry"] = []

        # Tier 0: Immutable (always first, no decay)
        result_entries.extend(immutable_entries)

        # Tier 1: Recent long-term
        result_entries.extend(entry for _, entry in recent_lt)

        # Tier 2: Older long-term
        result_entries.extend(entry for _, entry in old_lt)

        # Tier 3: Short-term (only used to supplement)
        # Avoid duplicating entries that are already in long-term
        existing_ids = {e.id for e in result_entries}
        for entry in short_term_entries:
            if entry.id not in existing_ids:
                result_entries.append(entry)

        # 5. Dedup by category (keep top-3 per category)
        result_entries = self._dedup_by_category(result_entries)

        return MemoryContext(
            entries=result_entries,
            total_hits=len(result_entries),
        )

    # ------------------------------------------------------------------
    # Decay scoring
    # ------------------------------------------------------------------

    def _calc_decay_score(self, entry: "MemoryEntry") -> float:
        """Compute decay-weighted importance score.

        score = importance × exp(-decay_rate × days_since_access)

        Immutable-like entries (importance >= 1.0, decay_rate == 0)
        always score their full importance value.
        """
        days = (datetime.now() - entry.last_accessed).total_seconds() / 86400.0
        return entry.importance * math.exp(-entry.decay_rate * days)

    # ------------------------------------------------------------------
    # Deduplication
    # ------------------------------------------------------------------

    @staticmethod
    def _dedup_by_category(
        entries: list["MemoryEntry"],
    ) -> list["MemoryEntry"]:
        """Within each category, keep only the top-3 entries.

        Persona entries (id starting with 'persona-') are never dropped.
        The order of entries is preserved otherwise.
        """
        from collections import OrderedDict

        # Separate persona (immutable) entries
        persona = [e for e in entries if e.id.startswith("persona-")]
        mutable = [e for e in entries if not e.id.startswith("persona-")]

        # Group mutable by category while preserving insertion order
        by_cat: dict[str, list["MemoryEntry"]] = OrderedDict()
        for entry in mutable:
            cat = entry.category.value if hasattr(entry.category, "value") else str(entry.category)
            by_cat.setdefault(cat, []).append(entry)

        # Top-3 per category
        kept: list["MemoryEntry"] = list(persona)
        for _cat, cat_entries in by_cat.items():
            kept.extend(cat_entries[:3])

        return kept
