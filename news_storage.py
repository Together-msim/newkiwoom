# news_storage.py
"""뉴스/급등주/테마 SQLite 저장소"""

import json
import logging
import sqlite3
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict

logger = logging.getLogger(__name__)

# 소스 채널 → source_type 매핑
# Seeking Signal (급등주): -1003342481653
# Signal Search (뉴스): -1003239561368
SOURCE_TYPE_MAP = {
    -1003342481653: "hot_stock",
    -1003239561368: "news",
}


def _get_source_type(source_chat_id: int) -> str:
    return SOURCE_TYPE_MAP.get(source_chat_id, "news")


class NewsStorage:
    """뉴스/급등주/테마 SQLite 저장소"""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_chat_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    message_id INTEGER NOT NULL,
                    text TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    date TEXT,
                    UNIQUE(source_chat_id, message_id)
                );

                CREATE TABLE IF NOT EXISTS filtered_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER REFERENCES messages(id),
                    dest_chat_id TEXT,
                    matched_keywords TEXT,
                    forwarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS themes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TIMESTAMP,
                    count INTEGER DEFAULT 1,
                    active BOOLEAN DEFAULT TRUE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);
                CREATE INDEX IF NOT EXISTS idx_messages_source_type ON messages(source_type);
                CREATE INDEX IF NOT EXISTS idx_messages_received_at ON messages(received_at);
            """)
        logger.info(f"NewsStorage 초기화 완료: {self.db_path}")

    # ─── 메시지 저장 ───────────────────────────────────────────

    def save_message(self, source_chat_id: int, message_id: int, text: str) -> Optional[int]:
        """수신 메시지 저장 (필터링 전 전체). 중복이면 기존 id 반환."""
        source_type = _get_source_type(source_chat_id)
        today = date.today().isoformat()
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    """INSERT OR IGNORE INTO messages
                       (source_chat_id, source_type, message_id, text, date)
                       VALUES (?, ?, ?, ?, ?)""",
                    (str(source_chat_id), source_type, message_id, text, today),
                )
                if cur.lastrowid:
                    return cur.lastrowid
                # 중복이면 기존 row id 반환
                row = conn.execute(
                    "SELECT id FROM messages WHERE source_chat_id=? AND message_id=?",
                    (str(source_chat_id), message_id),
                ).fetchone()
                return row["id"] if row else None
        except Exception as e:
            logger.error(f"save_message 실패: {e}")
            return None

    def save_filtered(self, message_db_id: int, dest_chat_id: int, matched_keywords: List[str]):
        """필터링 통과 메시지 기록."""
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO filtered_messages (message_id, dest_chat_id, matched_keywords)
                       VALUES (?, ?, ?)""",
                    (message_db_id, str(dest_chat_id), json.dumps(matched_keywords, ensure_ascii=False)),
                )
        except Exception as e:
            logger.error(f"save_filtered 실패: {e}")

    # ─── 조회 ──────────────────────────────────────────────────

    def get_messages(self, target_date: Optional[str] = None, source_type: Optional[str] = None) -> List[Dict]:
        """메시지 조회. target_date 없으면 오늘."""
        if target_date is None:
            target_date = date.today().isoformat()
        query = "SELECT * FROM messages WHERE date=?"
        params: list = [target_date]
        if source_type:
            query += " AND source_type=?"
            params.append(source_type)
        query += " ORDER BY received_at ASC"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_today_messages(self, source_type: Optional[str] = None) -> List[Dict]:
        return self.get_messages(source_type=source_type)

    def get_filtered_messages(self, target_date: Optional[str] = None, source_type: Optional[str] = None) -> List[Dict]:
        """필터링된 메시지 조회."""
        if target_date is None:
            target_date = date.today().isoformat()
        query = """
            SELECT m.*, f.dest_chat_id, f.matched_keywords, f.forwarded_at
            FROM filtered_messages f
            JOIN messages m ON f.message_id = m.id
            WHERE m.date=?
        """
        params: list = [target_date]
        if source_type:
            query += " AND m.source_type=?"
            params.append(source_type)
        query += " ORDER BY f.forwarded_at ASC"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_today_filtered(self, source_type: Optional[str] = None) -> List[Dict]:
        return self.get_filtered_messages(source_type=source_type)

    def get_messages_since(self, since_dt: str, source_type: Optional[str] = None) -> List[Dict]:
        """특정 시각 이후 메시지 조회 (인사이트 스킬용). since_dt: ISO format."""
        query = "SELECT * FROM messages WHERE received_at > ?"
        params: list = [since_dt]
        if source_type:
            query += " AND source_type=?"
            params.append(source_type)
        query += " ORDER BY received_at ASC"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_messages_by_ids(self, ids: List[int]) -> List[Dict]:
        """ID 목록으로 메시지 조회 (선택 인사이트 스킬용)."""
        if not ids:
            return []
        placeholders = ",".join("?" * len(ids))
        with self._conn() as conn:
            rows = conn.execute(
                f"SELECT * FROM messages WHERE id IN ({placeholders})", ids
            ).fetchall()
        return [dict(r) for r in rows]

    # ─── 테마 라이브러리 ────────────────────────────────────────

    def upsert_theme(self, name: str):
        """테마 추가 또는 count/last_seen 업데이트."""
        name = name.strip()
        if not name:
            return
        now = datetime.now().isoformat()
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO themes (name, last_seen_at)
                       VALUES (?, ?)
                       ON CONFLICT(name) DO UPDATE SET
                           count = count + 1,
                           last_seen_at = excluded.last_seen_at""",
                    (name, now),
                )
        except Exception as e:
            logger.error(f"upsert_theme 실패 ({name}): {e}")

    def get_themes(self, active_only: bool = False) -> List[Dict]:
        query = "SELECT * FROM themes"
        if active_only:
            query += " WHERE active=1"
        query += " ORDER BY count DESC, last_seen_at DESC"
        with self._conn() as conn:
            rows = conn.execute(query).fetchall()
        return [dict(r) for r in rows]

    def add_theme(self, name: str) -> bool:
        name = name.strip()
        if not name:
            return False
        try:
            with self._conn() as conn:
                conn.execute("INSERT OR IGNORE INTO themes (name) VALUES (?)", (name,))
            return True
        except Exception as e:
            logger.error(f"add_theme 실패: {e}")
            return False

    def toggle_theme(self, theme_id: int) -> bool:
        try:
            with self._conn() as conn:
                conn.execute(
                    "UPDATE themes SET active = NOT active WHERE id=?", (theme_id,)
                )
            return True
        except Exception as e:
            logger.error(f"toggle_theme 실패: {e}")
            return False

    def delete_theme(self, theme_id: int) -> bool:
        try:
            with self._conn() as conn:
                conn.execute("DELETE FROM themes WHERE id=?", (theme_id,))
            return True
        except Exception as e:
            logger.error(f"delete_theme 실패: {e}")
            return False
