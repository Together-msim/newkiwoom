"""
키움 API 비동기 클라이언트
기존 KiwoomClient의 비동기 버전
"""
import os
import time
import aiohttp
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from kiwoom_token import get_token
from utils.code import normalize_stock_code

logger = logging.getLogger(__name__)


class KiwoomClientAsync:
    """
    키움 API 비동기 클라이언트
    - 토큰 자동 갱신 (25분마다)
    - 비동기 현재가 조회 (aiohttp 사용)
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

        # 토큰 갱신 간격 (25분)
        self._token_refresh_seconds = 25 * 60

        # Rate limiting
        self._call_history = []
        self._max_calls_per_second = 5

    def _ensure_valid_token(self):
        """토큰 갱신 체크 (동기)"""
        now = time.time()
        if (now - self._token_issued_at) >= self._token_refresh_seconds:
            try:
                self.token = get_token()
                self._token_issued_at = now
                logger.info("토큰 갱신 완료")
            except Exception as e:
                logger.warning(f"토큰 갱신 실패: {e}")

    def _headers(self) -> Dict[str, str]:
        """요청 헤더 생성"""
        self._ensure_valid_token()
        return {
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": f"Bearer {self.token}",
        }

    async def _check_rate_limit(self):
        """Rate limit 체크 (비동기)"""
        import asyncio

        now = time.time()

        # 1초 이내 호출 기록 필터링
        self._call_history = [t for t in self._call_history if now - t < 1.0]

        if len(self._call_history) >= self._max_calls_per_second:
            # 초당 제한 초과, sleep
            sleep_time = 1.0 - (now - self._call_history[0])
            if sleep_time > 0:
                logger.debug(f"Rate limit 도달, {sleep_time:.2f}초 대기")
                await asyncio.sleep(sleep_time)

        self._call_history.append(time.time())

    async def get_last_price(self, symbol: str) -> float:
        """
        현재가 조회 (비동기)

        Args:
            symbol: 종목코드

        Returns:
            float: 현재가
        """
        symbol = normalize_stock_code(symbol)

        # 테스트 모드
        test_price = os.getenv("TEST_LAST_PRICE")
        if test_price:
            try:
                return float(test_price)
            except (ValueError, TypeError):
                pass

        # Rate limit 체크
        await self._check_rate_limit()

        # ka10003 API 사용
        try:
            url = f"{self.host}/api/dostk/stkinfo"
            headers = self._headers()
            headers["api-id"] = "ka10003"

            body = {"stk_cd": symbol}

            # 비동기 HTTP 요청
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        text = await resp.text()
                        raise ValueError(f"API 호출 실패: HTTP {resp.status} - {text[:200]}")

                    data = await resp.json()

            # 에러 응답 체크
            if data.get("return_code") != 0:
                error_msg = data.get("return_msg", "알 수 없는 오류")
                raise ValueError(f"API 오류: {error_msg}")

            # 체결 리스트에서 최근 체결가 추출
            contracts = data.get("cntr_infr", []) or []
            if not contracts:
                raise ValueError("체결 리스트가 비어있습니다")

            # 가장 최근 체결
            contracts.sort(key=lambda x: x.get("tm", ""), reverse=True)
            latest_contract = contracts[0]

            # 체결가 추출
            cur_prc = latest_contract.get("cur_prc", "")
            if not cur_prc:
                raise ValueError("체결가 정보가 없습니다")

            price_str = cur_prc.lstrip("+-")
            return float(price_str)

        except Exception as e:
            logger.error(f"현재가 조회 실패 ({symbol}): {e}")
            raise ValueError(f"현재가 조회 실패: {str(e)}")

    async def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        종목 정보 조회 (비동기)

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

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    headers=headers,
                    json=body,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        raise ValueError(f"API 호출 실패: HTTP {resp.status}")

                    data = await resp.json()

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
