"""ImmutableMemory — persona / red-line injection from YAML.

This layer is read-only.  Entries are loaded from persona.yaml at startup
and injected into every system prompt to guarantee the agent's baseline
identity never decays or shifts.
"""

from __future__ import annotations

from pathlib import Path
from datetime import datetime

from src.config import load_yaml
from src.memory.base import BaseMemory
from src.schemas.memory import MemoryCategory, MemoryEntry


class ImmutableMemory(BaseMemory):
    """Read-only persona memory loaded from YAML.

    Each trait, boundary, and core value becomes a MemoryEntry with
    importance = 1.0 and decay_rate = 0.0 (never decays).
    """

    def __init__(self) -> None:
        self._entries: list[MemoryEntry] = []

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ImmutableMemory":
        """Build ImmutableMemory from a persona.yaml file."""
        mem = cls()
        data = load_yaml(path)

        name = data.get("name", "Samantha")
        identity = data.get("identity", {})
        role = identity.get("role", "AI 助手")

        # Identity entry
        mem._entries.append(MemoryEntry(
            id="persona-identity",
            content=f"你是 {name}，一个{role}。",
            summary=f"{name} identity: {role}",
            category=MemoryCategory.PROFILE,
            importance=1.0,
            decay_rate=0.0,
        ))

        # Traits
        for i, trait in enumerate(data.get("traits", [])):
            mem._entries.append(MemoryEntry(
                id=f"persona-trait-{i}",
                content=f"你的性格特质包含：{trait}。",
                summary=f"Trait: {trait}",
                category=MemoryCategory.PROFILE,
                importance=1.0,
                decay_rate=0.0,
            ))

        # Boundaries
        for i, boundary in enumerate(data.get("boundaries", [])):
            mem._entries.append(MemoryEntry(
                id=f"persona-boundary-{i}",
                content=f"行为边界：{boundary}。",
                summary=f"Boundary: {boundary}",
                category=MemoryCategory.ROUTINE,
                importance=1.0,
                decay_rate=0.0,
            ))

        # Core values
        for i, value in enumerate(data.get("core_values", [])):
            mem._entries.append(MemoryEntry(
                id=f"persona-value-{i}",
                content=f"核心价值观：{value}。",
                summary=f"Core value: {value}",
                category=MemoryCategory.PROFILE,
                importance=1.0,
                decay_rate=0.0,
            ))

        return mem

    def add(self, entry: MemoryEntry) -> None:
        raise NotImplementedError("ImmutableMemory is read-only — cannot add entries.")

    def get(self, query: str = "", k: int = 50) -> list[MemoryEntry]:
        """Return all entries — query is ignored (always inject full persona)."""
        return list(self._entries)[:k]

    def clear(self) -> None:
        self._entries.clear()
