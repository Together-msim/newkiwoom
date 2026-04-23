"""
키움 REST API 래퍼 (기존 kiwoom_client 확장)
"""
import sys
from pathlib import Path
import time
import pandas as pd
import requests
from datetime import datetime, timedelta

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from kiwoom_client import KiwoomClient as BaseKiwoomClient
from .config import (
    KIWOOM_APP_KEY, KIWOOM_SECRET_KEY, KIWOOM_BASE_URL,
    DAILY_LOOKBACK_DAYS, MINUTE_3_LOOKBACK, MINUTE_60_LOOKBACK
)
from .cache import get_cache


class SeekingSignalClient:
    """키움 API 클라이언트 (연속조회 + 캐싱 지원)"""

    def __init__(self):
        self.base_client = BaseKiwoomClient()
        self.cache = get_cache()

    def _get_token(self):
        """유효한 토큰 반환"""
        self.base_client._ensure_valid_token()
        return self.base_client.token

    def get_stock_info(self, stock_code: str) -> dict:
        """종목 기본정보 조회 (ka10001)"""
        # 캐시 확인
        cached = self.cache.get(stock_code, 'stock_info')
        if cached:
            return cached

        # API 호출
        result = self.base_client.get_stock_info(stock_code)

        # 캐싱 (하루만 유효)
        self.cache.set(stock_code, 'stock_info', result)
        return result

    def get_daily_chart(self, stock_code: str, base_dt: str = None,
                       min_days: int = DAILY_LOOKBACK_DAYS) -> pd.DataFrame:
        """
        일봉 차트 조회 (ka10081) with 연속조회

        Args:
            stock_code: 종목코드
            base_dt: 기준일자 YYYYMMDD (None이면 오늘)
            min_days: 최소 조회 일수

        Returns:
            DataFrame with columns: dt, open_pric, high_pric, low_pric,
                                   cur_prc, trde_qty, trde_prica
        """
        if base_dt is None:
            base_dt = datetime.now().strftime('%Y%m%d')

        # 캐시 확인
        cache_key = f"{stock_code}_{base_dt}_{min_days}"
        cached = self.cache.get(stock_code, 'daily_chart', base_dt=base_dt, min_days=min_days)
        if cached is not None:
            return cached

        # API 호출 (연속조회)
        all_data = []
        next_key = ''
        cont_yn = 'N'
        max_iterations = 10  # 안전장치

        for iteration in range(max_iterations):
            try:
                headers = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'authorization': f'Bearer {self._get_token()}',
                    'cont-yn': cont_yn,
                    'next-key': next_key,
                    'api-id': 'ka10081',
                }

                body = {
                    'stk_cd': stock_code,
                    'base_dt': base_dt,
                    'upd_stkpc_tp': '1'  # 수정주가
                }

                response = requests.post(
                    f"{KIWOOM_BASE_URL}/api/dostk/chart",
                    json=body,
                    headers=headers,
                    timeout=30
                )

                if response.status_code != 200:
                    error_msg = f"API Error: {response.status_code} - {response.text[:200]}"
                    print(error_msg)
                    raise Exception(error_msg)

                result = response.json()
                return_code = result.get('return_code')
                return_msg = result.get('return_msg', '')
                print(f"API 응답 (iteration {iteration}): return_code={return_code}, return_msg={return_msg}")

                records = result.get('stk_dt_pole_chart_qry', [])
                print(f"일봉 조회 성공: {len(records)}개 레코드 (iteration {iteration})")

                if not records:
                    break

                all_data.extend(records)

                # 연속조회 체크 (헤더 키는 소문자로 정규화됨)
                cont_yn = response.headers.get('cont-yn', response.headers.get('Cont-Yn', 'N'))
                next_key = response.headers.get('next-key', response.headers.get('Next-Key', ''))

                if cont_yn != 'Y' or not next_key:
                    break

                # 충분한 데이터 확보 시 종료
                if len(all_data) >= min_days:
                    break

                time.sleep(0.25)  # Rate limit 방어

            except Exception as e:
                print(f"일봉 조회 실패 (iteration {iteration}): {e}")
                import traceback
                traceback.print_exc()
                break

        if not all_data:
            print(f"일봉 데이터 없음: {stock_code}")
            return pd.DataFrame()

        # DataFrame 변환
        df = pd.DataFrame(all_data)

        # 데이터 정제
        df['dt'] = pd.to_datetime(df['dt'], format='%Y%m%d', errors='coerce')

        numeric_cols = ['open_pric', 'high_pric', 'low_pric', 'cur_prc', 'trde_qty', 'trde_prica']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').abs()

        # 정렬 및 인덱스 리셋
        df = df.sort_values('dt').reset_index(drop=True)

        # 캐싱
        self.cache.set(stock_code, 'daily_chart', df, base_dt=base_dt, min_days=min_days)

        return df

    def get_minute_chart(self, stock_code: str, tic_scope: int,
                        min_bars: int = 120) -> pd.DataFrame:
        """
        분봉 차트 조회 (ka10080)

        Args:
            stock_code: 종목코드
            tic_scope: 분봉 간격 (3 or 60)
            min_bars: 최소 조회 봉 개수

        Returns:
            DataFrame with columns: cntr_tm, open_pric, high_pric, low_pric,
                                   cur_prc, trde_qty
        """
        # 캐시 확인 (분봉은 짧은 TTL)
        cached = self.cache.get(stock_code, f'minute_{tic_scope}', min_bars=min_bars)
        if cached is not None:
            return cached

        # API 호출
        all_data = []
        next_key = ''
        cont_yn = 'N'
        max_iterations = 5

        for iteration in range(max_iterations):
            try:
                headers = {
                    'Content-Type': 'application/json;charset=UTF-8',
                    'authorization': f'Bearer {self._get_token()}',
                    'cont-yn': cont_yn,
                    'next-key': next_key,
                    'api-id': 'ka10080',
                }

                body = {
                    'stk_cd': stock_code,
                    'tic_scope': str(tic_scope),
                    'upd_stkpc_tp': '1'
                }

                response = requests.post(
                    f"{KIWOOM_BASE_URL}/api/dostk/chart",
                    json=body,
                    headers=headers,
                    timeout=30
                )

                if response.status_code != 200:
                    raise Exception(f"API Error: {response.status_code}")

                result = response.json()
                records = result.get('stk_min_pole_chart_qry', [])

                if not records:
                    break

                all_data.extend(records)

                # 연속조회 체크 (헤더 키는 소문자로 정규화됨)
                cont_yn = response.headers.get('cont-yn', response.headers.get('Cont-Yn', 'N'))
                next_key = response.headers.get('next-key', response.headers.get('Next-Key', ''))

                if cont_yn != 'Y' or not next_key:
                    break

                if len(all_data) >= min_bars:
                    break

                time.sleep(0.25)

            except Exception as e:
                print(f"분봉 조회 실패 (iteration {iteration}): {e}")
                break

        if not all_data:
            return pd.DataFrame()

        # DataFrame 변환
        df = pd.DataFrame(all_data)

        # 데이터 정제
        df['cntr_tm'] = pd.to_datetime(df['cntr_tm'], format='%Y%m%d%H%M%S', errors='coerce')

        numeric_cols = ['open_pric', 'high_pric', 'low_pric', 'cur_prc', 'trde_qty']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').abs()

        # 정렬
        df = df.sort_values('cntr_tm').reset_index(drop=True)

        # 캐싱 (하루만 유효)
        self.cache.set(stock_code, f'minute_{tic_scope}', df, min_bars=min_bars)

        return df
