"""
키움 API 클라이언트
기존 kiwoom-min 프로젝트에서 검증된 방식 기반으로 단타 전략에 필요한 기능만 구현
"""
import os
import time
import requests
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from kiwoom_token import get_token
from utils.code import normalize_stock_code

logger = logging.getLogger(__name__)


class KiwoomClient:
    """
    키움 API 클라이언트
    - 토큰 자동 갱신 (25분마다)
    - 현재가 조회
    - 일일 가격 정보 조회 (시가, 전일종가 등)
    """

    def __init__(self, host: Optional[str] = None, token: Optional[str] = None):
        self.host = (host or os.getenv("KIWOOM_HOST") or "").rstrip("/")

        if not self.host:
            raise ValueError("KIWOOM_HOST is required")

        # 토큰 초기화
        if token:
            self.token = token
            self._token_issued_at = time.time()
        else:
            self.token = get_token()
            self._token_issued_at = time.time()

        # 토큰 갱신 간격 (25분, 키움 토큰 TTL에 맞춤)
        self._token_refresh_seconds = 25 * 60

    def _ensure_valid_token(self):
        """토큰이 만료되었거나 곧 만료될 경우 갱신합니다."""
        now = time.time()
        if (now - self._token_issued_at) >= self._token_refresh_seconds:
            try:
                self.token = get_token()
                self._token_issued_at = now
            except Exception:
                # 토큰 갱신 실패해도 기존 토큰으로 시도
                pass

    def _headers(self) -> Dict[str, str]:
        """요청 헤더를 생성합니다. 필요시 토큰을 자동 갱신합니다."""
        self._ensure_valid_token()
        return {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {self.token}",
        }

    def get_last_price(self, symbol: str) -> float:
        """
        현재가 조회 (ka10003 API 사용)

        Args:
            symbol: 종목코드 (예: "005930", "081180")

        Returns:
            float: 현재가

        Raises:
            ValueError: API 호출 실패 시
        """
        # 종목코드 정규화
        symbol = normalize_stock_code(symbol)

        # 테스트 모드: 환경 변수로 고정 가격 반환
        test_price = os.getenv("TEST_LAST_PRICE")
        if test_price:
            try:
                return float(test_price)
            except (ValueError, TypeError):
                pass

        # ka10003 API 사용
        try:
            url = f"{self.host}/api/dostk/stkinfo"
            headers = self._headers()
            headers["api-id"] = "ka10003"

            body = {"stk_cd": symbol}
            r = requests.post(url, headers=headers, json=body, timeout=10)

            if r.status_code != 200:
                raise ValueError(f"API 호출 실패: HTTP {r.status_code} - {r.text[:200]}")

            data = r.json()

            # 에러 응답 체크
            if data.get("return_code") != 0:
                error_msg = data.get("return_msg", "알 수 없는 오류")
                raise ValueError(f"API 오류: {error_msg}")

            # 체결 리스트에서 최근 체결가 추출
            contracts = data.get("cntr_infr", []) or []
            if not contracts:
                raise ValueError("체결 리스트가 비어있습니다")

            # 가장 최근 체결 찾기
            contracts.sort(key=lambda x: x.get("tm", ""), reverse=True)
            latest_contract = contracts[0]

            # 체결가 추출 (cur_prc: "-16120" 형식)
            cur_prc = latest_contract.get("cur_prc", "")
            if not cur_prc:
                raise ValueError("체결가 정보가 없습니다")

            # "+/-" 부호 제거 후 숫자만 추출
            price_str = cur_prc.lstrip("+-")
            # 종목명도 함께 추출 (있으면)
            stock_name = data.get("stk_nm", "")

            return float(price_str)

        except Exception as e:
            raise ValueError(f"현재가 조회 실패: {str(e)}")

    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        종목 정보 조회 (종목명 포함)

        Args:
            symbol: 종목코드

        Returns:
            {
                "code": str,
                "name": str,
                "current_price": float
            }
        """
        symbol = normalize_stock_code(symbol)

        # 테스트 모드
        test_price = os.getenv("TEST_LAST_PRICE")
        if test_price:
            try:
                return {
                    "code": symbol,
                    "name": f"테스트종목{symbol}",
                    "current_price": float(test_price)
                }
            except (ValueError, TypeError):
                pass

        try:
            url = f"{self.host}/api/dostk/stkinfo"
            headers = self._headers()
            headers["api-id"] = "ka10003"

            body = {"stk_cd": symbol}
            r = requests.post(url, headers=headers, json=body, timeout=10)

            if r.status_code != 200:
                raise ValueError(f"API 호출 실패: HTTP {r.status_code}")

            data = r.json()

            if data.get("return_code") != 0:
                error_msg = data.get("return_msg", "알 수 없는 오류")
                raise ValueError(f"API 오류: {error_msg}")

            # 종목명 추출
            stock_name = data.get("stk_nm", "").strip()

            # 현재가 추출
            contracts = data.get("cntr_infr", []) or []
            current_price = 0.0
            if contracts:
                contracts.sort(key=lambda x: x.get("tm", ""), reverse=True)
                cur_prc = contracts[0].get("cur_prc", "").lstrip("+-")
                current_price = float(cur_prc) if cur_prc else 0.0

            return {
                "code": symbol,
                "name": stock_name,
                "current_price": current_price
            }

        except Exception as e:
            logger.error(f"종목 정보 조회 실패: {e}")
            return {
                "code": symbol,
                "name": "",
                "current_price": 0.0
            }

    def get_daily_price_info(self, symbol: str) -> Dict[str, Any]:
        """
        일일 가격 정보 조회 (당일 시가, 전일 종가 등)

        Args:
            symbol: 종목코드

        Returns:
            {
                "open": float,       # 당일 시가
                "high": float,       # 당일 고가
                "low": float,        # 당일 저가
                "close": float,      # 현재가
                "prev_close": float, # 전일 종가
            }

        Raises:
            ValueError: API 호출 실패 시
        """
        # 종목코드 정규화
        symbol = normalize_stock_code(symbol)

        # 테스트 모드
        test_price = os.getenv("TEST_LAST_PRICE")
        if test_price:
            try:
                base_price = float(test_price)
                return {
                    "open": base_price,
                    "high": base_price * 1.02,
                    "low": base_price * 0.98,
                    "close": base_price,
                    "prev_close": base_price * 0.93,  # 7% 하락 가정
                }
            except (ValueError, TypeError):
                pass

        # TODO: 실제 API 구현 (ka10004 등 활용)
        # 현재는 간단히 현재가만 반환
        try:
            current_price = self.get_last_price(symbol)
            return {
                "open": current_price,
                "high": current_price,
                "low": current_price,
                "close": current_price,
                "prev_close": current_price,
            }
        except Exception as e:
            raise ValueError(f"일일 가격 정보 조회 실패: {str(e)}")

    def check_gap_up_stocks(self, codes: list[str], threshold: float = 7.0) -> list[str]:
        """
        시가 갭상승 종목 필터링

        Args:
            codes: 종목코드 리스트
            threshold: 상승률 임계값 (기본 7%)

        Returns:
            list[str]: 임계값 이상 상승한 종목코드 리스트
        """
        gap_up_stocks = []

        for code in codes:
            try:
                info = self.get_daily_price_info(code)
                open_price = info["open"]
                prev_close = info["prev_close"]

                # 상승률 계산
                if prev_close > 0:
                    gap_ratio = ((open_price - prev_close) / prev_close) * 100
                    if gap_ratio >= threshold:
                        gap_up_stocks.append(code)

            except Exception as e:
                # 개별 종목 조회 실패는 무시
                continue

        return gap_up_stocks

    def get_positions(self):
        """
        보유종목을 조회합니다 (ka01690 API 사용)

        Returns:
            (summary, rows) 튜플
            - summary: 계좌 요약 정보 (dict)
            - rows: 보유종목 리스트 (day_bal_rt)
              - stk_cd: 종목코드
              - stk_nm: 종목명
              - rmnd_qty: 잔고수량
              - buy_uv: 매입단가
              - evltv_prft: 평가손익
              - prft_rt: 수익률
        """
        self._ensure_valid_token()

        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")

        url = f"{self.host}/api/dostk/acnt"
        body = {"qry_dt": today}

        all_rows = []
        cont_yn = None
        next_key = None

        while True:
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "api-id": "ka01690",  # 보유종목 조회
                "authorization": f"Bearer {self.token}",
            }

            if cont_yn:
                headers["cont-yn"] = cont_yn
            if next_key:
                headers["next-key"] = next_key

            try:
                resp = requests.post(url, headers=headers, json=body, timeout=10)
                resp.raise_for_status()

                data = resp.json()
                h = resp.headers

                # 보유종목 리스트: day_bal_rt
                rows = data.get("day_bal_rt", []) or []
                all_rows.extend(rows)

                cont_yn = h.get("cont-yn")
                next_key = h.get("next-key")

                if cont_yn != "Y":
                    # 마지막 페이지
                    return data, all_rows

            except Exception as e:
                logger.error(f"보유종목 조회 실패: {e}")
                return {}, []

    def _get_dmst_stex_tp(self) -> str:
        """
        현재 시간에 따라 거래소 구분을 반환합니다.
        - 오전 8시~8시50분: "NXT" (장전 시간외 거래)
        - 기본값: "KRX" (한국거래소)
        """
        from zoneinfo import ZoneInfo
        from datetime import time as dt_time
        kst = ZoneInfo("Asia/Seoul")
        now = datetime.now(kst)
        current_time = now.time()

        # 오전 8시~8시50분: 장전 시간외 거래
        if dt_time(8, 0) <= current_time < dt_time(8, 50):
            return "NXT"
        # 기본값: KRX
        else:
            return "KRX"

    def _get_holding_qty(self, symbol: str) -> Optional[int]:
        """
        kt00018 API를 사용하여 특정 종목의 보유수량을 조회합니다.

        Args:
            symbol: 종목코드 (예: "081180")

        Returns:
            보유수량(int) 또는 None (보유하지 않은 경우)
        """
        symbol = normalize_stock_code(symbol)

        try:
            url = f"{self.host}/api/dostk/acnt"
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "api-id": "kt00018",  # 계좌평가잔고내역요청
                "authorization": f"Bearer {self.token}",
            }

            dmst_stex_tp = self._get_dmst_stex_tp()
            body = {
                "qry_tp": "2",  # 개별 조회
                "dmst_stex_tp": dmst_stex_tp,
            }

            resp = requests.post(url, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            # kt00018 응답: acnt_evlt_remn_indv_tot 리스트에서 보유수량 조회
            rows = data.get("acnt_evlt_remn_indv_tot", []) or []

            symbol_normalized = symbol
            for row in rows:
                stk_cd = row.get("stk_cd", "")
                stk_cd_normalized = normalize_stock_code(str(stk_cd))

                if stk_cd_normalized == symbol_normalized:
                    rmnd_qty = row.get("rmnd_qty", 0)
                    try:
                        qty = int(rmnd_qty) if rmnd_qty else 0
                        if qty > 0:
                            logger.debug(f"보유수량 조회: {symbol} → {qty}주")
                            return qty
                    except (ValueError, TypeError):
                        continue

            # 보유하지 않은 경우
            return None

        except Exception as e:
            logger.error(f"보유수량 조회 실패: {e}")
            return None

    def place_buy_order(
        self,
        symbol: str,
        quantity: int,
        price: int = 0,
        order_type: str = "market",
        simulation_mode: bool = None
    ) -> Dict[str, Any]:
        """
        매수 주문 (kt10000 API 사용)

        Args:
            symbol: 종목코드
            quantity: 매수 수량
            price: 지정가 (order_type="limit"일 때)
            order_type: "market" (시장가) 또는 "limit" (지정가)
            simulation_mode: True=시뮬레이션, False=실제주문, None=환경변수 사용

        Returns:
            {
                "success": bool,
                "order_no": str,  # 주문번호
                "message": str
            }
        """
        symbol = normalize_stock_code(symbol)
        self._ensure_valid_token()

        try:
            # 시뮬레이션 모드 체크 (파라미터가 우선, 없으면 환경변수 사용)
            is_simulation = simulation_mode if simulation_mode is not None else (os.getenv("ORDER_SIMULATION_MODE") == "1")

            if is_simulation:
                logger.info(f"[시뮬레이션] 매수 주문: {symbol} | {quantity}주 | {order_type} | {price if price > 0 else '시장가'}")
                return {
                    "success": True,
                    "order_no": f"SIM{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "message": f"매수 주문 완료 (시뮬레이션)"
                }

            # 거래소 구분
            dmst_stex_tp = self._get_dmst_stex_tp()

            # 매매구분
            if order_type.lower() == "market":
                trde_tp = "3"  # 시장가
                ord_uv = None
            elif order_type.lower() == "limit":
                trde_tp = "0"  # 보통(지정가)
                if not price or price <= 0:
                    return {
                        "success": False,
                        "order_no": None,
                        "message": "지정가 주문일 때 price가 필요합니다"
                    }
                ord_uv = str(int(price))
            else:
                return {
                    "success": False,
                    "order_no": None,
                    "message": f"지원하지 않는 주문 타입: {order_type}"
                }

            # 요청 body 구성
            body = {
                "dmst_stex_tp": dmst_stex_tp,
                "stk_cd": symbol,
                "ord_qty": str(quantity),
                "trde_tp": trde_tp,
            }

            if ord_uv is not None:
                body["ord_uv"] = ord_uv

            # API 호출
            url = f"{self.host}/api/dostk/ordr"
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "api-id": "kt10000",  # 매수
                "authorization": f"Bearer {self.token}",
            }

            logger.info(f"매수 주문: {symbol} | {quantity}주 | {order_type} | {price if price > 0 else '시장가'}")

            resp = requests.post(url, headers=headers, json=body, timeout=15)
            resp.raise_for_status()

            data = resp.json()

            # 응답 처리
            return_code = data.get("return_code", -1)
            return_msg = data.get("return_msg", "")
            order_no = data.get("ord_no") or data.get("order_no") or data.get("ordr_no")

            if return_code == 0 or order_no:
                logger.info(f"매수 주문 성공: {symbol} | 주문번호: {order_no}")
                return {
                    "success": True,
                    "order_no": str(order_no) if order_no else None,
                    "message": return_msg or "주문 접수 완료"
                }
            else:
                logger.error(f"매수 주문 실패: {return_msg} (code={return_code})")
                return {
                    "success": False,
                    "order_no": None,
                    "message": return_msg or f"주문 실패 (code={return_code})"
                }

        except Exception as e:
            logger.error(f"매수 주문 실패: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "order_no": None,
                "message": str(e)
            }

    def place_sell_order(
        self,
        symbol: str,
        quantity: int = None,
        price: int = 0,
        order_type: str = "market",
        simulation_mode: bool = None
    ) -> Dict[str, Any]:
        """
        매도 주문 (kt10001 API 사용)

        Args:
            symbol: 종목코드
            quantity: 매도 수량 (None이면 보유수량 전량 매도)
            price: 지정가 (order_type="limit"일 때)
            order_type: "market" (시장가) 또는 "limit" (지정가)
            simulation_mode: True=시뮬레이션, False=실제주문, None=환경변수 사용

        Returns:
            {
                "success": bool,
                "order_no": str,  # 주문번호
                "message": str
            }
        """
        symbol = normalize_stock_code(symbol)
        self._ensure_valid_token()

        try:
            # 시뮬레이션 모드 체크 (파라미터가 우선, 없으면 환경변수 사용)
            is_simulation = simulation_mode if simulation_mode is not None else (os.getenv("ORDER_SIMULATION_MODE") == "1")

            if is_simulation:
                qty_text = f"{quantity}주" if quantity else "전량"
                logger.info(f"[시뮬레이션] 매도 주문: {symbol} | {qty_text} | {order_type} | {price if price > 0 else '시장가'}")
                return {
                    "success": True,
                    "order_no": f"SIM{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    "message": f"매도 주문 완료 (시뮬레이션)"
                }

            # 수량이 없으면 보유수량 조회
            if quantity is None or quantity <= 0:
                quantity = self._get_holding_qty(symbol)
                if quantity is None or quantity <= 0:
                    return {
                        "success": False,
                        "order_no": None,
                        "message": f"{symbol} 종목을 보유하고 있지 않습니다"
                    }

            # 거래소 구분
            dmst_stex_tp = self._get_dmst_stex_tp()

            # 매매구분
            if order_type.lower() == "market":
                trde_tp = "3"  # 시장가
                ord_uv = None
            elif order_type.lower() == "limit":
                trde_tp = "0"  # 보통(지정가)
                if not price or price <= 0:
                    return {
                        "success": False,
                        "order_no": None,
                        "message": "지정가 주문일 때 price가 필요합니다"
                    }
                ord_uv = str(int(price))
            else:
                return {
                    "success": False,
                    "order_no": None,
                    "message": f"지원하지 않는 주문 타입: {order_type}"
                }

            # 요청 body 구성
            body = {
                "dmst_stex_tp": dmst_stex_tp,
                "stk_cd": symbol,
                "ord_qty": str(quantity),
                "trde_tp": trde_tp,
            }

            if ord_uv is not None:
                body["ord_uv"] = ord_uv

            # API 호출
            url = f"{self.host}/api/dostk/ordr"
            headers = {
                "Content-Type": "application/json;charset=UTF-8",
                "api-id": "kt10001",  # 매도
                "authorization": f"Bearer {self.token}",
            }

            logger.info(f"매도 주문: {symbol} | {quantity}주 | {order_type} | {price if price > 0 else '시장가'}")

            resp = requests.post(url, headers=headers, json=body, timeout=15)
            resp.raise_for_status()

            data = resp.json()

            # 응답 처리
            return_code = data.get("return_code", -1)
            return_msg = data.get("return_msg", "")
            order_no = data.get("ord_no") or data.get("order_no") or data.get("ordr_no")

            if return_code == 0 or order_no:
                logger.info(f"매도 주문 성공: {symbol} | 주문번호: {order_no}")
                return {
                    "success": True,
                    "order_no": str(order_no) if order_no else None,
                    "message": return_msg or "주문 접수 완료"
                }
            else:
                logger.error(f"매도 주문 실패: {return_msg} (code={return_code})")
                return {
                    "success": False,
                    "order_no": None,
                    "message": return_msg or f"주문 실패 (code={return_code})"
                }

        except Exception as e:
            logger.error(f"매도 주문 실패: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "order_no": None,
                "message": str(e)
            }
