"""Keyword-based emotion rule engine.

Maps Chinese emotion keywords to valence/arousal/label tuples.
Used by EmotionDetector as the fast first-pass before LLM fallback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Negation words in Chinese that invert the meaning of emotion keywords
NEGATION_WORDS: set[str] = {"\u4e0d", "\u6ca1", "\u522b", "\u4e0d\u8981", "\u6ca1\u6709", "\u4e0d\u4f1a", "\u4e0d\u80fd", "\u4e0d\u662f", "\u4ece\u6765\u4e0d", "\u518d\u4e5f\u4e0d"}

# Map negated emotions to their opposite label
OPPOSITE_LABEL: dict[str, str] = {
    "happy": "sad",
    "sad": "neutral",
    "angry": "neutral",
    "anxious": "neutral",
    "tired": "neutral",
    "neutral": "neutral",
}

# Opposite valence/arousal for negated emotions
OPPOSITE_VALENCE: dict[str, float] = {
    "happy": -0.3,
    "sad": 0.2,
    "angry": 0.0,
    "anxious": 0.0,
    "tired": 0.1,
    "neutral": 0.0,
}

OPPOSITE_AROUSAL: dict[str, float] = {
    "happy": -0.2,
    "sad": 0.1,
    "angry": -0.2,
    "anxious": -0.3,
    "tired": 0.2,
    "neutral": 0.0,
}


@dataclass(frozen=True)
class EmotionRule:
    """A single emotion rule: keywords to emotional dimensions."""

    keywords: tuple[str, ...]
    valence: float
    arousal: float
    label: str
    confidence: float = 0.85  # rule matches are high-confidence


# ---------------------------------------------------------------------------
# Rule table -- ordered so more specific / intense emotions match first.
# Each rule has a confidence of 0.85 (strong but not certain).
# ---------------------------------------------------------------------------

EMOTION_RULES: list[EmotionRule] = [
    EmotionRule(
        keywords=("\u5f00\u5fc3", "\u9ad8\u5174", "\u54c8\u54c8", "\u592a\u597d\u4e86", "\u592a\u68d2\u4e86", "\u597d\u5f00\u5fc3", "\u5feb\u4e50"),
        valence=0.7,
        arousal=0.6,
        label="happy",
    ),
    EmotionRule(
        keywords=("\u96be\u8fc7", "\u4f24\u5fc3", "\u54ed", "\u5931\u843d", "\u597d\u96be\u8fc7", "\u60f3\u54ed", "\u60b2\u4f24", "\u5fc3\u788e"),
        valence=-0.6,
        arousal=-0.3,
        label="sad",
    ),
    EmotionRule(
        keywords=("\u751f\u6c14", "\u6124\u6012", "\u706b", "\u8ba8\u538c", "\u706b\u5927", "\u6c14\u6b7b", "\u6df7\u86cb", "\u53d7\u4e0d\u4e86"),
        valence=-0.7,
        arousal=0.7,
        label="angry",
    ),
    EmotionRule(
        keywords=("\u7126\u8651", "\u62c5\u5fc3", "\u7d27\u5f20", "\u5bb3\u6015", "\u597d\u7126\u8651", "\u597d\u62c5\u5fc3", "\u4e0d\u5b89", "\u614c"),
        valence=-0.5,
        arousal=0.6,
        label="anxious",
    ),
    EmotionRule(
        keywords=("\u7d2f", "\u75b2\u60eb", "\u56f0", "\u6ca1\u7cbe\u795e", "\u597d\u7d2f", "\u7d2f\u6b7b", "\u4e4f\u529b", "\u7b4b\u75b2\u529b\u5c3d"),
        valence=-0.3,
        arousal=-0.5,
        label="tired",
    ),
    EmotionRule(
        keywords=("\u5e73\u9759", "\u8fd8\u597d", "\u4e00\u822c", "\u6ca1\u4e8b", "\u8fd8\u884c", "\u6b63\u5e38", "\u5c31\u8fd9\u6837", "\u6ca1\u5565"),
        valence=0.0,
        arousal=-0.3,
        label="neutral",
    ),
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _has_negation(text: str, keyword: str, start: int | None = None) -> bool:
    """Check if *keyword* at *start* position is negated by a preceding word."""
    idx = start if start is not None else text.find(keyword)
    if idx < 0:
        return False
    # Look back up to 5 characters for a negation word
    lookback_start = max(0, idx - 5)
    prefix = text[lookback_start:idx]
    for neg in NEGATION_WORDS:
        if neg in prefix:
            return True
    return False


def _apply_negation(rule: EmotionRule) -> EmotionRule:
    """Return an inverted EmotionRule for a negated keyword match."""
    return EmotionRule(
        keywords=rule.keywords,
        valence=OPPOSITE_VALENCE.get(rule.label, 0.0),
        arousal=OPPOSITE_AROUSAL.get(rule.label, 0.0),
        label=OPPOSITE_LABEL.get(rule.label, "neutral"),
        confidence=0.6,  # negation detection is less confident
    )


def match_rules(text: str) -> EmotionRule | None:
    """Return the first matching EmotionRule for *text*, or None.

    Matching is case-insensitive and keyword-order-based: earlier rules
    in EMOTION_RULES take priority.
    Negation handling: if a keyword is preceded by a negation word,
    the emotion is inverted (e.g. "not happy" -> sad instead of happy).
    """
    if not text:
        return _neutral_default()

    for rule in EMOTION_RULES:
        for kw in rule.keywords:
            idx = text.find(kw)
            if idx >= 0:
                if _has_negation(text, kw, idx):
                    # Keyword found but negated -- invert the emotion
                    return _apply_negation(rule)
                return rule

    return None


def _neutral_default() -> EmotionRule:
    """Return a low-confidence neutral default rule."""
    return EmotionRule(
        keywords=(),
        valence=0.0,
        arousal=0.0,
        label="neutral",
        confidence=0.3,
    )


def rule_to_emotion_state(rule: EmotionRule) -> dict[str, Any]:
    """Convert an EmotionRule to an EmotionState dict."""
    return {
        "valence": rule.valence,
        "arousal": max(0.0, rule.arousal),  # clamp arousal floor to 0
        "label": rule.label,
        "confidence": rule.confidence,
    }
