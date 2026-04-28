"""
통합 실행 스크립트
텔레그램 봇 + 웹 UI + 가격 모니터링을 동시에 실행
"""
import os
import sys
import asyncio
import logging
import threading
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


def run_web_server():
    """웹 서버 실행 (별도 스레드)"""
    from web_app import main
    logger.info("웹 서버 시작 (PriceMonitor 포함)")
    main()


def run_signal_listener():
    """Signal Listener 실행 (별도 스레드 - Pyrogram 채널 구독)"""
    try:
        from signal_listener import main as sl_main
        logger.info("Signal Listener 시작 (뉴스/급등주 아카이빙)")
        sl_main()
    except SystemExit as e:
        logger.warning(f"Signal Listener 종료 (code={e.code}) - 세션 파일 없을 수 있음")
    except Exception as e:
        logger.error(f"Signal Listener 오류: {e}", exc_info=True)


def run_telegram_bot():
    """텔레그램 봇 실행"""
    from bot_v3 import main
    logger.info("텔레그램 봇 시작")
    main()


def main():
    """메인 실행 함수"""
    logger.info("=" * 60)
    logger.info("🚀 Mode2 자동매매 시스템 시작")
    logger.info("=" * 60)
    logger.info("")
    logger.info("실행 중인 서비스:")
    logger.info("  1. 텔레그램 봇 (가격 모니터링 포함)")
    logger.info(f"  2. 웹 UI (http://localhost:{os.getenv('WEB_PORT', '5000')})")
    logger.info("  3. Signal Listener (뉴스/급등주 아카이빙)")
    logger.info("")
    logger.info("종료: Ctrl+C")
    logger.info("=" * 60)
    logger.info("")

    # 웹 서버를 별도 스레드에서 실행
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()

    # Signal Listener를 별도 스레드에서 실행
    signal_thread = threading.Thread(target=run_signal_listener, daemon=True, name="SignalListener")
    signal_thread.start()

    # 텔레그램 봇을 메인 스레드에서 실행
    try:
        run_telegram_bot()
    except KeyboardInterrupt:
        logger.info("\n시스템 종료 중...")
        sys.exit(0)


if __name__ == "__main__":
    main()
