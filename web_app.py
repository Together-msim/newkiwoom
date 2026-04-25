"""
웹 UI 서버
Mode2 전략 관리 웹 인터페이스
"""
import os
import logging
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
from kiwoom_chart import get_daily_chart, format_chart_info
from symbol_resolver import resolve_symbol
from global_config import get_global_config
from price_monitor import PriceMonitor
from tactic_manager import TacticManager
import asyncio
import threading

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

# PriceMonitor 초기화 (웹 서버에서도 모니터링)
price_monitor = None
if kiwoom_client:
    price_monitor = PriceMonitor(
        tactic_manager=tactic_mgr,
        kiwoom_client=kiwoom_client,
        bot_application=None,  # 웹 서버는 텔레그램 없음
        mode1_manager=mode1_mgr,
        mode2_manager=mode2_mgr
    )
    logger.info("PriceMonitor 초기화 완료")
else:
    logger.warning("Kiwoom API 미연결 - PriceMonitor 비활성화")


@app.route('/')
@auth.login_required
def index():
    """메인 페이지"""
    return render_template('index.html')


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

        # 일봉차트 조회
        chart_data = get_daily_chart(token=token, symbol=symbol_code)

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

        # 매수타점 체크 (현재가가 타점 이상이면 매수)
        buy_target = watcher.get('buy_target_price', 0)
        buy_triggered = False
        if buy_target > 0:
            buy_triggered = current_price >= buy_target

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
    """Mode2 감시 리스트 조회"""
    try:
        active_only = request.args.get('active_only', 'false').lower() == 'true'
        watchers = mode2_mgr.get_all_watchers(active_only=active_only)
        return jsonify({
            "success": True,
            "data": watchers
        })
    except Exception as e:
        logger.error(f"감시 리스트 조회 실패: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


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

    # PriceMonitor 시작
    start_price_monitor()

    logger.info(f"웹 서버 시작: http://{host}:{port}")
    app.run(host=host, port=port, debug=True, use_reloader=False)  # reloader 끄기 (중복 실행 방지)


if __name__ == "__main__":
    main()
