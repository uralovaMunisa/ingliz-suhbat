import os
import sqlite3
from pathlib import Path
from typing import Optional, List, Dict, Any


class Database:
    """SQLite database manager for Emma English Tutor."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.getenv("DATABASE_PATH", "data/emma_bot.db")
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    async def init_db(self):
        conn = self._get_connection()
        try:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    name TEXT,
                    level TEXT DEFAULT 'B1',
                    goal TEXT DEFAULT 'Daily conversation',
                    correction_mode TEXT DEFAULT 'standard',
                    onboarding_state TEXT DEFAULT 'completed',
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    role TEXT,
                    content TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS mistakes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    original_text TEXT,
                    corrected_text TEXT,
                    explanation TEXT,
                    explanation_uz TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                );
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    phrase TEXT,
                    definition TEXT,
                    example TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                );
            """)

            conn.execute("CREATE INDEX IF NOT EXISTS idx_history_user ON chat_history (user_id, timestamp);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_mistakes_user ON mistakes (user_id, timestamp);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_vocabulary_user ON vocabulary (user_id, timestamp);")
            conn.commit()
        finally:
            conn.close()

    async def get_or_create_user(self, user_id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)

            default_name = first_name or (f"@{username}" if username else "Friend")
            conn.execute("""
                INSERT INTO users (user_id, username, first_name, name, level, goal, correction_mode, onboarding_state)
                VALUES (?, ?, ?, ?, 'B1', 'Daily conversation', 'standard', 'completed')
            """, (user_id, username, first_name, default_name))
            conn.commit()

            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            new_row = cursor.fetchone()
            return dict(new_row)
        finally:
            conn.close()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    async def update_user(self, user_id: int, **kwargs):
        if not kwargs:
            return
        fields = []
        values = []
        for k, v in kwargs.items():
            fields.append(f"{k} = ?")
            values.append(v)
        fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(user_id)

        query = f"UPDATE users SET {', '.join(fields)} WHERE user_id = ?"
        conn = self._get_connection()
        try:
            conn.execute(query, tuple(values))
            conn.commit()
        finally:
            conn.close()

    async def increment_message_count(self, user_id: int) -> int:
        conn = self._get_connection()
        try:
            conn.execute("""
                UPDATE users SET message_count = message_count + 1 WHERE user_id = ?
            """, (user_id,))
            conn.commit()
            cursor = conn.execute("SELECT message_count FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return row["message_count"] if row else 1
        finally:
            conn.close()

    async def reset_message_count(self, user_id: int):
        conn = self._get_connection()
        try:
            conn.execute("UPDATE users SET message_count = 0 WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()

    async def add_chat_message(self, user_id: int, role: str, content: str):
        conn = self._get_connection()
        try:
            conn.execute("""
                INSERT INTO chat_history (user_id, role, content)
                VALUES (?, ?, ?)
            """, (user_id, role, content))
            conn.commit()
        finally:
            conn.close()

    async def get_recent_chat_history(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT role, content, timestamp FROM chat_history
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in reversed(rows)]
        finally:
            conn.close()

    async def clear_chat_history(self, user_id: int):
        conn = self._get_connection()
        try:
            conn.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
            conn.commit()
        finally:
            conn.close()

    async def log_mistake(self, user_id: int, original: str, corrected: str, explanation: str, explanation_uz: Optional[str] = None) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO mistakes (user_id, original_text, corrected_text, explanation, explanation_uz)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, original, corrected, explanation, explanation_uz))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    async def get_mistake(self, mistake_id: int) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM mistakes WHERE id = ?", (mistake_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    async def update_mistake_uzbek(self, mistake_id: int, explanation_uz: str):
        conn = self._get_connection()
        try:
            conn.execute("UPDATE mistakes SET explanation_uz = ? WHERE id = ?", (explanation_uz, mistake_id))
            conn.commit()
        finally:
            conn.close()

    async def get_recent_mistakes(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM mistakes
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    async def log_vocabulary(self, user_id: int, phrase: str, definition: str, example: str) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                INSERT INTO vocabulary (user_id, phrase, definition, example)
                VALUES (?, ?, ?, ?)
            """, (user_id, phrase, definition, example))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    async def get_recent_vocabulary(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.execute("""
                SELECT * FROM vocabulary
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (user_id, limit))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()
