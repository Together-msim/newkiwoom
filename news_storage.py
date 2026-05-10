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

                CREATE TABLE IF NOT EXISTS analysis_context (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_date TEXT NOT NULL UNIQUE,
                    morning_report TEXT,
                    interval_context TEXT,
                    next_instruction TEXT,
                    instruction_used INTEGER NOT NULL DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS trading_mottos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS stock_master (
                    stock_code TEXT PRIMARY KEY,
                    stock_name TEXT,
                    corp_code TEXT,
                    themes TEXT,
                    note TEXT,
                    market_cap_bil REAL,
                    per REAL,
                    roe REAL,
                    debt_ratio REAL,
                    current_ratio REAL,
                    op_income_bil REAL,
                    op_income_prev_bil REAL,
                    finance_updated_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS stock_siwhang_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT,
                    event_date TEXT NOT NULL,
                    tag_type TEXT,
                    theme TEXT,
                    feed_text TEXT,
                    source_message_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_stock_siwhang_history_code ON stock_siwhang_history(stock_code);
                CREATE INDEX IF NOT EXISTS idx_stock_siwhang_history_date ON stock_siwhang_history(event_date);

                CREATE TABLE IF NOT EXISTS trade_watchlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    stock_name TEXT NOT NULL,
                    buy_price REAL,
                    buy_date TEXT,
                    exit_price REAL,
                    exit_date TEXT,
                    status TEXT NOT NULL DEFAULT 'watching',
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS reentry_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    watchlist_id INTEGER REFERENCES trade_watchlist(id),
                    stock_code TEXT,
                    stock_name TEXT,
                    signal_type TEXT,
                    signal_date TEXT,
                    entry_price_suggestion REAL,
                    confidence TEXT,
                    reason TEXT,
                    ss_matched INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_trade_watchlist_status ON trade_watchlist(status);
                CREATE INDEX IF NOT EXISTS idx_reentry_signals_date ON reentry_signals(signal_date);
                CREATE INDEX IF NOT EXISTS idx_reentry_signals_code ON reentry_signals(stock_code);

                CREATE TABLE IF NOT EXISTS stock_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stock_code TEXT NOT NULL,
                    note_date TEXT NOT NULL,
                    content TEXT NOT NULL,
                    source TEXT DEFAULT 'manual',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_stock_notes_code ON stock_notes(stock_code);
                CREATE INDEX IF NOT EXISTS idx_stock_notes_date ON stock_notes(note_date);

                CREATE TABLE IF NOT EXISTS watchlist_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    file_origin TEXT,
                    pinned INTEGER NOT NULL DEFAULT 1,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS watchlist_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL REFERENCES watchlist_groups(id),
                    item_type TEXT NOT NULL DEFAULT 'stock',
                    stock_code TEXT,
                    stock_name TEXT,
                    subgroup_label TEXT,
                    memo TEXT,
                    display_order INTEGER NOT NULL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_watchlist_items_group ON watchlist_items(group_id);
                CREATE INDEX IF NOT EXISTS idx_watchlist_items_code ON watchlist_items(stock_code);
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
                ("sources_json", "TEXT"),
                ("price_at_signal", "REAL"),   # [SS/VI] 메시지 수신 시점 3분봉 종가
                ("prev_close", "REAL"),         # 전일 종가 (등락률 기준)
                ("today_open", "REAL"),         # 당일 시가 (등락률 기준)
            ]:
                try:
                    conn.execute(f"ALTER TABLE backtest_picks ADD COLUMN {col} {definition}")
                except Exception:
                    pass
            for col, definition in [
                ("analysis_request", "TEXT"),  # ISO datetime, null이면 pending 없음
            ]:
                try:
                    conn.execute(f"ALTER TABLE analysis_context ADD COLUMN {col} {definition}")
                except Exception:
                    pass
            for col, definition in [
                ("confidence", "TEXT"),       # H/M/L
                ("catalyst", "TEXT"),         # 촉매/시황 요약
                ("slot_time", "TEXT"),        # run_at 기반 슬롯 (09:15 등)
                ("price_at_slot", "REAL"),    # 추천 시점 현재가
                ("sources_json", "TEXT"),     # [{type, text}] 근거 목록
            ]:
                try:
                    conn.execute(f"ALTER TABLE siwhang_results ADD COLUMN {col} {definition}")
                except Exception:
                    pass
            for col, definition in [
                ("signal_time", "TEXT"),      # HH:MM 장중 시간
                ("support_price", "REAL"),    # C2 쌍바닥 지지가
                ("source", "TEXT DEFAULT 'watchlist'"),  # watchlist / morning
            ]:
                try:
                    conn.execute(f"ALTER TABLE reentry_signals ADD COLUMN {col} {definition}")
                except Exception:
                    pass
            for col, definition in [
                ("summary_2line", "TEXT"),    # AI 생성 2줄 요약
            ]:
                try:
                    conn.execute(f"ALTER TABLE stock_master ADD COLUMN {col} {definition}")
                except Exception:
                    pass
            # live_pick_backtest 테이블 생성 (없으면)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS live_pick_backtest (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pick_id INTEGER NOT NULL REFERENCES backtest_picks(id),
                    stock_code TEXT,
                    backtest_date TEXT NOT NULL,
                    slot_time TEXT,
                    c_signals_json TEXT,
                    closing_price REAL,
                    price_change_from_signal_pct REAL,
                    price_change_from_slot_pct REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_live_pick_backtest_pick_id
                ON live_pick_backtest(pick_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_live_pick_backtest_date
                ON live_pick_backtest(backtest_date)
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
        from datetime import timezone, timedelta
        today = (datetime.now(timezone.utc) + timedelta(hours=9)).date().isoformat()
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
                           sources: Optional[List[Dict]] = None,
                           source_message_id: Optional[int] = None,
                           note_source: Optional[str] = None,
                           price_at_signal: Optional[float] = None,
                           prev_close: Optional[float] = None,
                           today_open: Optional[float] = None) -> Optional[int]:
        """
        sources: [{"type":"hotstock"|"news"|"google"|"dart", "time":"HH:MM KST", "text":"..."}]
        price_at_signal: [SS/VI] 메시지 수신 시점 3분봉 종가
        prev_close: 전일 종가 (등락률 기준)
        today_open: 당일 시가 (등락률 기준)
        """
        sources_json = json.dumps(sources, ensure_ascii=False) if sources else None
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    """INSERT INTO backtest_picks
                       (session_id, slot_time, stock_code, stock_name, tag_type, theme,
                        price_at_slot, analysis_text, confidence, catalyst, sources_json,
                        source_message_id, note_source,
                        price_at_signal, prev_close, today_open)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (session_id, slot_time, stock_code, stock_name, tag_type, theme,
                     price_at_slot, analysis_text, confidence, catalyst, sources_json,
                     source_message_id, note_source,
                     price_at_signal, prev_close, today_open),
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
        result = []
        for r in rows:
            d = dict(r)
            try:
                d['sources'] = json.loads(d['sources_json']) if d.get('sources_json') else []
            except Exception:
                d['sources'] = []
            result.append(d)
        return result

    def upsert_live_pick_backtest(self, pick_id: int, stock_code: Optional[str],
                                  backtest_date: str, slot_time: Optional[str],
                                  c_signals: Optional[List[Dict]],
                                  closing_price: Optional[float],
                                  price_change_from_signal_pct: Optional[float],
                                  price_change_from_slot_pct: Optional[float]) -> Optional[int]:
        """장마감 백테스트 결과 저장/덮어쓰기 (pick_id 기준 upsert)."""
        c_signals_json = json.dumps(c_signals, ensure_ascii=False) if c_signals is not None else None
        try:
            with self._conn() as conn:
                cur = conn.execute(
                    """INSERT INTO live_pick_backtest
                       (pick_id, stock_code, backtest_date, slot_time, c_signals_json,
                        closing_price, price_change_from_signal_pct, price_change_from_slot_pct)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                       ON CONFLICT(pick_id) DO UPDATE SET
                           c_signals_json=excluded.c_signals_json,
                           closing_price=excluded.closing_price,
                           price_change_from_signal_pct=excluded.price_change_from_signal_pct,
                           price_change_from_slot_pct=excluded.price_change_from_slot_pct,
                           created_at=CURRENT_TIMESTAMP""",
                    (pick_id, stock_code, backtest_date, slot_time, c_signals_json,
                     closing_price, price_change_from_signal_pct, price_change_from_slot_pct),
                )
                return cur.lastrowid
        except Exception as e:
            logger.error(f"upsert_live_pick_backtest 실패: {e}")
            return None

    def get_live_pick_backtest_by_date(self, backtest_date: str) -> Dict[int, Dict]:
        """날짜별 pick_id → backtest 결과 매핑 반환."""
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    "SELECT * FROM live_pick_backtest WHERE backtest_date=?",
                    (backtest_date,)
                ).fetchall()
            result = {}
            for r in rows:
                d = dict(r)
                try:
                    d['c_signals'] = json.loads(d['c_signals_json']) if d.get('c_signals_json') else []
                except Exception:
                    d['c_signals'] = []
                result[d['pick_id']] = d
            return result
        except Exception as e:
            logger.error(f"get_live_pick_backtest_by_date 실패: {e}")
            return {}

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

    # ─── 분석 컨텍스트 ─────────────────────────────────────────

    def get_analysis_context(self, context_date: Optional[str] = None) -> Dict:
        """당일 분석 컨텍스트 조회. 없으면 빈 구조 반환."""
        if context_date is None:
            context_date = date.today().isoformat()
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM analysis_context WHERE context_date=?", (context_date,)
            ).fetchone()
        if not row:
            return {
                "context_date": context_date,
                "morning_report": None,
                "interval_context": None,
                "next_instruction": None,
                "instruction_used": 0,
            }
        d = dict(row)
        for field in ("morning_report", "interval_context"):
            if d.get(field):
                try:
                    d[field] = json.loads(d[field])
                except Exception:
                    pass
        return d

    def save_morning_report(self, morning_report: dict, context_date: Optional[str] = None) -> bool:
        if context_date is None:
            context_date = date.today().isoformat()
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO analysis_context (context_date, morning_report, updated_at)
                       VALUES (?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(context_date) DO UPDATE SET
                           morning_report=excluded.morning_report,
                           updated_at=CURRENT_TIMESTAMP""",
                    (context_date, json.dumps(morning_report, ensure_ascii=False)),
                )
            return True
        except Exception as e:
            logger.error(f"save_morning_report 실패: {e}")
            return False

    def save_next_instruction(self, instruction: Optional[str], context_date: Optional[str] = None) -> bool:
        if context_date is None:
            context_date = date.today().isoformat()
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO analysis_context (context_date, next_instruction, instruction_used, updated_at)
                       VALUES (?, ?, 0, CURRENT_TIMESTAMP)
                       ON CONFLICT(context_date) DO UPDATE SET
                           next_instruction=excluded.next_instruction,
                           instruction_used=0,
                           updated_at=CURRENT_TIMESTAMP""",
                    (context_date, instruction),
                )
            return True
        except Exception as e:
            logger.error(f"save_next_instruction 실패: {e}")
            return False

    def update_interval_context(self, interval_context: dict, context_date: Optional[str] = None) -> bool:
        """슬롯 분석 완료 후 누적 테마 컨텍스트 업데이트."""
        if context_date is None:
            context_date = date.today().isoformat()
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO analysis_context (context_date, interval_context, updated_at)
                       VALUES (?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(context_date) DO UPDATE SET
                           interval_context=excluded.interval_context,
                           updated_at=CURRENT_TIMESTAMP""",
                    (context_date, json.dumps(interval_context, ensure_ascii=False)),
                )
            return True
        except Exception as e:
            logger.error(f"update_interval_context 실패: {e}")
            return False

    def consume_next_instruction(self, context_date: Optional[str] = None) -> Optional[str]:
        """next_instruction 읽고 used 처리. 스킬 실행 시 1회 호출."""
        if context_date is None:
            context_date = date.today().isoformat()
        try:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT next_instruction, instruction_used FROM analysis_context WHERE context_date=?",
                    (context_date,),
                ).fetchone()
                if not row or row["instruction_used"] == 1 or not row["next_instruction"]:
                    return None
                conn.execute(
                    "UPDATE analysis_context SET instruction_used=1, updated_at=CURRENT_TIMESTAMP WHERE context_date=?",
                    (context_date,),
                )
                return row["next_instruction"]
        except Exception as e:
            logger.error(f"consume_next_instruction 실패: {e}")
            return None

    # ─── 분석 요청 트리거 ────────────────────────────────────────

    def set_analysis_request(self, context_date: Optional[str] = None) -> bool:
        """분석 요청 플래그 세팅. poll_trigger.py가 감지해 /siwhang 실행."""
        if context_date is None:
            context_date = date.today().isoformat()
        requested_at = datetime.utcnow().isoformat()
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO analysis_context (context_date, analysis_request, updated_at)
                       VALUES (?, ?, CURRENT_TIMESTAMP)
                       ON CONFLICT(context_date) DO UPDATE SET
                           analysis_request=excluded.analysis_request,
                           updated_at=CURRENT_TIMESTAMP""",
                    (context_date, requested_at),
                )
            return True
        except Exception as e:
            logger.error(f"set_analysis_request 실패: {e}")
            return False

    def get_and_clear_analysis_request(self, context_date: Optional[str] = None) -> Optional[str]:
        """pending 요청 읽고 즉시 null로 클리어. poll_trigger.py 전용."""
        if context_date is None:
            context_date = date.today().isoformat()
        try:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT analysis_request FROM analysis_context WHERE context_date=?",
                    (context_date,)
                ).fetchone()
                if not row or not row["analysis_request"]:
                    return None
                val = row["analysis_request"]
                conn.execute(
                    "UPDATE analysis_context SET analysis_request=NULL, updated_at=CURRENT_TIMESTAMP WHERE context_date=?",
                    (context_date,)
                )
                return val
        except Exception as e:
            logger.error(f"get_and_clear_analysis_request 실패: {e}")
            return None

    # ─── 격언(Trading Mottos) ──────────────────────────────────

    def get_mottos(self) -> List[Dict]:
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    "SELECT id, content, display_order, created_at FROM trading_mottos ORDER BY display_order ASC, id ASC"
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"get_mottos 실패: {e}")
            return []

    def add_motto(self, content: str) -> Optional[int]:
        try:
            with self._conn() as conn:
                max_order = conn.execute("SELECT COALESCE(MAX(display_order), -1) FROM trading_mottos").fetchone()[0]
                cur = conn.execute(
                    "INSERT INTO trading_mottos (content, display_order) VALUES (?, ?)",
                    (content.strip(), max_order + 1),
                )
                return cur.lastrowid
        except Exception as e:
            logger.error(f"add_motto 실패: {e}")
            return None

    def update_motto(self, motto_id: int, content: str) -> bool:
        try:
            with self._conn() as conn:
                conn.execute(
                    "UPDATE trading_mottos SET content=? WHERE id=?",
                    (content.strip(), motto_id),
                )
                return True
        except Exception as e:
            logger.error(f"update_motto 실패: {e}")
            return False

    def delete_motto(self, motto_id: int) -> bool:
        try:
            with self._conn() as conn:
                conn.execute("DELETE FROM trading_mottos WHERE id=?", (motto_id,))
                return True
        except Exception as e:
            logger.error(f"delete_motto 실패: {e}")
            return False

    def reorder_mottos(self, ordered_ids: List[int]) -> bool:
        try:
            with self._conn() as conn:
                for idx, mid in enumerate(ordered_ids):
                    conn.execute("UPDATE trading_mottos SET display_order=? WHERE id=?", (idx, mid))
                return True
        except Exception as e:
            logger.error(f"reorder_mottos 실패: {e}")
            return False

    # ─── 종목 마스터 (stock_master) ──────────────────────────────

    def get_stock_master_notes(self, codes: list) -> dict:
        """여러 종목코드의 note/summary_2line 일괄 조회. {code: {note, summary_2line}}"""
        if not codes:
            return {}
        try:
            placeholders = ','.join('?' * len(codes))
            with self._conn() as conn:
                rows = conn.execute(
                    f"SELECT stock_code, note, summary_2line FROM stock_master WHERE stock_code IN ({placeholders})",
                    codes
                ).fetchall()
                return {r['stock_code']: {'note': r['note'] or '', 'summary_2line': r['summary_2line'] or ''} for r in rows}
        except Exception as e:
            logger.error(f"get_stock_master_notes 실패: {e}")
            return {}

    def get_stock_master(self, stock_code: str) -> Optional[Dict]:
        try:
            with self._conn() as conn:
                row = conn.execute(
                    "SELECT * FROM stock_master WHERE stock_code=?", (stock_code,)
                ).fetchone()
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"get_stock_master 실패: {e}")
            return None

    def upsert_stock_master(self, stock_code: str, **fields) -> bool:
        """stock_master 행 생성 또는 업데이트. fields의 키만 업데이트."""
        allowed = {
            'stock_name', 'corp_code', 'themes', 'note',
            'market_cap_bil', 'per', 'roe', 'debt_ratio', 'current_ratio',
            'op_income_bil', 'op_income_prev_bil', 'finance_updated_at',
        }
        fields = {k: v for k, v in fields.items() if k in allowed}
        if not fields:
            return False
        try:
            with self._conn() as conn:
                existing = conn.execute(
                    "SELECT stock_code FROM stock_master WHERE stock_code=?", (stock_code,)
                ).fetchone()
                if existing:
                    set_clause = ', '.join(f"{k}=?" for k in fields) + ", updated_at=CURRENT_TIMESTAMP"
                    conn.execute(
                        f"UPDATE stock_master SET {set_clause} WHERE stock_code=?",
                        list(fields.values()) + [stock_code]
                    )
                else:
                    cols = ['stock_code'] + list(fields.keys())
                    placeholders = ', '.join(['?'] * len(cols))
                    conn.execute(
                        f"INSERT INTO stock_master ({', '.join(cols)}) VALUES ({placeholders})",
                        [stock_code] + list(fields.values())
                    )
            return True
        except Exception as e:
            logger.error(f"upsert_stock_master 실패: {e}")
            return False

    # ─── 종목 시황 히스토리 (stock_siwhang_history) ───────────────

    def add_stock_siwhang_history(self, stock_code: str, stock_name: str,
                                   event_date: str, tag_type: str,
                                   theme: str, feed_text: str,
                                   source_message_id: Optional[int] = None) -> bool:
        try:
            with self._conn() as conn:
                conn.execute(
                    """INSERT INTO stock_siwhang_history
                       (stock_code, stock_name, event_date, tag_type, theme, feed_text, source_message_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (stock_code, stock_name, event_date, tag_type, theme, feed_text, source_message_id)
                )
            return True
        except Exception as e:
            logger.error(f"add_stock_siwhang_history 실패: {e}")
            return False

    def get_stock_siwhang_history(self, stock_code: str, limit: int = 10) -> List[Dict]:
        try:
            with self._conn() as conn:
                rows = conn.execute(
                    """SELECT id, event_date, tag_type, theme, feed_text, source_message_id, created_at
                       FROM stock_siwhang_history
                       WHERE stock_code=?
                       ORDER BY event_date DESC, id DESC
                       LIMIT ?""",
                    (stock_code, limit)
                ).fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"get_stock_siwhang_history 실패: {e}")
            return []

    # ─── 매매 감시 목록 (trade_watchlist) ─────────────────────────

    def add_trade_watchlist(self, stock_code: str, stock_name: str,
                             buy_price: float, buy_date: str,
                             exit_price: float, exit_date: str,
                             notes: str = "", status: str = "watching") -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO trade_watchlist
                   (stock_code, stock_name, buy_price, buy_date, exit_price, exit_date, notes, status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (stock_code, stock_name, buy_price, buy_date, exit_price, exit_date, notes, status)
            )
            return cur.lastrowid

    def get_trade_watchlist(self, status: Optional[str] = None) -> List[Dict]:
        with self._conn() as conn:
            if status:
                rows = conn.execute(
                    "SELECT * FROM trade_watchlist WHERE status=? ORDER BY created_at DESC",
                    (status,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM trade_watchlist ORDER BY created_at DESC"
                ).fetchall()
            return [dict(r) for r in rows]

    def update_trade_watchlist(self, watchlist_id: int, **fields) -> bool:
        allowed = {"status", "buy_price", "buy_date", "exit_price", "exit_date", "notes", "stock_name"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        set_clause = ", ".join(f"{k}=?" for k in updates)
        try:
            with self._conn() as conn:
                conn.execute(
                    f"UPDATE trade_watchlist SET {set_clause} WHERE id=?",
                    list(updates.values()) + [watchlist_id]
                )
            return True
        except Exception as e:
            logger.error(f"update_trade_watchlist 실패: {e}")
            return False

    def delete_trade_watchlist(self, watchlist_id: int) -> bool:
        try:
            with self._conn() as conn:
                conn.execute("DELETE FROM trade_watchlist WHERE id=?", (watchlist_id,))
            return True
        except Exception as e:
            logger.error(f"delete_trade_watchlist 실패: {e}")
            return False

    # ─── 재진입 시그널 (reentry_signals) ──────────────────────────

    def get_latest_signal_today(self, stock_code: str, signal_type: str, signal_date: str) -> Optional[Dict]:
        """오늘 해당 종목+타입의 가장 최근 시그널 1개 반환. dedup 판단용."""
        with self._conn() as conn:
            row = conn.execute(
                """SELECT * FROM reentry_signals
                   WHERE stock_code=? AND signal_type=? AND signal_date=?
                   ORDER BY created_at DESC LIMIT 1""",
                (stock_code, signal_type, signal_date)
            ).fetchone()
        return dict(row) if row else None

    def save_reentry_signal(self, watchlist_id: int, stock_code: str, stock_name: str,
                             signal_type: str, signal_date: str,
                             entry_price_suggestion: float, confidence: str,
                             reason: str, ss_matched: bool = False,
                             signal_time: str = '', support_price: float = 0,
                             source: str = 'watchlist') -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO reentry_signals
                   (watchlist_id, stock_code, stock_name, signal_type, signal_date,
                    entry_price_suggestion, confidence, reason, ss_matched,
                    signal_time, support_price, source)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (watchlist_id, stock_code, stock_name, signal_type, signal_date,
                 entry_price_suggestion, confidence, reason, 1 if ss_matched else 0,
                 signal_time, support_price, source)
            )
            return cur.lastrowid

    def get_morning_signals(self, signal_date: Optional[str] = None) -> List[Dict]:
        """morning_watchlist 출처 시그널 조회 — 종목별로 그룹핑된 딕셔너리 반환."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT stock_code, stock_name, signal_type, signal_time,
                          entry_price_suggestion, confidence, reason, support_price
                   FROM reentry_signals
                   WHERE source='morning' AND signal_date=?
                   ORDER BY stock_code, signal_time""",
                (signal_date or date.today().isoformat(),)
            ).fetchall()
        grouped: dict = {}
        for r in rows:
            d = dict(r)
            code = d['stock_code']
            if code not in grouped:
                grouped[code] = {'stock_code': code, 'stock_name': d['stock_name'], 'signals': []}
            grouped[code]['signals'].append({
                'type': d['signal_type'],
                'time': d['signal_time'],
                'price': d['entry_price_suggestion'],
                'confidence': d['confidence'],
                'reason': d['reason'],
                'support_price': d['support_price'],
            })
        return list(grouped.values())

    def get_reentry_signals(self, signal_date: Optional[str] = None, limit: int = 50) -> List[Dict]:
        with self._conn() as conn:
            if signal_date:
                rows = conn.execute(
                    """SELECT r.*, w.buy_price, w.exit_price, w.buy_date, w.exit_date
                       FROM reentry_signals r
                       LEFT JOIN trade_watchlist w ON r.watchlist_id = w.id
                       WHERE r.signal_date=?
                       ORDER BY r.created_at DESC LIMIT ?""",
                    (signal_date, limit)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT r.*, w.buy_price, w.exit_price, w.buy_date, w.exit_date
                       FROM reentry_signals r
                       LEFT JOIN trade_watchlist w ON r.watchlist_id = w.id
                       ORDER BY r.created_at DESC LIMIT ?""",
                    (limit,)
                ).fetchall()
            return [dict(r) for r in rows]

    # ─── 종목 노트 (stock_master.note 단일 텍스트) ────────────────

    def update_stock_note(self, stock_code: str, note: str) -> bool:
        """stock_master.note 전체 텍스트 저장."""
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO stock_master (stock_code, note, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(stock_code) DO UPDATE SET
                       note=excluded.note,
                       updated_at=CURRENT_TIMESTAMP""",
                (stock_code, note)
            )
            return True

    def prepend_stock_note(self, stock_code: str, date_str: str, content: str) -> str:
        """날짜+내용을 기존 노트 앞에 붙여서 저장. 새 노트 텍스트 반환."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT note FROM stock_master WHERE stock_code=?", (stock_code,)
            ).fetchone()
            existing = (row['note'] or '') if row else ''
            new_block = f"{date_str} {content.strip()}"
            merged = new_block + ('\n\n' + existing if existing else '')
            conn.execute(
                """INSERT INTO stock_master (stock_code, note, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(stock_code) DO UPDATE SET
                       note=excluded.note, updated_at=CURRENT_TIMESTAMP""",
                (stock_code, merged)
            )
            return merged

    def update_stock_summary(self, stock_code: str, summary_2line: str) -> bool:
        with self._conn() as conn:
            conn.execute(
                """INSERT INTO stock_master (stock_code, summary_2line, updated_at)
                   VALUES (?, ?, CURRENT_TIMESTAMP)
                   ON CONFLICT(stock_code) DO UPDATE SET
                       summary_2line=excluded.summary_2line,
                       updated_at=CURRENT_TIMESTAMP""",
                (stock_code, summary_2line)
            )
            return True

    def search_stock_master(self, query: str, limit: int = 20) -> List[Dict]:
        """종목명 또는 코드로 stock_master 검색."""
        q = f'%{query}%'
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT stock_code, stock_name, themes, note, summary_2line,
                          market_cap_bil, per, roe, debt_ratio, current_ratio, op_income_bil,
                          finance_updated_at, updated_at
                   FROM stock_master
                   WHERE stock_name LIKE ? OR stock_code LIKE ?
                   ORDER BY updated_at DESC LIMIT ?""",
                (q, q, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_stock_master_list(self, limit: int = 30, offset: int = 0) -> List[Dict]:
        """전체 목록 (페이지네이션)."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT stock_code, stock_name, themes, note, summary_2line, updated_at
                   FROM stock_master ORDER BY updated_at DESC LIMIT ? OFFSET ?""",
                (limit, offset)
            ).fetchall()
            return [dict(r) for r in rows]

    # ─── 관심종목 그룹 (watchlist_groups / watchlist_items) ────────

    def get_watchlist_groups(self, pinned_only: bool = False) -> List[Dict]:
        with self._conn() as conn:
            if pinned_only:
                rows = conn.execute(
                    "SELECT * FROM watchlist_groups WHERE pinned=1 ORDER BY display_order, id"
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM watchlist_groups ORDER BY display_order, id"
                ).fetchall()
            return [dict(r) for r in rows]

    def get_watchlist_items(self, group_id: int) -> List[Dict]:
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT * FROM watchlist_items WHERE group_id=?
                   ORDER BY display_order, id""",
                (group_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_watchlist_item_by_code(self, stock_code: str) -> List[Dict]:
        """종목코드로 전체 그룹에서 검색."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT wi.*, wg.name as group_name
                   FROM watchlist_items wi
                   JOIN watchlist_groups wg ON wi.group_id = wg.id
                   WHERE wi.stock_code=? AND wi.item_type='stock'""",
                (stock_code,)
            ).fetchall()
            return [dict(r) for r in rows]

    def search_watchlist(self, query: str, limit: int = 50) -> List[Dict]:
        """종목명/코드/메모 전체 검색."""
        q = f"%{query}%"
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT wi.*, wg.name as group_name
                   FROM watchlist_items wi
                   JOIN watchlist_groups wg ON wi.group_id = wg.id
                   WHERE wi.item_type='stock'
                     AND (wi.stock_name LIKE ? OR wi.stock_code LIKE ? OR wi.memo LIKE ?)
                   ORDER BY wg.display_order, wi.display_order
                   LIMIT ?""",
                (q, q, q, limit)
            ).fetchall()
            return [dict(r) for r in rows]

    def add_watchlist_group(self, name: str, file_origin: str = None, pinned: bool = True,
                            display_order: int = 0) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO watchlist_groups (name, file_origin, pinned, display_order)
                   VALUES (?, ?, ?, ?)""",
                (name, file_origin, 1 if pinned else 0, display_order)
            )
            return cur.lastrowid

    def update_watchlist_group(self, group_id: int, **fields) -> bool:
        allowed = {'name', 'pinned', 'display_order'}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        set_clause = ', '.join(f"{k}=?" for k in updates)
        try:
            with self._conn() as conn:
                conn.execute(
                    f"UPDATE watchlist_groups SET {set_clause} WHERE id=?",
                    (*updates.values(), group_id)
                )
            return True
        except Exception as e:
            logger.error(f"update_watchlist_group 실패: {e}")
            return False

    def delete_watchlist_group(self, group_id: int) -> bool:
        try:
            with self._conn() as conn:
                conn.execute("DELETE FROM watchlist_items WHERE group_id=?", (group_id,))
                conn.execute("DELETE FROM watchlist_groups WHERE id=?", (group_id,))
            return True
        except Exception as e:
            logger.error(f"delete_watchlist_group 실패: {e}")
            return False

    def add_watchlist_item(self, group_id: int, item_type: str, stock_code: str = None,
                           stock_name: str = None, subgroup_label: str = None,
                           memo: str = None, display_order: int = 0) -> int:
        with self._conn() as conn:
            cur = conn.execute(
                """INSERT INTO watchlist_items
                   (group_id, item_type, stock_code, stock_name, subgroup_label, memo, display_order)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (group_id, item_type, stock_code, stock_name, subgroup_label, memo, display_order)
            )
            return cur.lastrowid

    def update_watchlist_item(self, item_id: int, **fields) -> bool:
        allowed = {'memo', 'display_order', 'stock_name', 'subgroup_label', 'group_id'}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return False
        set_clause = ', '.join(f"{k}=?" for k in updates)
        try:
            with self._conn() as conn:
                conn.execute(
                    f"UPDATE watchlist_items SET {set_clause} WHERE id=?",
                    (*updates.values(), item_id)
                )
            return True
        except Exception as e:
            logger.error(f"update_watchlist_item 실패: {e}")
            return False

    def delete_watchlist_item(self, item_id: int) -> bool:
        try:
            with self._conn() as conn:
                conn.execute("DELETE FROM watchlist_items WHERE id=?", (item_id,))
            return True
        except Exception as e:
            logger.error(f"delete_watchlist_item 실패: {e}")
            return False

    def move_watchlist_item(self, item_id: int, target_group_id: int, target_order: int = 9999) -> bool:
        """종목을 다른 그룹으로 이동."""
        try:
            with self._conn() as conn:
                conn.execute(
                    "UPDATE watchlist_items SET group_id=?, display_order=? WHERE id=?",
                    (target_group_id, target_order, item_id)
                )
            return True
        except Exception as e:
            logger.error(f"move_watchlist_item 실패: {e}")
            return False

    def reorder_watchlist_items(self, group_id: int, ordered_ids: List[int]) -> bool:
        """ordered_ids 순서대로 display_order 재설정."""
        try:
            with self._conn() as conn:
                for i, iid in enumerate(ordered_ids):
                    conn.execute(
                        "UPDATE watchlist_items SET display_order=? WHERE id=? AND group_id=?",
                        (i, iid, group_id)
                    )
            return True
        except Exception as e:
            logger.error(f"reorder_watchlist_items 실패: {e}")
            return False

    def get_note_updated_items(self, since_date: str) -> List[Dict]:
        """since_date(YYYY-MM-DD) 이후 stock_master.note가 수정된 관심종목."""
        with self._conn() as conn:
            rows = conn.execute(
                """SELECT wi.id, wi.stock_code, wi.stock_name, wi.group_id,
                          wg.name as group_name,
                          sm.note, sm.summary_2line, sm.updated_at as note_updated_at
                   FROM watchlist_items wi
                   JOIN watchlist_groups wg ON wi.group_id = wg.id
                   LEFT JOIN stock_master sm ON wi.stock_code = sm.stock_code
                   WHERE wi.item_type = 'stock'
                     AND sm.updated_at >= ?
                   ORDER BY sm.updated_at DESC""",
                (since_date,)
            ).fetchall()
            return [dict(r) for r in rows]

    def bulk_insert_watchlist_items(self, group_id: int, items: List[Dict]) -> int:
        """items: [{item_type, stock_code, stock_name, subgroup_label, memo, display_order}]"""
        count = 0
        with self._conn() as conn:
            for item in items:
                conn.execute(
                    """INSERT INTO watchlist_items
                       (group_id, item_type, stock_code, stock_name, subgroup_label, memo, display_order)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        group_id,
                        item.get('item_type', 'stock'),
                        item.get('stock_code'),
                        item.get('stock_name'),
                        item.get('subgroup_label'),
                        item.get('memo'),
                        item.get('display_order', count),
                    )
                )
                count += 1
        return count
