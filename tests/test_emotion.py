"""Tests for emotion detector — src/emotion/detector.py and rules.py."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from src.schemas.emotion import EmotionState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_detector(*, rules_only: bool = False, llm_override: object = None):
    """Build an EmotionDetector for testing.

    When *rules_only* is True the detector is created without an LLM
    client so every detection falls through to the rules layer.
    """
    from src.emotion.detector import EmotionDetector

    if rules_only:
        return EmotionDetector(llm_client=None)
    llm = llm_override
    return EmotionDetector(llm_client=llm)


# ---------------------------------------------------------------------------
# Rules layer tests
# ---------------------------------------------------------------------------


class TestRuleMatch:
    def test_rule_match_happy(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("今天太开心了！")
        assert result.label == "happy"
        assert result.valence > 0.5
        assert result.confidence > 0.5

    def test_rule_match_happy_alternative(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("哈哈太好了")
        assert result.label == "happy"

    def test_rule_match_sad(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("我很难过")
        assert result.label == "sad"
        assert result.valence < -0.3

    def test_rule_match_sad_cry(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("今天哭了一整天")
        assert result.label == "sad"

    def test_rule_match_angry(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("我真的很生气")
        assert result.label == "angry"
        assert result.valence < -0.5
        assert result.arousal > 0.5

    def test_rule_match_anxious(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("明天面试我好焦虑")
        assert result.label == "anxious"
        assert result.valence < 0

    def test_rule_match_tired(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("好累啊没精神")
        assert result.label == "tired"
        assert result.valence < 0
        # arousal is clamped to [0, 1] by EmotionState; tired = low arousal
        assert result.arousal <= 0.1

    def test_rule_match_neutral(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("今天天气不错")
        assert result.label == "neutral"

    def test_rule_match_neutral_other(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("还好吧一般般")
        assert result.label == "neutral"


# ---------------------------------------------------------------------------
# LLM fallback tests
# ---------------------------------------------------------------------------


class TestLLMFallback:
    def test_llm_called_when_no_rule_match(self):
        """When no keyword matches, the detector should fall back to LLM."""
        mock_llm = MagicMock()
        mock_llm.chat.return_value = '{"valence": 0.1, "arousal": 0.2, "label": "neutral"}'
        detector = _make_detector(llm_override=mock_llm)

        result = detector.detect("xyz123完全没有匹配的词")
        # The LLM should have been called
        mock_llm.chat.assert_called_once()
        assert isinstance(result, EmotionState)

    def test_llm_fallback_parses_json(self):
        mock_llm = MagicMock()
        mock_llm.chat.return_value = (
            '{"valence": 0.8, "arousal": 0.7, "label": "happy"}'
        )
        detector = _make_detector(llm_override=mock_llm)

        result = detector.detect("xyz456")
        assert result.label == "happy"
        assert result.valence == 0.8
        assert result.arousal == 0.7


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEmotionEdgeCases:
    def test_valence_clamped(self):
        """Valence must always be in [-1, 1]."""
        detector = _make_detector(rules_only=True)
        result = detector.detect("我很难过")
        assert -1.0 <= result.valence <= 1.0

    def test_arousal_clamped(self):
        """Arousal must always be in [0, 1]."""
        detector = _make_detector(rules_only=True)
        result = detector.detect("我很生气")
        assert 0.0 <= result.arousal <= 1.0

    def test_empty_message_returns_neutral(self):
        detector = _make_detector(rules_only=True)
        result = detector.detect("")
        assert result.label == "neutral"

    def test_llm_failure_returns_neutral(self):
        """When LLM call fails, return a neutral default."""
        mock_llm = MagicMock()
        mock_llm.chat.side_effect = RuntimeError("API error")
        detector = _make_detector(llm_override=mock_llm)

        result = detector.detect("xyz_no_match_789")
        assert result.label == "neutral"
        assert result.valence == 0.0

    def test_rules_only_detector_returns_neutral_for_unknown(self):
        """Without an LLM, unknown text gets neutral."""
        detector = _make_detector(rules_only=True)
        result = detector.detect("asdf qwer zxcv")
        assert result.label == "neutral"
        assert result.confidence < 0.7
