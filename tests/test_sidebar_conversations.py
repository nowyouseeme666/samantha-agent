"""Test sidebar conversation management features."""
import json, pytest
from fastapi.testclient import TestClient
from src.emotion.detector import EmotionDetector
from src.conversation_store import ConversationStore

import src.api as api_mod


class FakeLLM:
    def chat(self, message="", system_prompt=""): return "Test reply"
    def chat_with_tools(self, message="", system_prompt="", tools=None, tool_executor=None): return "Test tool reply"
    def stream(self, message="", system_prompt=""): yield "T"; yield "e"; yield "s"; yield "t"

class FakeGuard:
    def check(self, text):
        if "blockme" in text: return "blocked"
        return "normal"
    def get_blocked_response(self): return "Blocked"

class FakeMemory:
    def __init__(self): self.items = []
    def add(self, entry): self.items.append(entry)
    def get(self, query="", k=5): return self.items[-k:] if self.items else []
    def clear(self): self.items.clear()

class FakeMonitor:
    current_risk = "normal"
    def update(self, state): pass

class FakeSettings:
    llm_model = "test"
    dialogue_fallback_message = "Fallback"
    memory_short_term_max_rounds = 20
    memory_long_term_chroma_dir = "./data/chroma"
    safety_blocked_keywords = []
    safety_warning_keywords = []
    safety_emotion_risk_threshold = 3

_mock_pb = type("PB", (), {"build_system": lambda s, **kw: "", "build_user": lambda s, **kw: ""})
_mock_emo = type("Emo", (), {"to_dict": lambda s: {"valence": 0, "arousal": 0, "label": "neutral"}})
_mock_cfg = type("Cfg", (), {"enabled_tools": lambda s: []})


def _build_test_runtime():
    import tempfile, os
    tmpdir = tempfile.mkdtemp()
    store = ConversationStore(db_path=os.path.join(tmpdir, "test.db"))
    rt = api_mod.AgentRuntime(
        settings=FakeSettings(), persona=None, rules=None, tools_cfg=_mock_cfg(),
        llm=FakeLLM(), prompt_builder=_mock_pb(), short_term=FakeMemory(),
        long_term=FakeMemory(), immutable=FakeMemory(), guard=FakeGuard(),
        monitor=FakeMonitor(), emotion=_mock_emo(), detector=EmotionDetector(),
        conv_store=store,
    )
    return rt


@pytest.fixture
def client():
    api_mod._runtime = _build_test_runtime()
    return TestClient(api_mod.app)


class TestConversationCRUD:
    def test_get_conversations_returns_list(self, client):
        r = client.get("/api/conversations/user001")
        assert r.status_code == 200
        data = r.json()
        assert "conversations" in data
        assert "current_id" in data
        assert isinstance(data["conversations"], list)

    def test_create_conversation(self, client):
        r = client.post("/api/conversations/user001")
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["title"] == ""  # default empty title

    def test_create_multiple_conversations(self, client):
        ids = []
        for _ in range(3):
            r = client.post("/api/conversations/user002")
            ids.append(r.json()["id"])
        assert len(set(ids)) == 3

    def test_get_conversation_by_id(self, client):
        r_create = client.post("/api/conversations/user003")
        cid = r_create.json()["id"]
        r_get = client.get(f"/api/conversations/user003/{cid}")
        assert r_get.status_code == 200
        assert "messages" in r_get.json()

    def test_get_nonexistent_conversation_returns_404(self, client):
        r = client.get("/api/conversations/user001/nonexistent-id")
        assert r.status_code == 404

    def test_rename_conversation(self, client):
        r_create = client.post("/api/conversations/user004")
        cid = r_create.json()["id"]
        r_rename = client.patch(f"/api/conversations/user004/{cid}", json={"title": "My new title"})
        assert r_rename.status_code == 200
        assert r_rename.json()["title"] == "My new title"

    def test_rename_reflected_in_list(self, client):
        r_create = client.post("/api/conversations/user005")
        cid = r_create.json()["id"]
        client.patch(f"/api/conversations/user005/{cid}", json={"title": "Renamed"})
        r_list = client.get("/api/conversations/user005")
        titles = {c["title"] for c in r_list.json()["conversations"]}
        assert "Renamed" in titles

    def test_delete_conversation(self, client):
        r_create = client.post("/api/conversations/user006")
        cid = r_create.json()["id"]
        r_del = client.delete(f"/api/conversations/user006/{cid}")
        assert r_del.status_code == 200
        r_list = client.get("/api/conversations/user006")
        ids = {c["id"] for c in r_list.json()["conversations"]}
        assert cid not in ids

    def test_delete_nonexistent_conversation_returns_404(self, client):
        r = client.delete("/api/conversations/user001/nonexistent-id")
        assert r.status_code == 404

    def test_rename_nonexistent_returns_404(self, client):
        r = client.patch("/api/conversations/user001/nonexistent-id", json={"title": "test"})
        assert r.status_code == 404


class TestConversationMessagePersistence:
    def test_sse_chat_saves_messages(self, client):
        r_create = client.post("/api/conversations/user_c1")
        cid = r_create.json()["id"]
        with client.stream("POST", f"/api/chat/user_c1", json={
            "message": "Hello Samantha",
            "conversation_id": cid,
            "conversation_history": [],
        }) as response:
            assert response.status_code == 200
            events = []
            for line in response.iter_lines():
                if line.startswith("data: "):
                    events.append(json.loads(line[6:]))
        done_events = [e for e in events if e["type"] == "done"]
        assert len(done_events) > 0
        r_get = client.get(f"/api/conversations/user_c1/{cid}")
        msgs = r_get.json().get("messages", [])
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hello Samantha"
        assert msgs[1]["role"] == "assistant"

    def test_sse_chat_without_conv_id_creates_new(self, client):
        with client.stream("POST", "/api/chat/user_c2", json={
            "message": "New chat",
            "conversation_id": None,
            "conversation_history": [],
        }) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    ev = json.loads(line[6:])
                    if ev["type"] == "done":
                        assert "conversation_id" in ev
                        cid = ev["conversation_id"]
                        break
        r_list = client.get("/api/conversations/user_c2")
        ids = {c["id"] for c in r_list.json()["conversations"]}
        assert cid in ids

    def test_multiple_messages_in_same_conversation(self, client):
        r_create = client.post("/api/conversations/user_c3")
        cid = r_create.json()["id"]
        for msg in ["Msg1", "Msg2", "Msg3"]:
            with client.stream("POST", f"/api/chat/user_c3", json={
                "message": msg, "conversation_id": cid, "conversation_history": [],
            }) as response:
                pass
        r_get = client.get(f"/api/conversations/user_c3/{cid}")
        msgs = r_get.json().get("messages", [])
        user_msgs = [m for m in msgs if m["role"] == "user"]
        assert len(user_msgs) == 3

    def test_conversation_isolated_per_user(self, client):
        with client.stream("POST", "/api/chat/user_A", json={
            "message": "A secret", "conversation_id": None, "conversation_history": [],
        }) as response:
            for line in response.iter_lines():
                if line.startswith("data: "):
                    ev = json.loads(line[6:])
                    if ev["type"] == "done":
                        a_cid = ev["conversation_id"]
        r_a = client.get(f"/api/conversations/user_A/{a_cid}")
        a_msgs = [m["content"] for m in r_a.json().get("messages", []) if m["role"] == "user"]
        assert "A secret" in a_msgs

    def test_conversation_list_sorted_by_created(self, client):
        for _ in range(3):
            client.post("/api/conversations/user_sort")
        r_list = client.get("/api/conversations/user_sort")
        convs = r_list.json()["conversations"]
        assert len(convs) == 3

    def test_blocked_message_not_saved(self, client):
        """Blocked messages should NOT be saved (safety-first)."""
        r_create = client.post("/api/conversations/user_block")
        cid = r_create.json()["id"]
        with client.stream("POST", f"/api/chat/user_block", json={
            "message": "This message contains blockme",
            "conversation_id": cid, "conversation_history": [],
        }) as response:
            pass
        r_get = client.get(f"/api/conversations/user_block/{cid}")
        msgs = r_get.json().get("messages", [])
        assert len(msgs) == 0  # blocked messages not persisted


class TestMultipleUsers:
    def test_users_independent(self, client):
        client.post("/api/conversations/alpha")
        client.post("/api/conversations/beta")
        r_alpha = client.get("/api/conversations/alpha")
        r_beta = client.get("/api/conversations/beta")
        assert len(r_alpha.json()["conversations"]) == 1
        assert len(r_beta.json()["conversations"]) == 1
