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

                CREATE TABLE IF NOT EXISTS saved_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    text TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    original_date TEXT,
                    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS siwhang_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_id INTEGER REFERENCES messages(id),
                    stock_code TEXT,
                    stock_name TEXT,
                    tag_type TEXT,
                    theme TEXT,
                    related_stocks TEXT,
                    has_news_match BOOLEAN DEFAULT 0,
                    news_summary TEXT,
                    watchlist_match TEXT,
                    analysis_text TEXT,
                    date TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_messages_date ON messages(date);
                CREATE INDEX IF NOT EXISTS idx_messages_source_type ON messages(source_type);
                CREATE INDEX IF NOT EXISTS idx_messages_received_at ON messages(received_at);
                CREATE INDEX IF NOT EXISTS idx_saved_news_source_type ON saved_news(source_type);
                CREATE INDEX IF NOT EXISTS idx_saved_news_saved_at ON saved_news(saved_at);
                CREATE INDEX IF NOT EXISTS idx_siwhang_results_date ON siwhang_results(date);

                CREATE TABLE IF NOT EXISTS backtest_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_date TEXT NOT NULL,
                    version TEXT NOT NULL DEFAULT 'v1',
                    strategy_desc TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS backtest_picks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER REFERENCES backtest_sessions(id),
                    slot_time TEXT NOT NULL,
                    stock_code TEXT,
                    stock_name TEXT NOT NULL,
                    tag_type TEXT,
                    theme TEXT,
                    price_at_slot REAL,
                    analysis_text TEXT,
                    confidence TEXT,
                    catalyst TEXT,
                    source_message_id INTEGER,
                    note_source TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS backtest_pnl (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pick_id INTEGER UNIQUE REFERENCES backtest_picks(id),
                    buy_price REAL,
                    exit_price REAL,
                    stoploss_price REAL,
                    result TEXT,
                    profit_pct REAL,
                    notes TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_backtest_picks_session ON backtest_picks(session_id);
                CREATE INDEX IF NOT EXISTS idx_backtest_sessions_date ON backtest_sessions(run_date);
            """)
            # 기존 DB 마이그레이션 (컬럼 없으면 추가)
            for col, definition in [
                ("version", "TEXT NOT NULL DEFAULT 'v1'"),
                ("strategy_desc", "TEXT"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE backtest_sessions ADD COLUMN {col} {definition}")
                except Exception:
                    pass
            for col, definition in [
                ("catalyst", "TEXT"),
            ]:
                try:
                    conn.execute(f"ALTER TABLE backtest_picks ADD COLUMN {col} {definition}")
                except Exception:
                    pass
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

    def get_messages(self, target_date: Optional[str] = None, source_type: Optional[str] = None, until_utc: Optional[str] = None) -> List[Dict]:
        """메시지 조회. target_date 없으면 오늘. until_utc: received_at <= until_utc 필터 (ISO UTC)."""
        if target_date is None:
            target_date = date.today().isoformat()
        query = "SELECT * FROM messages WHERE date=?"
        params: list = [target_date]
        if source_type:
            query += " AND source_type=?"
            params.append(source_type)
        if until_utc:
            query += " AND received_at <= ?"
            params.append(until_utc)
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

    # ─── 삭제 / 정리 ───────────────────────────────────────────

    def delete_messages(self, ids: List[int], source_type: Optional[str] = None) -> int:
        """메시지 선택 삭제. source_type 지정 시 해당 타입만. filtered_messages도 같이 삭제."""
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        query = f"SELECT id FROM messages WHERE id IN ({placeholders})"
        params: list = list(ids)
        if source_type:
            query += " AND source_type=?"
            params.append(source_type)
        try:
            with self._conn() as conn:
                rows = conn.execute(query, params).fetchall()
                valid_ids = [r["id"] for r in rows]
                if not valid_ids:
                    return 0
                ph2 = ",".join("?" * len(valid_ids))
                conn.execute(f"DELETE FROM filtered_messages WHERE message_id IN ({ph2})", valid_ids)
                cur = conn.execute(f"DELETE FROM messages WHERE id IN ({ph2})", valid_ids)
                return cur.rowcount
        except Exception as e:
            logger.error(f"delete_messages 실패: {e}")
            return 0

    def cleanup_old_messages(self, source_type: Optional[str] = None) -> int:
        """오늘 날짜 이전 메시지 삭제 (saved_news는 보존). 삭제된 건수 반환.
        source_type 지정 시 해당 타입만 삭제."""
        today = date.today().isoformat()
        try:
            with self._conn() as conn:
                # saved_news에 있는 message_id는 보존
                saved_msg_ids = [
                    r["message_id"] for r in
                    conn.execute("SELECT message_id FROM saved_news WHERE message_id IS NOT NULL").fetchall()
                ]
                query = "SELECT id FROM messages WHERE date < ?"
                params: list = [today]
                if source_type:
                    query += " AND source_type = ?"
                    params.append(source_type)
                if saved_msg_ids:
                    ph = ",".join("?" * len(saved_msg_ids))
                    query += f" AND id NOT IN ({ph})"
                    params.extend(saved_msg_ids)
                old_ids = [r["id"] for r in conn.execute(query, params).fetchall()]
                if not old_ids:
                    return 0
                ph2 = ",".join("?" * len(old_ids))
                conn.execute(f"DELETE FROM filtered_messages WHERE message_id IN ({ph2})", old_ids)
                cur = conn.execute(f"DELETE FROM messages WHERE id IN ({ph2})", old_ids)
                deleted = cur.rowcount
                logger.info(f"cleanup_old_messages: {deleted}건 삭제 (date < {today}, source_type={source_type})")
                return deleted
        except Exception as e:
            logger.error(f"cleanup_old_messages 실패: {e}")
            return 0

    # ─── 스크래핑 (영구 보관) ───────────────────────────────────

    def save_scraped_news(self, message_id: Optional[int], text: str, source_type: str, original_date: str) -> Optional[int]:
        """중요 뉴스 영구 보관."""
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    """INSERT INTO saved_news (message_id, text, source_type, original_date)
                       VALUES (?, ?, ?, ?)""",
                    (message_id, text, source_type, original_date),
                )
                return cur.lastrowid
        except Exception as e:
            logger.error(f"save_scraped_news 실패: {e}")
            return None

    def get_saved_news(self, search_query: Optional[str] = None, source_type: Optional[str] = None) -> List[Dict]:
        """저장된 뉴스 조회. search_query: 텍스트 포함 검색."""
        query = "SELECT * FROM saved_news WHERE 1=1"
        params: list = []
        if source_type:
            query += " AND source_type=?"
            params.append(source_type)
        if search_query:
            query += " AND text LIKE ?"
            params.append(f"%{search_query}%")
        query += " ORDER BY saved_at DESC"
        with self._conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def delete_saved_news(self, saved_id: int) -> bool:
        """저장된 뉴스 삭제."""
        try:
            with self._conn() as conn:
                conn.execute("DELETE FROM saved_news WHERE id=?", (saved_id,))
            return True
        except Exception as e:
            logger.error(f"delete_saved_news 실패: {e}")
            return False

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

    # ─── 시황체크 분석 결과 ────────────────────────────────────

    def save_siwhang_results(self, results: List[Dict]) -> int:
        """시황체크 분석 결과 배치 저장. 저장된 건수 반환."""
        if not results:
            return 0
        today = date.today().isoformat()
        saved = 0
        try:
            with self._conn() as conn:
                for r in results:
                    conn.execute(
                        """INSERT INTO siwhang_results
                           (message_id, stock_code, stock_name, tag_type, theme,
                            related_stocks, has_news_match, news_summary, watchlist_match,
                            analysis_text, date)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            r.get('message_id'),
                            r.get('stock_code'),
                            r.get('stock_name'),
                            r.get('tag_type'),
                            r.get('theme'),
                            json.dumps(r.get('related_stocks', []), ensure_ascii=False),
                            1 if r.get('has_news_match') else 0,
                            r.get('news_summary'),
                            json.dumps(r.get('watchlist_match', []), ensure_ascii=False),
                            r.get('analysis_text'),
                            r.get('date', today),
                        )
                    )
                    saved += 1
        except Exception as e:
            logger.error(f"save_siwhang_results 실패: {e}")
        return saved

    def get_siwhang_results(self, target_date: Optional[str] = None) -> List[Dict]:
        """시황체크 분석 결과 조회."""
        if target_date is None:
            target_date = date.today().isoformat()
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM siwhang_results WHERE date=? ORDER BY run_at DESC",
                (target_date,)
            ).fetchall()
        results = []
        for r in rows:
            d = dict(r)
            for field in ('related_stocks', 'watchlist_match'):
                try:
                    d[field] = json.loads(d[field]) if d[field] else []
                except Exception:
                    d[field] = []
            results.append(d)
        return results

    # ─── 백테스트 ─────────────────────────────────────────────

    def create_backtest_session(self, run_date: str, notes: str = '',
                                version: str = 'v1', strategy_desc: str = '') -> Optional[int]:
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    "INSERT INTO backtest_sessions (run_date, notes, version, strategy_desc) VALUES (?, ?, ?, ?)",
                    (run_date, notes, version, strategy_desc),
                )
                return cur.lastrowid
        except Exception as e:
            logger.error(f"create_backtest_session 실패: {e}")
            return None

    def get_backtest_sessions(self) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM backtest_sessions ORDER BY created_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def save_backtest_pick(self, session_id: int, slot_time: str, stock_name: str,
                           stock_code: Optional[str] = None, tag_type: Optional[str] = None,
                           theme: Optional[str] = None, price_at_slot: Optional[float] = None,
                           analysis_text: Optional[str] = None, confidence: Optional[str] = None,
                           catalyst: Optional[str] = None,
                           source_message_id: Optional[int] = None,
                           note_source: Optional[str] = None) -> Optional[int]:
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    """INSERT INTO backtest_picks
                       (session_id, slot_time, stock_code, stock_name, tag_type, theme,
                        price_at_slot, analysis_text, confidence, catalyst, source_message_id, note_source)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (session_id, slot_time, stock_code, stock_name, tag_type, theme,
                     price_at_slot, analysis_text, confidence, catalyst, source_message_id, note_source),
                )
                return cur.lastrowid
        except Exception as e:
            logger.error(f"save_backtest_pick 실패: {e}")
            return None

    def get_backtest_picks(self, session_id: int) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT p.*, n.buy_price, n.exit_price, n.stoploss_price,
                          n.result, n.profit_pct, n.notes as pnl_notes
                   FROM backtest_picks p
                   LEFT JOIN backtest_pnl n ON n.pick_id = p.id
                   WHERE p.session_id=?
                   ORDER BY p.slot_time ASC, p.id ASC""",
                (session_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def upsert_backtest_pnl(self, pick_id: int, buy_price: Optional[float],
                             exit_price: Optional[float], stoploss_price: Optional[float],
                             result: Optional[str], profit_pct: Optional[float],
                             notes: str = '') -> bool:
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO backtest_pnl (pick_id, buy_price, exit_price, stoploss_price, result, profit_pct, notes)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(pick_id) DO UPDATE SET
                           buy_price=excluded.buy_price,
                           exit_price=excluded.exit_price,
                           stoploss_price=excluded.stoploss_price,
                           result=excluded.result,
                           profit_pct=excluded.profit_pct,
                           notes=excluded.notes,
                           updated_at=CURRENT_TIMESTAMP""",
                    (pick_id, buy_price, exit_price, stoploss_price, result, profit_pct, notes),
                )
            return True
        except Exception as e:
            logger.error(f"upsert_backtest_pnl 실패: {e}")
            return False
