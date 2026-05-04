"""
웹 UI 서버
Mode2 전략 관리 웹 인터페이스
"""
import os
import logging
from pathlib import Path
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

from mode1_manager import Mode1Manager
from mode2_manager import Mode2Manager
from utils.code import normalize_stock_code
from kiwoom_client import KiwoomClient
from kiwoom_token import get_token
from kiwoom_chart import get_daily_chart, get_nxt_daily_chart, format_chart_info
from symbol_resolver import resolve_symbol
from global_config import get_global_config
from price_monitor import PriceMonitor
from tactic_manager import TacticManager
import asyncio
import threading
from telegram.ext import Application

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Basic Auth 설정
auth = HTTPBasicAuth()

# 사용자 인증 정보 (환경변수에서 로드)
WEB_USERNAME = os.getenv("WEB_USERNAME", "admin")
WEB_PASSWORD = os.getenv("WEB_PASSWORD", "changeme")

users = {
    WEB_USERNAME: generate_password_hash(WEB_PASSWORD)
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username
    return None

# Manager 초기화
mode1_mgr = Mode1Manager()
mode2_mgr = Mode2Manager()
tactic_mgr = TacticManager()

# Kiwoom Client 초기화
try:
    kiwoom_client = KiwoomClient()
    logger.info("Kiwoom API 연결 완료")
except Exception as e:
    logger.warning(f"Kiwoom API 연결 실패: {e}")
    kiwoom_client = None

# 텔레그램 봇 초기화 (알림 전송용)
bot_application = None
telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
if telegram_token:
    try:
        bot_application = Application.builder().token(telegram_token).build()
        logger.info("텔레그램 봇 초기화 완료 (알림 전용)")
    except Exception as e:
        logger.warning(f"텔레그램 봇 초기화 실패: {e}")
else:
    logger.warning("TELEGRAM_BOT_TOKEN 없음 - 텔레그램 알림 비활성화")

# PriceMonitor 초기화 (웹 서버에서도 모니터링)
price_monitor = None
if kiwoom_client:
    price_monitor = PriceMonitor(
        tactic_manager=tactic_mgr,
        kiwoom_client=kiwoom_client,
        bot_application=bot_application,  # 텔레그램 봇 연결
        mode1_manager=mode1_mgr,
        mode2_manager=mode2_mgr
    )
    try:
        from news_storage import NewsStorage as _NS
        _ns_db = os.getenv("NEWS_DB_PATH", ".data/news.db")
        price_monitor.news_storage = _NS(_ns_db)
    except Exception as _e:
        logger.warning(f"PriceMonitor news_storage 연결 실패: {_e}")
    logger.info("PriceMonitor 초기화 완료")
else:
    logger.warning("Kiwoom API 미연결 - PriceMonitor 비활성화")


@app.route('/')
@auth.login_required
def index():
    """메인 페이지 (장중 전용)"""
    return render_template('index.html', is_admin=False)


@app.route('/adminpage')
@auth.login_required
def adminpage():
    """어드민 페이지 (장마감 후 분석용)"""
    return render_template('index.html', is_admin=True)


# ========== Mode1 API ==========

@app.route('/api/mode1/watchers', methods=['GET'])
def get_mode1_watchers():
    """Mode1 감시 리스트 조회"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        watchers = mode1_mgr.get_all_watchers(active_only=active_only)
        return jsonify({
            "success": True,
            "data": watchers
        })
    except Exception as e:
        logger.error(f"Mode1 감시 리스트 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode1/watchers', methods=['POST'])
def create_mode1_watcher():
    """Mode1 전략 추가"""
    try:
        data = request.json

        # 필수 필드 검증
        required_fields = ["code"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"필수 필드 누락: {field}"
                }), 400

        # 종목코드 정규화
        data["code"] = normalize_stock_code(data["code"])

        # 중복 체크
        if mode1_mgr.get_watcher(data["code"]):
            return jsonify({
                "success": False,
                "error": f"이미 등록된 종목입니다: {data['code']}"
            }), 400

        # 종목명 자동 조회
        if kiwoom_client and not data.get("name"):
            try:
                stock_info = kiwoom_client.get_stock_info(data["code"])
                data["name"] = stock_info.get("name", "")
                logger.info(f"종목명 조회: {data['code']} -> {data['name']}")
            except Exception as e:
                logger.warning(f"종목명 조회 실패: {e}")
                data["name"] = ""

        # 추가
        watcher = mode1_mgr.add_watcher(data)

        return jsonify({
            "success": True,
            "data": watcher
        }), 201

    except Exception as e:
        logger.error(f"Mode1 종목 추가 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode1/watchers/<code>', methods=['GET'])
def get_mode1_watcher(code):
    """특정 종목 조회"""
    try:
        code = normalize_stock_code(code)
        watcher = mode1_mgr.get_watcher(code)

        if not watcher:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "data": watcher
        })

    except Exception as e:
        logger.error(f"Mode1 종목 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode1/watchers/<code>', methods=['PUT'])
def update_mode1_watcher(code):
    """종목 정보 업데이트"""
    try:
        code = normalize_stock_code(code)
        data = request.json

        watcher = mode1_mgr.update_watcher(code, data)

        if not watcher:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "data": watcher
        })

    except Exception as e:
        logger.error(f"Mode1 종목 업데이트 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode1/watchers/<code>', methods=['DELETE'])
def delete_mode1_watcher(code):
    """종목 삭제"""
    try:
        code = normalize_stock_code(code)
        success = mode1_mgr.delete_watcher(code)

        if not success:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "message": f"종목 삭제 완료: {code}"
        })

    except Exception as e:
        logger.error(f"Mode1 종목 삭제 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode1/watchers/<code>/active', methods=['PATCH'])
def toggle_mode1_active(code):
    """종목 활성화/비활성화"""
    try:
        code = normalize_stock_code(code)
        data = request.json
        active = data.get("active", True)

        success = mode1_mgr.set_active(code, active)

        if not success:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "message": f"종목 {'활성화' if active else '비활성화'} 완료: {code}"
        })

    except Exception as e:
        logger.error(f"Mode1 활성화 토글 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode1/watchers/<code>/status', methods=['PATCH'])
def update_mode1_status(code):
    """종목 상태 업데이트"""
    try:
        code = normalize_stock_code(code)
        data = request.json
        status = data.get("status")

        if not status:
            return jsonify({
                "success": False,
                "error": "status 필드가 필요합니다"
            }), 400

        success = mode1_mgr.update_status(code, status)

        if not success:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "message": f"상태 변경 완료: {code} -> {status}"
        })

    except Exception as e:
        logger.error(f"Mode1 상태 업데이트 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== Mode2 섹션 관리 API ==========

@app.route('/api/mode2/sections', methods=['GET'])
def get_mode2_sections():
    """섹션 리스트 조회"""
    try:
        sections = mode2_mgr.get_all_sections()
        return jsonify({
            "success": True,
            "data": sections
        })
    except Exception as e:
        logger.error(f"섹션 리스트 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/sections', methods=['POST'])
def create_mode2_section():
    """섹션 추가"""
    try:
        data = request.json
        name = data.get('name', '').strip()

        if not name:
            return jsonify({
                "success": False,
                "error": "섹션명을 입력하세요"
            }), 400

        section = mode2_mgr.add_section(name)
        return jsonify({
            "success": True,
            "data": section
        })
    except Exception as e:
        logger.error(f"섹션 추가 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/sections/<section_id>', methods=['PUT'])
def update_mode2_section(section_id):
    """섹션명 변경"""
    try:
        data = request.json
        name = data.get('name', '').strip()

        if not name:
            return jsonify({
                "success": False,
                "error": "섹션명을 입력하세요"
            }), 400

        if mode2_mgr.update_section(section_id, name):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "섹션을 찾을 수 없습니다"
            }), 404
    except Exception as e:
        logger.error(f"섹션 수정 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/sections/<section_id>', methods=['DELETE'])
def delete_mode2_section(section_id):
    """섹션 삭제 (종목은 미분류로 이동)"""
    try:
        if section_id == 'uncategorized':
            return jsonify({
                "success": False,
                "error": "미분류 섹션은 삭제할 수 없습니다"
            }), 400

        if mode2_mgr.delete_section(section_id):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "섹션을 찾을 수 없습니다"
            }), 404
    except Exception as e:
        logger.error(f"섹션 삭제 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/sections/<section_id>/toggle-collapse', methods=['POST'])
def toggle_section_collapse(section_id):
    """섹션 접기/펴기"""
    try:
        if mode2_mgr.toggle_section_collapsed(section_id):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "섹션을 찾을 수 없습니다"
            }), 404
    except Exception as e:
        logger.error(f"섹션 토글 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/sections/reorder', methods=['POST'])
def reorder_mode2_sections():
    """섹션 순서 변경"""
    try:
        data = request.json
        section_orders = data.get('section_orders', [])

        if mode2_mgr.reorder_sections(section_orders):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "순서 변경 실패"
            }), 500
    except Exception as e:
        logger.error(f"섹션 순서 변경 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/watchers/<code>/move-section', methods=['POST'])
def move_watcher_section(code):
    """종목을 다른 섹션으로 이동"""
    try:
        data = request.json
        section_id = data.get('section_id')

        if not section_id:
            return jsonify({
                "success": False,
                "error": "섹션 ID가 필요합니다"
            }), 400

        if mode2_mgr.move_watcher_to_section(code, section_id):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404
    except Exception as e:
        logger.error(f"종목 이동 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/sections/<section_id>/reorder-watchers', methods=['POST'])
def reorder_section_watchers(section_id):
    """섹션 내 종목 순서 변경"""
    try:
        data = request.json
        watcher_orders = data.get('watcher_orders', [])

        if mode2_mgr.reorder_watchers_in_section(section_id, watcher_orders):
            return jsonify({"success": True})
        else:
            return jsonify({
                "success": False,
                "error": "순서 변경 실패"
            }), 500
    except Exception as e:
        logger.error(f"종목 순서 변경 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/sections/<section_id>/watchers', methods=['GET'])
def get_section_watchers(section_id):
    """특정 섹션의 종목 리스트 조회"""
    try:
        watchers = mode2_mgr.get_watchers_by_section(section_id)
        return jsonify({
            "success": True,
            "data": watchers
        })
    except Exception as e:
        logger.error(f"섹션 종목 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== Test API ==========

@app.route('/api/test/stock-info/<code>', methods=['GET'])
def test_stock_info(code):
    """종목 정보 조회 테스트"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        code = normalize_stock_code(code)
        info = kiwoom_client.get_stock_info(code)

        return jsonify({
            "success": True,
            "data": info
        })
    except Exception as e:
        logger.error(f"종목 정보 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/test/chart/<code>', methods=['GET'])
def test_chart(code):
    """분봉 차트 조회 테스트"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        code = normalize_stock_code(code)
        interval = request.args.get('interval', '1')

        # TODO: 실제 차트 API 호출 구현
        # 현재는 시뮬레이션 데이터
        data = {
            "code": code,
            "interval": f"{interval}분봉",
            "data": [
                {"time": "09:00", "open": 13000, "high": 13200, "low": 12900, "close": 13100},
                {"time": "09:01", "open": 13100, "high": 13300, "low": 13000, "close": 13200},
                {"time": "09:02", "open": 13200, "high": 13400, "low": 13100, "close": 13300},
            ]
        }

        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"차트 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/test/token', methods=['GET'])
def test_token():
    """토큰 상태 확인"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        # 토큰 상태 정보
        token_info = {
            "connected": True,
            "token_length": len(kiwoom_client.token) if kiwoom_client.token else 0,
            "host": kiwoom_client.host
        }

        return jsonify({
            "success": True,
            "data": token_info
        })
    except Exception as e:
        logger.error(f"토큰 확인 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== Account API ==========

@app.route('/api/account/positions', methods=['GET'])
def get_account_positions():
    """계좌 보유 종목 조회"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        summary, rows = kiwoom_client.get_positions()

        # 계좌 요약 정보 추출
        account_summary = {
            "total_value": summary.get("tot_evlt_amt", 0),  # 총 평가금액
            "total_profit": summary.get("tot_evltv_prft", 0),  # 총 평가손익
            "total_profit_rate": summary.get("tot_prft_rt", 0),  # 총 수익률
            "deposit_balance": summary.get("dbst_bal", 0),  # 예수금 잔고
        }

        # 보유종목 정보 정리
        positions = []
        for row in rows:
            positions.append({
                "code": row.get("stk_cd", ""),
                "name": row.get("stk_nm", ""),
                "quantity": int(row.get("rmnd_qty", 0) or 0),
                "buy_price": float(row.get("buy_uv", 0) or 0),
                "current_price": float(row.get("eval_prc", 0) or 0),  # 평가단가
                "profit": float(row.get("evltv_prft", 0) or 0),  # 평가손익
                "profit_rate": float(row.get("prft_rt", 0) or 0),  # 수익률
                "eval_amount": float(row.get("evlt_amt", 0) or 0),  # 평가금액
            })

        return jsonify({
            "success": True,
            "data": {
                "summary": account_summary,
                "positions": positions,
                "count": len(positions)
            }
        })

    except Exception as e:
        logger.error(f"보유종목 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/watchlist/sync-holdings', methods=['POST'])
def sync_holdings_to_watchlist():
    """보유 종목 수량을 감시리스트에 동기화"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        # 계좌 보유 종목 조회
        summary, rows = kiwoom_client.get_positions()

        # 보유 종목을 딕셔너리로 변환 (코드: 수량)
        holdings_map = {}
        for row in rows:
            code = normalize_stock_code(row.get("stk_cd", ""))
            quantity = int(row.get("rmnd_qty", 0) or 0)
            if code and quantity > 0:
                holdings_map[code] = quantity

        updated_count = 0

        # Mode1 감시리스트 업데이트
        if mode1_mgr:
            mode1_watchers = mode1_mgr.get_all_watchers()
            for watcher in mode1_watchers:
                code = watcher['code']
                current_qty = watcher.get('bought_quantity') or 0

                if code in holdings_map:
                    mode1_mgr.update_watcher(code, {
                        "bought_quantity": holdings_map[code]
                    })
                    updated_count += 1
                else:
                    # 보유하지 않은 경우 0으로 설정
                    if current_qty > 0:
                        mode1_mgr.update_watcher(code, {
                            "bought_quantity": 0
                        })
                        updated_count += 1

        # Mode2 감시리스트 업데이트
        if mode2_mgr:
            mode2_watchers = mode2_mgr.get_all_watchers()
            for watcher in mode2_watchers:
                code = watcher['code']
                current_qty = watcher.get('bought_quantity') or 0

                if code in holdings_map:
                    mode2_mgr.update_watcher(code, {
                        "bought_quantity": holdings_map[code]
                    })
                    updated_count += 1
                else:
                    # 보유하지 않은 경우 0으로 설정
                    if current_qty > 0:
                        mode2_mgr.update_watcher(code, {
                            "bought_quantity": 0
                        })
                        updated_count += 1

        return jsonify({
            "success": True,
            "message": f"{updated_count}개 종목 보유수량 동기화 완료",
            "holdings_count": len(holdings_map)
        })

    except Exception as e:
        logger.error(f"보유수량 동기화 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/test/daily-chart', methods=['POST'])
def test_daily_chart():
    """일봉차트 정보 조회 (종목명/종목코드)"""
    try:
        data = request.json
        symbol_input = data.get('symbol', '').strip()

        if not symbol_input:
            return jsonify({
                "success": False,
                "error": "종목명 또는 종목코드를 입력하세요"
            }), 400

        # 종목명인 경우 종목코드로 변환
        symbol_result = resolve_symbol(symbol_input)

        if not symbol_result or not symbol_result.get("stock_code"):
            return jsonify({
                "success": False,
                "error": f"종목을 찾을 수 없습니다: {symbol_input}"
            }), 404

        symbol_code = symbol_result["stock_code"]
        symbol_name = symbol_result.get("corp_name") or symbol_code

        # 토큰 발급
        token = get_token()
        if not token:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 토큰 발급 실패"
            }), 503

        # 일봉차트 조회 (NXT 종목 지원)
        chart_data = get_nxt_daily_chart(token=token, symbol=symbol_code)

        if not chart_data:
            return jsonify({
                "success": False,
                "error": f"일봉차트 정보를 가져올 수 없습니다: {symbol_name} ({symbol_code})"
            }), 500

        # 현재가 조회
        try:
            if kiwoom_client:
                current_price = kiwoom_client.get_last_price(symbol_code)
            else:
                current_price = float(chart_data.get("today_current", 0))
        except Exception:
            current_price = float(chart_data.get("today_current", 0))

        # 분봉 요약 조회 (고가/저가 시간 파악)
        intraday_summary = None
        try:
            from kiwoom_chart import get_intraday_summary
            intraday_summary = get_intraday_summary(token=token, code=symbol_code, tic_scope="10", cnt=50)
        except Exception as e:
            logger.warning(f"분봉 요약 조회 실패 (무시): {e}")

        # 포맷팅된 메시지 생성
        formatted_msg = format_chart_info(chart_data, current_price)

        # 고가/저가 시간 정보 추가
        if intraday_summary:
            high_time = intraday_summary.get("high_time", "")
            low_time = intraday_summary.get("low_time", "")
            if high_time and low_time:
                formatted_msg += f"\n\n⏱️ 당일 시간 정보:"
                formatted_msg += f"\n고가 시간: {high_time[:2]}:{high_time[2:4]}:{high_time[4:6]}"
                formatted_msg += f"\n저가 시간: {low_time[:2]}:{low_time[2:4]}:{low_time[4:6]}"

                # 선후 관계 판단
                if high_time < low_time:
                    formatted_msg += f"\n📊 고가가 저가보다 먼저 발생"
                elif low_time < high_time:
                    formatted_msg += f"\n📊 저가가 고가보다 먼저 발생"
                else:
                    formatted_msg += f"\n📊 고가와 저가가 동시 발생"

        return jsonify({
            "success": True,
            "data": {
                "code": symbol_code,
                "name": symbol_name,
                "chart": chart_data,
                "current_price": current_price,
                "formatted_message": formatted_msg,
                "intraday_summary": intraday_summary
            }
        })

    except Exception as e:
        logger.error(f"일봉차트 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/test/telegram', methods=['POST'])
def test_telegram():
    """텔레그램 메시지 전송 테스트"""
    try:
        import requests

        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        chat_id = os.getenv('TELEGRAM_CHAT_ID')

        if not bot_token or not chat_id:
            return jsonify({
                "success": False,
                "error": "텔레그램 설정이 없습니다 (.env 파일 확인)"
            }), 400

        data = request.json
        message = data.get('message', '')

        if not message:
            return jsonify({
                "success": False,
                "error": "메시지가 필요합니다"
            }), 400

        # 텔레그램 API 호출
        telegram_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(telegram_url, json={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        })

        if response.status_code == 200:
            logger.info(f"텔레그램 메시지 전송 완료: {message[:50]}...")
            return jsonify({
                "success": True,
                "message": "텔레그램 메시지 전송 완료"
            })
        else:
            logger.error(f"텔레그램 전송 실패: {response.text}")
            return jsonify({
                "success": False,
                "error": f"텔레그램 API 오류: {response.text}"
            }), 500

    except Exception as e:
        logger.error(f"텔레그램 전송 실패: {e}")
        import traceback


@app.route('/api/test/mode2-monitor', methods=['POST'])
def test_mode2_monitor():
    """Mode2 모니터링 테스트 (단일 체크)"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        data = request.json
        code = data.get('code', '').strip()

        if not code:
            return jsonify({
                "success": False,
                "error": "종목코드가 필요합니다"
            }), 400

        # 종목코드 정규화
        code = normalize_stock_code(code)

        # Mode2 watcher 조회
        watcher = mode2_mgr.get_watcher(code)
        if not watcher:
            return jsonify({
                "success": False,
                "error": f"Mode2 감시 종목이 아닙니다: {code}"
            }), 404

        # 현재가 조회
        try:
            current_price = kiwoom_client.get_last_price(code)
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"현재가 조회 실패: {str(e)}"
            }), 500

        # 매수타점 체크 (현재가가 타점 이하로 떨어지면 매수 - 눌림 매매)
        buy_target = watcher.get('buy_target_price', 0)
        buy_triggered = False
        if buy_target > 0:
            buy_triggered = current_price <= buy_target

        # 저항/지지 레벨 체크
        resist1 = watcher.get('resistance_1_price', 0)
        resist2 = watcher.get('resistance_2_price', 0)
        support1 = watcher.get('support_1_price', 0)
        support2 = watcher.get('support_2_price', 0)

        resist1_triggered = resist1 > 0 and current_price >= resist1
        resist2_triggered = resist2 > 0 and current_price >= resist2
        support1_triggered = support1 > 0 and current_price <= support1
        support2_triggered = support2 > 0 and current_price <= support2

        # 시그널 판단
        signal = None
        if watcher['status'] == 'waiting_buy' and buy_triggered:
            signal = '매수'
        elif watcher['status'] == 'waiting_sell':
            if resist2_triggered:
                signal = '2차저항 익절'
            elif resist1_triggered:
                signal = '1차저항 익절'
            elif support2_triggered:
                signal = '2차지지 손절'
            elif support1_triggered:
                signal = '1차지지 손절'

        return jsonify({
            "success": True,
            "data": {
                "code": code,
                "name": watcher.get('name', ''),
                "status": watcher['status'],
                "current_price": current_price,
                "buy_target_price": buy_target,
                "resistance_1": resist1,
                "resistance_2": resist2,
                "support_1": support1,
                "support_2": support2,
                "buy_triggered": buy_triggered,
                "resist1_triggered": resist1_triggered,
                "resist2_triggered": resist2_triggered,
                "support1_triggered": support1_triggered,
                "support2_triggered": support2_triggered,
                "signal": signal,
                "notify_only": watcher.get('notify_only', False)
            }
        })

    except Exception as e:
        logger.error(f"Mode2 모니터링 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== Mode2 API ==========

@app.route('/api/mode2/watchers', methods=['GET'])
def get_mode2_watchers():
    """Mode2 감시 리스트 조회 (stock_master.note 포함)"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        watchers = mode2_mgr.get_all_watchers(active_only=active_only)
        # stock_master note/summary 병합
        codes = [w['code'] for w in watchers if w.get('code')]
        if codes:
            sm_map = _get_news_storage().get_stock_master_notes(codes)
            for w in watchers:
                sm = sm_map.get(w.get('code'), {})
                w['sm_note'] = sm.get('note', '')
                w['sm_summary'] = sm.get('summary_2line', '')
        return jsonify({"success": True, "data": watchers})
    except Exception as e:
        logger.error(f"감시 리스트 조회 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/mode2/watchers', methods=['POST'])
def create_mode2_watcher():
    """Mode2 전략 추가"""
    try:
        data = request.json

        # 필수 필드 검증
        required_fields = ["code", "buy_target_price", "budget"]
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"필수 필드 누락: {field}"
                }), 400

        # 종목코드 정규화
        data["code"] = normalize_stock_code(data["code"])

        # 중복 체크
        if mode2_mgr.get_watcher(data["code"]):
            return jsonify({
                "success": False,
                "error": f"이미 등록된 종목입니다: {data['code']}"
            }), 400

        # 종목명 자동 조회
        if kiwoom_client and not data.get("name"):
            try:
                stock_info = kiwoom_client.get_stock_info(data["code"])
                data["name"] = stock_info.get("name", "")
                logger.info(f"종목명 조회: {data['code']} -> {data['name']}")
            except Exception as e:
                logger.warning(f"종목명 조회 실패: {e}")
                data["name"] = ""

        # 추가
        watcher = mode2_mgr.add_watcher(data)

        return jsonify({
            "success": True,
            "data": watcher
        }), 201

    except Exception as e:
        logger.error(f"종목 추가 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/watchers/<code>', methods=['GET'])
def get_mode2_watcher(code):
    """특정 종목 조회"""
    try:
        code = normalize_stock_code(code)
        watcher = mode2_mgr.get_watcher(code)

        if not watcher:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "data": watcher
        })

    except Exception as e:
        logger.error(f"종목 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/watchers/<code>', methods=['PUT'])
def update_mode2_watcher(code):
    """종목 정보 업데이트"""
    try:
        code = normalize_stock_code(code)
        data = request.json

        watcher = mode2_mgr.update_watcher(code, data)

        if not watcher:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "data": watcher
        })

    except Exception as e:
        logger.error(f"종목 업데이트 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/watchers/<code>', methods=['DELETE'])
def delete_mode2_watcher(code):
    """종목 삭제"""
    try:
        code = normalize_stock_code(code)
        success = mode2_mgr.delete_watcher(code)

        if not success:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "message": f"종목 삭제 완료: {code}"
        })

    except Exception as e:
        logger.error(f"종목 삭제 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/watchers/<code>/active', methods=['PATCH'])
def toggle_mode2_active(code):
    """종목 활성화/비활성화"""
    try:
        code = normalize_stock_code(code)
        data = request.json
        active = data.get("active", True)

        success = mode2_mgr.set_active(code, active)

        if not success:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "message": f"종목 {'활성화' if active else '비활성화'} 완료: {code}"
        })

    except Exception as e:
        logger.error(f"활성화 토글 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/mode2/watchers/<code>/reset', methods=['POST'])
def reset_mode2_watcher(code):
    """새 매매 리셋 — status/sold_history/bought 초기화"""
    try:
        code = normalize_stock_code(code)
        watcher = mode2_mgr.reset_for_new_trade(code)
        if not watcher:
            return jsonify({"success": False, "error": "종목을 찾을 수 없습니다"}), 404

        name = watcher.get('name', code)
        # 텔레그램 알림 (동기 방식)
        try:
            import requests as _req
            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
            chat_id = os.getenv('TELEGRAM_CHAT_ID')
            if bot_token and chat_id:
                msg = (f"🔄 Mode2 새 매매 시작\n\n"
                       f"종목: {name} ({code})\n"
                       f"매수타점: {watcher.get('buy_target_price', 0):,}원\n"
                       f"sold_history 초기화 → 모니터링 재개")
                _req.post(f"https://api.telegram.org/bot{bot_token}/sendMessage",
                          json={"chat_id": chat_id, "text": msg}, timeout=5)
        except Exception:
            pass
        return jsonify({"success": True, "message": f"{name} 새 매매 리셋 완료", "data": watcher})
    except Exception as e:
        logger.error(f"Mode2 리셋 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/mode2/watchers/<code>/status', methods=['PATCH'])
def update_mode2_status(code):
    """종목 상태 업데이트"""
    try:
        code = normalize_stock_code(code)
        data = request.json
        status = data.get("status")

        if not status:
            return jsonify({
                "success": False,
                "error": "status 필드가 필요합니다"
            }), 400

        success = mode2_mgr.update_status(code, status)

        if not success:
            return jsonify({
                "success": False,
                "error": "종목을 찾을 수 없습니다"
            }), 404

        return jsonify({
            "success": True,
            "message": f"상태 변경 완료: {code} -> {status}"
        })

    except Exception as e:
        logger.error(f"상태 업데이트 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== Order API ==========

@app.route('/api/config/order-mode', methods=['GET'])
def get_order_mode():
    """주문 모드 조회"""
    try:
        global_config = get_global_config()
        config = global_config.get_config()

        return jsonify({
            "success": True,
            "data": {
                "order_mode": config['order_mode'],
                "updated_at": config.get('updated_at')
            }
        })
    except Exception as e:
        logger.error(f"주문 모드 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/config/order-mode', methods=['PUT'])
def set_order_mode():
    """주문 모드 설정"""
    try:
        data = request.json
        mode = data.get('mode', '').strip()

        if mode not in ['simulation', 'real']:
            return jsonify({
                "success": False,
                "error": "주문 모드는 'simulation' 또는 'real'만 가능합니다"
            }), 400

        global_config = get_global_config()
        success = global_config.set_order_mode(mode)

        if success:
            mode_text = "시뮬레이션" if mode == 'simulation' else "실전"
            return jsonify({
                "success": True,
                "message": f"주문 모드가 '{mode_text}'으로 변경되었습니다",
                "data": {
                    "order_mode": mode
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "주문 모드 변경 실패"
            }), 500

    except Exception as e:
        logger.error(f"주문 모드 설정 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/order/buy', methods=['POST'])
def place_buy_order():
    """매수 주문"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        data = request.json
        code = data.get('code', '').strip()
        quantity = data.get('quantity')
        order_type = data.get('order_type', 'market')
        price = data.get('price', 0)
        simulation_mode = data.get('simulation_mode', None)  # None이면 환경변수 사용

        if not code:
            return jsonify({
                "success": False,
                "error": "종목코드가 필요합니다"
            }), 400

        if not quantity or quantity <= 0:
            return jsonify({
                "success": False,
                "error": "수량이 필요합니다"
            }), 400

        # 종목코드 정규화
        code = normalize_stock_code(code)

        # 주문 실행 (simulation_mode가 제공되면 환경변수보다 우선)
        result = kiwoom_client.place_buy_order(
            symbol=code,
            quantity=quantity,
            price=price,
            order_type=order_type,
            simulation_mode=simulation_mode
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"매수 주문 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/order/sell', methods=['POST'])
def place_sell_order():
    """매도 주문"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        data = request.json
        code = data.get('code', '').strip()
        quantity = data.get('quantity')  # None이면 전량
        order_type = data.get('order_type', 'market')
        price = data.get('price', 0)
        mode = data.get('mode', '').strip()  # mode1 or mode2
        simulation_mode = data.get('simulation_mode', None)  # None이면 환경변수 사용

        if not code:
            return jsonify({
                "success": False,
                "error": "종목코드가 필요합니다"
            }), 400

        # 종목코드 정규화
        code = normalize_stock_code(code)

        # 주문 실행 (simulation_mode가 제공되면 환경변수보다 우선)
        result = kiwoom_client.place_sell_order(
            symbol=code,
            quantity=quantity,
            price=price,
            order_type=order_type,
            simulation_mode=simulation_mode
        )

        # 주문 성공 시 manager에 기록
        if result['success']:
            if mode == 'mode1' and mode1_mgr:
                mode1_mgr.record_sell(code, is_auto=False)  # 수동 매도
            elif mode == 'mode2' and mode2_mgr:
                mode2_mgr.record_sell(code, is_auto=False)  # 수동 매도

        return jsonify(result)

    except Exception as e:
        logger.error(f"매도 주문 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/order/pending', methods=['GET'])
def get_pending_orders():
    """미체결 주문 조회"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        result = kiwoom_client.get_pending_orders()
        return jsonify(result)

    except Exception as e:
        logger.error(f"미체결 주문 조회 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/order/cancel', methods=['POST'])
def cancel_order():
    """주문 취소"""
    try:
        if not kiwoom_client:
            return jsonify({
                "success": False,
                "error": "Kiwoom API 미연결"
            }), 503

        data = request.json
        order_no = data.get('order_no', '').strip()
        code = data.get('code', '').strip()
        quantity = data.get('quantity')
        order_type = data.get('order_type', 'buy').strip()

        if not order_no:
            return jsonify({
                "success": False,
                "error": "주문번호가 필요합니다"
            }), 400

        if not code:
            return jsonify({
                "success": False,
                "error": "종목코드가 필요합니다"
            }), 400

        if not quantity or quantity <= 0:
            return jsonify({
                "success": False,
                "error": "취소 수량이 필요합니다"
            }), 400

        # 종목코드 정규화
        code = normalize_stock_code(code)

        # 주문 취소
        result = kiwoom_client.cancel_order(
            order_no=order_no,
            symbol=code,
            quantity=quantity,
            order_type=order_type
        )

        return jsonify(result)

    except Exception as e:
        logger.error(f"주문 취소 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== Seeking Signal API ==========

@app.route('/api/seeking-signal/analyze', methods=['POST'])
def seeking_signal_analyze():
    """Seeking Signal 종목 분석"""
    try:
        from seeking_signal_minho import analyze_with_custom_params

        data = request.json
        stock_code = normalize_stock_code(data.get('stock_code', ''))

        if not stock_code:
            return jsonify({
                "success": False,
                "error": "종목코드를 입력하세요"
            }), 400

        # 파라미터 추출 (UI에서 전송)
        params = {
            'bbwp_threshold': float(data.get('bbwp_threshold', 25)),
            'bbwp_consecutive_days': int(data.get('bbwp_consecutive_days', 5)),
            'pullback_max_pct': float(data.get('pullback_max_pct', 15)),
            'rally_min_pct': float(data.get('rally_min_pct', 20)),
            'range_threshold_pct': float(data.get('range_threshold_pct', 7)),
            'volume_ratio': float(data.get('volume_ratio', 0.5)),
            'adx_threshold': float(data.get('adx_threshold', 20)),
        }

        # 분석 실행
        report = analyze_with_custom_params(stock_code, **params)

        if 'error' in report:
            return jsonify({
                "success": False,
                "error": report['error']
            }), 500

        return jsonify({
            "success": True,
            "data": report
        })

    except Exception as e:
        logger.error(f"Seeking Signal 분석 실패: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/seeking-signal/defaults', methods=['GET'])
def seeking_signal_defaults():
    """기본 파라미터 조회"""
    try:
        from seeking_signal_minho.config import TYPE1_DEFAULTS, TYPE2_DEFAULTS, MICRO_DEFAULTS

        return jsonify({
            "success": True,
            "data": {
                "type1": TYPE1_DEFAULTS,
                "type2": TYPE2_DEFAULTS,
                "micro": MICRO_DEFAULTS,
            }
        })
    except Exception as e:
        logger.error(f"기본 파라미터 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========== Watchlist API ==========

def _get_watchlist_path():
    from pathlib import Path
    p = Path(os.getenv("WATCHLIST_PATH", ".data/watchlist.json"))
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _load_manual_watchlist():
    p = _get_watchlist_path()
    if not p.exists():
        return []
    try:
        import json as _json
        return _json.loads(p.read_text(encoding='utf-8')).get('manual', [])
    except Exception:
        return []


def _save_manual_watchlist(items):
    import json as _json
    _get_watchlist_path().write_text(
        _json.dumps({'manual': items}, ensure_ascii=False, indent=2), encoding='utf-8'
    )


@app.route('/api/watchlist', methods=['GET'])
@auth.login_required
def get_watchlist():
    try:
        manual = _load_manual_watchlist()
        manual_codes = {item['code'] for item in manual}
        # Mode2 watchers
        mode2_mgr = Mode2Manager()
        m2_watchers = mode2_mgr.get_all_watchers()
        m2_codes = {w['code'] for w in m2_watchers}
        result = []
        # Mode2 종목 먼저
        for w in m2_watchers:
            origin = 'both' if w['code'] in manual_codes else 'mode2'
            result.append({'code': w['code'], 'name': w.get('name', w['code']), 'origin': origin})
        # manual 전용 종목
        for item in manual:
            if item['code'] not in m2_codes:
                result.append({'code': item['code'], 'name': item.get('name', item['code']), 'origin': 'manual'})
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        logger.error(f"get_watchlist 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/watchlist', methods=['POST'])
@auth.login_required
def add_watchlist():
    data = request.json or {}
    raw = (data.get('codes') or '').strip()
    if not raw:
        return jsonify({'success': False, 'error': 'codes 필드 필요'}), 400
    try:
        manual = _load_manual_watchlist()
        existing = {item['code'] for item in manual}
        added = 0
        for part in raw.split(','):
            part = part.strip()
            if not part:
                continue
            code = normalize_stock_code(part) if part.isdigit() or (len(part) <= 6 and part.isalnum()) else part
            if code not in existing:
                manual.append({'code': code, 'name': code})
                existing.add(code)
                added += 1
        _save_manual_watchlist(manual)
        return jsonify({'success': True, 'added': added})
    except Exception as e:
        logger.error(f"add_watchlist 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/watchlist/bulk', methods=['POST'])
@auth.login_required
def bulk_set_watchlist():
    """수동 추가 종목 전체 교체 (편집 모드 저장용)."""
    data = request.json or {}
    codes = data.get('codes', [])
    if not isinstance(codes, list):
        return jsonify({'success': False, 'error': 'codes 배열 필요'}), 400
    try:
        items = []
        seen = set()
        for code in codes:
            code = code.strip()
            if not code:
                continue
            normalized = normalize_stock_code(code) if (code.isdigit() or (len(code) <= 6 and code.isalnum())) else code
            if normalized not in seen:
                items.append({'code': normalized, 'name': normalized})
                seen.add(normalized)
        _save_manual_watchlist(items)
        return jsonify({'success': True, 'count': len(items)})
    except Exception as e:
        logger.error(f"bulk_set_watchlist 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/watchlist/<code>', methods=['DELETE'])
@auth.login_required
def delete_watchlist(code):
    try:
        manual = _load_manual_watchlist()
        before = len(manual)
        manual = [item for item in manual if item['code'] != normalize_stock_code(code) and item['code'] != code]
        if len(manual) == before:
            return jsonify({'success': False, 'error': '해당 종목이 없거나 Mode2 종목입니다'}), 404
        _save_manual_watchlist(manual)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"delete_watchlist 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== Hotstock Parsed API ==========

import re as _re

_TAG_PATTERN = _re.compile(r'^\[(SS⬆️?|VI|SS)\]', _re.UNICODE)
_PRICE_PATTERN = _re.compile(r'현재가\s*:\s*(-?[\d,]+)\s*\(([^)]+)\)')
_THEME_PATTERN = _re.compile(r'테마\s*[：:]\s*(.+)')
_RELATED_PATTERN = _re.compile(r'^Y\s+[^:：]+[：:]\s*(.+)', _re.MULTILINE)


def _parse_hotstock_message(text: str) -> dict:
    """급등주 메시지 파싱. tag_type, stock_name, price, change, theme, related_stocks 반환."""
    first_line = text.split('\n')[0].strip()
    tag_type = None
    stock_name = None

    if '[SS⬆️]' in first_line or '[SS⬆]' in first_line:
        tag_type = 'ss_up'
        stock_name = _re.sub(r'^\[SS[⬆️⬆]*\]\s*', '', first_line)
    elif '[VI]' in first_line:
        tag_type = 'vi'
        stock_name = _re.sub(r'^\[VI\]\s*', '', first_line)
    elif '[SS]' in first_line:
        tag_type = 'ss'
        stock_name = _re.sub(r'^\[SS\]\s*', '', first_line)
    else:
        return {}

    # 종목명에서 현재가 부분 제거
    price_m = _PRICE_PATTERN.search(stock_name)
    price, change = None, None
    if price_m:
        stock_name = stock_name[:price_m.start()].strip()
        price = price_m.group(1)
        change = price_m.group(2)

    theme_m = _THEME_PATTERN.search(text)
    theme = theme_m.group(1).strip() if theme_m else None

    related = []
    for m in _RELATED_PATTERN.finditer(text):
        for name in m.group(1).split(','):
            name = name.strip()
            if name:
                related.append(name)

    return {
        'tag_type': tag_type,
        'stock_name': stock_name,
        'price': price,
        'change': change,
        'theme': theme,
        'related_stocks': related,
    }


@app.route('/api/hotstock/parsed', methods=['GET'])
@auth.login_required
def get_hotstock_parsed():
    target_date = request.args.get('date')
    since = request.args.get('since')
    until = request.args.get('until')
    try:
        ns = _get_news_storage()
        if since:
            messages = ns.get_messages_since(since, source_type='hot_stock')
        else:
            messages = ns.get_messages(target_date=target_date, source_type='hot_stock', until_utc=until)

        # 관심종목 목록
        manual = _load_manual_watchlist()
        manual_codes = {item['code'] for item in manual}
        mode2_mgr = Mode2Manager()
        m2_watchers = mode2_mgr.get_all_watchers()
        watchlist_names = set()
        for w in m2_watchers:
            watchlist_names.add(w.get('name', '').strip())
        for item in manual:
            watchlist_names.add(item.get('name', item['code']).strip())
        watchlist_names.discard('')

        result = []
        for msg in messages:
            parsed = _parse_hotstock_message(msg.get('text', ''))
            if not parsed:
                continue
            # 관심종목 매칭
            all_names = [parsed.get('stock_name', '')] + parsed.get('related_stocks', [])
            matches = [n for n in all_names if n and n in watchlist_names]
            parsed['message_id'] = msg['id']
            parsed['received_at'] = msg.get('received_at')
            parsed['watchlist_match'] = matches
            parsed['raw_text'] = msg.get('text', '')
            result.append(parsed)

        return jsonify({'success': True, 'data': result, 'count': len(result)})
    except Exception as e:
        logger.error(f"get_hotstock_parsed 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== Siwhang Results API ==========


@app.route('/api/siwhang/results', methods=['GET'])
@auth.login_required
def get_siwhang_results():
    target_date = request.args.get('date')
    try:
        ns = _get_news_storage()
        data = ns.get_siwhang_results(target_date=target_date)
        return jsonify({'success': True, 'data': data, 'count': len(data)})
    except Exception as e:
        logger.error(f"get_siwhang_results 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/siwhang/results', methods=['POST'])
@auth.login_required
def save_siwhang_results():
    data = request.json or {}
    results = data.get('results', [])
    if not isinstance(results, list):
        return jsonify({'success': False, 'error': 'results 배열 필요'}), 400
    try:
        ns = _get_news_storage()
        saved = ns.save_siwhang_results(results)
        return jsonify({'success': True, 'saved': saved})
    except Exception as e:
        logger.error(f"save_siwhang_results 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== News Filter API ==========

def _get_news_storage():
    """NewsStorage 인스턴스를 반환 (지연 초기화)."""
    if not hasattr(_get_news_storage, "_instance") or _get_news_storage._instance is None:
        from news_storage import NewsStorage
        db_path = os.getenv("NEWS_DB_PATH", ".data/news.db")
        _get_news_storage._instance = NewsStorage(db_path)
    return _get_news_storage._instance


def _get_keyword_storage(kw_type: str = 'news'):
    """KeywordStorage 인스턴스를 반환 (지연 초기화). kw_type: 'news' | 'hotstock'"""
    attr = f"_instance_{kw_type}"
    if not hasattr(_get_keyword_storage, attr) or getattr(_get_keyword_storage, attr) is None:
        from keyword_storage import KeywordStorage
        from keyword_config import resolve_news_keywords_path, resolve_hotstock_keywords_path
        if kw_type == 'hotstock':
            path = resolve_hotstock_keywords_path()
        else:
            path = resolve_news_keywords_path()
        setattr(_get_keyword_storage, attr, KeywordStorage(str(path)))
    return getattr(_get_keyword_storage, attr)


@app.route('/api/news/today', methods=['GET'])
@auth.login_required
def get_news_today():
    target_date = request.args.get('date')
    until = request.args.get('until')
    try:
        ns = _get_news_storage()
        messages = ns.get_messages(target_date=target_date, source_type='news', until_utc=until)
        return jsonify({"success": True, "data": messages, "count": len(messages)})
    except Exception as e:
        logger.error(f"get_news_today 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/news/filtered', methods=['GET'])
@auth.login_required
def get_news_filtered():
    target_date = request.args.get('date')
    try:
        ns = _get_news_storage()
        messages = ns.get_filtered_messages(target_date=target_date, source_type='news')
        return jsonify({"success": True, "data": messages, "count": len(messages)})
    except Exception as e:
        logger.error(f"get_news_filtered 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/hotstock/today', methods=['GET'])
@auth.login_required
def get_hotstock_today():
    target_date = request.args.get('date')
    try:
        ns = _get_news_storage()
        messages = ns.get_messages(target_date=target_date, source_type='hot_stock')
        return jsonify({"success": True, "data": messages, "count": len(messages)})
    except Exception as e:
        logger.error(f"get_hotstock_today 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/hotstock/filtered', methods=['GET'])
@auth.login_required
def get_hotstock_filtered():
    target_date = request.args.get('date')
    try:
        ns = _get_news_storage()
        messages = ns.get_filtered_messages(target_date=target_date, source_type='hot_stock')
        return jsonify({"success": True, "data": messages, "count": len(messages)})
    except Exception as e:
        logger.error(f"get_hotstock_filtered 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords', methods=['GET'])
@auth.login_required
def get_keywords():
    kw_type = request.args.get('type', 'news')
    try:
        ks = _get_keyword_storage(kw_type)
        return jsonify({"success": True, "data": ks.get_all(), "type": kw_type})
    except Exception as e:
        logger.error(f"get_keywords 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/include', methods=['POST'])
@auth.login_required
def add_include_keyword():
    data = request.json or {}
    keyword = (data.get('keyword') or '').strip()
    kw_type = data.get('type', 'news')
    if not keyword:
        return jsonify({"success": False, "error": "keyword 필드 필요"}), 400
    try:
        ks = _get_keyword_storage(kw_type)
        added = ks.add_include_keyword(keyword)
        return jsonify({"success": True, "added": added, "keywords": ks.get_all()})
    except Exception as e:
        logger.error(f"add_include_keyword 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/include', methods=['DELETE'])
@auth.login_required
def remove_include_keyword():
    data = request.json or {}
    keyword = (data.get('keyword') or '').strip()
    kw_type = data.get('type', 'news')
    if not keyword:
        return jsonify({"success": False, "error": "keyword 필드 필요"}), 400
    try:
        ks = _get_keyword_storage(kw_type)
        removed = ks.remove_include_keyword(keyword)
        return jsonify({"success": True, "removed": removed, "keywords": ks.get_all()})
    except Exception as e:
        logger.error(f"remove_include_keyword 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/exclude', methods=['POST'])
@auth.login_required
def add_exclude_keyword():
    data = request.json or {}
    keyword = (data.get('keyword') or '').strip()
    kw_type = data.get('type', 'news')
    if not keyword:
        return jsonify({"success": False, "error": "keyword 필드 필요"}), 400
    try:
        ks = _get_keyword_storage(kw_type)
        added = ks.add_exclude_keyword(keyword)
        return jsonify({"success": True, "added": added, "keywords": ks.get_all()})
    except Exception as e:
        logger.error(f"add_exclude_keyword 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/exclude', methods=['DELETE'])
@auth.login_required
def remove_exclude_keyword():
    data = request.json or {}
    keyword = (data.get('keyword') or '').strip()
    kw_type = data.get('type', 'news')
    if not keyword:
        return jsonify({"success": False, "error": "keyword 필드 필요"}), 400
    try:
        ks = _get_keyword_storage(kw_type)
        removed = ks.remove_exclude_keyword(keyword)
        return jsonify({"success": True, "removed": removed, "keywords": ks.get_all()})
    except Exception as e:
        logger.error(f"remove_exclude_keyword 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/set', methods=['POST'])
@auth.login_required
def set_keywords_bulk():
    """Include 또는 Exclude 키워드 전체 교체."""
    data = request.json or {}
    kw_type = data.get('type', 'news')
    field = data.get('field', 'include')  # 'include' | 'exclude'
    keywords = data.get('keywords', [])
    try:
        ks = _get_keyword_storage(kw_type)
        if field == 'include':
            ks.set_include_keywords(keywords)
        else:
            ks.set_exclude_keywords(keywords)
        return jsonify({"success": True, "keywords": ks.get_all()})
    except Exception as e:
        logger.error(f"set_keywords_bulk 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/group', methods=['POST'])
@auth.login_required
def add_keyword_group():
    data = request.json or {}
    keywords = data.get('keywords', [])
    kw_type = data.get('type', 'news')
    if not keywords or len(keywords) < 2:
        return jsonify({"success": False, "error": "keywords 2개 이상 필요"}), 400
    try:
        ks = _get_keyword_storage(kw_type)
        added = ks.add_include_group(keywords)
        return jsonify({"success": True, "added": added, "keywords": ks.get_all()})
    except Exception as e:
        logger.error(f"add_keyword_group 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/group', methods=['DELETE'])
@auth.login_required
def remove_keyword_group():
    data = request.json or {}
    keywords = data.get('keywords', [])
    kw_type = data.get('type', 'news')
    if not keywords:
        return jsonify({"success": False, "error": "keywords 필드 필요"}), 400
    try:
        ks = _get_keyword_storage(kw_type)
        removed = ks.remove_include_group(keywords)
        return jsonify({"success": True, "removed": removed, "keywords": ks.get_all()})
    except Exception as e:
        logger.error(f"remove_keyword_group 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/keywords/mode', methods=['PATCH'])
@auth.login_required
def set_keyword_mode():
    data = request.json or {}
    mode = (data.get('mode') or '').strip()
    kw_type = data.get('type', 'news')
    if mode not in ('loose', 'strict'):
        return jsonify({"success": False, "error": "mode는 loose 또는 strict"}), 400
    try:
        ks = _get_keyword_storage(kw_type)
        ks.set_mode(mode)
        return jsonify({"success": True, "mode": mode})
    except Exception as e:
        logger.error(f"set_keyword_mode 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/messages/delete', methods=['POST'])
@auth.login_required
def delete_messages():
    """메시지 선택 삭제. { ids: [], source_type: 'news'|'hotstock'|null }"""
    data = request.json or {}
    ids = [int(i) for i in data.get('ids', []) if str(i).isdigit()]
    source_type = data.get('source_type') or None
    if not ids:
        return jsonify({"success": False, "error": "ids 필드 필요"}), 400
    try:
        ns = _get_news_storage()
        deleted = ns.delete_messages(ids, source_type=source_type)
        return jsonify({"success": True, "deleted": deleted})
    except Exception as e:
        logger.error(f"delete_messages 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


_LISTENING_PAUSED_FLAG = Path(".data/listening_paused")

@app.route('/api/listening/status', methods=['GET'])
@auth.login_required
def get_listening_status():
    """리스닝 일시정지 상태 조회"""
    return jsonify({"paused": _LISTENING_PAUSED_FLAG.exists()})

@app.route('/api/listening/pause', methods=['POST'])
@auth.login_required
def pause_listening():
    """신규 메시지 수신 일시정지"""
    _LISTENING_PAUSED_FLAG.parent.mkdir(exist_ok=True)
    _LISTENING_PAUSED_FLAG.touch()
    logger.info("🔇 리스닝 일시정지 ON")
    return jsonify({"success": True, "paused": True})

@app.route('/api/listening/resume', methods=['POST'])
@auth.login_required
def resume_listening():
    """신규 메시지 수신 재개"""
    if _LISTENING_PAUSED_FLAG.exists():
        _LISTENING_PAUSED_FLAG.unlink()
    logger.info("🔊 리스닝 재개")
    return jsonify({"success": True, "paused": False})


@app.route('/api/messages/cleanup', methods=['POST'])
@auth.login_required
def cleanup_messages():
    """1일 지난 메시지 삭제. source_type 지정 시 해당 타입만."""
    data = request.json or {}
    source_type = data.get('source_type') or None
    try:
        ns = _get_news_storage()
        deleted = ns.cleanup_old_messages(source_type=source_type)
        return jsonify({"success": True, "deleted": deleted, "message": f"{deleted}건 삭제됨"})
    except Exception as e:
        logger.error(f"cleanup_messages 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/news/save', methods=['POST'])
@auth.login_required
def save_news_scrape():
    """선택 뉴스 스크래핑 저장. { ids: [] }"""
    data = request.json or {}
    ids = [int(i) for i in data.get('ids', []) if str(i).isdigit()]
    if not ids:
        return jsonify({"success": False, "error": "ids 필드 필요"}), 400
    try:
        ns = _get_news_storage()
        messages = ns.get_messages_by_ids(ids)
        saved_count = 0
        for msg in messages:
            ns.save_scraped_news(
                message_id=msg.get('id'),
                text=msg.get('text', ''),
                source_type=msg.get('source_type', 'news'),
                original_date=msg.get('date', ''),
            )
            saved_count += 1
        return jsonify({"success": True, "saved": saved_count})
    except Exception as e:
        logger.error(f"save_news_scrape 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/news/saved', methods=['GET'])
@auth.login_required
def get_saved_news():
    """저장된 뉴스 조회. ?q=검색어&source_type=news|hotstock"""
    search_query = request.args.get('q', '').strip() or None
    source_type = request.args.get('source_type', '').strip() or None
    try:
        ns = _get_news_storage()
        items = ns.get_saved_news(search_query=search_query, source_type=source_type)
        return jsonify({"success": True, "data": items, "count": len(items)})
    except Exception as e:
        logger.error(f"get_saved_news 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/news/saved/<int:saved_id>', methods=['DELETE'])
@auth.login_required
def delete_saved_news(saved_id):
    """저장된 뉴스 삭제."""
    try:
        ns = _get_news_storage()
        ns.delete_saved_news(saved_id)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"delete_saved_news 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/themes', methods=['GET'])
@auth.login_required
def get_themes():
    active_only = request.args.get('active_only', '0') == '1'
    try:
        ns = _get_news_storage()
        themes = ns.get_themes(active_only=active_only)
        return jsonify({"success": True, "data": themes})
    except Exception as e:
        logger.error(f"get_themes 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/themes', methods=['POST'])
@auth.login_required
def add_theme():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({"success": False, "error": "name 필드 필요"}), 400
    try:
        ns = _get_news_storage()
        ns.add_theme(name)
        return jsonify({"success": True, "message": f"테마 추가: {name}"}), 201
    except Exception as e:
        logger.error(f"add_theme 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/themes/<int:theme_id>', methods=['PATCH'])
@auth.login_required
def toggle_theme(theme_id):
    try:
        ns = _get_news_storage()
        ns.toggle_theme(theme_id)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"toggle_theme 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/themes/<int:theme_id>', methods=['DELETE'])
@auth.login_required
def delete_theme(theme_id):
    try:
        ns = _get_news_storage()
        ns.delete_theme(theme_id)
        return jsonify({"success": True})
    except Exception as e:
        logger.error(f"delete_theme 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/themes/reset', methods=['POST'])
@auth.login_required
def reset_themes():
    """테마 라이브러리 전체 초기화"""
    try:
        ns = _get_news_storage()
        with ns._conn() as conn:
            conn.execute("DELETE FROM themes")
        logger.info("테마 라이브러리 초기화 완료")
        return jsonify({"success": True, "message": "테마 라이브러리가 초기화되었습니다"})
    except Exception as e:
        logger.error(f"reset_themes 실패: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# ========== Backtest API ==========

@app.route('/api/backtest/sessions', methods=['GET'])
@auth.login_required
def get_backtest_sessions():
    try:
        ns = _get_news_storage()
        sessions = ns.get_backtest_sessions()
        return jsonify({'success': True, 'data': sessions})
    except Exception as e:
        logger.error(f"get_backtest_sessions 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backtest/sessions', methods=['POST'])
@auth.login_required
def create_backtest_session():
    data = request.json or {}
    run_date = (data.get('run_date') or '').strip()
    notes = (data.get('notes') or '').strip()
    version = (data.get('version') or 'v1').strip()
    strategy_desc = (data.get('strategy_desc') or '').strip()
    if not run_date:
        return jsonify({'success': False, 'error': 'run_date 필드 필요'}), 400
    try:
        ns = _get_news_storage()
        session_id = ns.create_backtest_session(run_date, notes, version, strategy_desc)
        return jsonify({'success': True, 'session_id': session_id}), 201
    except Exception as e:
        logger.error(f"create_backtest_session 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backtest/sessions/<int:session_id>', methods=['GET'])
@auth.login_required
def get_backtest_session(session_id):
    try:
        ns = _get_news_storage()
        picks = ns.get_backtest_picks(session_id)
        return jsonify({'success': True, 'data': picks})
    except Exception as e:
        logger.error(f"get_backtest_session 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backtest/picks', methods=['POST'])
@auth.login_required
def save_backtest_picks():
    """백테스트 추천 종목 배치 저장. { session_id, picks: [...] }"""
    data = request.json or {}
    session_id = data.get('session_id')
    picks = data.get('picks', [])
    if not session_id or not isinstance(picks, list):
        return jsonify({'success': False, 'error': 'session_id, picks 필드 필요'}), 400
    try:
        ns = _get_news_storage()
        saved_ids = []
        for p in picks:
            pid = ns.save_backtest_pick(
                session_id=session_id,
                slot_time=p.get('slot_time', ''),
                stock_name=p.get('stock_name', ''),
                stock_code=p.get('stock_code'),
                tag_type=p.get('tag_type'),
                theme=p.get('theme'),
                price_at_slot=p.get('price_at_slot'),
                analysis_text=p.get('analysis_text'),
                confidence=p.get('confidence'),
                catalyst=p.get('catalyst'),
                sources=p.get('sources'),
                source_message_id=p.get('source_message_id'),
                note_source=p.get('note_source'),
            )
            if pid:
                saved_ids.append(pid)
        return jsonify({'success': True, 'saved': len(saved_ids), 'ids': saved_ids}), 201
    except Exception as e:
        logger.error(f"save_backtest_picks 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backtest/compare', methods=['GET'])
@auth.login_required
def compare_backtest_sessions():
    """같은 날짜의 두 세션 picks 비교. ?session_a=1&session_b=2"""
    sid_a = request.args.get('session_a', type=int)
    sid_b = request.args.get('session_b', type=int)
    if not sid_a or not sid_b:
        return jsonify({'success': False, 'error': 'session_a, session_b 필요'}), 400
    try:
        ns = _get_news_storage()
        picks_a = ns.get_backtest_picks(sid_a)
        picks_b = ns.get_backtest_picks(sid_b)
        sessions = ns.get_backtest_sessions()
        meta = {str(s['id']): s for s in sessions}
        return jsonify({'success': True,
                        'session_a': {'meta': meta.get(str(sid_a), {}), 'picks': picks_a},
                        'session_b': {'meta': meta.get(str(sid_b), {}), 'picks': picks_b}})
    except Exception as e:
        logger.error(f"compare_backtest_sessions 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/backtest/picks/<int:pick_id>/pnl', methods=['PUT'])
@auth.login_required
def update_backtest_pnl(pick_id):
    """P&L 입력/수정. { buy_price, exit_price, stoploss_price, notes }"""
    data = request.json or {}
    buy_price = data.get('buy_price')
    exit_price = data.get('exit_price')
    stoploss_price = data.get('stoploss_price')
    notes = (data.get('notes') or '').strip()

    # profit_pct 계산
    profit_pct = None
    result = None
    if buy_price and buy_price > 0:
        if exit_price is not None:
            profit_pct = round((exit_price - buy_price) / buy_price * 100, 2)
            if stoploss_price and exit_price <= stoploss_price:
                result = 'stoploss'
            elif exit_price > buy_price:
                result = 'win'
            else:
                result = 'loss'

    try:
        ns = _get_news_storage()
        ok = ns.upsert_backtest_pnl(pick_id, buy_price, exit_price, stoploss_price, result, profit_pct, notes)
        if not ok:
            return jsonify({'success': False, 'error': '저장 실패'}), 500
        return jsonify({'success': True, 'profit_pct': profit_pct, 'result': result})
    except Exception as e:
        logger.error(f"update_backtest_pnl 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/analysis/context', methods=['GET'])
@auth.login_required
def get_analysis_context():
    """당일 분석 컨텍스트 조회."""
    ctx_date = request.args.get('date')
    ns = _get_news_storage()
    return jsonify({'success': True, 'context': ns.get_analysis_context(ctx_date)})


@app.route('/api/analysis/morning-report', methods=['POST'])
@auth.login_required
def save_morning_report():
    """아침 시황 리포트 저장. { morning_report: {...}, date: 'YYYY-MM-DD' }"""
    data = request.json or {}
    report = data.get('morning_report')
    ctx_date = data.get('date')
    if not report:
        return jsonify({'success': False, 'error': 'morning_report 필요'}), 400
    ns = _get_news_storage()
    ok = ns.save_morning_report(report, ctx_date)
    return jsonify({'success': ok})


@app.route('/api/analysis/instruction', methods=['POST'])
@auth.login_required
def save_next_instruction():
    """다음 슬롯 분석용 추가 인스트럭션 저장. { instruction: "...", date: "YYYY-MM-DD" }"""
    data = request.json or {}
    instruction = (data.get('instruction') or '').strip() or None
    ctx_date = data.get('date')
    ns = _get_news_storage()
    ok = ns.save_next_instruction(instruction, ctx_date)
    return jsonify({'success': ok})


@app.route('/api/analysis/interval-context', methods=['POST'])
@auth.login_required
def update_interval_context():
    """슬롯 분석 완료 후 interval_context 업데이트 (스킬에서 호출). { interval_context: {...} }"""
    data = request.json or {}
    ctx = data.get('interval_context')
    ctx_date = data.get('date')
    if not ctx:
        return jsonify({'success': False, 'error': 'interval_context 필요'}), 400
    ns = _get_news_storage()
    ok = ns.update_interval_context(ctx, ctx_date)
    return jsonify({'success': ok})


@app.route('/api/analysis/request', methods=['POST'])
@auth.login_required
def request_analysis():
    """웹 UI '▶ 지금 분석' 버튼 → 분석 트리거 플래그 세팅. poll_trigger.py가 감지해 실행."""
    ns = _get_news_storage()
    ok = ns.set_analysis_request()
    return jsonify({'success': ok})


@app.route('/api/analysis/pending', methods=['GET'])
@auth.login_required
def get_analysis_pending():
    """poll_trigger.py가 30초마다 polling. pending이면 값 반환 + 자동 클리어."""
    ns = _get_news_storage()
    val = ns.get_and_clear_analysis_request()
    return jsonify({'pending': val is not None, 'requested_at': val})


@app.route('/api/live/picks', methods=['GET'])
@auth.login_required
def get_live_picks():
    """오늘 날짜 최신 backtest session의 picks 반환.
    ?date=YYYY-MM-DD 로 날짜 지정 가능. 기본값: 오늘.
    stock_code 없는 항목은 stock_name_map으로 자동 보완.
    """
    from datetime import date as _date
    target_date = request.args.get('date') or _date.today().isoformat()
    ns = _get_news_storage()

    # 오늘 날짜 최신 session 조회
    sessions = ns.get_backtest_sessions()
    today_sessions = [s for s in sessions if s.get('run_date') == target_date]
    if not today_sessions:
        return jsonify({'success': True, 'data': [], 'date': target_date, 'session_id': None})

    session = today_sessions[0]  # created_at DESC 정렬이므로 첫 번째가 최신
    picks = ns.get_backtest_picks(session['id'])

    # stock_code 없는 항목 자동 보완
    name_map = _load_stock_name_map()
    for p in picks:
        if not p.get('stock_code') and p.get('stock_name'):
            code = name_map.get(p['stock_name'])
            if code:
                p['stock_code'] = code

    return jsonify({'success': True, 'data': picks, 'date': target_date, 'session_id': session['id']})


# ─── 재무정보 (Financial Info) ────────────────────────────────────────────

import json as _json
import zipfile as _zipfile
import io as _io
import urllib.request as _urlreq
import xml.etree.ElementTree as _ET

_DART_KEY = 'c77a3bdb4d1b8bdf50792863473f716db261d989'
_CORP_CODE_MAP_PATH = Path('.data/corp_code_map.json')
_STOCK_NAME_MAP_PATH = Path('.data/stock_name_map.json')
_corp_code_map_cache: dict = {}
_stock_name_map_cache: dict = {}   # 종목명 → stock_code


def _load_corp_code_map() -> dict:
    """stock_code → {corp_code, corp_name} 매핑. 파일 캐시 우선."""
    global _corp_code_map_cache
    if _corp_code_map_cache:
        return _corp_code_map_cache
    if _CORP_CODE_MAP_PATH.exists():
        try:
            with open(_CORP_CODE_MAP_PATH, 'r', encoding='utf-8') as f:
                _corp_code_map_cache = _json.load(f)
            return _corp_code_map_cache
        except Exception:
            pass
    # 파일 없으면 DART에서 다운로드 (최초 1회)
    try:
        url = f'https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={_DART_KEY}'
        data = _urlreq.urlopen(url, timeout=30).read()
        zf = _zipfile.ZipFile(_io.BytesIO(data))
        xml_data = zf.read(zf.namelist()[0])
        root = _ET.fromstring(xml_data)
        result = {}
        name_map = {}
        for item in root.findall('list'):
            code = item.findtext('stock_code', '').strip()
            corp_code = item.findtext('corp_code', '').strip()
            corp_name = item.findtext('corp_name', '').strip()
            if code:
                result[code] = {'corp_code': corp_code, 'corp_name': corp_name}
                name_map[corp_name] = code
        _CORP_CODE_MAP_PATH.parent.mkdir(exist_ok=True)
        with open(_CORP_CODE_MAP_PATH, 'w', encoding='utf-8') as f:
            _json.dump(result, f, ensure_ascii=False, separators=(',', ':'))
        with open(_STOCK_NAME_MAP_PATH, 'w', encoding='utf-8') as f:
            _json.dump(name_map, f, ensure_ascii=False, separators=(',', ':'))
        _corp_code_map_cache = result
        logger.info(f"corp_code_map 저장 완료: {len(result)}개")
        return result
    except Exception as e:
        logger.error(f"corp_code_map 로드 실패: {e}")
        return {}


def _load_stock_name_map() -> dict:
    """종목명 → stock_code 역방향 매핑."""
    global _stock_name_map_cache
    if _stock_name_map_cache:
        return _stock_name_map_cache
    if _STOCK_NAME_MAP_PATH.exists():
        try:
            with open(_STOCK_NAME_MAP_PATH, 'r', encoding='utf-8') as f:
                _stock_name_map_cache = _json.load(f)
            return _stock_name_map_cache
        except Exception:
            pass
    # stock_name_map 없으면 corp_code_map에서 역방향 생성
    corp_map = _load_corp_code_map()
    _stock_name_map_cache = {v['corp_name']: k for k, v in corp_map.items()}
    return _stock_name_map_cache


@app.route('/api/stock/search', methods=['GET'])
@auth.login_required
def stock_search():
    """종목명 키워드 검색. ?q=삼성  → 매칭되는 종목 목록 반환 (최대 20개)."""
    q = (request.args.get('q') or '').strip()
    if len(q) < 1:
        return jsonify({'success': True, 'results': []})
    name_map = _load_stock_name_map()
    results = [
        {'stock_code': code, 'stock_name': name}
        for name, code in name_map.items()
        if q in name
    ]
    results.sort(key=lambda x: (not x['stock_name'].startswith(q), x['stock_name']))
    return jsonify({'success': True, 'results': results[:20]})


@app.route('/api/backtest/fix-stock-codes', methods=['POST'])
@auth.login_required
def fix_backtest_stock_codes():
    """backtest_picks 중 stock_code가 NULL인 종목을 stock_name_map으로 자동 채움."""
    ns = _get_news_storage()
    name_map = _load_stock_name_map()
    updated = 0
    try:
        with ns._conn() as conn:
            rows = conn.execute(
                "SELECT id, stock_name FROM backtest_picks WHERE stock_code IS NULL OR stock_code = ''"
            ).fetchall()
            for row in rows:
                code = name_map.get(row['stock_name'])
                if code:
                    conn.execute(
                        "UPDATE backtest_picks SET stock_code=? WHERE id=?",
                        (code, row['id'])
                    )
                    updated += 1
        return jsonify({'success': True, 'updated': updated, 'total_null': len(rows)})
    except Exception as e:
        logger.error(f"fix_backtest_stock_codes 실패: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


def _dart_financial(corp_code: str) -> dict:
    """DART fnlttSinglAcntAll: 부채비율, 유동비율 계산용 재무제표 조회."""
    from datetime import date as _date
    year = _date.today().year - 1  # 작년 사업보고서
    url = (f'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
           f'?crtfc_key={_DART_KEY}&corp_code={corp_code}'
           f'&bsns_year={year}&reprt_code=11011&fs_div=CFS')
    try:
        r = _urlreq.urlopen(url, timeout=15).read()
        data = _json.loads(r)
        if data.get('status') != '000':
            return {}
        items = data.get('list', [])
        accts: dict = {}
        priority = {'자산총계': 0, '부채총계': 0, '자본총계': 0, '유동자산': 0, '유동부채': 0}
        for item in items:
            nm = item.get('account_nm', '')
            if nm in priority and priority[nm] == 0:
                try:
                    v = int(str(item.get('thstrm_amount', '0')).replace(',', ''))
                    accts[nm] = v
                    priority[nm] = 1  # 첫 번째 값만 사용
                except Exception:
                    pass
        result = {'bsns_year': year}
        total_assets = accts.get('자산총계', 0)
        total_liab   = accts.get('부채총계', 0)
        total_equity = accts.get('자본총계', 0)
        cur_assets   = accts.get('유동자산', 0)
        cur_liab     = accts.get('유동부채', 0)
        if total_equity > 0:
            result['debt_ratio'] = round(total_liab / total_equity * 100, 1)
        if cur_liab > 0:
            result['current_ratio'] = round(cur_assets / cur_liab * 100, 1)
        if total_assets > 0:
            result['total_assets_bil'] = round(total_assets / 1e8)
        return result
    except Exception as e:
        logger.warning(f"DART 재무조회 실패 ({corp_code}): {e}")
        return {}


def _kiwoom_basic_info(stock_code: str) -> dict:
    """Kiwoom ka10001 주식기본정보조회: 시가총액, PER, ROE, 영업이익 등."""
    if not kiwoom_client:
        return {}
    try:
        import requests as _req
        token = get_token()
        headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'authorization': f'Bearer {token}',
            'api-id': 'ka10001',
        }
        r = _req.post(
            f"{kiwoom_client.host}/api/dostk/stkinfo",
            headers=headers, json={'stk_cd': stock_code}, timeout=10
        )
        if r.status_code != 200:
            return {}
        d = r.json()
        if d.get('return_code') != 0:
            return {}

        def _clean(v):
            try:
                return float(str(v).lstrip('+-').replace(',', ''))
            except Exception:
                return None

        return {
            'market_cap_bil': _clean(d.get('mac')),      # 시가총액 (억원)
            'per': _clean(d.get('per')),
            'pbr': _clean(d.get('pbr')),
            'roe': _clean(d.get('roe')),
            'eps': _clean(d.get('eps')),
            'bps': _clean(d.get('bps')),
            'sales_bil': _clean(d.get('sale_amt')),        # 매출액 (억원)
            'op_income_bil': _clean(d.get('bus_pro')),     # 영업이익 (억원)
            'net_income_bil': _clean(d.get('cup_nga')),    # 당기순이익 (억원)
            'flo_stk': _clean(d.get('flo_stk')),           # 유동주식수 (천주)
            'flo_rt': _clean(d.get('dstr_rt')),            # 유통비율 %
        }
    except Exception as e:
        logger.warning(f"Kiwoom ka10001 조회 실패 ({stock_code}): {e}")
        return {}


@app.route('/api/financial-info', methods=['GET'])
@auth.login_required
def get_financial_info():
    """종목 재무정보 조회. ?stock_code=XXXXXX
    Kiwoom ka10001(시가총액/PER/ROE/영업이익) + DART(부채비율/유동비율) 결합.
    """
    stock_code = (request.args.get('stock_code') or '').strip().zfill(6)
    if not stock_code:
        return jsonify({'success': False, 'error': 'stock_code 필요'}), 400

    result = {'stock_code': stock_code}

    # 1) Kiwoom 기본정보
    kw = _kiwoom_basic_info(stock_code)
    result.update(kw)

    # 2) DART 재무제표 (부채비율, 유동비율)
    corp_map = _load_corp_code_map()
    corp_info = corp_map.get(stock_code)
    if corp_info:
        corp_code = corp_info['corp_code']
        dart = _dart_financial(corp_code)
        result.update(dart)
        result['corp_name_dart'] = corp_info.get('corp_name', '')
    else:
        result['dart_error'] = 'corp_code 매핑 없음'

    return jsonify({'success': True, 'data': result})


# ─── 종목 마스터 (stock_master) ─────────────────────────────────────────────

@app.route('/api/stock-master/<stock_code>', methods=['GET'])
@auth.login_required
def get_stock_master(stock_code):
    """종목 마스터 조회. 재무정보가 없거나 오래됐으면 refresh=true 포함."""
    stock_code = stock_code.strip().zfill(6)
    ns = _get_news_storage()
    data = ns.get_stock_master(stock_code) or {'stock_code': stock_code}

    # 재무 fresh 여부 (24시간 이내)
    finance_stale = True
    fu = data.get('finance_updated_at')
    if fu:
        try:
            from datetime import datetime as _dt
            updated = _dt.fromisoformat(fu)
            finance_stale = (_dt.utcnow() - updated).total_seconds() > 86400
        except Exception:
            pass

    # 시황 히스토리
    history = ns.get_stock_siwhang_history(stock_code, limit=10)

    return jsonify({
        'success': True,
        'data': data,
        'finance_stale': finance_stale,
        'history': history,
    })


@app.route('/api/stock-master/<stock_code>', methods=['POST'])
@auth.login_required
def update_stock_master(stock_code):
    """종목 마스터 수동 업데이트 (테마, 노트 등)."""
    stock_code = stock_code.strip().zfill(6)
    body = request.json or {}
    ns = _get_news_storage()
    ok = ns.upsert_stock_master(stock_code, **{
        k: v for k, v in body.items()
        if k in ('stock_name', 'themes', 'note')
    })
    return jsonify({'success': ok})


@app.route('/api/stock-master/<stock_code>/refresh-finance', methods=['POST'])
@auth.login_required
def refresh_stock_finance(stock_code):
    """재무정보 강제 갱신: Kiwoom ka10001 + DART 분기(2년) 조회 후 stock_master 저장."""
    stock_code = stock_code.strip().zfill(6)
    ns = _get_news_storage()

    # 1) Kiwoom 기본정보
    kw = _kiwoom_basic_info(stock_code)

    # 2) DART 재무제표
    corp_map = _load_corp_code_map()
    corp_info = corp_map.get(stock_code)
    dart_annual = {}
    dart_q_this = {}
    dart_q_prev = {}
    if corp_info:
        corp_code = corp_info['corp_code']
        dart_annual = _dart_financial(corp_code)
        dart_q_this, dart_q_prev = _dart_financial_quarterly(corp_code)

    from datetime import datetime as _dt
    now_iso = _dt.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

    fields = {
        'finance_updated_at': now_iso,
    }
    if kw:
        fields['market_cap_bil'] = kw.get('market_cap_bil')
        fields['per'] = kw.get('per')
        fields['roe'] = kw.get('roe')
        fields['op_income_bil'] = kw.get('op_income_bil')
    if dart_annual:
        fields['debt_ratio'] = dart_annual.get('debt_ratio')
        fields['current_ratio'] = dart_annual.get('current_ratio')
    if dart_q_this:
        fields['op_income_bil'] = dart_q_this.get('op_income_bil', fields.get('op_income_bil'))
    if dart_q_prev:
        fields['op_income_prev_bil'] = dart_q_prev.get('op_income_bil')

    # 종목명 저장 (있으면)
    name_map = _load_stock_name_map()
    for nm, cd in name_map.items():
        if cd == stock_code:
            fields['stock_name'] = nm
            break

    if corp_info:
        fields['corp_code'] = corp_info['corp_code']

    ns.upsert_stock_master(stock_code, **fields)

    result = {'stock_code': stock_code}
    result.update(kw)
    result.update(dart_annual)
    if dart_q_this:
        result['op_income_bil_q'] = dart_q_this.get('op_income_bil')
        result['bsns_year_q'] = dart_q_this.get('bsns_year')
        result['reprt_q'] = dart_q_this.get('reprt_code')
    if dart_q_prev:
        result['op_income_prev_bil_q'] = dart_q_prev.get('op_income_bil')
        result['bsns_year_prev_q'] = dart_q_prev.get('bsns_year')

    result['finance_updated_at'] = now_iso
    return jsonify({'success': True, 'data': result})


@app.route('/api/stock-master/<stock_code>/history', methods=['GET'])
@auth.login_required
def get_stock_siwhang_history(stock_code):
    """종목별 시황 히스토리 (급등주 feed 기반, 최근 10개)."""
    stock_code = stock_code.strip().zfill(6)
    ns = _get_news_storage()
    history = ns.get_stock_siwhang_history(stock_code, limit=10)
    return jsonify({'success': True, 'history': history})


@app.route('/api/stock-master/<stock_code>/history', methods=['POST'])
@auth.login_required
def add_stock_siwhang_history(stock_code):
    """시황 히스토리 추가 (백테스트 스킬에서 호출)."""
    stock_code = stock_code.strip().zfill(6)
    body = request.json or {}
    ns = _get_news_storage()
    ok = ns.add_stock_siwhang_history(
        stock_code=stock_code,
        stock_name=body.get('stock_name', ''),
        event_date=body.get('event_date', ''),
        tag_type=body.get('tag_type', ''),
        theme=body.get('theme', ''),
        feed_text=body.get('feed_text', ''),
        source_message_id=body.get('source_message_id'),
    )
    return jsonify({'success': ok})


def _dart_financial_quarterly(corp_code: str):
    """DART 1분기 보고서 2개 연도 조회: (올해1Q, 작년1Q) → (dict, dict)."""
    from datetime import date as _date
    results = []
    for year in [_date.today().year, _date.today().year - 1]:
        url = (f'https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json'
               f'?crtfc_key={_DART_KEY}&corp_code={corp_code}'
               f'&bsns_year={year}&reprt_code=11014&fs_div=CFS')
        try:
            import urllib.request as _urlreq2
            r = _urlreq2.urlopen(url, timeout=15).read()
            data = _json.loads(r)
            if data.get('status') != '000':
                results.append({})
                continue
            items = data.get('list', [])
            accts: dict = {}
            for item in items:
                nm = item.get('account_nm', '')
                if nm == '영업이익' and '영업이익' not in accts:
                    try:
                        v = int(str(item.get('thstrm_amount', '0')).replace(',', ''))
                        accts['영업이익'] = v
                    except Exception:
                        pass
            op = accts.get('영업이익', 0)
            results.append({'bsns_year': year, 'reprt_code': '11014',
                             'op_income_bil': round(op / 1e8, 1) if op else None})
        except Exception as e:
            logger.warning(f"DART 분기 재무조회 실패 ({corp_code}, {year}): {e}")
            results.append({})
    this_q = results[0] if len(results) > 0 else {}
    prev_q = results[1] if len(results) > 1 else {}
    return this_q, prev_q


# ─── 종목 마스터 노트 / 검색 ─────────────────────────────────────────────────

@app.route('/api/stock-master/search', methods=['GET'])
@auth.login_required
def search_stock_master():
    ns = _get_news_storage()
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'success': True, 'data': []})
    results = ns.search_stock_master(q, limit=20)
    return jsonify({'success': True, 'data': results})


@app.route('/api/stock-master/<stock_code>/note', methods=['GET'])
@auth.login_required
def get_stock_note(stock_code):
    ns = _get_news_storage()
    data = ns.get_stock_master(stock_code) or {}
    return jsonify({'success': True, 'note': data.get('note', ''), 'summary_2line': data.get('summary_2line', '')})


@app.route('/api/stock-master/<stock_code>/note', methods=['PUT'])
@auth.login_required
def update_stock_note_api(stock_code):
    ns = _get_news_storage()
    data = request.get_json() or {}
    note = data.get('note', '')
    ns.update_stock_note(stock_code, note)
    return jsonify({'success': True})


@app.route('/api/stock-master/<stock_code>/note/prepend', methods=['POST'])
@auth.login_required
def prepend_stock_note(stock_code):
    """날짜+내용을 기존 노트 앞에 붙이기."""
    ns = _get_news_storage()
    data = request.get_json() or {}
    date_str = data.get('date_str', '').strip()
    content = data.get('content', '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'content 필수'}), 400
    merged = ns.prepend_stock_note(stock_code, date_str, content)
    return jsonify({'success': True, 'note': merged})


@app.route('/api/stock-master/<stock_code>/summary', methods=['PUT'])
@auth.login_required
def update_stock_summary(stock_code):
    ns = _get_news_storage()
    data = request.get_json() or {}
    summary = data.get('summary_2line', '').strip()
    if not summary:
        return jsonify({'success': False, 'error': 'summary_2line 필수'}), 400
    ns.update_stock_summary(stock_code, summary)
    return jsonify({'success': True})


# ─── 종목 마스터 ← 관심종목 동기화 ──────────────────────────────────────────

@app.route('/api/stock-master/sync-watchlist', methods=['POST'])
@auth.login_required
def sync_watchlist_to_master():
    """Mode1/Mode2 감시종목을 stock_master에 upsert."""
    ns = _get_news_storage()
    from mode2_manager import Mode2Manager
    from mode1_manager import Mode1Manager
    m2 = Mode2Manager()
    m1 = Mode1Manager()
    synced = 0
    for w in m2.get_all_watchers() + m1.get_all_watchers():
        code = w.get('code') or w.get('stock_code')
        name = w.get('name') or w.get('stock_name')
        if code:
            ns.upsert_stock_master(code, stock_name=name)
            synced += 1
    return jsonify({'success': True, 'synced': synced})


# ─── 관심종목 그룹 (watchlist_groups) ─────────────────────────────────────────

@app.route('/api/watchlist-groups', methods=['GET'])
@auth.login_required
def get_watchlist_groups():
    ns = _get_news_storage()
    pinned_only = request.args.get('pinned') == '1'
    groups = ns.get_watchlist_groups(pinned_only=pinned_only)
    return jsonify({'success': True, 'groups': groups})


@app.route('/api/watchlist-groups', methods=['POST'])
@auth.login_required
def add_watchlist_group():
    data = request.json or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'success': False, 'error': 'name 필요'}), 400
    ns = _get_news_storage()
    gid = ns.add_watchlist_group(
        name=name,
        file_origin=data.get('file_origin'),
        pinned=data.get('pinned', True),
        display_order=data.get('display_order', 0),
    )
    return jsonify({'success': True, 'id': gid})


@app.route('/api/watchlist-groups/<int:group_id>', methods=['PUT'])
@auth.login_required
def update_watchlist_group(group_id):
    data = request.json or {}
    ns = _get_news_storage()
    ok = ns.update_watchlist_group(group_id, **data)
    return jsonify({'success': ok})


@app.route('/api/watchlist-groups/<int:group_id>', methods=['DELETE'])
@auth.login_required
def delete_watchlist_group(group_id):
    ns = _get_news_storage()
    ok = ns.delete_watchlist_group(group_id)
    return jsonify({'success': ok})


@app.route('/api/watchlist-groups/<int:group_id>/items', methods=['GET'])
@auth.login_required
def get_watchlist_group_items(group_id):
    ns = _get_news_storage()
    items = ns.get_watchlist_items(group_id)
    # Enrich with stock_master note/themes
    codes = [it['stock_code'] for it in items if it.get('stock_code')]
    master_map = {}
    if codes:
        with ns._conn() as conn:
            placeholders = ','.join('?' * len(codes))
            rows = conn.execute(
                f"SELECT stock_code, stock_name, themes, note FROM stock_master WHERE stock_code IN ({placeholders})",
                codes
            ).fetchall()
            for r in rows:
                master_map[r['stock_code']] = dict(r)
    for it in items:
        if it.get('stock_code') and it['stock_code'] in master_map:
            m = master_map[it['stock_code']]
            it['master_themes'] = m.get('themes')
            it['master_note_snippet'] = (m.get('note') or '')[:120]
    return jsonify({'success': True, 'items': items})


@app.route('/api/watchlist-groups/<int:group_id>/items', methods=['POST'])
@auth.login_required
def add_watchlist_item(group_id):
    data = request.json or {}
    ns = _get_news_storage()
    iid = ns.add_watchlist_item(
        group_id=group_id,
        item_type=data.get('item_type', 'stock'),
        stock_code=data.get('stock_code'),
        stock_name=data.get('stock_name'),
        subgroup_label=data.get('subgroup_label'),
        memo=data.get('memo'),
        display_order=data.get('display_order', 9999),
    )
    return jsonify({'success': True, 'id': iid})


@app.route('/api/watchlist-items/<int:item_id>', methods=['PUT'])
@auth.login_required
def update_watchlist_item(item_id):
    data = request.json or {}
    ns = _get_news_storage()
    ok = ns.update_watchlist_item(item_id, **data)
    return jsonify({'success': ok})


@app.route('/api/watchlist-items/<int:item_id>', methods=['DELETE'])
@auth.login_required
def delete_watchlist_item(item_id):
    ns = _get_news_storage()
    ok = ns.delete_watchlist_item(item_id)
    return jsonify({'success': ok})


@app.route('/api/watchlist-items/<int:item_id>/move', methods=['POST'])
@auth.login_required
def move_watchlist_item(item_id):
    data = request.json or {}
    target_group_id = data.get('target_group_id')
    if not target_group_id:
        return jsonify({'success': False, 'error': 'target_group_id 필요'}), 400
    ns = _get_news_storage()
    ok = ns.move_watchlist_item(item_id, int(target_group_id), data.get('target_order', 9999))
    return jsonify({'success': ok})


@app.route('/api/watchlist-groups/<int:group_id>/reorder', methods=['POST'])
@auth.login_required
def reorder_watchlist_items(group_id):
    data = request.json or {}
    ordered_ids = data.get('ordered_ids', [])
    ns = _get_news_storage()
    ok = ns.reorder_watchlist_items(group_id, ordered_ids)
    return jsonify({'success': ok})


@app.route('/api/watchlist-groups/reorder-groups', methods=['POST'])
@auth.login_required
def reorder_watchlist_groups():
    data = request.json or {}
    ordered_ids = data.get('ordered_ids', [])
    ns = _get_news_storage()
    with ns._conn() as conn:
        for i, gid in enumerate(ordered_ids):
            conn.execute("UPDATE watchlist_groups SET display_order=? WHERE id=?", (i, gid))
    return jsonify({'success': True})


@app.route('/api/watchlist-groups/export-csv', methods=['GET'])
@auth.login_required
def export_watchlist_notes_csv():
    """당일(또는 since 날짜 이후) 노트 수정 종목을 CSV로 반환."""
    since = request.args.get('date', date.today().isoformat())
    ns = _get_news_storage()
    items = ns.get_note_updated_items(since)
    import io, csv as _csv
    buf = io.StringIO()
    w = _csv.writer(buf)
    w.writerow(['종목코드', '종목명', '그룹', '노트요약', '수정시각'])
    for it in items:
        summary = (it.get('summary_2line') or '').replace('\n', ' ')
        note_raw = (it.get('note') or '')
        note_snippet = note_raw.replace('\n', ' ')[:200]
        w.writerow([it.get('stock_code',''), it.get('stock_name',''),
                    it.get('group_name',''), summary or note_snippet,
                    it.get('note_updated_at','')])
    csv_bytes = buf.getvalue().encode('utf-8-sig')
    from flask import Response
    return Response(
        csv_bytes,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename="watchlist_notes_{since}.csv"'}
    )


@app.route('/api/watchlist-groups/search', methods=['GET'])
@auth.login_required
def search_watchlist_items():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify({'success': False, 'error': 'q 필요'}), 400
    ns = _get_news_storage()
    results = ns.search_watchlist(q, limit=50)
    return jsonify({'success': True, 'results': results})


# ─── 格言(Trading Mottos) ──────────────────────────────────────────────────

@app.route('/api/mottos', methods=['GET'])
@auth.login_required
def get_mottos():
    ns = _get_news_storage()
    return jsonify({'success': True, 'mottos': ns.get_mottos()})


@app.route('/api/mottos', methods=['POST'])
@auth.login_required
def add_motto():
    data = request.json or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'content 필요'}), 400
    ns = _get_news_storage()
    mid = ns.add_motto(content)
    if mid is None:
        return jsonify({'success': False, 'error': '저장 실패'}), 500
    return jsonify({'success': True, 'id': mid})


@app.route('/api/mottos/<int:motto_id>', methods=['PUT'])
@auth.login_required
def update_motto(motto_id):
    data = request.json or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'content 필요'}), 400
    ns = _get_news_storage()
    ok = ns.update_motto(motto_id, content)
    return jsonify({'success': ok})


@app.route('/api/mottos/<int:motto_id>', methods=['DELETE'])
@auth.login_required
def delete_motto(motto_id):
    ns = _get_news_storage()
    ok = ns.delete_motto(motto_id)
    return jsonify({'success': ok})


@app.route('/api/mottos/reorder', methods=['POST'])
@auth.login_required
def reorder_mottos():
    data = request.json or {}
    ordered_ids = data.get('ids', [])
    if not ordered_ids:
        return jsonify({'success': False, 'error': 'ids 필요'}), 400
    ns = _get_news_storage()
    ok = ns.reorder_mottos(ordered_ids)
    return jsonify({'success': ok})


# ─── 매매 감시 목록 (trade_watchlist) ────────────────────────────────

@app.route('/api/trade-watchlist', methods=['GET'])
@auth.login_required
def get_trade_watchlist():
    status = request.args.get('status')
    ns = _get_news_storage()
    items = ns.get_trade_watchlist(status=status)
    return jsonify({'success': True, 'data': items})


@app.route('/api/trade-watchlist', methods=['POST'])
@auth.login_required
def add_trade_watchlist():
    data = request.json or {}
    stock_code = normalize_stock_code(data.get('stock_code', ''))
    stock_name = data.get('stock_name', '')
    if not stock_code or not stock_name:
        return jsonify({'success': False, 'error': 'stock_code, stock_name 필요'}), 400
    ns = _get_news_storage()
    wid = ns.add_trade_watchlist(
        stock_code=stock_code,
        stock_name=stock_name,
        buy_price=float(data.get('buy_price', 0)),
        buy_date=data.get('buy_date', ''),
        exit_price=float(data.get('exit_price', 0)),
        exit_date=data.get('exit_date', ''),
        notes=data.get('notes', ''),
    )
    return jsonify({'success': True, 'id': wid})


@app.route('/api/trade-watchlist/<int:wid>', methods=['PUT'])
@auth.login_required
def update_trade_watchlist(wid):
    data = request.json or {}
    ns = _get_news_storage()
    ok = ns.update_trade_watchlist(wid, **data)
    return jsonify({'success': ok})


@app.route('/api/trade-watchlist/<int:wid>', methods=['DELETE'])
@auth.login_required
def delete_trade_watchlist(wid):
    ns = _get_news_storage()
    ok = ns.delete_trade_watchlist(wid)
    return jsonify({'success': ok})


# ─── 재진입 시그널 (reentry_signals) ─────────────────────────────────

@app.route('/api/reentry/signals', methods=['GET'])
@auth.login_required
def get_reentry_signals():
    signal_date = request.args.get('date')
    limit = int(request.args.get('limit', 50))
    ns = _get_news_storage()
    signals = ns.get_reentry_signals(signal_date=signal_date, limit=limit)
    return jsonify({'success': True, 'data': signals})


@app.route('/api/reentry/signals', methods=['POST'])
@auth.login_required
def save_reentry_signal():
    data = request.json or {}
    results = data.get('results', [data])
    ns = _get_news_storage()
    saved_ids = []
    for r in results:
        sid = ns.save_reentry_signal(
            watchlist_id=r.get('watchlist_id', 0),
            stock_code=normalize_stock_code(r.get('stock_code', '')),
            stock_name=r.get('stock_name', ''),
            signal_type=r.get('signal_type', 'C'),
            signal_date=r.get('signal_date', ''),
            entry_price_suggestion=float(r.get('entry_price_suggestion', 0)),
            confidence=r.get('confidence', 'M'),
            reason=r.get('reason', ''),
            ss_matched=bool(r.get('ss_matched', False)),
        )
        saved_ids.append(sid)
    return jsonify({'success': True, 'ids': saved_ids})


# ─── Seeking Signal 재진입 체크 ───────────────────────────────────────

@app.route('/api/seeking-signal/reentry-check', methods=['POST'])
@auth.login_required
def seeking_signal_reentry_check():
    """일봉 데이터 기반 Type A/B/C 재진입 시그널 체크.
    backtest_mode=True 이면 exit_date 이후 전체 구간을 일별 시뮬레이션.
    """
    data = request.json or {}
    stock_code = normalize_stock_code(data.get('stock_code', ''))
    buy_price = float(data.get('buy_price', 0))
    exit_price = float(data.get('exit_price', 0))
    # Mode2 기반 가격 (우선 사용); 없으면 buy_price/exit_price fallback
    buy_target_price = float(data.get('buy_target_price') or buy_price)
    resistance_1_price = float(data.get('resistance_1_price') or exit_price)
    resistance_2_price = float(data.get('resistance_2_price') or 0)
    exit_date = data.get('exit_date', '')   # YYYY-MM-DD
    exit_time = data.get('exit_time', '')   # HH:MM (익절 시간 — 당일 이 시각 이후 봉부터 분석)
    backtest_mode = bool(data.get('backtest_mode', False))

    if not stock_code or not buy_target_price:
        return jsonify({'success': False, 'error': 'stock_code, buy_price 필요'}), 400

    try:
        token = kiwoom_client.token if kiwoom_client else None
        if not token:
            return jsonify({'success': False, 'error': 'Kiwoom API 미연결'}), 503

        import requests as rq
        from datetime import datetime as _dt
        from zoneinfo import ZoneInfo as _ZI

        HOST = os.environ.get('KIWOOM_HOST', 'https://api.kiwoom.com')
        kw_headers = {
            'Content-Type': 'application/json;charset=UTF-8',
            'api-id': 'ka10081',
            'authorization': f'Bearer {token}',
        }
        _today = _dt.now(_ZI('Asia/Seoul')).strftime('%Y%m%d')
        payload = {'stk_cd': stock_code, 'base_dt': _today, 'upd_stkpc_tp': '1'}
        resp = rq.post(HOST.rstrip('/') + '/api/dostk/chart', headers=kw_headers, json=payload, timeout=15)
        chart_resp = resp.json() if resp.ok else {}
        daily_bars_raw = chart_resp.get('stk_dt_pole_chart_qry', [])

        def pp(v):
            return abs(int(str(v).replace('+', '').replace('-', '').replace(',', ''))) if v else 0

        all_bars = []
        for b in daily_bars_raw:
            all_bars.append({
                'date': str(b.get('dt', '')),
                'open': pp(b.get('open_pric')),
                'high': pp(b.get('high_pric')),
                'low': pp(b.get('low_pric')),
                'close': pp(b.get('cur_prc')),
                'volume': int(str(b.get('trde_qty', '0')).replace(',', '')),
            })
        all_bars.sort(key=lambda x: x['date'])

        # exit_date 이후 봉만 분석 대상
        exit_date_compact = exit_date.replace('-', '') if exit_date else ''
        analysis_bars = [b for b in all_bars if b['date'] > exit_date_compact] if exit_date_compact else all_bars

        # ── 익절 당일 선행 체크 (analysis_bars에 포함 안 되므로 별도 처리) ──
        exit_day_signals = []
        if exit_date_compact:
            exit_bar = next((b for b in all_bars if b['date'] == exit_date_compact), None)
            if exit_bar:
                # Type A: 익절 당일 저가가 매수가 존 터치 → 재매수 기회
                # 저가=당일 저점이므로 오전~오후 장중 언제든 가능. 시가 기준으로 시각 추정
                if exit_bar['low'] <= buy_price * 1.03:
                    # 시가보다 저가가 낮으면 오전 하락, 높으면 오후 하락
                    timing = "오전 장중 (시가 하회)" if exit_bar['low'] < exit_bar['open'] else "오후 장중"
                    exit_day_signals.append({
                        'type': 'A',
                        'date': exit_bar['date'],
                        'signal_timing': timing,
                        'desc': f"익절 당일 저가({exit_bar['low']:,}원) → 매수가({int(buy_price):,}원) 존 터치. 재매수 기회",
                        'entry_price': exit_bar['low'],
                        'confidence': 'H',
                        'note': f"타점 시각 추정: {timing}",
                    })
                # Type B: 익절 당일 익절가보다 5%+ 고가 형성 (돌파 확인 진입)
                if exit_price and exit_bar['high'] > exit_price * 1.05:
                    # 고가 = 종가보다 높으면 오전에 찍고 내려온 것, 종가 근처면 오후 마감 강세
                    if exit_bar['high'] > exit_bar['close'] * 1.05:
                        b_timing = "오전 고점 (이후 하락)"
                    else:
                        b_timing = "오후 마감 강세"
                    exit_day_signals.append({
                        'type': 'B',
                        'date': exit_bar['date'],
                        'signal_timing': b_timing,
                        'desc': f"익절 당일 고가({exit_bar['high']:,}원) → 익절가({int(exit_price):,}원) +{(exit_bar['high']/exit_price-1)*100:.0f}% 돌파. 돌파 확인 진입",
                        'entry_price': int(exit_price * 1.01),
                        'confidence': 'M',
                        'note': f"타점 시각 추정: {b_timing} / 기록용",
                    })

        def _detect_overheat(bars):
            """최근 봉 중 폭등일(거래량 5배+, 등락률 10%+) 탐지.
            반환: {'date': '20260420', 'days_ago': 2} or None
            """
            if len(bars) < 2:
                return None
            vol_avg = sum(b['volume'] for b in bars) / len(bars)
            for i in range(len(bars) - 1, -1, -1):
                b = bars[i]
                if b['open'] == 0:
                    continue
                change_pct = (b['close'] - b['open']) / b['open'] * 100
                if b['volume'] >= vol_avg * 5 and change_pct >= 10:
                    days_ago = len(bars) - 1 - i  # 마지막 봉 기준 몇 봉 전인지
                    return {'date': b['date'], 'days_ago': days_ago}
            return None

        def _count_weak_bars(bars_slice):
            """거감봉(거래량 감소 약세봉) 연속 카운트.
            조건 (OR):
            - 음봉(close < open) + 거래량 감소
            - 양봉이어도 거래량이 평균 45% 미만인 힘없는 봉
            → 4/22처럼 미세 양봉이지만 거래량 대폭 감소인 봉도 포함
            """
            if not bars_slice:
                return 0
            vol_avg = sum(b['volume'] for b in bars_slice) / len(bars_slice)
            count = 0
            for b in reversed(bars_slice):
                is_bearish = b['close'] < b['open']
                is_weak_vol = b['volume'] < vol_avg * 0.50
                # 음봉이면서 거래량 감소 OR 양봉이어도 거래량이 매우 적으면
                if (is_bearish and is_weak_vol) or (is_weak_vol and b['volume'] < vol_avg * 0.45):
                    count += 1
                else:
                    break
            return count

        def _find_double_bottom(bars_slice, tolerance=0.04):
            """쌍바닥 탐지: 저점 2개가 tolerance(4%) 이내.
            반환: (저점가격, 첫번째저점날짜, 두번째저점날짜) or None
            """
            lows = [(b['low'], b['date']) for b in bars_slice if b['low'] > 0]
            if len(lows) < 2:
                return None
            min_low = min(lows, key=lambda x: x[0])
            base = min_low[0]
            bottoms = [(v, d) for v, d in lows if v <= base * (1 + tolerance)]
            if len(bottoms) >= 2:
                bottoms_sorted = sorted(bottoms, key=lambda x: x[1])
                return (base, bottoms_sorted[0][1], bottoms_sorted[-1][1])
            return None

        def _scan_signals(bars, window_end_idx, overheat_suppressed=False):
            """bars[0..window_end_idx] 구간에서 시그널 탐색.
            overheat_suppressed=True 면 백테스트 과열기간 — 시그널 생성 안 함.
            """
            if window_end_idx < 2:
                return []
            window = bars[:window_end_idx + 1]
            last = window[-1]
            prev = window[:-1]
            vol_avg = sum(b['volume'] for b in prev) / max(len(prev), 1)

            # 실전: 과열 감지 (시그널은 생성하되 overheat_warning 플래그)
            overheat_info = None
            if not overheat_suppressed:
                overheat_info = _detect_overheat(window)
                # 폭등일이 마지막 봉이면 과열 아직 미진입 — 제외
                if overheat_info and overheat_info['days_ago'] == 0:
                    overheat_info = None

            found = []

            # ── Type A: 원가 복귀 ──────────────────────────────────────────
            if last['close'] and last['close'] <= buy_price * 1.03:
                sig = {
                    'type': 'A',
                    'date': last['date'],
                    'desc': f"종가({last['close']:,}원) ≤ 매수가({int(buy_price):,}원) 존",
                    'entry_price': last['close'],
                    'confidence': 'M',
                }
                if overheat_info and overheat_info['days_ago'] <= 3:
                    sig['overheat_warning'] = True
                    sig['overheat_msg'] = f"⚠️ {overheat_info['date']} 폭등 후 {overheat_info['days_ago']}거래일째 — 단기과열 주의"
                found.append(sig)

            # ── Type C: 거감봉 + 저점 형성 단계 알림 ─────────────────────
            weak_bars = _count_weak_bars(prev[-6:])
            double_bottom = _find_double_bottom(prev[-8:])
            near_buy_zone = any(b['low'] <= buy_price * 1.08 for b in prev[-6:])

            # C1: 거감봉 1봉 이상 + 1차 저점 형성 중 (진행 중 알림)
            if weak_bars >= 1 and near_buy_zone:
                lows_recent = [b['low'] for b in prev[-4:] if b['low'] > 0]
                bottom1 = min(lows_recent) if lows_recent else 0
                sig = {
                    'type': 'C1',
                    'date': last['date'],
                    'desc': f"거감봉 {weak_bars}일 진행 중 — 1차 저점 {bottom1:,}원 형성 (매수가 존 근처). 추가 확인 대기",
                    'entry_price': bottom1,
                    'confidence': 'L',
                    'note': '아직 진입 아님 — 바닥 확인 중',
                }
                if overheat_info and overheat_info['days_ago'] <= 3:
                    sig['overheat_warning'] = True
                    sig['overheat_msg'] = f"⚠️ {overheat_info['date']} 폭등 후 {overheat_info['days_ago']}거래일째 — 단기과열 주의"
                found.append(sig)

            # C2: 쌍바닥 형성 확인 (가격 패턴만 체크 — 거감봉 카운트 불필요)
            if double_bottom:
                bottom_price, d1, d2 = double_bottom
                # 두 저점이 서로 다른 날이어야 진짜 쌍바닥
                if d1 != d2:
                    # 일봉 기준 시그널 확정 시각: 당일 종가 확정 = 15:30
                    sig = {
                        'type': 'C2',
                        'date': last['date'],
                        'signal_timing': '15:30 (당일 종가 확정 후)',
                        'support_price': bottom_price,
                        'desc': f"쌍바닥 [{d1}·{d2}] 저점 {bottom_price:,}원 지지 확인. 타점: {int(bottom_price*1.005):,}원",
                        'entry_price': int(bottom_price * 1.005),
                        'confidence': 'M',
                        'note': f"저점 {bottom_price:,}원 지지선 근처 반등 확인 후 진입",
                    }
                    if overheat_info and overheat_info['days_ago'] <= 3:
                        sig['overheat_warning'] = True
                        sig['overheat_msg'] = f"⚠️ {overheat_info['date']} 폭등 후 {overheat_info['days_ago']}거래일째 — 단기과열 주의"
                    found.append(sig)

            # C3: 거감봉 이후 거래량 증가 양봉 (재상승 시작)
            is_vol_up = last['volume'] > vol_avg * 1.5
            is_bullish = last['close'] >= last['open']
            if weak_bars >= 1 and is_vol_up and is_bullish:
                confidence = 'H' if weak_bars >= 2 and double_bottom else 'M'
                sig = {
                    'type': 'C3',
                    'date': last['date'],
                    'desc': f"거감봉 {weak_bars}일 후 거래량 증가 양봉 (거래량 {last['volume']:,} / 평균 {int(vol_avg):,}, {last['volume']/vol_avg:.1f}배). 재상승 시작",
                    'entry_price': last['open'],
                    'confidence': confidence,
                }
                if overheat_info and overheat_info['days_ago'] <= 3:
                    sig['overheat_warning'] = True
                    sig['overheat_msg'] = f"⚠️ {overheat_info['date']} 폭등 후 {overheat_info['days_ago']}거래일째 — 단기과열 주의"
                found.append(sig)

            # ── Type B: 익절가 5%+ 확실한 돌파 (기록용) ──────────────────
            # 익절가 근처(±5%) 는 지지 형성 구간 — 돌파 아님
            if exit_price and last['close'] > exit_price * 1.05:
                found.append({
                    'type': 'B',
                    'date': last['date'],
                    'signal_timing': '15:30 (당일 종가 확정 후)',
                    'desc': f"익절가({int(exit_price):,}원) +{(last['close']/exit_price-1)*100:.0f}% 돌파 (종가 {last['close']:,}원) — 상승 추세 확인",
                    'entry_price': int(exit_price * 1.01),
                    'confidence': 'M',
                    'note': '기록용 — 돌파 확인 후 재진입',
                })

            return found

        # 단기과열 기준일 산정
        # exit_date가 있으면 익절일 = 폭등일로 직접 사용 (가장 정확)
        # 없으면 all_bars에서 자동 탐지
        def _find_overheat_date(bars):
            if len(bars) < 3:
                return None
            vol_avg = sum(b['volume'] for b in bars) / len(bars)
            # exit_date 이후 봉에서 탐색 (exit_date 자체 포함)
            for b in bars:
                if b['open'] == 0:
                    continue
                change_pct = (b['close'] - b['open']) / b['open'] * 100
                if b['volume'] >= vol_avg * 5 and change_pct >= 10:
                    return b['date']
            return None

        exit_date_compact = exit_date.replace('-', '') if exit_date else ''
        if exit_date_compact:
            # 익절일 봉이 all_bars에 있으면 그게 폭등일
            exit_bar = next((b for b in all_bars if b['date'] == exit_date_compact), None)
            if exit_bar and exit_bar['open'] > 0:
                change_pct = (exit_bar['close'] - exit_bar['open']) / exit_bar['open'] * 100
                if exit_bar['volume'] > 0 and change_pct >= 5:
                    overheat_date = exit_date_compact
                else:
                    overheat_date = _find_overheat_date(all_bars)
            else:
                overheat_date = exit_date_compact  # 봉이 없어도 직접 사용
        else:
            overheat_date = _find_overheat_date(all_bars)

        if backtest_mode:
            # ── 3분봉 기반 발라먹기 백테스트 ──────────────────────────────
            from kiwoom_chart import get_minute_chart
            from style3_signals import scan_style3_signals, calc_c2_support

            # 분석 대상 거래일 목록
            # - exit_time이 있으면: 익절 당일도 포함 (해당 시각 이후 봉만 분석)
            # - 과열기간(3거래일) 이후 5거래일 분석
            all_after_exit = [b['date'] for b in analysis_bars]
            if overheat_date:
                overheat_idx = next((i for i, d in enumerate(all_after_exit) if d > overheat_date), 0)
                start_idx = overheat_idx + 3
                trading_dates = all_after_exit[start_idx:start_idx + 5]
            else:
                trading_dates = all_after_exit[:5]

            # exit_time이 있으면 익절 당일도 분석 대상에 앞에 추가
            exit_date_compact = exit_date.replace('-', '') if exit_date else ''
            # exit_time: "HH:MM" → "HHMM" (4자리)
            exit_time_hhmm = exit_time.replace(':', '') if exit_time else ''
            if exit_date_compact and exit_time_hhmm:
                trading_dates = [exit_date_compact] + trading_dates

            # C2 지지가 — 과열기간 이후 일봉에서 계산
            # 과열기간(3거래일) 봉을 제외해야 실제 재진입 구간의 지지가 나옴
            _c2_base_date = overheat_date if overheat_date else (exit_date_compact or '')
            # 과열 3거래일 이후 봉부터 쌍바닥 탐색
            _c2_after_bars = [b for b in all_bars if b['date'] > _c2_base_date]
            _c2_after_idx = next((i for i, b in enumerate(all_bars) if b['date'] > _c2_base_date), None)
            if _c2_after_idx is not None and _c2_after_idx + 3 <= len(all_bars):
                _c2_start_idx = _c2_after_idx + 3  # 과열 3거래일 제외
                _c2_bars_for_support = all_bars[_c2_start_idx:]
            else:
                _c2_bars_for_support = _c2_after_bars
            from style3_signals import find_double_bottom
            _db = find_double_bottom(_c2_bars_for_support[-8:], tolerance=0.04) if len(_c2_bars_for_support) >= 2 else None
            support_price = int(_db[0] * 1.005) if _db else None

            all_signals = []
            seen_key = set()
            total_bars = 0

            for day_date in trading_dates:
                # 과열기간 체크
                if overheat_date:
                    overheat_all_idx = next((j for j, b in enumerate(all_bars) if b['date'] == overheat_date), None)
                    day_all_idx = next((j for j, b in enumerate(all_bars) if b['date'] == day_date), None)
                    if overheat_all_idx is not None and day_all_idx is not None:
                        days_since = day_all_idx - overheat_all_idx
                        if 1 <= days_since <= 3:
                            key = ('OVERHEAT', day_date)
                            if key not in seen_key:
                                seen_key.add(key)
                                all_signals.append({
                                    'type': 'OVERHEAT',
                                    'date': day_date,
                                    'signal_time': '',
                                    'desc': f"단기과열 기간 ({overheat_date} 폭등 후 {days_since}거래일째) — 시그널 억제",
                                    'confidence': '-',
                                })
                            continue

                # 해당 날짜 3분봉 조회
                # base_dt를 당일로 고정하는 대신 임시로 환경 조작 없이
                # get_minute_chart의 최근 거래일 자동감지 사용 — 단, 과거 날짜는
                # API가 base_dt 파라미터로 해당 날짜 데이터를 반환함
                import requests as _rq
                HOST2 = os.environ.get('KIWOOM_HOST', 'https://api.kiwoom.com')
                _min_headers = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'api-id': 'ka10080',
                    'authorization': f'Bearer {token}',
                }
                _min_payload = {
                    'stk_cd': stock_code,
                    'base_dt': day_date,
                    'tic_scope': '3',
                    'cnt': 80,
                    'upd_stkpc_tp': '1',
                }
                try:
                    _r = _rq.post(HOST2.rstrip('/') + '/api/dostk/chart',
                                  headers=_min_headers, json=_min_payload, timeout=15)
                    _raw = _r.json() if _r.ok else {}
                except Exception:
                    _raw = {}

                raw_bars = _raw.get('stk_min_pole_chart_qry') or []
                # 해당 날짜 봉만 필터 + 시간순
                day_bars = [b for b in raw_bars if isinstance(b, dict) and (b.get('cntr_tm') or '')[:8] == day_date]
                day_bars.sort(key=lambda b: b.get('cntr_tm', ''))
                if not day_bars:
                    continue

                def _parse_min_bar(bar):
                    def _p(keys):
                        for k in keys:
                            v = bar.get(k)
                            if v:
                                try:
                                    return abs(float(str(v).replace(',', '')))
                                except Exception:
                                    pass
                        return 0.0
                    raw_vol = bar.get('trde_qty') or bar.get('volume') or 0
                    try:
                        vol = abs(int(str(raw_vol).replace(',', '')))
                    except Exception:
                        vol = 0
                    cntr = bar.get('cntr_tm', '')
                    hhmm = cntr[8:12] if len(cntr) >= 12 else ''
                    hhmmss = cntr[8:14] if len(cntr) >= 14 else ''
                    return {
                        'time': hhmmss,
                        'hhmm': hhmm,
                        'open': _p(['open_pric', 'open']),
                        'high': _p(['high_pric', 'high']),
                        'low': _p(['low_pric', 'low']),
                        'close': _p(['cur_prc', 'close']),
                        'volume': vol,
                        'date': day_date,
                    }

                minute_bars = [_parse_min_bar(b) for b in day_bars]

                # 익절 당일: exit_time 이후 봉만 분석 (그 이전은 익절 전 구간)
                if day_date == exit_date_compact and exit_time_hhmm:
                    minute_bars = [b for b in minute_bars if b.get('hhmm', '') >= exit_time_hhmm]

                total_bars += len(minute_bars)

                # 봉 단위 롤링 시그널 감지 (최소 3봉 필요)
                # 같은 날 같은 타입은 첫 감지 1개만 (C2는 지지가 다를 수 있어 예외)
                for idx in range(3, len(minute_bars) + 1):
                    window = minute_bars[:idx]
                    raw_sigs = scan_style3_signals(window, buy_target_price, resistance_1_price, resistance_2_price, support_price)
                    for s in raw_sigs:
                        sig_time = s.get('signal_time', '')  # HH:MM
                        sig_type = s['type']
                        # C2는 지지가 기준 dedup, 나머지는 날짜+타입 기준 (첫 감지만)
                        if sig_type == 'C2':
                            key = (sig_type, day_date, int(s.get('support_price', 0) or 0) // 100)
                        else:
                            key = (sig_type, day_date)
                        if key in seen_key:
                            continue
                        seen_key.add(key)
                        all_signals.append({
                            'type': sig_type,
                            'date': day_date,
                            'signal_time': sig_time,
                            'desc': s['reason'],
                            'entry_price': s['entry_price'],
                            'support_price': s.get('support_price', 0),
                            'confidence': s['confidence'],
                            'note': f"3분봉 기준 {day_date} {sig_time} 감지",
                        })

            # 날짜+시간순 정렬
            all_signals.sort(key=lambda x: (x.get('date', ''), x.get('signal_time', '')))

            return jsonify({
                'success': True,
                'mode': 'backtest',
                'data': {
                    'stock_code': stock_code,
                    'buy_price': buy_price,
                    'buy_target_price': buy_target_price,
                    'resistance_1_price': resistance_1_price,
                    'resistance_2_price': resistance_2_price,
                    'exit_price': exit_price,
                    'exit_date': exit_date,
                    'bars_analyzed': total_bars,
                    'trading_days': len(trading_dates),
                    'overheat_date': overheat_date,
                    'support_price': support_price,
                    # exit_time이 있으면 당일 3분봉 분석이 all_signals에 포함됨
                    'signals': ([] if exit_time_hhmm else exit_day_signals) + all_signals,
                    'chart_source': '3분봉',
                }
            })
        else:
            # 실시간 모드 — 3분봉 기반 즉시 시그널 감지
            from kiwoom_chart import get_minute_chart
            from style3_signals import (scan_style3_signals, is_overheat_period,
                                        calc_c2_support)
            from zoneinfo import ZoneInfo as _ZI2

            # 단기과열 체크
            overheat_suppressed = is_overheat_period(exit_date)

            # C2 지지가 — 일봉에서 계산
            support_price = calc_c2_support(all_bars, exit_date)

            # 3분봉 조회 (최근 20봉)
            minute_bars = get_minute_chart(token, stock_code, '3분', count=20)

            signals = []
            last_close = 0
            signal_time_str = ''

            if overheat_suppressed:
                signals = [{
                    'type': 'OVERHEAT',
                    'desc': f'단기과열 기간 ({exit_date} 익절 후 3거래일 이내) — 시그널 억제',
                    'confidence': '-',
                    'signal_time': '',
                }]
            elif minute_bars and len(minute_bars) >= 3:
                raw_sigs = scan_style3_signals(minute_bars, buy_target_price, resistance_1_price, resistance_2_price, support_price)
                last_close = minute_bars[-1].get('close', 0)
                from datetime import date as _date
                today_str = _date.today().strftime('%Y-%m-%d')
                for s in raw_sigs:
                    st = s.get('signal_time', '')
                    signals.append({
                        'type': s['type'],
                        'signal_time': st,
                        'date': today_str,
                        'desc': s['reason'],
                        'entry_price': s['entry_price'],
                        'confidence': s['confidence'],
                        'note': f"3분봉 기준 {today_str} {st} 감지" if st else f"3분봉 기준 {today_str}",
                    })
            else:
                # 분봉 조회 실패 시 일봉 fallback
                recent = analysis_bars[-10:] if len(analysis_bars) >= 10 else analysis_bars
                if recent:
                    last_close = recent[-1]['close']
                fallback_sigs = _scan_signals(recent, len(recent) - 1) if len(recent) >= 3 else []
                for s in fallback_sigs:
                    s['note'] = '(일봉 기준 — 분봉 조회 실패)'
                signals = fallback_sigs

            return jsonify({
                'success': True,
                'mode': 'realtime',
                'data': {
                    'stock_code': stock_code,
                    'buy_price': buy_price,
                    'buy_target_price': buy_target_price,
                    'resistance_1_price': resistance_1_price,
                    'resistance_2_price': resistance_2_price,
                    'exit_price': exit_price,
                    'signals': signals,
                    'last_close': last_close,
                    'support_price': support_price,
                    'overheat_date': overheat_date,
                    'overheat_suppressed': overheat_suppressed,
                    'chart_source': '3분봉' if minute_bars else '일봉(fallback)',
                }
            })
    except Exception as e:
        logger.error(f'reentry-check 실패: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


def start_price_monitor():
    """PriceMonitor를 별도 스레드에서 실행"""
    if not price_monitor:
        logger.warning("PriceMonitor가 초기화되지 않음")
        return

    # 모니터링 활성화
    price_monitor.start()

    def run_monitor():
        """asyncio 이벤트 루프에서 PriceMonitor 실행"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(price_monitor.start_monitoring_task())
            loop.run_forever()
        except Exception as e:
            logger.error(f"PriceMonitor 실행 실패: {e}")
        finally:
            loop.close()

    # 별도 스레드로 실행
    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    logger.info("PriceMonitor 백그라운드 시작 완료")


def main():
    """웹 서버 실행"""
    port = int(os.getenv("WEB_PORT", "5000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")

    # SSL 설정 (HTTPS)
    ssl_context = None
    if os.path.exists('cert.pem') and os.path.exists('key.pem'):
        ssl_context = ('cert.pem', 'key.pem')
        logger.info(f"SSL 인증서 발견 - HTTPS 모드로 시작")

    # PriceMonitor 시작
    start_price_monitor()

    protocol = "https" if ssl_context else "http"
    logger.info(f"웹 서버 시작: {protocol}://{host}:{port}")

    # 운영 환경에서는 debug=False (HTTPS 사용 시)
    debug_mode = False if ssl_context else True
    app.run(host=host, port=port, debug=debug_mode, use_reloader=False, ssl_context=ssl_context)


if __name__ == "__main__":
    main()
