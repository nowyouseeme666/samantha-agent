"""Configuration system: pydantic Settings model and YAML loaders.

SamanthaSettings reads global settings from config/settings.yaml with
environment variable overrides via pydantic-settings.

PersonaConfig, RulesConfig, and ToolsConfig parse their respective YAML
files and provide helper methods for prompt assembly.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


# ---------------------------------------------------------------------------
# YAML utility
# ---------------------------------------------------------------------------

def load_yaml(path: str | Path) -> dict[str, Any]:
    """Load and parse a YAML file.  Raises FileNotFoundError if missing."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


# ---------------------------------------------------------------------------
# Settings model (pydantic-settings)
# ---------------------------------------------------------------------------

class SamanthaSettings(BaseSettings):
    """Global settings backed by config/settings.yaml.

    Fields with an env prefix can be overridden via environment variables.
    ``DEEPSEEK_API_KEY`` is read from the environment only (never from YAML).
    """

    # -- LLM --
    llm_model: str = "deepseek-chat"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 2048

    # -- Memory --
    memory_short_term_max_rounds: int = 20
    memory_long_term_chroma_dir: str = "./data/chroma"
    memory_long_term_collection_name: str = "samantha_memory"
    memory_long_term_retrieval_k: int = 5
    memory_long_term_similarity_threshold: float = 0.5

    # -- Safety --
    safety_emotion_risk_threshold: int = 3
    safety_blocked_keywords: list[str] = Field(default_factory=list)
    safety_warning_keywords: list[str] = Field(default_factory=list)

    # -- Dialogue --
    dialogue_max_response_length: int = 500
    dialogue_fallback_message: str = "我在听，你想跟我说说你的感受吗？"

    # -- Logging --
    logging_level: str = "INFO"
    logging_format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function} | {message}"
    logging_rotation: str = "10 MB"
    logging_retention: str = "7 days"

    # -- Secrets (env-only) --
    deepseek_api_key: str = Field(
        default="",
        description="DeepSeek API key — set via DEEPSEEK_API_KEY env var only.",
    )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @model_validator(mode="before")
    @classmethod
    def _load_from_yaml(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Merge values from _yaml_config into the model on init."""
        yaml_path = values.pop("_yaml_config", None)
        persona_dir = values.pop("_persona_dir", None)

        if yaml_path is None:
            return values

        yaml_data = load_yaml(yaml_path)

        # Flatten YAML sections into flat field names
        mapping = {
            # llm
            "llm_model": ("llm", "model"),
            "llm_temperature": ("llm", "temperature"),
            "llm_max_tokens": ("llm", "max_tokens"),
            # memory.short_term
            "memory_short_term_max_rounds": ("memory", "short_term", "max_rounds"),
            # memory.long_term
            "memory_long_term_chroma_dir": ("memory", "long_term", "chroma_dir"),
            "memory_long_term_collection_name": ("memory", "long_term", "collection_name"),
            "memory_long_term_retrieval_k": ("memory", "long_term", "retrieval_k"),
            "memory_long_term_similarity_threshold": ("memory", "long_term", "similarity_threshold"),
            # safety
            "safety_emotion_risk_threshold": ("safety", "emotion_risk_threshold"),
            "safety_blocked_keywords": ("safety", "blocked_keywords"),
            "safety_warning_keywords": ("safety", "warning_keywords"),
            # dialogue
            "dialogue_max_response_length": ("dialogue", "max_response_length"),
            "dialogue_fallback_message": ("dialogue", "fallback_message"),
            # logging
            "logging_level": ("logging", "level"),
            "logging_format": ("logging", "format"),
            "logging_rotation": ("logging", "rotation"),
            "logging_retention": ("logging", "retention"),
        }

        for field_name, keys in mapping.items():
            if field_name not in values or values[field_name] == cls.model_fields[field_name].default:
                value = yaml_data
                for k in keys:
                    value = value.get(k, {}) if isinstance(value, dict) else {}
                if value and not isinstance(value, dict):
                    values[field_name] = value

        return values

    def __str__(self) -> str:
        """Human-readable representation with API key masked."""
        lines = ["SamanthaSettings:"]
        for field_name in type(self).model_fields:
            value = getattr(self, field_name)
            if "api_key" in field_name and value:
                value = value[:7] + "***"
            lines.append(f"  {field_name}: {value}")
        return "\n".join(lines)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "allow",
    }


# ---------------------------------------------------------------------------
# PersonaConfig
# ---------------------------------------------------------------------------

class PersonaConfig:
    """Parsed persona.yaml — Samantha's immutable identity."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PersonaConfig":
        return cls(load_yaml(path))

    @property
    def name(self) -> str:
        return self._data.get("name", "")

    @property
    def traits(self) -> list[str]:
        return self._data.get("traits", [])

    @property
    def boundaries(self) -> list[str]:
        return self._data.get("boundaries", [])

    @property
    def core_values(self) -> list[str]:
        return self._data.get("core_values", [])

    def greeting(self, default: str = "嗯，我在呢~") -> str:
        """Return a greeting message from config, falling back to *default*."""
        greeting_data = self._data.get("greeting", {})
        if isinstance(greeting_data, dict):
            return greeting_data.get("default", default)
        return default

    def to_system_text(self) -> str:
        """Format persona as a system prompt block."""
        parts = [f"你是 {self.name}，一个{self._data.get('identity', {}).get('role', 'AI 助手')}。"]
        if self.traits:
            parts.append("性格特质：" + "、".join(self.traits) + "。")
        if self.boundaries:
            parts.append("行为边界：" + "；".join(self.boundaries) + "。")
        if self.core_values:
            parts.append("核心价值观：" + "；".join(self.core_values) + "。")
        return " ".join(parts)


# ---------------------------------------------------------------------------
# RulesConfig
# ---------------------------------------------------------------------------

class RulesConfig:
    """Parsed rules.yaml — conversation rules & safety red-lines."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RulesConfig":
        return cls(load_yaml(path))

    @property
    def red_lines(self) -> list[str]:
        return self._data.get("safety", {}).get("red_lines", [])

    @property
    def escalation_trigger_count(self) -> int:
        return self._data.get("safety", {}).get("escalation", {}).get("trigger_count", 3)

    @property
    def escalation_response(self) -> str:
        return self._data.get("safety", {}).get("escalation", {}).get("response", "")

    def to_system_text(self) -> str:
        """Format safety rules as a system prompt block."""
        parts = []
        if self.red_lines:
            parts.append("安全红线（绝对不可违反）：\n- " + "\n- ".join(self.red_lines))
        escalation = self._data.get("safety", {}).get("escalation", {})
        if escalation.get("trigger_count"):
            parts.append(
                f"当连续检测到 {escalation['trigger_count']} 轮负面情绪时，"
                f"回复：「{escalation.get('response', '')}」"
            )
        return "\n".join(parts) if parts else ""


# ---------------------------------------------------------------------------
# ToolsConfig
# ---------------------------------------------------------------------------

class ToolsConfig:
    """Parsed tools.yaml — tool definitions."""

    def __init__(self, data: dict[str, Any]) -> None:
        raw = data.get("tools", [])
        self.tools: list[dict[str, Any]] = list(raw)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "ToolsConfig":
        return cls(load_yaml(path))

    def enabled_tools(self) -> list[dict[str, Any]]:
        """Return only tools where enabled is True."""
        return [t for t in self.tools if t.get("enabled", False)]

    def get_tool(self, name: str) -> dict[str, Any] | None:
        """Return a tool definition by name, or None."""
        for t in self.tools:
            if t.get("name") == name:
                return dict(t)
        return None
