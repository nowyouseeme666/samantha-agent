"""PromptBuilder — assembles system and human messages for the LLM.

Follows the prompt assembly strategy from the design doc:

  System Message:
    [固化人格 persona.yaml]
    [安全红线 rules.yaml]
    [可用工具列表]

  Human Message:
    [长期记忆摘要 (top-k)]
    [近期对话 (recent N rounds)]
    [用户当前消息]
"""

from __future__ import annotations

from pathlib import Path

from src.config import PersonaConfig, RulesConfig


class PromptBuilder:
    """Builds System and Human messages for the DeepSeek LLM call."""

    def __init__(
        self,
        persona_path: str | Path | None = None,
        rules_path: str | Path | None = None,
    ) -> None:
        self._persona: PersonaConfig | None = None
        self._rules: RulesConfig | None = None

        if persona_path is not None:
            self._persona = PersonaConfig.from_yaml(persona_path)
        if rules_path is not None:
            self._rules = RulesConfig.from_yaml(rules_path)

    # ------------------------------------------------------------------
    # System message
    # ------------------------------------------------------------------

    def build_system(
        self,
        emotion_state: dict | None = None,
        tools: list[dict] | None = None,
    ) -> str:
        """Assemble the system prompt block."""
        parts: list[str] = []

        # 1. Persona (immutable identity)
        if self._persona is not None:
            parts.append(self._persona.to_system_text())

        # 2. Safety red-lines
        if self._rules is not None:
            rules_text = self._rules.to_system_text()
            if rules_text:
                parts.append(rules_text)

        # 3. Current emotion state
        if emotion_state and emotion_state.get("label"):
            parts.append(
                f"当前情绪状态：{emotion_state['label']} "
                f"(效价={emotion_state.get('valence', 0):+.1f}, "
                f"唤醒度={emotion_state.get('arousal', 0):.1f})。"
                f"请根据情绪状态调整回复语气。"
            )

        # 4. Available tools
        if tools:
            lines = ["你可以使用以下工具来帮助用户："]
            for t in tools:
                desc = t.get("description", "")
                lines.append(f"  - {t['name']}: {desc}")
            lines.append(
                "重要规则：当用户的问题可以通过以上工具解决时（如查询天气、搜索记忆、"
                "设置提醒、推荐音乐等），你必须调用对应的工具函数来获取真实数据。"
                "不要回复说你无法获取这些信息或建议用户使用其他方式——你确实拥有这些能力。"
            )
            parts.append("\n".join(lines))

        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Human / user message
    # ------------------------------------------------------------------

    def build_user(
        self,
        long_term_memories: list[str] | None = None,
        recent_history: list[str] | None = None,
        current_message: str = "",
    ) -> str:
        """Assemble the human message block by layering memories → history → current."""
        blocks: list[str] = []

        # 1. Long-term memory summaries
        if long_term_memories:
            blocks.append("【相关记忆】\n" + "\n".join(f"- {m}" for m in long_term_memories))

        # 2. Recent conversation history
        if recent_history:
            blocks.append("【近期对话】\n" + "\n".join(recent_history))

        # 3. Current user message
        blocks.append(f"【用户消息】\n{current_message}")

        return "\n\n".join(blocks)
