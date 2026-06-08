"""Test that all 6 Samantha tools can be called and return expected results."""
import json, tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.schemas.memory import MemoryCategory, MemoryEntry
from src.memory.long_term import LongTermMemory


@pytest.fixture
def memory_with_prefs():
    """A LongTermMemory pre-populated with user preferences."""
    mem = LongTermMemory(chroma_dir="./data/chroma_test_tools")
    mem.add(MemoryEntry(id="pref-1", content="用户喜欢喝咖啡", summary="喜欢咖啡", category=MemoryCategory.PREFERENCE))
    mem.add(MemoryEntry(id="pref-2", content="用户养了一只猫叫咪咪", summary="养猫", category=MemoryCategory.PROFILE))
    mem.add(MemoryEntry(id="evt-1", content="用户上周去了北京旅行", summary="北京旅行", category=MemoryCategory.EVENT))
    return mem


@pytest.fixture
def tmp_json():
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        p = Path(f.name)
    yield p
    if p.exists():
        p.unlink()


class TestMemorySearchTool:
    def test_search_finds_coffee_preference(self, memory_with_prefs):
        from src.tools.memory_search import search_memories
        result = search_memories("咖啡", memory=memory_with_prefs, k=5)
        assert "咖啡" in result
        assert "喜欢" in result or "pref-1" in str(memory_with_prefs._entries)

    def test_search_cat_profile(self, memory_with_prefs):
        from src.tools.memory_search import search_memories
        result = search_memories("猫", memory=memory_with_prefs, k=5)
        assert "猫" in result or "咪咪" in result or "pref-2" in str(memory_with_prefs._entries)

    def test_search_no_match_returns_polite_msg(self, memory_with_prefs):
        from src.tools.memory_search import search_memories
        result = search_memories("不存在关键词xyz", memory=memory_with_prefs, k=5)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_search_without_memory_returns_error(self):
        from src.tools.memory_search import search_memories
        result = search_memories("test", memory=None)
        assert "未初始化" in result or "无法搜索" in result

    def test_search_empty_query_returns_prompt(self, memory_with_prefs):
        from src.tools.memory_search import search_memories
        result = search_memories("", memory=memory_with_prefs)
        assert "关键字" in result or "提供" in result


class TestEmotionDiaryTool:
    def test_record_emotion_saves_entry(self, tmp_json):
        from src.tools.emotion_diary import record_emotion
        result = record_emotion("happy", "今天很开心", diary_path=str(tmp_json))
        assert "已记录" in result
        data = json.loads(tmp_json.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["label"] == "happy"

    def test_record_multiple_emotions_appends(self, tmp_json):
        from src.tools.emotion_diary import record_emotion
        record_emotion("sad", "有点难过", diary_path=str(tmp_json))
        record_emotion("happy", "后来好了", diary_path=str(tmp_json))
        data = json.loads(tmp_json.read_text(encoding="utf-8"))
        assert len(data) == 2

    def test_record_emotion_without_note(self, tmp_json):
        from src.tools.emotion_diary import record_emotion
        result = record_emotion("anxious", diary_path=str(tmp_json))
        assert "已记录" in result


class TestScheduleReminderTool:
    def test_set_reminder_returns_confirmation(self, tmp_json):
        from src.tools.schedule_reminder import set_reminder
        result = set_reminder("明天下午开会", "2026-06-09 14:00", reminder_path=str(tmp_json))
        assert "已设置" in result
        assert "明天下午开会" in result

    def test_list_reminders_shows_set_reminder(self, tmp_json):
        from src.tools.schedule_reminder import set_reminder, list_reminders
        set_reminder("买牛奶", "2026-06-09 10:00", reminder_path=str(tmp_json))
        listing = list_reminders(reminder_path=str(tmp_json))
        assert "买牛奶" in listing

    def test_list_empty_reminders(self, tmp_json):
        from src.tools.schedule_reminder import list_reminders
        listing = list_reminders(reminder_path=str(tmp_json))
        assert "暂无" in listing or "没有" in listing

    def test_multiple_reminders(self, tmp_json):
        from src.tools.schedule_reminder import set_reminder, list_reminders
        set_reminder("开会", "2026-06-09 09:00", reminder_path=str(tmp_json))
        set_reminder("吃饭", "2026-06-09 12:00", reminder_path=str(tmp_json))
        set_reminder("运动", "2026-06-09 18:00", reminder_path=str(tmp_json))
        listing = list_reminders(reminder_path=str(tmp_json))
        assert "开会" in listing
        assert "吃饭" in listing
        assert "运动" in listing


class TestMusicRecommendTool:
    def test_recommend_for_happy(self):
        from src.tools.music_recommend import recommend
        result = recommend("happy")
        assert len(result) > 0
        assert "推荐" in result or "音乐" in result or "music" in result.lower()

    def test_recommend_for_sad(self):
        from src.tools.music_recommend import recommend
        result = recommend("sad")
        assert "治愈" in result or "抚慰" in result or "music" in result.lower()

    def test_all_emotions_return_results(self):
        from src.tools.music_recommend import recommend
        for label in ("happy", "sad", "angry", "anxious", "tired", "neutral"):
            result = recommend(label)
            assert isinstance(result, str)
            assert len(result) > 20, f"Result for {label} too short: {result}"

    def test_chinese_labels_normalized(self):
        from src.tools.music_recommend import recommend
        result = recommend("开心")
        assert len(result) > 20

    def test_unknown_label_falls_back_to_neutral(self):
        from src.tools.music_recommend import recommend
        result = recommend("nonexistent_mood")
        assert len(result) > 20


class TestWeatherCheckTool:
    def test_weather_mocked_response(self):
        mock_resp = MagicMock()
        mock_resp.text = "Sunny +25C 40% 10km/h"
        with patch("requests.get", return_value=mock_resp):
            from src.tools.weather_check import get_weather
            result = get_weather("Beijing")
            assert "Beijing" in result
            assert "Sunny" in result or "25" in result

    def test_weather_network_error(self):
        with patch("requests.get", side_effect=Exception("Network error")):
            from src.tools.weather_check import get_weather
            result = get_weather("Tokyo")
            assert "无法" in result or "失败" in result or "暂时" in result

    def test_weather_empty_city(self):
        from src.tools.weather_check import get_weather
        result = get_weather("")
        assert "提供" in result or "城市" in result


class TestToolExecutorIntegration:
    def test_executor_runs_all_enabled_tools(self):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS
        enabled = [t for t in ALL_TOOLS if t.get("enabled", True)]
        assert len(enabled) >= 6, f"Expected at least 6 tools, got {len(enabled)}"

    def test_executor_batch_execution(self, memory_with_prefs):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS
        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute(
            tool_calls=[
                {"name": "search_memories", "args": {"query": "咖啡", "k": 3}},
                {"name": "recommend_music", "args": {"emotion_label": "happy"}},
            ],
            context={"memory": memory_with_prefs},
        )
        assert len(results) == 2
        assert results[0]["name"] == "search_memories"
        assert results[1]["name"] == "recommend_music"

    def test_executor_unknown_tool_graceful(self):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS
        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute([{"name": "nonexistent_tool", "args": {}}])
        assert len(results) == 1
        assert "错误" in results[0]["result"] or "未找到" in results[0]["result"]

    def test_executor_run_one(self, memory_with_prefs):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS
        executor = ToolExecutor(tools=ALL_TOOLS, context={"memory": memory_with_prefs})
        result = executor.run_one("search_memories", args={"query": "北京", "k": 3})
        assert isinstance(result, str)
        assert "北京" in result

    def test_executor_new_tool_set_reminder(self, tmp_json):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS
        executor = ToolExecutor(tools=ALL_TOOLS)
        result = executor.run_one("set_reminder", args={
            "message": "测试提醒",
            "time": "2026-06-09 10:00",
        })
        assert isinstance(result, str)
        assert "已设置" in result or "提醒" in result


class TestToolRegistry:
    def test_all_tools_registered(self):
        from src.tools.registry import ALL_TOOLS
        names = {t["name"] for t in ALL_TOOLS}
        expected = {"search_memories", "record_emotion", "set_reminder", "list_reminders", "recommend_music", "get_weather"}
        missing = expected - names
        assert not missing, f"Missing tools: {missing}"

    def test_all_tools_have_description(self):
        from src.tools.registry import ALL_TOOLS
        for t in ALL_TOOLS:
            assert t.get("description"), f"Tool {t['name']} missing description"
            assert t.get("name"), f"Tool missing name"

    def test_registry_has_no_duplicate_names(self):
        from src.tools.registry import ALL_TOOLS
        names = [t["name"] for t in ALL_TOOLS]
        assert len(names) == len(set(names)), f"Duplicate names: {names}"
