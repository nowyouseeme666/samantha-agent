"""EmotionDetector — hybrid rule + LLM emotion detection.

Architecture:
    User input → [rule match] → confidence >= 0.7? → yes → EmotionState
                                  ↓ no
                             [LLM analysis] → EmotionState

Rules provide fast, high-confidence detection for explicit emotion words.
The LLM fallback handles subtle, implicit, or mixed-emotion expressions.
"""

from __future__ import annotations

import json
from typing import Any

from src.emotion.rules import (
    EMOTION_RULES,
    EmotionRule,
    match_rules,
    rule_to_emotion_state,
)
from src.schemas.emotion import EmotionState


class EmotionDetector:
    """Detect emotion from user text using rules first, LLM as fallback."""

    RULE_CONFIDENCE_THRESHOLD = 0.7

    def __init__(self, llm_client: object | None = None) -> None:
        """*llm_client* must expose a ``chat(message, system_prompt)`` method."""
        self._llm = llm_client

    # ------------------------------------------------------------------
    def detect(self, message: str) -> EmotionState:
        """Detect the emotional content of *message*.

        Returns an EmotionState — guaranteed to have clamped valence
        and arousal.
        """
        # 1. Try rule matching
        rule = match_rules(message)
        if rule is not None and rule.confidence >= self.RULE_CONFIDENCE_THRESHOLD:
            return EmotionState.from_dict(rule_to_emotion_state(rule))

        # 2. If we have a low-confidence rule and no LLM, return it as-is
        if self._llm is None:
            if rule is not None:
                return EmotionState.from_dict(rule_to_emotion_state(rule))
            return EmotionState(
                valence=0.0, arousal=0.0, label="neutral", confidence=0.3
            )

        # 3. LLM fallback
        return self._llm_detect(message)

    # ------------------------------------------------------------------
    # LLM fallback
    # ------------------------------------------------------------------

    def _llm_detect(self, message: str) -> EmotionState:
        """Use the LLM to analyse emotion and return an EmotionState."""
        system_prompt = (
            "你是一个情绪分析助手。分析用户消息的情绪，只返回一个JSON对象，"
            "包含以下字段：\n"
            "- valence: 效价，范围 -1.0（极度负面）到 1.0（极度正面）\n"
            "- arousal: 唤醒度，范围 0.0（平静）到 1.0（激动）\n"
            '- label: 情绪标签，必须是以下之一: "happy", "sad", "angry", "anxious", "tired", "neutral"\n'
            "只返回JSON，不要返回其他内容。"
        )

        try:
            raw = self._llm.chat(message=message, system_prompt=system_prompt)
            return self._parse_llm_response(raw)
        except Exception:
            return EmotionState(
                valence=0.0, arousal=0.0, label="neutral", confidence=0.3
            )

    def _parse_llm_response(self, raw: str) -> EmotionState:
        """Parse the LLM's JSON response into an EmotionState."""
        # Strip possible markdown code fences
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[-1]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

        data = json.loads(text)
        return EmotionState.from_dict(data)
