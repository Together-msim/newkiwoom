"""
단타 전략 텔레그램 봇 - 대화형 버전
"""
import os
import logging
from dotenv import load_dotenv

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from tactic_manager import TacticManager
from kiwoom_client import KiwoomClient
from utils.code import normalize_stock_code

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.")

tactic_mgr = TacticManager()

try:
    kiwoom_client = KiwoomClient()
except Exception as e:
    logger.warning(f"키움 API 클라이언트 초기화 실패: {e}")
    kiwoom_client = None

# Conversation states
(TACTIC1_CODE, TACTIC1_CONFIG,
 TACTIC2_CODE, TACTIC2_CONFIG) = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """봇 시작"""
    msg = """
🤖 단타 전략 트레이딩 봇

📋 사용 가능한 명령어:
/tactic1 - Tactic1 전략 등록 (급상승 첫 조정)
/tactic2 - Tactic2 전략 등록 (스윙 분할 매수)
/list - 감시 중인 종목 리스트
/status - 현재 상태 확인
/cancel - 현재 작업 취소

자연어 명령어:
"종목코드(005930) 삭제"
"감시 중인 종목 알려줘"
"""
    await update.message.reply_text(msg)


async def list_watchers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """감시 리스트"""
    watchers = tactic_mgr.get_all_watchers()

    if not watchers:
        await update.message.reply_text("📭 현재 감시 중인 종목이 없습니다.")
        return

    msg_lines = ["📊 감시 중인 종목:\n"]

    for w in watchers:
        tactic = w['tactic']
        code = w['code']
        status = w['status']

        if tactic == 'tactic1':
            config = w['config']
            msg_lines.append(
                f"🔹 T1 | {code} | {status}\n"
                f"   손절:{config.get('최대_손실_퍼센트')}% 익절:{config.get('기대_수익률_퍼센트', '자동')}"
            )
        else:
            config = w['config']
            msg_lines.append(
                f"🔹 T2 | {code} | {status}\n"
                f"   1차:{config['1차_매수가']:,}원 2차:{config['2차_지지선']:,}원"
            )

    await update.message.reply_text("\n".join(msg_lines))


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """상태 확인"""
    status = tactic_mgr.get_status()
    msg = f"""
📊 전략 상태

🔹 Tactic1: {status['tactic1']['active']}개
🔹 Tactic2: {status['tactic2']['active']}개
"""
    await update.message.reply_text(msg)


# ==================== Tactic1 대화형 ====================

async def tactic1_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tactic1 시작"""
    msg = """
📈 Tactic1: 급상승 첫 조정 매매

종목코드를 입력하세요.
• 단일 종목: 005930
• 복수 종목: 005930,000660,035720

입력 후 Enter를 눌러주세요.
취소하려면 /cancel
"""
    await update.message.reply_text(msg)
    return TACTIC1_CODE


async def tactic1_receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """종목코드 입력 받기"""
    text = update.message.text.strip()
    codes = [normalize_stock_code(c.strip()) for c in text.split(',')]

    # 저장
    context.user_data['tactic1_codes'] = codes

    msg = f"""
✅ 종목: {', '.join(codes)}

이제 설정값을 입력하세요.
📋 입력 형식: 기준봉, 손절%, 익절%, 익절비중%

예시:
1분, -5, 7, 100
1분, -5, auto, 50

설명:
• 기준봉: 1분, 3분, 5분 등
• 손절%: -5 (매수가 대비 -5%)
• 익절%: 7 (목표 수익률 7%) 또는 auto (자동)
• 익절비중%: 100 (전량 매도) 또는 50 (절반만)

취소: /cancel
"""
    await update.message.reply_text(msg)
    return TACTIC1_CONFIG


async def tactic1_receive_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """설정값 입력 받기"""
    text = update.message.text.strip()
    parts = [p.strip() for p in text.split(',')]

    if len(parts) < 4:
        await update.message.reply_text("❌ 4개 값을 입력해주세요: 기준봉, 손절%, 익절%, 익절비중%")
        return TACTIC1_CONFIG

    try:
        config = {
            "기준봉": parts[0],
            "최대_손실_퍼센트": abs(float(parts[1])),
            "기대_수익률_퍼센트": None if parts[2].lower() == 'auto' else float(parts[2]),
            "익절_비중_퍼센트": float(parts[3]),
        }

        codes = context.user_data['tactic1_codes']
        added = tactic_mgr.add_tactic1(codes, config)

        msg = f"""
✅ Tactic1 등록 완료!

종목: {', '.join(added)}
기준봉: {config['기준봉']}
손절: {config['최대_손실_퍼센트']}%
익절: {config['기대_수익률_퍼센트'] or '자동'}%
익절비중: {config['익절_비중_퍼센트']}%
"""
        await update.message.reply_text(msg)
        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {str(e)}\n다시 입력해주세요.")
        return TACTIC1_CONFIG


# ==================== Tactic2 대화형 ====================

async def tactic2_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tactic2 시작"""
    msg = """
📊 Tactic2: 스윙 분할 매수

종목코드를 입력하세요.
예: 005930

취소: /cancel
"""
    await update.message.reply_text(msg)
    return TACTIC2_CODE


async def tactic2_receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """종목코드 입력"""
    text = update.message.text.strip()
    code = normalize_stock_code(text)
    context.user_data['tactic2_code'] = code

    msg = f"""
✅ 종목: {code}

설정값을 입력하세요.
📋 입력 형식: 1차매수가, 1차수량, 2차지지선, 2차수량

예시:
70000, 10, 68000, 10

설명:
• 1차매수가: 70000 (원)
• 1차수량: 10 (주)
• 2차지지선: 68000 (원)
• 2차수량: 10 (주)

취소: /cancel
"""
    await update.message.reply_text(msg)
    return TACTIC2_CONFIG


async def tactic2_receive_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """설정값 입력"""
    text = update.message.text.strip()
    parts = [p.strip() for p in text.split(',')]

    if len(parts) < 4:
        await update.message.reply_text("❌ 4개 값을 입력해주세요")
        return TACTIC2_CONFIG

    try:
        code = context.user_data['tactic2_code']
        config = {
            "1차_매수가": int(parts[0]),
            "1차_수량": int(parts[1]),
            "2차_지지선": int(parts[2]),
            "2차_수량": int(parts[3]),
        }

        result = tactic_mgr.add_tactic2(code, config)

        if result:
            msg = f"""
✅ Tactic2 등록 완료!

종목: {code}
1차: {config['1차_매수가']:,}원 x {config['1차_수량']}주
2차: {config['2차_지지선']:,}원 x {config['2차_수량']}주
"""
            await update.message.reply_text(msg)
        else:
            await update.message.reply_text("❌ 등록 실패")

        return ConversationHandler.END

    except Exception as e:
        await update.message.reply_text(f"❌ 오류: {str(e)}\n다시 입력해주세요.")
        return TACTIC2_CONFIG


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """취소"""
    await update.message.reply_text("❌ 취소되었습니다.")
    return ConversationHandler.END


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """자연어 처리"""
    text = update.message.text.strip()

    # 삭제
    if '삭제' in text:
        import re
        match = re.search(r'(\d{6})', text)
        if match:
            code = match.group(1)
            result = tactic_mgr.delete_watcher(code)
            if result:
                await update.message.reply_text(f"✅ {code} 삭제 완료")
            else:
                await update.message.reply_text(f"❌ {code} 찾을 수 없음")
            return

    # 리스트
    if '감시' in text or '리스트' in text or '종목' in text:
        await list_watchers(update, context)
        return

    await update.message.reply_text("❓ 명령을 이해하지 못했습니다. /start를 입력하세요.")


def main():
    """봇 실행"""
    logger.info("단타 전략 봇을 시작합니다...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Tactic1 대화
    tactic1_handler = ConversationHandler(
        entry_points=[CommandHandler("tactic1", tactic1_start)],
        states={
            TACTIC1_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic1_receive_code)],
            TACTIC1_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic1_receive_config)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # Tactic2 대화
    tactic2_handler = ConversationHandler(
        entry_points=[CommandHandler("tactic2", tactic2_start)],
        states={
            TACTIC2_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic2_receive_code)],
            TACTIC2_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic2_receive_config)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_watchers))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(tactic1_handler)
    app.add_handler(tactic2_handler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("봇이 실행되었습니다.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
