"""Tests for agent tools — src/tools/."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.schemas.memory import MemoryCategory, MemoryEntry


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
def long_term_memory():
    """Return a pre-populated LongTermMemory for search tests.

    Uses a temporary directory so stale ChromaDB data from other test runs
    or the real app does not pollute search results.
    """
    import shutil
    from src.memory.long_term import LongTermMemory

    tmp = tempfile.mkdtemp(prefix="chroma_tools_")
    try:
        mem = LongTermMemory(chroma_dir=tmp)
        mem.add(MemoryEntry(
            id="lt-1", content="用户喜欢喝咖啡", summary="喜欢咖啡",
            category=MemoryCategory.PREFERENCE,
        ))
        mem.add(MemoryEntry(
            id="lt-2", content="用户上周去了北京", summary="去北京旅行",
            category=MemoryCategory.EVENT,
        ))
        mem.add(MemoryEntry(
            id="lt-3", content="用户有一只猫叫咪咪", summary="养猫",
            category=MemoryCategory.PROFILE,
        ))
        yield mem
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@pytest.fixture
def tmp_json_file():
    """Create a temporary JSON file and clean up after test."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    yield path
    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------------
# Memory search
# ---------------------------------------------------------------------------


class TestMemorySearch:
    def test_search_finds_matching_entry(self, long_term_memory):
        from src.tools.memory_search import search_memories

        results = search_memories("咖啡", memory=long_term_memory, k=5)
        assert "咖啡" in results

    def test_search_no_match_returns_empty_hint(self, long_term_memory):
        from src.tools.memory_search import search_memories

        results = search_memories("xyz不存在的关键词", memory=long_term_memory, k=5)
        # Should return a polite "not found" message
        assert isinstance(results, str)
        assert len(results) > 0

    def test_search_respects_k(self, long_term_memory):
        from src.tools.memory_search import search_memories

        results = search_memories("用户", memory=long_term_memory, k=1)
        assert isinstance(results, str)


# ---------------------------------------------------------------------------
# Emotion diary
# ---------------------------------------------------------------------------


class TestEmotionDiary:
    def test_record_emotion_saves_to_json(self, tmp_json_file):
        from src.tools.emotion_diary import record_emotion

        result = record_emotion(
            label="happy",
            note="今天很开心！",
            diary_path=str(tmp_json_file),
        )
        assert "已记录" in result
        assert tmp_json_file.exists()

        # Verify the file content
        data = json.loads(tmp_json_file.read_text(encoding="utf-8"))
        assert len(data) == 1
        assert data[0]["label"] == "happy"
        assert data[0]["note"] == "今天很开心！"

    def test_record_emotion_appends_to_existing(self, tmp_json_file):
        from src.tools.emotion_diary import record_emotion

        record_emotion("sad", "有点难过", diary_path=str(tmp_json_file))
        record_emotion("happy", "后来开心了", diary_path=str(tmp_json_file))

        data = json.loads(tmp_json_file.read_text(encoding="utf-8"))
        assert len(data) == 2
        assert data[0]["label"] == "sad"
        assert data[1]["label"] == "happy"


# ---------------------------------------------------------------------------
# Schedule reminder
# ---------------------------------------------------------------------------


class TestScheduleReminder:
    def test_set_and_list_reminders(self, tmp_json_file):
        from src.tools.schedule_reminder import set_reminder, list_reminders

        result = set_reminder(
            message="明天下午开会",
            time="2026-06-08 14:00",
            reminder_path=str(tmp_json_file),
        )
        assert "已设置" in result or "提醒" in result

        listing = list_reminders(reminder_path=str(tmp_json_file))
        assert "明天下午开会" in listing

    def test_list_empty_reminders(self, tmp_json_file):
        from src.tools.schedule_reminder import list_reminders

        listing = list_reminders(reminder_path=str(tmp_json_file))
        assert "暂无" in listing or "没有" in listing


# ---------------------------------------------------------------------------
# Music recommend
# ---------------------------------------------------------------------------


class TestMusicRecommend:
    def test_recommend_returns_for_valid_emotion(self):
        from src.tools.music_recommend import recommend

        result = recommend("happy")
        assert len(result) > 0
        assert "推荐" in result or "🎵" in result or "歌曲" in result or "音乐" in result

    def test_recommend_all_emotions_work(self):
        from src.tools.music_recommend import recommend

        for label in ("happy", "sad", "angry", "anxious", "tired", "neutral"):
            result = recommend(label)
            assert isinstance(result, str)
            assert len(result) > 0


# ---------------------------------------------------------------------------
# Weather check
# ---------------------------------------------------------------------------


class TestWeatherCheck:
    def test_get_weather_mocked(self):
        """Test weather with a mocked HTTP response."""
        mock_response = MagicMock()
        mock_response.text = "Weather for Beijing: Sunny, 25°C"

        with patch("requests.get", return_value=mock_response):
            from src.tools.weather_check import get_weather

            result = get_weather("Beijing")
            assert "Beijing" in result
            assert "Sunny" in result or "25" in result

    def test_get_weather_network_error(self):
        """Graceful handling when the weather API is unreachable."""
        with patch("requests.get", side_effect=Exception("Network error")):
            from src.tools.weather_check import get_weather

            result = get_weather("Beijing")
            assert "无法" in result or "失败" in result or "暂时" in result


# ---------------------------------------------------------------------------
# Executor
# ---------------------------------------------------------------------------


class TestExecutor:
    def test_executor_runs_single_tool(self, long_term_memory):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS

        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute(
            tool_calls=[{
                "name": "search_memories",
                "args": {"query": "咖啡", "k": 3},
            }],
            context={"memory": long_term_memory},
        )
        assert len(results) == 1
        assert results[0]["name"] == "search_memories"
        assert "咖啡" in results[0]["result"]

    def test_executor_unknown_tool_returns_error(self):
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS

        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute(
            tool_calls=[{
                "name": "nonexistent_tool_xyz",
                "args": {},
            }],
            context={},
        )
        assert len(results) == 1
        assert "错误" in results[0]["result"] or "未找到" in results[0]["result"]

    def test_executor_tool_failure_is_handled(self, long_term_memory):
        """A tool that raises should not crash the executor."""
        from src.tools.executor import ToolExecutor
        from src.tools.registry import ALL_TOOLS

        executor = ToolExecutor(tools=ALL_TOOLS)
        results = executor.execute(
            tool_calls=[{
                "name": "search_memories",
                "args": {"query": None},  # will cause issues
            }],
            context={"memory": long_term_memory},
        )
        assert len(results) == 1
        # Should return an error message, not crash
        assert isinstance(results[0]["result"], str)
