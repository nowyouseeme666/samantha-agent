"""BaseMemory — abstract base class for the three-layer memory system."""

from __future__ import annotations

from abc import ABC, abstractmethod

from src.schemas.memory import MemoryEntry


class BaseMemory(ABC):
    """Abstract memory layer.

    Each concrete memory layer must implement add() and get().
    """

    @abstractmethod
    def add(self, entry: MemoryEntry) -> None:
        """Store a memory entry."""
        ...

    @abstractmethod
    def get(self, query: str, k: int = 5) -> list[MemoryEntry]:
        """Retrieve relevant memory entries."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries from this memory layer."""
        ...
