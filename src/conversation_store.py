"""ConversationStore -- SQLite-backed multi-session persistence."""
import json, os, sqlite3, threading
from typing import Dict, Optional, Tuple

class ConversationStore:
    def __init__(self, db_path: str = ""):
        if not db_path:
            db_path = os.path.join(os.path.dirname(__file__), "..", "data", "conversations.db")
        db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._local = threading.local()
        self._init_db()

    def _get_conn(self):
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        return self._local.conn

    def _init_db(self):
        c = self._get_conn()
        c.execute("CREATE TABLE IF NOT EXISTS conversations (user_id TEXT PRIMARY KEY, data TEXT NOT NULL)")
        c.commit()

    def save(self, user_id, conversations, current_id):
        data = json.dumps({"current_id": current_id, "conversations": conversations}, ensure_ascii=False)
        c = self._get_conn()
        c.execute("INSERT OR REPLACE INTO conversations (user_id, data) VALUES (?, ?)", (user_id, data))
        c.commit()

    def load(self, user_id):
        c = self._get_conn()
        row = c.execute("SELECT data FROM conversations WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return None, None
        try:
            data = json.loads(row[0])
            return data.get("conversations", {}), data.get("current_id")
        except (json.JSONDecodeError, KeyError):
            return None, None
