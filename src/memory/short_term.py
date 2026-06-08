"""ShortTermMemory — sliding-window conversation buffer."""

from __future__ import annotations

from collections import deque

from src.memory.base import BaseMemory
from src.schemas.memory import MemoryEntry


class ShortTermMemory(BaseMemory):
    """Fixed-size sliding window of recent conversation rounds.

    The underlying deque maintains entries in insertion order;
    ``get()`` returns them **most-recent-first** to match agent
    prompting conventions.
    """

    def __init__(self, max_rounds: int = 20) -> None:
        self._max_rounds = max_rounds
        self._buffer: deque[MemoryEntry] = deque(maxlen=max_rounds)

    def add(self, entry: MemoryEntry) -> None:
        self._buffer.append(entry)

    def get(self, query: str = "", k: int = 5) -> list[MemoryEntry]:
        # Return most-recent-first, capped at k
        return list(reversed(self._buffer))[:k]

    def clear(self) -> None:
        self._buffer.clear()

    def __len__(self) -> int:
        return len(self._buffer)
