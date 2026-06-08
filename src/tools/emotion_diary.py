"""emotion_diary — record the user's emotional state.

Writes entries to a local JSON file so users can track their emotional
journey over time.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


_DEFAULT_DIARY = Path("data/emotion_diary.json")


def record_emotion(
    label: str,
    note: str = "",
    diary_path: str | None = None,
) -> str:
    """Record an emotion entry in the diary.

    Args:
        label: Emotion label (happy, sad, angry, anxious, tired, neutral).
        note: Optional free-text note.
        diary_path: Path to the diary JSON file (defaults to data/emotion_diary.json).

    Returns:
        A confirmation message.
    """
    path = Path(diary_path) if diary_path else _DEFAULT_DIARY

    # Load existing entries
    entries: list[dict] = []
    if path.exists():
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []

    # Add new entry
    entries.append({
        "label": label,
        "note": note,
        "timestamp": datetime.now().isoformat(),
    })

    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write back
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    return f"[emotion_diary] 已记录情绪：{label} — {note}" if note else f"[emotion_diary] 已记录情绪：{label}"
