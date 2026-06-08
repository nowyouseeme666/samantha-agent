"""FastAPI endpoint tests."""
import pytest
from fastapi.testclient import TestClient
from src.emotion.detector import EmotionDetector
from src.emotion.rules import EmotionRule

# Override runtime before importing app
import src.api as api_mod

class FakeLLM:
    def chat(self, message="", system_prompt=""):
        return "Test response"
    def chat_with_tools(self, message="", system_prompt="", tools=None, tool_executor=None):
        return "Test response with tools"

class FakeGuard:
    def check(self, text):
        if "blockme" in text:
            return "blocked"
        return "normal"
    def get_blocked_response(self):
        return "Blocked message"

class FakeMemory:
    def __init__(self):
        self.items = []
    def add(self, entry):
        self.items.append(entry)
    def get(self, query="", k=5):
        return self.items[-k:] if self.items else []
    def clear(self):
        self.items.clear()

class FakeMonitor:
    current_risk = "normal"
    def update(self, state):
        pass

class FakeSettings:
    llm_model = "test-model"
    dialogue_fallback_message = "Fallback"
    memory_short_term_max_rounds = 20
    memory_long_term_chroma_dir = "./data/chroma"
    safety_blocked_keywords = []
    safety_warning_keywords = []
    safety_emotion_risk_threshold = 3

# Lambdas must accept 'self' since they're used as bound methods
_mock_prompt_builder = type("MockPB", (), {
    "build_system": lambda s, **kw: "",
    "build_user": lambda s, **kw: "",
})
_mock_emotion = type("MockEmo", (), {
    "to_dict": lambda s: {"valence": 0, "arousal": 0, "label": "neutral"},
})
_mock_cfg = type("MockCfg", (), {
    "enabled_tools": lambda s: [],
})

def _build_test_runtime():
    runtime = api_mod.AgentRuntime(
        settings=FakeSettings(),
        persona=None,
        rules=None,
        tools_cfg=_mock_cfg(),
        llm=FakeLLM(),
        prompt_builder=_mock_prompt_builder(),
        short_term=FakeMemory(),
        long_term=FakeMemory(),
        immutable=FakeMemory(),
        guard=FakeGuard(),
        monitor=FakeMonitor(),
        emotion=_mock_emotion(),
        detector=EmotionDetector(),
    )
    return runtime

@pytest.fixture
def client():
    api_mod._runtime = _build_test_runtime()
    return TestClient(api_mod.app)

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        r = client.get("/api/health")
        assert r.status_code == 200
    def test_health_contains_status(self, client):
        r = client.get("/api/health")
        assert r.json()["status"] == "ok"
    def test_health_contains_model(self, client):
        r = client.get("/api/health")
        assert "model" in r.json()

class TestChatEndpoint:
    def test_chat_returns_reply(self, client):
        r = client.post("/api/chat", json={"message":"hello"})
        assert r.status_code == 200
        assert "reply" in r.json()
    def test_chat_returns_emotion(self, client):
        r = client.post("/api/chat", json={"message":"hello"})
        assert "emotion" in r.json()
    def test_chat_returns_memories_used(self, client):
        r = client.post("/api/chat", json={"message":"hello"})
        assert "memories_used" in r.json()
    def test_chat_returns_safety_flag(self, client):
        r = client.post("/api/chat", json={"message":"hello"})
        assert "safety_flag" in r.json()
    def test_chat_empty_message(self, client):
        r = client.post("/api/chat", json={"message":""})
        assert r.status_code == 200
    def test_chat_blocked_message(self, client):
        r = client.post("/api/chat", json={"message":"blockme"})
        assert r.json()["safety_flag"] == "blocked"
    def test_chat_missing_message_field(self, client):
        r = client.post("/api/chat", json={})
        assert r.status_code in (200, 422)

class TestMemoryEndpoint:
    def test_memory_returns_structure(self, client):
        r = client.get("/api/memory")
        assert r.status_code == 200
        assert "short_term" in r.json()
        assert "long_term" in r.json()
    def test_memory_reflects_chat(self, client):
        client.post("/api/chat", json={"message":"hello"})
        r = client.get("/api/memory")
        assert len(r.json()["short_term"]) > 0

class TestEmotionEndpoint:
    def test_emotion_returns_structure(self, client):
        r = client.get("/api/emotion")
        assert r.status_code == 200
        assert "valence" in r.json()
    def test_emotion_valence_in_range(self, client):
        r = client.get("/api/emotion")
        v = r.json()["valence"]
        assert -1.0 <= v <= 1.0

class TestCORS:
    def test_cors_headers_present(self, client):
        r = client.options("/api/chat", headers={
            "Origin":"http://localhost:5173",
            "Access-Control-Request-Method":"POST",
        })
        assert r.status_code == 200
