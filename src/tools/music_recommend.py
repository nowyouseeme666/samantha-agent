"""music_recommend — recommend music based on emotional state.

Uses a local mapping table from emotion labels to music genres / artists.
Phase 3 may integrate with a real music API (Spotify, NetEase, etc.).
"""

from __future__ import annotations


# Chinese-to-English label mapping for when EmotionState uses Chinese labels
LABEL_ZH_TO_EN: dict[str, str] = {
    "开心": "happy",
    "悲伤": "sad",
    "生气": "angry",
    "焦虑": "anxious",
    "疲惫": "tired",
    "平静": "neutral",
}

EMOTION_MUSIC: dict[str, list[str]] = {
    "happy": [
        "轻快流行: Jason Mraz - I'm Yours",
        "活力摇滚: Queen - Don't Stop Me Now",
        "温暖民谣: 陈绮贞 - 旅行的意义",
    ],
    "sad": [
        "治愈抒情: 中島美嘉 - 雪の華",
        "温柔抚慰: Coldplay - Fix You",
        "安静钢琴: Yiruma - River Flows in You",
    ],
    "angry": [
        "宣泄摇滚: Linkin Park - Numb",
        "力量金属: Nightwish - Nemo",
        "情绪释放: 五月天 - 倔强",
    ],
    "anxious": [
        "放松纯音乐: 久石让 - Summer",
        "自然白噪音: 海浪声 / 雨声",
        "冥想引导: 正念呼吸练习音频",
    ],
    "tired": [
        "舒缓爵士: Norah Jones - Don't Know Why",
        "温暖低吟: 李健 - 贝加尔湖畔",
        "轻音乐: Bandari - 安妮的仙境",
    ],
    "neutral": [
        "日常陪伴: 卢广仲 - 慢灵魂",
        "清爽后摇: Mogwai - Take Me Somewhere Nice",
        "轻松吉他: 押尾コータロー - 風の詩",
    ],
}


def recommend(emotion_label: str) -> str:
    """Return music recommendations for the given emotion.

    Args:
        emotion_label: One of happy, sad, angry, anxious, tired, neutral
                       (accepts both English and Chinese labels).

    Returns:
        A formatted string with music suggestions.
    """
    label = emotion_label.lower().strip()
    # Normalize Chinese label to English
    label = LABEL_ZH_TO_EN.get(label, label)
    songs = EMOTION_MUSIC.get(label)

    if songs is None:
        songs = EMOTION_MUSIC["neutral"]
        label = "neutral"

    lines = [f"[music] 根据你当前的情绪（{label}），推荐以下音乐："]
    for i, song in enumerate(songs, start=1):
        lines.append(f"  {i}. {song}")

    return "\n".join(lines)
