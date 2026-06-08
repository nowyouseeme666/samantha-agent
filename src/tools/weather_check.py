"""weather_check — query current weather for a city via wttr.in.

Uses the free wttr.in API (no key required).  Returns a concise text
summary suitable for conversation.
"""

from __future__ import annotations


def get_weather(city: str) -> str:
    """Fetch current weather for *city* from wttr.in.

    Args:
        city: City name (Chinese or English).

    Returns:
        A formatted weather summary, or an error message.
    """
    if not city or not city.strip():
        return "[weather] 请提供城市名称。"

    city = city.strip()

    try:
        import requests

        url = f"https://wttr.in/{city}?format=%C+%t+%h+%w&lang=zh"
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        weather_text = resp.text.strip()

        if not weather_text or weather_text.startswith("Unknown"):
            return f"[weather] 未找到 '{city}' 的天气信息，请确认城市名。"

        return f"[weather] {city} 当前天气：{weather_text}"

    except Exception:
        return f"[weather] 暂时无法获取 '{city}' 的天气信息，请稍后再试。"
