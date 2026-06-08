"""EmotionMonitor — tracks emotional risk across conversation turns.

Counts consecutive negative-emotion turns.  When the streak exceeds
the configured risk_threshold, the monitor escalates to 'warning'.
Positive or neutral emotions reset the streak.
"""

from __future__ import annotations


class EmotionMonitor:
    """Monitors consecutive negative emotion turns for risk escalation."""

    def __init__(self, risk_threshold: int = 3) -> None:
        self.risk_threshold = risk_threshold
        self._negative_streak: int = 0
        self._current_risk: str = "normal"

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def current_risk(self) -> str:
        return self._current_risk

    @property
    def negative_streak(self) -> int:
        return self._negative_streak

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, emotion_state: object) -> str:
        """Feed a new EmotionState into the monitor.

        Returns the current risk level after the update ('normal' or 'warning').
        """
        valence = getattr(emotion_state, "valence", 0.0)

        if valence < 0.0:
            self._negative_streak += 1
        else:
            self._negative_streak = 0

        # Re-evaluate risk
        if self._negative_streak >= self.risk_threshold:
            self._current_risk = "warning"
        else:
            self._current_risk = "normal"

        return self._current_risk

    def reset(self) -> None:
        """Clear all counters and return to 'normal'."""
        self._negative_streak = 0
        self._current_risk = "normal"
