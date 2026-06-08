"""schedule_reminder — simple reminder management backed by local JSON.

Supports setting one-off reminders and listing existing ones.
Phase 2: in-memory JSON store.  Phase 3+: may integrate with system
notification or a proper scheduler.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


_DEFAULT_REMINDERS = Path("data/reminders.json")


def set_reminder(
    message: str,
    time: str,
    reminder_path: str | None = None,
) -> str:
    """Set a new reminder.

    Args:
        message: What to be reminded about.
        time: ISO-format time string (e.g. "2026-06-08 14:00").
        reminder_path: Path to the reminders JSON file.

    Returns:
        Confirmation message.
    """
    path = Path(reminder_path) if reminder_path else _DEFAULT_REMINDERS

    entries: list[dict] = []
    if path.exists():
        try:
            entries = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            entries = []

    entries.append({
        "message": message,
        "time": time,
        "created_at": datetime.now().isoformat(),
    })

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    return f"[reminder] 已设置提醒：{time} — {message}"


def list_reminders(reminder_path: str | None = None) -> str:
    """List all pending reminders.

    Args:
        reminder_path: Path to the reminders JSON file.

    Returns:
        Formatted list of reminders, or an empty message.
    """
    path = Path(reminder_path) if reminder_path else _DEFAULT_REMINDERS

    if not path.exists():
        return "[reminder] 暂无提醒。"

    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "[reminder] 暂无提醒。"

    if not entries:
        return "[reminder] 暂无提醒。"

    lines = [f"[reminder] 当前有 {len(entries)} 条提醒："]
    for i, e in enumerate(entries, start=1):
        lines.append(f"  {i}. {e.get('time', '?')} — {e.get('message', '')}")
    return "\n".join(lines)
