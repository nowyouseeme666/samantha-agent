"""MemoryEntry dataclass and MemoryCategory enum."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MemoryCategory(str, Enum):
    PREFERENCE = "preference"
    EVENT = "event"
    EMOTION = "emotion"
    PROFILE = "profile"
    ROUTINE = "routine"


@dataclass
class MemoryEntry:
    """A single memory entry in the three-layer memory system."""

    id: str
    content: str
    summary: str
    category: MemoryCategory
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    decay_rate: float = 0.01

    def __post_init__(self) -> None:
        # Clamp importance to [0.0, 1.0]
        if self.importance > 1.0:
            self.importance = 1.0
        elif self.importance < 0.0:
            self.importance = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "summary": self.summary,
            "category": self.category.value,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "decay_rate": self.decay_rate,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryEntry":
        return cls(
            id=data["id"],
            content=data["content"],
            summary=data["summary"],
            category=MemoryCategory(data["category"]),
            importance=data.get("importance", 0.5),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data
            else datetime.now(),
            last_accessed=datetime.fromisoformat(data["last_accessed"])
            if "last_accessed" in data
            else datetime.now(),
            decay_rate=data.get("decay_rate", 0.01),
        )
