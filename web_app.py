"""
웹 UI 서버
Mode2 전략 관리 웹 인터페이스
"""
import os
import logging
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv

from mode1_manager import Mode1Manager
from mode2_manager import Mode2Manager
from utils.code import normalize_stock_code
from kiwoom_client import KiwoomClient
from kiwoom_token import get_token
from kiwoom_chart import get_daily_chart, format_chart_info
from symbol_resolver import resolve_symbol

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Manager 초기화
mode1_mgr = Mode1Manager()
mode2_mgr = Mode2Manager()

# Kiwoom Client 초기화
try:
    kiwoom_client = KiwoomClient()
    logger.info("Kiwoom API 연결 완료")
except Exception as e:
    logger.warning(f"Kiwoom API 연결 실패: {e}")
    kiwoom_client = None


@app.route('/')
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

        # 포맷팅된 메시지 생성
        formatted_msg = format_chart_info(chart_data, current_price)

        return jsonify({
            "success": True,
            "data": {
                "code": symbol_code,
                "name": symbol_name,
                "chart": chart_data,
                "current_price": current_price,
                "formatted_message": formatted_msg
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

        # 주문 실행
        result = kiwoom_client.place_buy_order(
            symbol=code,
            quantity=quantity,
            price=price,
            order_type=order_type
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

        if not code:
            return jsonify({
                "success": False,
                "error": "종목코드가 필요합니다"
            }), 400

        # 종목코드 정규화
        code = normalize_stock_code(code)

        # 주문 실행
        result = kiwoom_client.place_sell_order(
            symbol=code,
            quantity=quantity,
            price=price,
            order_type=order_type
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


def main():
    """웹 서버 실행"""
    port = int(os.getenv("WEB_PORT", "5000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")

    logger.info(f"웹 서버 시작: http://{host}:{port}")
    app.run(host=host, port=port, debug=True)


if __name__ == "__main__":
    main()
