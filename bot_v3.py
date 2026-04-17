"""
단타 전략 텔레그램 봇 - 대화형 버전 v3
"""
import os
import logging
import asyncio
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters,
)
from tactic_manager import TacticManager
from kiwoom_client import KiwoomClient
from utils.code import normalize_stock_code
from price_monitor import PriceMonitor
from mode2_manager import Mode2Manager
from server_scheduler import ServerScheduler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
tactic_mgr = TacticManager()
mode2_mgr = Mode2Manager()
server_scheduler = ServerScheduler()

try:
    kiwoom_client = KiwoomClient()
except Exception as e:
    logger.warning(f"키움 API 초기화 실패: {e}")
    kiwoom_client = None

# 가격 모니터 (봇 실행 후 초기화)
price_monitor = None

# States
(TACTIC1_CODE, TACTIC1_CONFIG,
 TACTIC2_CODE, TACTIC2_CONFIG,
 LIST_ACTION, LIST_UPDATE_CODE, LIST_UPDATE_CONFIG, LIST_DELETE_CODE) = range(8)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = """🤖 단타 전략 봇

/tactic1 - T1 등록
/tactic2 - T2 등록
/list - 감시 리스트 (수정/삭제)
/status - 상태
/start_monitoring - 감시 시작
/stop_monitoring - 감시 중지

🖥 서버 제어
/server - 서버 상태 확인
/on - 서버 수동 시작
/off - 서버 수동 중지

/cancel - 취소"""
    await update.message.reply_text(msg)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status = tactic_mgr.get_status()
    monitoring_status = "✅ 실행 중" if (price_monitor and price_monitor.is_monitoring) else "❌ 중지됨"
    interval = os.getenv("MONITOR_INTERVAL", "10")
    msg = (f"📊 T1: {status['tactic1']['active']}개 | T2: {status['tactic2']['active']}개\n"
           f"🔍 모니터링: {monitoring_status} (간격: {interval}초)")
    await update.message.reply_text(msg)

async def start_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """모니터링 시작"""
    if not price_monitor:
        await update.message.reply_text("❌ 가격 모니터가 초기화되지 않았습니다")
        return

    if price_monitor.start():
        interval = os.getenv("MONITOR_INTERVAL", "10")
        await update.message.reply_text(f"✅ 가격 모니터링 시작 (간격: {interval}초)")
    else:
        await update.message.reply_text("⚠️ 이미 모니터링 중입니다")

async def stop_monitoring(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """모니터링 중지"""
    if not price_monitor:
        await update.message.reply_text("❌ 가격 모니터가 초기화되지 않았습니다")
        return

    if price_monitor.stop():
        await update.message.reply_text("✅ 가격 모니터링 중지")
    else:
        await update.message.reply_text("⚠️ 모니터링이 실행 중이 아닙니다")

# ========== 서버 제어 ==========
async def server_status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """서버 상태 확인"""
    status_msg = server_scheduler.get_status_message()
    is_running = await server_scheduler.check_server_status()

    actual_status = "🟢 RUNNING" if is_running else "🔴 STOPPED"
    full_msg = f"{status_msg}\n실제 서버: {actual_status}"

    await update.message.reply_text(full_msg)

async def server_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """서버 수동 시작"""
    await update.message.reply_text("🔄 서버를 시작하는 중...")

    success, message = await server_scheduler.manual_start()
    await update.message.reply_text(message)

    if success:
        # 상태 메시지 추가
        status_msg = server_scheduler.get_status_message()
        await update.message.reply_text(status_msg)

async def server_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """서버 수동 중지"""
    await update.message.reply_text("🔄 서버를 중지하는 중...")

    success, message = await server_scheduler.manual_stop()
    await update.message.reply_text(message)

    if success:
        # 상태 메시지 추가
        status_msg = server_scheduler.get_status_message()
        await update.message.reply_text(status_msg)

# ========== Tactic1 ==========
async def tactic1_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 T1: 종목코드 입력 (예: 005930 또는 005930,000660)\n/cancel - 취소")
    return TACTIC1_CODE

async def tactic1_receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    codes = [normalize_stock_code(c.strip()) for c in update.message.text.split(',')]
    context.user_data['tactic1_codes'] = codes
    await update.message.reply_text(
        f"✅ {', '.join(codes)}\n\n"
        "설정: 기준봉, 손절%, 익절%, 익절비중%\n"
        "예: 1분, -5, 7, 100"
    )
    return TACTIC1_CONFIG

async def tactic1_receive_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = [p.strip() for p in update.message.text.split(',')]
    if len(parts) < 4:
        await update.message.reply_text("❌ 4개 값 필요")
        return TACTIC1_CONFIG

    config = {
        "기준봉": parts[0],
        "최대_손실_퍼센트": abs(float(parts[1])),
        "기대_수익률_퍼센트": None if parts[2].lower() == 'auto' else float(parts[2]),
        "익절_비중_퍼센트": float(parts[3]),
    }
    codes = context.user_data['tactic1_codes']
    tactic_mgr.add_tactic1(codes, config)
    await update.message.reply_text(f"✅ T1 등록: {', '.join(codes)}")
    return ConversationHandler.END

# ========== Tactic2 ==========
async def tactic2_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 T2: 종목코드 (예: 005930)\n/cancel - 취소")
    return TACTIC2_CODE

async def tactic2_receive_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = normalize_stock_code(update.message.text.strip())
    context.user_data['tactic2_code'] = code
    await update.message.reply_text(
        f"✅ {code}\n\n"
        "설정: 1차매수가, 1차수량, 2차지지선, 2차수량\n"
        "예: 70000, 10, 68000, 10"
    )
    return TACTIC2_CONFIG

async def tactic2_receive_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = [p.strip() for p in update.message.text.split(',')]
    if len(parts) < 4:
        await update.message.reply_text("❌ 4개 값 필요")
        return TACTIC2_CONFIG

    code = context.user_data['tactic2_code']
    config = {
        "1차_매수가": int(parts[0]),
        "1차_수량": int(parts[1]),
        "2차_지지선": int(parts[2]),
        "2차_수량": int(parts[3]),
    }
    tactic_mgr.add_tactic2(code, config)
    await update.message.reply_text(f"✅ T2 등록: {code}")
    return ConversationHandler.END

# ========== List (Update/Delete) ==========
async def list_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    watchers = tactic_mgr.get_all_watchers()
    if not watchers:
        await update.message.reply_text("📭 감시 중인 종목 없음")
        return ConversationHandler.END

    lines = ["📊 감시 리스트:\n"]
    for w in watchers:
        tactic = w['tactic']
        code = w['code']
        if tactic == 'tactic1':
            cfg = w['config']
            lines.append(f"T1 | {code} | 손절{cfg.get('최대_손실_퍼센트')}% 익절{cfg.get('기대_수익률_퍼센트', 'auto')}")
        else:
            cfg = w['config']
            lines.append(f"T2 | {code} | 1차{cfg['1차_매수가']:,}원 2차{cfg['2차_지지선']:,}원")

    lines.append("\n선택: Update 또는 Delete")
    await update.message.reply_text("\n".join(lines))
    return LIST_ACTION

async def list_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = update.message.text.strip().lower()

    if action == 'update':
        await update.message.reply_text("수정할 종목코드 입력\n(T1: 복수 가능, T2: 단일만)")
        return LIST_UPDATE_CODE
    elif action == 'delete':
        await update.message.reply_text("삭제할 종목코드 입력\n(전체 삭제: all 또는 전체)")
        return LIST_DELETE_CODE
    else:
        await update.message.reply_text("❌ Update 또는 Delete 입력")
        return LIST_ACTION

async def list_update_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    codes = [normalize_stock_code(c.strip()) for c in update.message.text.split(',')]

    # 첫 번째 종목의 tactic 확인
    first = tactic_mgr.get_watcher(codes[0])
    if not first:
        await update.message.reply_text(f"❌ {codes[0]} 없음")
        return ConversationHandler.END

    tactic = first['tactic']

    # T2는 단일만
    if tactic == 'tactic2' and len(codes) > 1:
        await update.message.reply_text("❌ T2는 단일 종목만 수정 가능")
        return LIST_UPDATE_CODE

    context.user_data['update_codes'] = codes
    context.user_data['update_tactic'] = tactic

    if tactic == 'tactic1':
        await update.message.reply_text(
            f"✅ {', '.join(codes)}\n\n"
            "새 설정: 기준봉, 손절%, 익절%, 익절비중%\n"
            "예: 1분, -5, 8, 100"
        )
    else:
        await update.message.reply_text(
            f"✅ {codes[0]}\n\n"
            "새 설정: 1차매수가, 1차수량, 2차지지선, 2차수량\n"
            "예: 70000, 10, 68000, 10"
        )
    return LIST_UPDATE_CONFIG

async def list_update_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = [p.strip() for p in update.message.text.split(',')]
    codes = context.user_data['update_codes']
    tactic = context.user_data['update_tactic']

    if tactic == 'tactic1':
        if len(parts) < 4:
            await update.message.reply_text("❌ 4개 값 필요")
            return LIST_UPDATE_CONFIG

        config = {
            "기준봉": parts[0],
            "최대_손실_퍼센트": abs(float(parts[1])),
            "기대_수익률_퍼센트": None if parts[2].lower() == 'auto' else float(parts[2]),
            "익절_비중_퍼센트": float(parts[3]),
        }

        for code in codes:
            tactic_mgr.delete_watcher(code)
        tactic_mgr.add_tactic1(codes, config)
        await update.message.reply_text(f"✅ T1 수정: {', '.join(codes)}")
    else:
        if len(parts) < 4:
            await update.message.reply_text("❌ 4개 값 필요")
            return LIST_UPDATE_CONFIG

        code = codes[0]
        config = {
            "1차_매수가": int(parts[0]),
            "1차_수량": int(parts[1]),
            "2차_지지선": int(parts[2]),
            "2차_수량": int(parts[3]),
        }
        tactic_mgr.delete_watcher(code)
        tactic_mgr.add_tactic2(code, config)
        await update.message.reply_text(f"✅ T2 수정: {code}")

    return ConversationHandler.END

async def list_delete_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().lower()

    # 전체 삭제
    if text in ['all', '전체', 'all종목', '전체삭제']:
        watchers = tactic_mgr.get_all_watchers()
        if not watchers:
            await update.message.reply_text("❌ 삭제할 종목 없음")
            return ConversationHandler.END

        deleted = []
        for w in watchers:
            if tactic_mgr.delete_watcher(w['code']):
                deleted.append(w['code'])

        await update.message.reply_text(f"✅ 전체 삭제 ({len(deleted)}개): {', '.join(deleted)}")
        return ConversationHandler.END

    # 개별 삭제
    codes = [normalize_stock_code(c.strip()) for c in update.message.text.split(',')]
    deleted = []
    for code in codes:
        if tactic_mgr.delete_watcher(code):
            deleted.append(code)

    if deleted:
        await update.message.reply_text(f"✅ 삭제: {', '.join(deleted)}")
    else:
        await update.message.reply_text("❌ 삭제할 종목 없음")
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ 취소")
    return ConversationHandler.END

async def post_init(application: Application):
    """봇 초기화 후 실행"""
    global price_monitor

    # 가격 모니터 초기화 (Tactic1/2 + Mode2)
    if kiwoom_client:
        price_monitor = PriceMonitor(tactic_mgr, kiwoom_client, application, mode2_mgr)
        await price_monitor.start_monitoring_task()
        logger.info("가격 모니터 초기화 완료 (Tactic1/2 + Mode2)")
    else:
        logger.warning("키움 API 미연결 - 가격 모니터링 비활성화")

    # 서버 스케줄러 시작
    asyncio.create_task(server_scheduler.start_monitoring())
    logger.info("서버 스케줄러 시작 완료")

def main():
    logger.info("봇 시작")
    app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    tactic1_conv = ConversationHandler(
        entry_points=[CommandHandler("tactic1", tactic1_start)],
        states={
            TACTIC1_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic1_receive_code)],
            TACTIC1_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic1_receive_config)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    tactic2_conv = ConversationHandler(
        entry_points=[CommandHandler("tactic2", tactic2_start)],
        states={
            TACTIC2_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic2_receive_code)],
            TACTIC2_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, tactic2_receive_config)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    list_conv = ConversationHandler(
        entry_points=[CommandHandler("list", list_start)],
        states={
            LIST_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, list_action)],
            LIST_UPDATE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, list_update_code)],
            LIST_UPDATE_CONFIG: [MessageHandler(filters.TEXT & ~filters.COMMAND, list_update_config)],
            LIST_DELETE_CODE: [MessageHandler(filters.TEXT & ~filters.COMMAND, list_delete_code)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("start_monitoring", start_monitoring))
    app.add_handler(CommandHandler("stop_monitoring", stop_monitoring))
    app.add_handler(CommandHandler("server", server_status_command))
    app.add_handler(CommandHandler("on", server_on_command))
    app.add_handler(CommandHandler("off", server_off_command))
    app.add_handler(tactic1_conv)
    app.add_handler(tactic2_conv)
    app.add_handler(list_conv)

    logger.info("봇 실행 중")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
