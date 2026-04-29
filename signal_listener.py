#!/usr/bin/env python3
"""
Signal Listener: 소스 채널 모니터링 → 아카이빙 → 필터링 → 전달

사용법:
1. .env 설정 (TG_API_ID, TG_API_HASH, SOURCE_CHAT_IDS, TELEGRAM_BOT_TOKEN, DEST_CHAT_ID)
2. 최초 1회 터미널에서 직접 실행 → 전화번호 인증 (signal_listener.session 생성)
3. 이후 run_all.py에서 자동 실행
"""

import os
import re
import sys
import asyncio
import logging
import threading
from pathlib import Path

# Python 3.14+에서 asyncio.get_event_loop()가 자동으로 루프를 생성하지 않음
# Pyrogram import 전에 이벤트 루프를 명시적으로 생성
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from dotenv import load_dotenv
from pyrogram import Client
from telegram import Bot
from telegram.error import TelegramError

# ─── 경로 설정 ────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path, override=True)

from keyword_config import resolve_news_keywords_path, resolve_hotstock_keywords_path
from keyword_storage import KeywordStorage
from keyword_filter import KeywordFilter
from news_storage import NewsStorage, _get_source_type

# ─── 로깅 ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ─── 환경 변수 ────────────────────────────────────────────────
TG_API_ID = os.getenv("TG_API_ID")
TG_API_HASH = os.getenv("TG_API_HASH")
SOURCE_CHAT_IDS_STR = os.getenv("SOURCE_CHAT_IDS", "")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEST_CHAT_ID = os.getenv("DEST_CHAT_ID", "").strip()
SOURCE_DEST_MAPPING_STR = os.getenv("SOURCE_DEST_MAPPING", "")
PRINT_CHAT_META = os.getenv("PRINT_CHAT_META", "0").strip().lower() in ("1", "true", "yes")
LOG_MATCH_TEXT = os.getenv("LOG_MATCH_TEXT", "0").strip().lower() in ("1", "true", "yes")
KEYWORD_RELOAD_INTERVAL = int(os.getenv("KEYWORD_RELOAD_INTERVAL", "30"))
NEWS_DB_PATH = os.getenv("NEWS_DB_PATH", str(ROOT_DIR / ".data" / "news.db"))

if not TG_API_ID or not TG_API_HASH:
    logger.error("❌ TG_API_ID와 TG_API_HASH 환경 변수가 필요합니다.")
    sys.exit(1)
if not BOT_TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN 환경 변수가 필요합니다.")
    sys.exit(1)
if not DEST_CHAT_ID:
    logger.error("❌ DEST_CHAT_ID 환경 변수가 필요합니다.")
    sys.exit(1)

# ─── 소스 채널 파싱 ───────────────────────────────────────────
SOURCE_CHAT_IDS: list[int] = []
for _s in SOURCE_CHAT_IDS_STR.split(","):
    _s = _s.strip()
    if _s:
        try:
            SOURCE_CHAT_IDS.append(int(_s))
        except ValueError:
            logger.warning(f"⚠️ 잘못된 채널 ID: {_s}")

if not SOURCE_CHAT_IDS:
    logger.error("❌ SOURCE_CHAT_IDS 환경 변수가 없거나 유효한 채널이 없습니다.")
    sys.exit(1)

# ─── 저장소 & 필터 초기화 ─────────────────────────────────────
NEWS_KEYWORDS_PATH = resolve_news_keywords_path()
HOTSTOCK_KEYWORDS_PATH = resolve_hotstock_keywords_path()
NEWS_KEYWORDS_PATH.parent.mkdir(parents=True, exist_ok=True)
HOTSTOCK_KEYWORDS_PATH.parent.mkdir(parents=True, exist_ok=True)

MESSAGE_HASHES_PATH = Path(os.getenv("MESSAGE_HASHES_PATH", str(ROOT_DIR / ".data" / "message_hashes.txt")))
MESSAGE_HASHES_PATH.parent.mkdir(parents=True, exist_ok=True)

news_keyword_storage = KeywordStorage(str(NEWS_KEYWORDS_PATH))
hotstock_keyword_storage = KeywordStorage(str(HOTSTOCK_KEYWORDS_PATH))
news_keyword_filter = KeywordFilter(news_keyword_storage, str(MESSAGE_HASHES_PATH))
hotstock_keyword_filter = KeywordFilter(hotstock_keyword_storage, str(MESSAGE_HASHES_PATH))
news_storage = NewsStorage(NEWS_DB_PATH)


def _get_keyword_filter(chat_id: int) -> KeywordFilter:
    """채널 ID에 따라 적절한 키워드 필터 반환."""
    if _get_source_type(chat_id) == "hot_stock":
        return hotstock_keyword_filter
    return news_keyword_filter

# ─── Pyrogram & Bot 초기화 ────────────────────────────────────
SESSION_FILE_PATH = ROOT_DIR / "signal_listener.session"

pyrogram_client = Client(
    "signal_listener",
    api_id=int(TG_API_ID),
    api_hash=TG_API_HASH,
    workdir=str(ROOT_DIR),
)
telegram_bot = Bot(token=BOT_TOKEN)

_reload_thread = None
_reload_thread_stop_event = threading.Event()

# ─── 테마 파싱 ────────────────────────────────────────────────
# 급등주 메시지 포맷: ✅ 테마 : 테마A , 테마B\n✅ ...
_HOTSTOCK_THEME_PATTERN = re.compile(
    r'✅\s*테마\s*[：:]\s*(.*?)(?=✅|$)', re.DOTALL
)
# 불필요 테마 필터 (메시지 타입 태그)
_THEME_BLACKLIST = {'SS', 'VI', 'SS⬆', '단독', '리포트 브리핑', '특징주', '브리핑', '뉴스'}


def extract_themes(text: str) -> list[str]:
    """급등주 메시지의 ✅ 테마 : 섹션에서 테마를 추출합니다."""
    m = _HOTSTOCK_THEME_PATTERN.search(text)
    if not m:
        return []
    raw = m.group(1).replace('\n', ' ')
    themes = []
    for part in re.split(r'[,，]', raw):
        theme = part.strip()
        if theme and len(theme) >= 2 and theme not in _THEME_BLACKLIST:
            themes.append(theme)
    return list(dict.fromkeys(themes))  # 순서 유지 중복 제거


# ─── 유틸리티 ────────────────────────────────────────────────

def build_match_text(message) -> str:
    """메시지에서 매칭용 텍스트를 추출합니다."""
    parts = []
    text = getattr(message, "text", None)
    if text:
        parts.append(str(text))
    caption = getattr(message, "caption", None)
    if caption:
        parts.append(str(caption))
    web_page = getattr(message, "web_page", None)
    if web_page:
        web_title = getattr(web_page, "title", None)
        if web_title:
            parts.append(str(web_title))
        web_desc = getattr(web_page, "description", None)
        if web_desc:
            parts.append(str(web_desc))
    match_text = " ".join(parts).strip()
    return re.sub(r"\s+", " ", match_text)


def format_message(chat_title: str, message_text: str, chat_id: int) -> str:
    return f"📢 **{chat_title}**\n\n{message_text}\n\n_채널 ID: {chat_id}_"


async def send_notification(text: str, source_chat_id: int, dest_chat_id: int):
    if dest_chat_id is None:
        logger.error(f"❌ 목적지 채팅 ID가 None (소스: {source_chat_id})")
        return
    try:
        await telegram_bot.send_message(
            chat_id=dest_chat_id,
            text=text,
            parse_mode="Markdown",
        )
        logger.info(f"✅ 전달 완료 {source_chat_id} → {dest_chat_id}: {text[:50]}...")
    except TelegramError as e:
        logger.error(f"❌ 전달 실패 ({source_chat_id} → {dest_chat_id}): {e}")


# ─── 메시지 핸들러 ────────────────────────────────────────────

@pyrogram_client.on_message()
async def handle_message(client, message):
    news_keyword_filter.reload_if_changed()
    hotstock_keyword_filter.reload_if_changed()

    try:
        chat = message.chat
        if not chat:
            return

        chat_id = chat.id

        if PRINT_CHAT_META:
            logger.info(
                "📩 RECV | title=%s | chat_id=%s | msg_id=%s | text=%s",
                getattr(chat, "title", "Unknown"),
                chat_id,
                getattr(message, "id", None),
                (message.text or message.caption or "")[:80].replace("\n", " "),
            )

        if chat_id not in SOURCE_CHAT_IDS:
            return

        match_text = build_match_text(message)
        if not match_text:
            return

        if LOG_MATCH_TEXT:
            logger.info(f"🔍 [MATCH_TEXT] {match_text[:300]}")

        # ── 1. 전체 메시지 아카이빙 (필터 통과 여부 무관) ──────
        msg_db_id = news_storage.save_message(chat_id, message.id, match_text)

        # ── 2. 급등주 채널이면 테마 자동 추출 ──────────────────
        if _get_source_type(chat_id) == "hot_stock":
            themes = extract_themes(match_text)
            for theme in themes:
                news_storage.upsert_theme(theme)
                logger.debug(f"🏷️  테마 누적: {theme}")

        # ── 3. 키워드 필터링 & 전달 ─────────────────────────────
        kf = _get_keyword_filter(chat_id)
        dest_chat_id = kf.should_forward_to(chat_id, message.id, match_text)
        if dest_chat_id is None:
            logger.debug(f"🔍 필터링됨: {getattr(chat, 'title', '')} - {match_text[:50]}...")
            return

        # 필터링 통과 기록
        if msg_db_id:
            news_storage.save_filtered(msg_db_id, dest_chat_id, [])

        message_text = message.text or message.caption or match_text
        chat_title = chat.title or f"채널 {chat_id}"
        formatted = format_message(chat_title, message_text, chat_id)
        await send_notification(formatted, chat_id, dest_chat_id)

    except Exception as e:
        logger.error(f"❌ 메시지 처리 오류: {e}", exc_info=True)


# ─── 키워드 리로드 스레드 ─────────────────────────────────────

def keyword_reload_polling_thread():
    logger.info(f"🔄 키워드 자동 리로드 스레드 시작 (주기: {KEYWORD_RELOAD_INTERVAL}초)")
    while not _reload_thread_stop_event.is_set():
        try:
            if _reload_thread_stop_event.wait(timeout=KEYWORD_RELOAD_INTERVAL):
                break
            news_keyword_filter.reload_if_changed()
            hotstock_keyword_filter.reload_if_changed()
        except Exception as e:
            logger.error(f"❌ 키워드 리로드 오류: {e}", exc_info=True)
    logger.info("🛑 키워드 리로드 스레드 종료")


def exception_handler(loop, context):
    exception = context.get("exception")
    if exception:
        if isinstance(exception, ValueError) and "Peer id invalid" in str(exception):
            return
        if isinstance(exception, KeyError) and "ID not found" in str(exception):
            return
    logger.error(f"백그라운드 태스크 예외: {context}", exc_info=True)


# ─── 메인 ─────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Signal Listener 시작 (newkiwoom)")
    logger.info(f"  ROOT_DIR: {ROOT_DIR}")
    logger.info(f"  news_keywords.json: {NEWS_KEYWORDS_PATH}")
    logger.info(f"  hotstock_keywords.json: {HOTSTOCK_KEYWORDS_PATH}")
    logger.info(f"  news.db: {NEWS_DB_PATH}")
    logger.info(f"  모니터링 채널: {SOURCE_CHAT_IDS}")
    logger.info("=" * 60)

    global _reload_thread
    _reload_thread_stop_event.clear()
    _reload_thread = threading.Thread(
        target=keyword_reload_polling_thread,
        name="KeywordReloadThread",
        daemon=True,
    )
    _reload_thread.start()

    loop = asyncio.get_event_loop()
    loop.set_exception_handler(exception_handler)

    try:
        pyrogram_client.run()
    except EOFError:
        logger.error("❌ Pyrogram 인증 오류 - 터미널에서 직접 실행해 인증을 완료하세요.")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("👋 종료합니다.")
    except Exception as e:
        logger.error(f"❌ 오류: {e}", exc_info=True)
        sys.exit(1)
    finally:
        if _reload_thread and _reload_thread.is_alive():
            _reload_thread_stop_event.set()
            _reload_thread.join(timeout=5)


if __name__ == "__main__":
    main()
