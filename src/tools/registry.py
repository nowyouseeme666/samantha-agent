"""Tool registry — LangChain-compatible tool definitions.

Each tool is defined with a name, description, and function reference.
The descriptions are used by the LLM to decide when to invoke each tool.
"""

from __future__ import annotations

from src.tools.memory_search import search_memories
from src.tools.emotion_diary import record_emotion
from src.tools.schedule_reminder import set_reminder, list_reminders
from src.tools.music_recommend import recommend
from src.tools.weather_check import get_weather

ALL_TOOLS: list[dict] = [
    {
        "name": "search_memories",
        "description": "搜索 Samantha 的长期记忆库。当用户提到过去的事情、询问偏好或个人信息时使用。",
        "function": search_memories,
        "parameters": {
            "query": {"type": "string", "description": "搜索关键词"},
            "k": {"type": "integer", "description": "返回条数，默认5"},
        },
        "enabled": True,
    },
    {
        "name": "record_emotion",
        "description": "记录用户的情绪日记。当用户表达强烈情绪或主动要求记录心情时使用。",
        "function": record_emotion,
        "parameters": {
            "label": {"type": "string", "description": "情绪标签"},
            "note": {"type": "string", "description": "备注文字"},
        },
        "enabled": True,
    },
    {
        "name": "set_reminder",
        "description": "设置一个日程提醒。当用户说'提醒我'、'帮我记一下'时使用。",
        "function": set_reminder,
        "parameters": {
            "message": {"type": "string", "description": "提醒内容"},
            "time": {"type": "string", "description": "提醒时间，ISO格式"},
        },
        "enabled": True,
    },
    {
        "name": "list_reminders",
        "description": "列出所有待办提醒。当用户询问'有什么提醒'或'我的日程'时使用。",
        "function": list_reminders,
        "parameters": {},
        "enabled": True,
    },
    {
        "name": "recommend_music",
        "description": "根据当前情绪推荐音乐。当用户感到无聊、需要安慰或想要听歌时使用。",
        "function": recommend,
        "parameters": {
            "emotion_label": {"type": "string", "description": "情绪标签"},
        },
        "enabled": True,
    },
    {
        "name": "get_weather",
        "description": "查询指定城市的当前天气。当用户询问天气信息时使用。",
        "function": get_weather,
        "parameters": {
            "city": {"type": "string", "description": "城市名称"},
        },
        "enabled": True,
    },
]
