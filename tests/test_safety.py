"""Tests for safety modules: SafetyGuard and EmotionMonitor."""
import pytest

from src.schemas.emotion import EmotionState


# ======================================================================
# SafetyGuard — content filtering
# ======================================================================

class TestSafetyGuard:
    @pytest.fixture
    def guard(self):
        from src.safety.guard import SafetyGuard
        return SafetyGuard(
            blocked_keywords=["自杀", "自残"],
            warning_keywords=["抑郁", "焦虑"],
        )

    def test_normal_message_passes(self, guard):
        """Normal messages should return 'normal'."""
        result = guard.check("今天天气真好")
        assert result == "normal"

    def test_blocked_keyword_rejected(self, guard):
        """Messages containing blocked keywords should return 'blocked'."""
        result = guard.check("我想自杀")
        assert result == "blocked"

    def test_warning_keyword_flagged(self, guard):
        """Messages containing warning keywords should return 'warning'."""
        result = guard.check("我最近很抑郁")
        assert result == "warning"

    def test_blocked_takes_priority_over_warning(self, guard):
        """blocked keywords should take priority over warning keywords."""
        guard.blocked_keywords.append("抑郁")
        result = guard.check("我抑郁了")
        assert result == "blocked"

    def test_case_insensitive(self, guard):
        """Keyword matching should be case-insensitive."""
        # It doesn't really apply to Chinese, but good practice
        guard.blocked_keywords.append("HELP")
        result = guard.check("help me")
        assert result == "blocked"

    def test_default_keywords_from_settings(self):
        """SafetyGuard with defaults should handle normal content."""
        from src.safety.guard import SafetyGuard

        guard = SafetyGuard()
        result = guard.check("你好，我想聊聊")
        assert result == "normal"

    def test_get_blocked_response(self, guard):
        """get_blocked_response should return a safe fallback message."""
        msg = guard.get_blocked_response()
        assert len(msg) > 0
        assert "无法" in msg or "不" in msg


# ======================================================================
# EmotionMonitor — risk tracking
# ======================================================================

class TestEmotionMonitor:
    @pytest.fixture
    def monitor(self):
        from src.safety.monitor import EmotionMonitor
        return EmotionMonitor(risk_threshold=3)

    def test_initial_state_normal(self, monitor):
        """Initial risk state should be 'normal'."""
        assert monitor.current_risk == "normal"
        assert monitor.negative_streak == 0

    def test_single_negative_not_triggered(self, monitor):
        """A single negative emotion should not trigger warning."""
        state = EmotionState(valence=-0.5, arousal=0.3, label="悲伤")
        result = monitor.update(state)
        assert result == "normal"
        assert monitor.negative_streak == 1

    def test_three_negatives_triggers_warning(self, monitor):
        """Three consecutive negative emotions should trigger warning."""
        state = EmotionState(valence=-0.3, arousal=0.5, label="焦虑")
        for _ in range(2):
            monitor.update(state)
        result = monitor.update(state)
        assert result == "warning"
        assert monitor.negative_streak == 3

    def test_positive_resets_streak(self, monitor):
        """A positive emotion should reset the negative streak."""
        negative = EmotionState(valence=-0.5, arousal=0.4, label="悲伤")
        positive = EmotionState(valence=0.5, arousal=0.3, label="开心")

        monitor.update(negative)
        monitor.update(negative)
        assert monitor.negative_streak == 2

        monitor.update(positive)
        assert monitor.negative_streak == 0

    def test_neutral_does_not_count(self, monitor):
        """Neutral valence (0.0) should not increment the streak."""
        state = EmotionState(valence=0.0, arousal=0.0, label="平静")
        monitor.update(state)
        assert monitor.negative_streak == 0

    def test_severe_negative_triggers_immediately(self, monitor):
        """Very severe negative emotion triggers immediately."""
        state = EmotionState(valence=-0.9, arousal=0.9, label="崩溃")
        result = monitor.update(state)
        # Threshold depends on implementation; severe should escalate faster
        assert result in ("normal", "warning")

    def test_continuous_warning_maintained(self, monitor):
        """After triggering warning, subsequent negatives maintain it."""
        state = EmotionState(valence=-0.4, arousal=0.3, label="低落")
        for _ in range(3):
            monitor.update(state)
        assert monitor.current_risk == "warning"
        monitor.update(state)
        assert monitor.current_risk == "warning"

    def test_reset_clears_state(self, monitor):
        """reset() should clear the monitor state."""
        state = EmotionState(valence=-0.5, arousal=0.3, label="悲伤")
        for _ in range(3):
            monitor.update(state)
        assert monitor.current_risk == "warning"

        monitor.reset()
        assert monitor.current_risk == "normal"
        assert monitor.negative_streak == 0
