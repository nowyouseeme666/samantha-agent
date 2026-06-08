"""EmotionState dataclass — valence/arousal emotion model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class EmotionState:
    """Represents the current emotional state using dimensional model.

    Attributes:
        valence: -1.0 (negative) to 1.0 (positive)
        arousal: 0.0 (calm) to 1.0 (excited)
        label: Human-readable emotion label
        confidence: Detection confidence 0.0–1.0
    """

    valence: float = 0.0
    arousal: float = 0.0
    label: str = "平静"
    confidence: float = 0.5

    def __post_init__(self) -> None:
        # Clamp valence to [-1.0, 1.0]
        if self.valence > 1.0:
            self.valence = 1.0
        elif self.valence < -1.0:
            self.valence = -1.0
        # Clamp arousal to [0.0, 1.0]
        if self.arousal > 1.0:
            self.arousal = 1.0
        elif self.arousal < 0.0:
            self.arousal = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "valence": self.valence,
            "arousal": self.arousal,
            "label": self.label,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "EmotionState":
        return cls(
            valence=data.get("valence", 0.0),
            arousal=data.get("arousal", 0.0),
            label=data.get("label", "平静"),
            confidence=data.get("confidence", 0.5),
        )
