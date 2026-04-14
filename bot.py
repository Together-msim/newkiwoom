"""
단타 전략 텔레그램 봇
Tactic1: 급상승 첫 조정 매매
Tactic2: 스윙 분할 매수
"""
import os
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from tactic_manager import TacticManager
from strategy_parser import parse_natural_language, parse_tactic1_config, parse_tactic2_config
from kiwoom_client import KiwoomClient
from utils.code import normalize_stock_code

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")

# Tactic Manager 초기화
tactic_mgr = TacticManager()

# Kiwoom API Client 초기화
try:
    kiwoom_client = KiwoomClient()
except Exception as e:
    logger.warning(f"키움 API 클라이언트 초기화 실패: {e}")
    kiwoom_client = None


# =========================
# 명령어 핸들러
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 시작 명령어"""
    welcome_msg = """
🤖 단타 전략 트레이딩 봇에 오신 것을 환영합니다!

📋 사용 가능한 명령어:
/start - 도움말 표시
/list - 감시 중인 종목 리스트 확인
/tactic1 - Tactic1 전략 등록 (급상승 첫 조정)
/tactic2 - Tactic2 전략 등록 (스윙 분할 매수)
/status - 현재 전략 상태 확인

💬 자연어 명령어:
"종목코드(000660) 삭제"
"종목코드(005930) 수정"
"감시 중인 종목 알려줘"

📈 Tactic1: 1분봉 급상승 후 첫 조정 잡기
📊 Tactic2: 지지선 분할 매수 스윙 전략
"""
    await update.message.reply_text(welcome_msg)


async def list_watchers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """감시 중인 종목 리스트 확인"""
    watchers = tactic_mgr.get_all_watchers()

    if not watchers:
        await update.message.reply_text("📭 현재 감시 중인 종목이 없습니다.")
        return

    msg_lines = ["📊 감시 중인 종목 리스트:\n"]

    # Tactic1 종목들
    tactic1_list = [w for w in watchers if w['tactic'] == 'tactic1']
    if tactic1_list:
        msg_lines.append("🔹 Tactic1 (급상승 첫 조정):")
        for w in tactic1_list:
            msg_lines.append(
                f"  • {w['code']} | 기준봉: {w['config']['기준봉']} | "
                f"손절: {w['config']['손절라인']} | 익절: {w['config']['기대_수익률_퍼센트']}%"
            )
        msg_lines.append("")

    # Tactic2 종목들
    tactic2_list = [w for w in watchers if w['tactic'] == 'tactic2']
    if tactic2_list:
        msg_lines.append("🔹 Tactic2 (스윙 분할 매수):")
        for w in tactic2_list:
            msg_lines.append(
                f"  • {w['code']} | 1차: {w['config']['1차_매수가']}원 {w['config']['1차_수량']}주 | "
                f"2차지지: {w['config']['2차_지지선']}"
            )
        msg_lines.append("")

    await update.message.reply_text("\n".join(msg_lines))


async def tactic1_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tactic1 전략 등록"""
    help_text = """
📈 Tactic1: 급상승 첫 조정 매매

입력 형식:
/tactic1 <종목코드> [옵션]

예시:
/tactic1 005930
/tactic1 000660 기준봉=1분 손절=-5% 익절=7%

기본값:
- 기준봉: 1분
- 손절: 매수가 -5%
- 익절: 첫 상승폭만큼
- 익절비중: 100%

복수 종목:
/tactic1 005930,000660 익절=10%
"""

    if not context.args:
        await update.message.reply_text(help_text)
        return

    try:
        # 파싱
        parsed = parse_tactic1_config(context.args)
        if not parsed:
            await update.message.reply_text("❌ 입력 형식이 잘못되었습니다.\n\n" + help_text)
            return

        codes = parsed["codes"]
        config = parsed["config"]

        # 종목코드 정규화
        codes = [normalize_stock_code(c) for c in codes]

        # 전략 등록
        added = tactic_mgr.add_tactic1(codes, config)

        msg = f"✅ Tactic1 전략 등록 완료!\n\n"
        msg += f"📊 등록 종목: {', '.join(added)}\n"
        msg += f"⚙️ 설정:\n"
        msg += f"  • 기준봉: {config.get('기준봉', '1분')}\n"
        msg += f"  • 손절: {config.get('최대_손실_퍼센트', 5)}%\n"
        msg += f"  • 익절: {config.get('기대_수익률_퍼센트', '자동')}%\n"
        msg += f"  • 익절비중: {config.get('익절_비중_퍼센트', 100)}%\n"

        await update.message.reply_text(msg)

    except Exception as e:
        logger.error(f"Tactic1 등록 실패: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 등록 실패: {str(e)}")


async def tactic2_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tactic2 전략 등록"""
    help_text = """
📊 Tactic2: 스윙 분할 매수

입력 형식:
/tactic2 <종목코드> <1차매수가> <1차수량> <2차지지선> <2차수량>

예시:
/tactic2 005930 70000 10 68000 10

옵션:
- 손절라인: 기본값 1차매수가 -5%
- 익절감시: 평균매수가 +10%부터
"""

    if not context.args:
        await update.message.reply_text(help_text)
        return

    try:
        # 파싱
        parsed = parse_tactic2_config(context.args)
        if not parsed:
            await update.message.reply_text("❌ 입력 형식이 잘못되었습니다.\n\n" + help_text)
            return

        code = normalize_stock_code(parsed["code"])
        config = parsed["config"]

        # 전략 등록
        result = tactic_mgr.add_tactic2(code, config)

        if result:
            msg = f"✅ Tactic2 전략 등록 완료!\n\n"
            msg += f"📊 종목: {code}\n"
            msg += f"⚙️ 설정:\n"
            msg += f"  • 1차 매수: {config['1차_매수가']:,}원 x {config['1차_수량']}주\n"
            msg += f"  • 2차 지지선: {config['2차_지지선']:,}원\n"
            msg += f"  • 2차 수량: {config['2차_수량']}주\n"
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ 등록 실패: 필수 항목을 확인하세요.")

    except Exception as e:
        logger.error(f"Tactic2 등록 실패: {e}", exc_info=True)
        await update.message.reply_text(f"❌ 등록 실패: {str(e)}")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """현재 전략 상태 확인"""
    status = tactic_mgr.get_status()

    msg = f"""
📊 전략 상태 요약

🔹 Tactic1: {status['tactic1']['active']}개 감시 중
🔹 Tactic2: {status['tactic2']['active']}개 감시 중

⏰ 마지막 업데이트: {status['last_update']}
"""

    await update.message.reply_text(msg)


async def handle_natural_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """자연어 명령어 처리"""
    text = update.message.text
    logger.info(f"자연어 입력: {text}")

    # 자연어 파싱
    parsed = parse_natural_language(text)

    if not parsed:
        await update.message.reply_text("❓ 명령을 이해하지 못했습니다. /start를 입력해서 도움말을 확인하세요.")
        return

    action = parsed['action']

    # 삭제 명령
    if action == 'delete':
        code = parsed['code']
        result = tactic_mgr.delete_watcher(code)
        if result:
            await update.message.reply_text(f"✅ 종목코드 {code}를 감시 리스트에서 삭제했습니다.")
        else:
            await update.message.reply_text(f"❌ 종목코드 {code}를 찾을 수 없습니다.")

    # 수정 명령
    elif action == 'modify':
        code = parsed['code']
        watcher = tactic_mgr.get_watcher(code)
        if not watcher:
            await update.message.reply_text(f"❌ 종목코드 {code}를 찾을 수 없습니다.")
            return

        # 기존 설정 표시
        config_text = f"""
📝 종목코드 {code} 현재 설정:

전략: {watcher['tactic']}
설정:
{format_config(watcher['config'])}

수정할 항목을 입력하세요.
예: 손절라인=9500 익절=8%
"""
        await update.message.reply_text(config_text)

    # 조회 명령
    elif action == 'list':
        await list_watchers(update, context)


def format_config(config: dict) -> str:
    """설정을 읽기 쉽게 포맷"""
    lines = []
    for key, value in config.items():
        lines.append(f"  • {key}: {value}")
    return "\n".join(lines)


# =========================
# 메인 실행
# =========================

def main():
    """봇 실행"""
    logger.info("단타 전략 봇을 시작합니다...")

    # Application 생성
    app = Application.builder().token(BOT_TOKEN).build()

    # 명령어 핸들러 등록
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_watchers))
    app.add_handler(CommandHandler("tactic1", tactic1_command))
    app.add_handler(CommandHandler("tactic2", tactic2_command))
    app.add_handler(CommandHandler("status", status_command))

    # 자연어 메시지 핸들러
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_natural_language))

    # 봇 시작
    logger.info("봇이 실행되었습니다. Ctrl+C로 종료할 수 있습니다.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
