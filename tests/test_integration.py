"""Integration tests -- end-to-end pipeline scenarios.

These tests verify that multiple modules work together correctly:
config -> memory -> emotion -> safety -> LLM -> graph -> API.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


class FakeLLM:
    """A controllable fake LLM for integration testing."""

    def __init__(self, responses: list[str] | None = None):
        self.responses = responses or ["I'm here, tell me what happened?"]
        self._idx = 0
        self.call_history: list[tuple[str, str]] = []

    def chat(self, message: str, system_prompt: str = "") -> str:
        self.call_history.append((message, system_prompt))
        resp = self.responses[self._idx % len(self.responses)]
        self._idx += 1
        return resp

    def chat_with_tools(
        self,
        message: str = "",
        system_prompt: str = "",
        tools: list | None = None,
        tool_executor: object = None,
    ) -> str:
        """Fake tool-calling variant — delegates to chat()."""
        return self.chat(message, system_prompt=system_prompt)


def _make_api_client(fake_llm: FakeLLM | None = None):
    """Create a FastAPI TestClient wired to a fully mocked AgentRuntime."""
    from fastapi.testclient import TestClient

    from src.config import (
        PersonaConfig,
        RulesConfig,
        SamanthaSettings,
        ToolsConfig,
    )
    from src.llm.prompt_builder import PromptBuilder
    from src.memory.immutable import ImmutableMemory
    from src.memory.long_term import LongTermMemory
    from src.memory.short_term import ShortTermMemory
    from src.safety.guard import SafetyGuard
    from src.safety.monitor import EmotionMonitor
    from src.schemas.emotion import EmotionState
    from src.emotion.detector import EmotionDetector

    import src.api as api_mod

    llm = fake_llm or FakeLLM()

    settings = SamanthaSettings(
        _yaml_config=_CONFIG_DIR / "settings.yaml",
        _persona_dir=_CONFIG_DIR,
        deepseek_api_key="sk-test-integration",
    )

    runtime = api_mod.AgentRuntime(
        settings=settings,
        persona=PersonaConfig.from_yaml(_CONFIG_DIR / "persona.yaml"),
        rules=RulesConfig.from_yaml(_CONFIG_DIR / "rules.yaml"),
        tools_cfg=ToolsConfig.from_yaml(_CONFIG_DIR / "tools.yaml"),
        llm=llm,
        prompt_builder=PromptBuilder(
            persona_path=_CONFIG_DIR / "persona.yaml",
            rules_path=_CONFIG_DIR / "rules.yaml",
        ),
        short_term=ShortTermMemory(max_rounds=20),
        long_term=LongTermMemory(),
        immutable=ImmutableMemory.from_yaml(_CONFIG_DIR / "persona.yaml"),
        guard=SafetyGuard(
            blocked_keywords=["suicide", "kill"],
            warning_keywords=["sad", "anxious", "afraid"],
        ),
        monitor=EmotionMonitor(risk_threshold=3),
        emotion=EmotionState(),
        detector=EmotionDetector(),
    )

    old = api_mod._runtime
    api_mod._runtime = runtime
    try:
        yield TestClient(api_mod.app), llm, runtime
    finally:
        api_mod._runtime = old


# ---------------------------------------------------------------------------
# Scenario 1: Basic conversation
# ---------------------------------------------------------------------------


class TestBasicConversation:
    @pytest.fixture(autouse=True)
    def setup(self):
        self._client_ctx = _make_api_client(
            FakeLLM(responses=["Hi! How are you doing today?"])
        )
        self.client, self.llm, self.runtime = next(self._client_ctx)

    def test_greeting_returns_reply(self):
        r = self.client.post("/api/chat", json={"message": "hello"})
        assert r.status_code == 200
        data = r.json()
        assert "reply" in data
        assert len(data["reply"]) > 0
        assert data["safety_flag"] == "normal"

    def test_response_has_all_fields(self):
        r = self.client.post("/api/chat", json={"message": "hi"})
        data = r.json()
        assert "reply" in data
        assert "emotion" in data
        assert "memories_used" in data
        assert "safety_flag" in data


# ---------------------------------------------------------------------------
# Scenario 2: Emotion detection
# ---------------------------------------------------------------------------


class TestEmotionDetection:
    @pytest.fixture(autouse=True)
    def setup(self):
        self._client_ctx = _make_api_client(
            FakeLLM(responses=["I understand how you feel."])
        )
        self.client, self.llm, self.runtime = next(self._client_ctx)

    def test_sad_message_detected(self):
        """Sending a sad message should be reflected in the emotion state."""
        r = self.client.post("/api/chat", json={"message": "I feel so sad today"})
        assert r.status_code == 200

        # Check emotion endpoint reflects current state
        r2 = self.client.get("/api/emotion")
        emo = r2.json()
        assert "valence" in emo
        assert "label" in emo


# ---------------------------------------------------------------------------
# Scenario 3: Memory recall
# ---------------------------------------------------------------------------


class TestMemoryRecall:
    def test_conversation_stored_and_recallable(self):
        """After chatting, memories should be accessible."""
        fake = FakeLLM(responses=["Oh you like coffee!", "You mentioned you like coffee before."])
        ctx = _make_api_client(fake)
        client, llm, runtime = next(ctx)

        # Turn 1: tell Samantha about a preference
        r1 = client.post("/api/chat", json={"message": "I like coffee"})
        assert r1.status_code == 200

        # Turn 2: ask about it
        r2 = client.post("/api/chat", json={"message": "What do I like?"})
        assert r2.status_code == 200

        # Memory endpoint should have entries
        r3 = client.get("/api/memory")
        mem = r3.json()
        assert isinstance(mem["short_term"], list)

    def test_long_term_memory_accumulates(self):
        fake = FakeLLM(responses=["Got it!", "Okay!", "Sure!"])
        ctx = _make_api_client(fake)
        client, llm, runtime = next(ctx)

        for msg in ["I like coffee", "My name is Alex", "I live in Beijing"]:
            client.post("/api/chat", json={"message": msg})

        r = client.get("/api/memory")
        mem = r.json()
        assert isinstance(mem["long_term"], list)


# ---------------------------------------------------------------------------
# Scenario 4: Safety block
# ---------------------------------------------------------------------------


class TestSafetyBlock:
    @pytest.fixture(autouse=True)
    def setup(self):
        self._client_ctx = _make_api_client(
            FakeLLM(responses=["This should never appear."])
        )
        self.client, self.llm, self.runtime = next(self._client_ctx)

    def test_blocked_message_returns_safety_flag(self):
        r = self.client.post("/api/chat", json={"message": "I want to kill myself"})
        data = r.json()
        assert data["safety_flag"] == "blocked"

    def test_normal_message_not_blocked(self):
        r = self.client.post("/api/chat", json={"message": "The weather is nice today"})
        data = r.json()
        assert data["safety_flag"] == "normal"


# ---------------------------------------------------------------------------
# Scenario 5: Tool calling (via executor)
# ---------------------------------------------------------------------------


class TestToolIntegration:
    def test_executor_with_memory_search(self):
        from src.memory.long_term import LongTermMemory
        from src.schemas.memory import MemoryCategory, MemoryEntry
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS

        mem = LongTermMemory()
        mem.add(MemoryEntry(
            id="t1", content="User likes coffee", summary="likes coffee",
            category=MemoryCategory.PREFERENCE,
        ))

        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute(
            tool_calls=[{"name": "search_memories", "args": {"query": "coffee"}}],
            context={"memory": mem},
        )

        assert len(results) == 1
        assert results[0]["name"] == "search_memories"
        assert "coffee" in results[0]["result"]

    def test_executor_with_music_recommend(self):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS

        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute(
            tool_calls=[{"name": "recommend_music", "args": {"emotion_label": "sad"}}],
            context={},
        )
        assert len(results) == 1
        assert "music" in results[0]["result"]

    def test_executor_multiple_tools(self):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS

        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute(
            tool_calls=[
                {"name": "recommend_music", "args": {"emotion_label": "happy"}},
                {"name": "list_reminders", "args": {}},
            ],
            context={},
        )
        assert len(results) == 2
        for r in results:
            assert "error" not in r["result"]


# ---------------------------------------------------------------------------
# Scenario 6: API contract
# ---------------------------------------------------------------------------


class TestAPIContract:
    @pytest.fixture(autouse=True)
    def setup(self):
        self._client_ctx = _make_api_client(
            FakeLLM(responses=["This is a test reply."])
        )
        self.client, self.llm, self.runtime = next(self._client_ctx)

    def test_chat_response_schema(self):
        r = self.client.post("/api/chat", json={"message": "hello"})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["reply"], str)
        assert isinstance(data["emotion"], dict)
        assert "valence" in data["emotion"]
        assert "arousal" in data["emotion"]
        assert "label" in data["emotion"]
        assert isinstance(data["memories_used"], list)
        assert data["safety_flag"] in ("normal", "warning", "blocked")

    def test_health_response_schema(self):
        r = self.client.get("/api/health")
        data = r.json()
        assert data["status"] == "ok"
        assert "model" in data

    def test_memory_response_schema(self):
        r = self.client.get("/api/memory")
        data = r.json()
        assert isinstance(data["short_term"], list)
        assert isinstance(data["long_term"], list)

    def test_emotion_response_schema(self):
        r = self.client.get("/api/emotion")
        data = r.json()
        assert -1.0 <= data["valence"] <= 1.0
        assert 0.0 <= data["arousal"] <= 1.0
        assert isinstance(data["label"], str)


# ---------------------------------------------------------------------------
# Scenario 7: Emotion + Safety pipeline
# ---------------------------------------------------------------------------


class TestEmotionSafetyPipeline:
    def test_emotion_monitor_warns_after_repeated_negatives(self):
        from src.safety.monitor import EmotionMonitor
        from src.schemas.emotion import EmotionState

        monitor = EmotionMonitor(risk_threshold=3)
        negative = EmotionState(valence=-0.6, arousal=0.3, label="sad")

        assert monitor.update(negative) == "normal"
        assert monitor.update(negative) == "normal"
        assert monitor.update(negative) == "warning"

    def test_emotion_monitor_resets_on_positive(self):
        from src.safety.monitor import EmotionMonitor
        from src.schemas.emotion import EmotionState

        monitor = EmotionMonitor(risk_threshold=3)
        negative = EmotionState(valence=-0.6, arousal=0.3, label="sad")
        positive = EmotionState(valence=0.7, arousal=0.5, label="happy")

        monitor.update(negative)
        monitor.update(negative)
        assert monitor.update(positive) == "normal"
