#!/usr/bin/env python3
"""
일봉차트 조회 모듈
키움증권 REST API를 사용하여 일봉차트 정보를 조회합니다.
"""
import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from utils.code import normalize_stock_code

load_dotenv()

HOST = os.getenv("KIWOOM_HOST")


def get_daily_chart(
    token: str,
    symbol: str,
    error_out: Optional[list] = None,
) -> Optional[Dict[str, Any]]:
    """
    일봉차트 정보 조회 (ka10081 API 사용)

    Args:
        token: 키움 API 토큰
        symbol: 종목코드 (예: "081180")
        error_out: 실패 시 사유를 append할 리스트 (선택)

    Returns:
        {
            "date": "20240101",           # 기준일자(가장 최근 봉의 dt)
            "today_open": 50000,          # 당일 시가
            "today_high": 52000,          # 당일 고가
            "today_low": 49000,           # 당일 저가
            "today_current": 51000,       # 당일 종가(=일봉 cur_prc)
            "yesterday_close": 50000,     # 전일 종가
            "yesterday_high": 51000,      # 전일 고가
            "yesterday_low": 49000,       # 전일 저가
        } 또는 None (실패 시)

    Notes:
        - 키움 REST API 문서 기준: POST /api/dostk/chart, api-id=ka10081
        - 응답의 `stk_dt_pole_chart_qry` 리스트에서 [0]=당일(가장 최근), [1]=전일로 간주
    """
    # 종목코드 정규화
    symbol = normalize_stock_code(symbol)
    
    if not HOST:
        msg = "KIWOOM_HOST 환경 변수가 설정되어 있지 않습니다."
        print(f"❌ {msg}")
        if error_out is not None:
            error_out.append(msg)
        return None

    base_dt = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")

    url = HOST.rstrip("/") + "/api/dostk/chart"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "api-id": "ka10081",
        "authorization": f"Bearer {token}",
    }
    payload = {
        "stk_cd": symbol,
        "base_dt": base_dt,
        "upd_stkpc_tp": "1",  # 수정주가 적용(문서 예시 기준)
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

        # 차트 리스트는 보통 최상위에 오지만, 혹시 모를 중첩도 방어
        chart_list = None
        if isinstance(data, dict):
            if isinstance(data.get("stk_dt_pole_chart_qry"), list):
                chart_list = data.get("stk_dt_pole_chart_qry")
            elif isinstance(data.get("output"), dict) and isinstance(data["output"].get("stk_dt_pole_chart_qry"), list):
                chart_list = data["output"].get("stk_dt_pole_chart_qry")

        if not chart_list or not isinstance(chart_list, list) or len(chart_list) == 0:
            # 일부 에러는 200으로 내려오기도 하므로 message/code를 출력
            msg = None
            if isinstance(data, dict):
                rc = data.get("return_code")
                msg = data.get("return_msg") or data.get("message") or data.get("msg")
                if rc is not None and rc != 0:
                    msg = f"return_code={rc} {msg or ''}".strip()
            err = f"일봉 데이터 없음 (message={msg})" if msg else "일봉 데이터 없음"
            print(f"❌ 일봉차트 조회 실패: {err}")
            if error_out is not None:
                error_out.append(err)
            return None

        today_bar = chart_list[0] if len(chart_list) >= 1 else {}
        yday_bar = chart_list[1] if len(chart_list) >= 2 else {}

        def _p(bar: Dict[str, Any], keys: list, default: Optional[float] = None) -> Optional[float]:
            val = _extract_price(bar, keys)
            return val if val is not None else default

        today_open = _p(today_bar, ["open_pric", "open", "today_open"]) or 0.0
        today_high = _p(today_bar, ["high_pric", "high", "today_high"], today_open) or 0.0
        today_low = _p(today_bar, ["low_pric", "low", "today_low"], today_open) or 0.0
        today_cur = _p(today_bar, ["cur_prc", "close", "today_current"], today_open) or 0.0

        yday_open = _p(yday_bar, ["open_pric", "open", "yesterday_open"], today_cur) or 0.0
        yday_close = _p(yday_bar, ["cur_prc", "close", "yesterday_close"], today_cur) or 0.0
        yday_high = _p(yday_bar, ["high_pric", "high", "yesterday_high"], yday_close) or 0.0
        yday_low = _p(yday_bar, ["low_pric", "low", "yesterday_low"], yday_close) or 0.0

        # 날짜는 시스템 날짜가 아니라, 가장 최근 봉의 dt를 신뢰
        dt_val = None
        if isinstance(today_bar, dict):
            dt_val = today_bar.get("dt") or today_bar.get("date")
        date_str = str(dt_val) if dt_val else base_dt

        # 혹시 today_cur가 0이면 현재가 API로 보정(선택적)
        if today_cur <= 0:
            try:
                from kiwoom_client import KiwoomClient
                client = KiwoomClient(token=token)
                today_cur = float(client.get_last_price(symbol))
            except Exception:
                pass

        return {
            "date": date_str,
            "today_open": float(today_open),
            "today_high": float(today_high),
            "today_low": float(today_low),
            "today_current": float(today_cur),
            "yesterday_open": float(yday_open),
            "yesterday_close": float(yday_close),
            "yesterday_high": float(yday_high),
            "yesterday_low": float(yday_low),
        }

    except requests.HTTPError as http_err:
        resp = getattr(http_err, "response", None)
        body = getattr(resp, "text", None) if resp else None
        status = getattr(resp, "status_code", "?") if resp else "?"
        err = f"HTTP {status} {str(body or '')[:200]}"
        print(f"❌ 일봉차트 조회 HTTP 오류: {http_err} body={body}")
        if error_out is not None:
            error_out.append(err)
        return None
    except Exception as e:
        import traceback
        err = str(e)
        print(f"❌ 일봉차트 조회 실패: {e}")
        traceback.print_exc()
        if error_out is not None:
            error_out.append(err)
        return None


def _parse_bar_price(bar: Dict[str, Any], keys: List[str]) -> Optional[float]:
    """분봉 한 개에서 가격 추출 (문자열 부호 제거 후 절대값)."""
    val = _extract_price(bar, keys)
    return abs(val) if val is not None else None


def get_intraday_summary(
    token: str,
    code: str,
    tic_scope: str = "10",
    cnt: int = 50,
    error_out: Optional[list] = None,
) -> Optional[Dict[str, Any]]:
    """
    당일 분봉 요약 조회 (ka10080). 시가/고가/저가/현재가와 각각 처음 발생한 시간 반환.

    Args:
        token: 키움 API 토큰
        code: 종목코드 (6자리)
        tic_scope: 분봉 단위 ("1","3","5","10","15","30","45","60"). 기본 10분봉
        cnt: 조회 봉 개수. 기본 50

    Returns:
        {
            "date": "20250204",
            "today_open", "today_high", "today_low", "today_current": float,
            "open_time", "high_time", "low_time", "current_time": "HHMMSS",
            "yesterday_close", "yesterday_high", "yesterday_low": float,
        } 또는 None
    """
    code = normalize_stock_code(code)
    if not HOST:
        msg = "KIWOOM_HOST 환경 변수가 설정되어 있지 않습니다."
        print(f"❌ {msg}")
        if error_out is not None:
            error_out.append(msg)
        return None

    base_dt = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
    url = HOST.rstrip("/") + "/api/dostk/chart"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "api-id": "ka10080",
        "authorization": f"Bearer {token}",
    }
    payload = {
        "stk_cd": code,
        "base_dt": base_dt,
        "tic_scope": tic_scope,
        "cnt": cnt,
        "upd_stkpc_tp": "1",
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

        if not isinstance(data, dict) or data.get("return_code") != 0:
            rc = data.get("return_code") if isinstance(data, dict) else "?"
            msg = data.get("return_msg") or data.get("message") or "unknown" if isinstance(data, dict) else "unknown"
            err = f"분봉 return_code={rc} {msg}"
            print(f"❌ 분봉 조회 실패: {err}")
            if error_out is not None:
                error_out.append(err)
            return None

        raw_list = data.get("stk_min_pole_chart_qry") or []
        if not isinstance(raw_list, list):
            err = "stk_min_pole_chart_qry가 리스트가 아님"
            print(f"❌ 분봉 조회 실패: {err}")
            if error_out is not None:
                error_out.append(err)
            return None

        # 당일만 필터, 시간순 정렬 (과거 → 최근)
        bars = [b for b in raw_list if isinstance(b, dict) and (b.get("cntr_tm") or "")[:8] == base_dt]
        bars.sort(key=lambda b: b.get("cntr_tm", ""))

        if not bars:
            err = f"당일 분봉 데이터 없음 (base_dt={base_dt})"
            print(f"❌ 분봉 {err}: stk_cd={code}")
            if error_out is not None:
                error_out.append(err)
            return None

        def hhmmss(cntr_tm: str) -> str:
            """cntr_tm 14자리에서 HHMMSS 6자리 추출"""
            s = (cntr_tm or "").strip()
            return s[8:14] if len(s) >= 14 else ""

        first = bars[0]
        last = bars[-1]

        today_open = _parse_bar_price(first, ["open_pric", "open"])
        open_time = hhmmss(first.get("cntr_tm", ""))

        today_high = None
        for b in bars:
            p = _parse_bar_price(b, ["high_pric", "high"])
            if p is not None and (today_high is None or p > today_high):
                today_high = p
        if today_high is None:
            today_high = today_open or 0.0
        high_time = ""
        for b in bars:
            p = _parse_bar_price(b, ["high_pric", "high"])
            if p is not None and abs(p - today_high) < 0.01:
                high_time = hhmmss(b.get("cntr_tm", ""))
                break

        today_low = None
        for b in bars:
            p = _parse_bar_price(b, ["low_pric", "low"])
            if p is not None and p > 0 and (today_low is None or p < today_low):
                today_low = p
        if today_low is None:
            today_low = today_open or 0.0
        low_time = ""
        for b in bars:
            p = _parse_bar_price(b, ["low_pric", "low"])
            if p is not None and p > 0 and abs(p - today_low) < 0.01:
                low_time = hhmmss(b.get("cntr_tm", ""))
                break

        today_current = _parse_bar_price(last, ["cur_prc", "close"])
        if not today_current or today_current <= 0:
            try:
                from kiwoom_client import KiwoomClient
                today_current = float(KiwoomClient(token=token).get_last_price(code))
            except Exception:
                today_current = today_open or 0.0
        current_time = hhmmss(last.get("cntr_tm", ""))
        if not current_time:
            current_time = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H%M%S")

        # 고가/저가 "처음 발생" 시간: 이미 위에서 첫 등장 시점으로 저장함
        # (고가는 최댓값 갱신 시, 저가는 최솟값 갱신 시 해당 봉의 cntr_tm 저장)

        yesterday_close = 0.0
        yesterday_high = 0.0
        yesterday_low = 0.0
        try:
            daily = get_daily_chart(token, code)
            if daily:
                yesterday_close = float(daily.get("yesterday_close", 0) or 0)
                yesterday_high = float(daily.get("yesterday_high", 0) or 0)
                yesterday_low = float(daily.get("yesterday_low", 0) or 0)
        except Exception:
            pass

        return {
            "date": base_dt,
            "today_open": float(today_open or 0),
            "today_high": float(today_high),
            "today_low": float(today_low),
            "today_current": float(today_current),
            "open_time": open_time or current_time,
            "high_time": high_time or current_time,
            "low_time": low_time or current_time,
            "current_time": current_time,
            "yesterday_close": yesterday_close,
            "yesterday_high": yesterday_high,
            "yesterday_low": yesterday_low,
        }
    except requests.HTTPError as http_err:
        resp = getattr(http_err, "response", None)
        body = getattr(resp, "text", None) if resp else None
        status = getattr(resp, "status_code", "?") if resp else "?"
        err = f"분봉 HTTP {status} {str(body or '')[:150]}"
        print(f"❌ 분봉 조회 HTTP 오류: {http_err} body={body}")
        if error_out is not None:
            error_out.append(err)
        return None
    except Exception as e:
        import traceback
        err = str(e)
        print(f"❌ 분봉 조회 실패: {e}")
        traceback.print_exc()
        if error_out is not None:
            error_out.append(err)
        return None


def get_nxt_daily_chart(
    token: str,
    symbol: str,
    target_date: Optional[str] = None,
    error_out: Optional[list] = None,
) -> Optional[Dict[str, Any]]:
    """
    NXT 종목 일봉차트 조회 (분봉 데이터로 08:00~20:00 범위 계산)

    Args:
        token: 키움 API 토큰
        symbol: 종목코드
        target_date: 조회 날짜 (YYYYMMDD, None이면 당일)
        error_out: 실패 시 사유를 append할 리스트

    Returns:
        일봉차트와 동일한 형식
        {
            "date": "20260427",
            "today_open": 160000,  # 08:00 시가
            "today_high": 176000,
            "today_low": 159000,
            "today_current": 172700,  # 20:00 종가 (또는 마지막 체결가)
            "yesterday_close": 157200,
            "yesterday_high": 159100,
            "yesterday_low": 150400,
        }
    """
    symbol = normalize_stock_code(symbol)

    if not HOST:
        msg = "KIWOOM_HOST 환경 변수가 설정되어 있지 않습니다."
        print(f"❌ {msg}")
        if error_out is not None:
            error_out.append(msg)
        return None

    if target_date is None:
        target_date = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")

    # 1분봉 데이터 조회 (최대 200개)
    url = HOST.rstrip("/") + "/api/dostk/chart"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "api-id": "ka10080",
        "authorization": f"Bearer {token}",
    }
    payload = {
        "stk_cd": symbol,
        "base_dt": target_date,
        "tic_scope": "1",  # 1분봉
        "cnt": 200,
        "upd_stkpc_tp": "1",
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

        if not isinstance(data, dict) or data.get("return_code") != 0:
            # NXT가 아니면 일반 일봉 API 사용
            return get_daily_chart(token, symbol, error_out)

        raw_list = data.get("stk_min_pole_chart_qry") or []
        if not isinstance(raw_list, list):
            return get_daily_chart(token, symbol, error_out)

        # 당일 데이터만 필터 (08:00~20:00)
        bars = []
        for b in raw_list:
            if not isinstance(b, dict):
                continue
            cntr_tm = b.get("cntr_tm", "")
            if len(cntr_tm) < 14:
                continue
            date_part = cntr_tm[:8]
            time_part = cntr_tm[8:14]

            if date_part == target_date:
                hour = time_part[:2]
                if "08" <= hour <= "20":  # 08:00~20:59
                    bars.append(b)

        if not bars:
            # 분봉 데이터 없으면 일반 일봉 + 현재가 조합
            daily_data = get_daily_chart(token, symbol, error_out)
            if not daily_data:
                return None

            # 현재가 조회하여 today_current 업데이트
            try:
                from kiwoom_client import KiwoomClient
                client = KiwoomClient(token=token)
                current_price = float(client.get_last_price(symbol))
                daily_data["today_current"] = current_price
            except Exception as e:
                print(f"⚠️  NXT 현재가 조회 실패: {e}")

            return daily_data

        # 시간순 정렬
        bars.sort(key=lambda b: b.get("cntr_tm", ""))

        # OHLC 계산
        def parse_price(bar: Dict[str, Any], keys: List[str]) -> float:
            val = _extract_price(bar, keys)
            return abs(float(val)) if val is not None else 0.0

        first_bar = bars[0]
        last_bar = bars[-1]

        today_open = parse_price(first_bar, ["open_pric", "open"])
        today_current = parse_price(last_bar, ["cur_prc", "close"])

        today_high = 0.0
        today_low = float('inf')

        for bar in bars:
            high = parse_price(bar, ["high_pric", "high"])
            low = parse_price(bar, ["low_pric", "low"])

            if high > today_high:
                today_high = high
            if low > 0 and low < today_low:
                today_low = low

        if today_low == float('inf'):
            today_low = today_open

        # 전일 데이터는 일봉 API에서 가져오기
        daily_data = get_daily_chart(token, symbol)
        yesterday_open = daily_data.get("yesterday_open", 0) if daily_data else 0
        yesterday_close = daily_data.get("yesterday_close", 0) if daily_data else 0
        yesterday_high = daily_data.get("yesterday_high", 0) if daily_data else 0
        yesterday_low = daily_data.get("yesterday_low", 0) if daily_data else 0

        return {
            "date": target_date,
            "today_open": float(today_open),
            "today_high": float(today_high),
            "today_low": float(today_low),
            "today_current": float(today_current),
            "yesterday_open": float(yesterday_open),
            "yesterday_close": float(yesterday_close),
            "yesterday_high": float(yesterday_high),
            "yesterday_low": float(yesterday_low),
            "is_nxt": True,  # NXT 종목 표시
        }

    except Exception as e:
        print(f"❌ NXT 일봉 조회 실패: {e}")
        if error_out is not None:
            error_out.append(str(e))
        # 실패 시 일반 일봉 사용
        return get_daily_chart(token, symbol, error_out)


def get_minute_chart(
    token: str,
    symbol: str,
    interval: str,
    count: int = 20,
    error_out: Optional[list] = None,
) -> Optional[List[Dict[str, Any]]]:
    """
    분봉차트 정보 조회 (ka10080 API 사용)

    Args:
        token: 키움 API 토큰
        symbol: 종목코드 (예: "081180")
        interval: 분봉 종류 ("1분", "3분", "5분", "10분")
        count: 조회할 봉 개수 (기본 20, 최대 200)
        error_out: 실패 시 사유를 append할 리스트 (선택)

    Returns:
        [
            {
                "time": "091500",  # HHMMSS
                "open": 13000,
                "high": 13200,
                "low": 12900,
                "close": 13100
            },
            ...
        ] 또는 None (실패 시)

        리스트는 시간순 정렬 (과거 → 최근)
    """
    symbol = normalize_stock_code(symbol)

    if not HOST:
        msg = "KIWOOM_HOST 환경 변수가 설정되어 있지 않습니다."
        print(f"❌ {msg}")
        if error_out is not None:
            error_out.append(msg)
        return None

    # interval을 tic_scope로 변환
    interval_map = {
        "1분": "1",
        "3분": "3",
        "5분": "5",
        "10분": "10",
    }
    tic_scope = interval_map.get(interval)
    if not tic_scope:
        msg = f"지원하지 않는 interval: {interval}"
        print(f"❌ {msg}")
        if error_out is not None:
            error_out.append(msg)
        return None

    base_dt = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y%m%d")
    url = HOST.rstrip("/") + "/api/dostk/chart"
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
        "api-id": "ka10080",
        "authorization": f"Bearer {token}",
    }
    payload = {
        "stk_cd": symbol,
        "base_dt": base_dt,
        "tic_scope": tic_scope,
        "cnt": min(count, 200),  # 최대 200개
        "upd_stkpc_tp": "1",
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=15)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

        if not isinstance(data, dict) or data.get("return_code") != 0:
            rc = data.get("return_code") if isinstance(data, dict) else "?"
            msg = data.get("return_msg") or data.get("message") or "unknown"
            err = f"분봉 return_code={rc} {msg}"
            print(f"❌ 분봉 조회 실패: {err}")
            if error_out is not None:
                error_out.append(err)
            return None

        raw_list = data.get("stk_min_pole_chart_qry") or []
        if not isinstance(raw_list, list):
            err = "stk_min_pole_chart_qry가 리스트가 아님"
            print(f"❌ 분봉 조회 실패: {err}")
            if error_out is not None:
                error_out.append(err)
            return None

        valid = [b for b in raw_list if isinstance(b, dict) and b.get("cntr_tm")]
        if not valid:
            err = f"분봉 데이터 없음 (base_dt={base_dt})"
            print(f"❌ 분봉 {err}: stk_cd={symbol}")
            if error_out is not None:
                error_out.append(err)
            return None

        # 가장 최근 거래일 기준으로 필터 (휴장일/주말에도 마지막 거래일 데이터 반환)
        latest_date = max((b.get("cntr_tm") or "")[:8] for b in valid)
        bars = [b for b in valid if (b.get("cntr_tm") or "")[:8] == latest_date]
        bars.sort(key=lambda b: b.get("cntr_tm", ""))

        def parse_price(bar: Dict[str, Any], keys: List[str]) -> float:
            """분봉 한 개에서 가격 추출"""
            val = _extract_price(bar, keys)
            return abs(float(val)) if val is not None else 0.0

        def hhmmss(cntr_tm: str) -> str:
            """cntr_tm 14자리에서 HHMMSS 6자리 추출"""
            s = (cntr_tm or "").strip()
            return s[8:14] if len(s) >= 14 else ""

        result = []
        for bar in bars:
            result.append({
                "time": hhmmss(bar.get("cntr_tm", "")),
                "open": parse_price(bar, ["open_pric", "open"]),
                "high": parse_price(bar, ["high_pric", "high"]),
                "low": parse_price(bar, ["low_pric", "low"]),
                "close": parse_price(bar, ["cur_prc", "close"]),
            })

        return result

    except requests.HTTPError as http_err:
        resp = getattr(http_err, "response", None)
        body = getattr(resp, "text", None) if resp else None
        status = getattr(resp, "status_code", "?") if resp else "?"
        err = f"분봉 HTTP {status} {str(body or '')[:150]}"
        print(f"❌ 분봉 조회 HTTP 오류: {http_err} body={body}")
        if error_out is not None:
            error_out.append(err)
        return None
    except Exception as e:
        import traceback
        err = str(e)
        print(f"❌ 분봉 조회 실패: {e}")
        traceback.print_exc()
        if error_out is not None:
            error_out.append(err)
        return None


def _extract_price(data: Dict[str, Any], candidate_keys: list) -> Optional[float]:
    """응답 데이터에서 가격 정보를 추출합니다."""
    # 중첩된 구조도 확인 (예: data["output"]["cur_prc"])
    if isinstance(data, dict):
        for key in candidate_keys:
            if key in data:
                value = data[key]
                if value is None:
                    continue
                try:
                    # 문자열인 경우 부호 제거 및 쉼표 제거
                    if isinstance(value, str):
                        value = value.lstrip("+-").replace(",", "")
                    return float(value)
                except (ValueError, TypeError):
                    continue
        
        # 중첩된 구조 확인
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                result = _extract_price(value, candidate_keys)
                if result is not None:
                    return result
    
    elif isinstance(data, list) and len(data) > 0:
        # 리스트의 첫 번째 요소 확인
        return _extract_price(data[0], candidate_keys)
    
    return None


def format_chart_info(chart_data: Dict[str, Any], current_price: float) -> str:
    """
    일봉차트 정보를 텔레그램 메시지 형식으로 포맷팅합니다.
    
    Args:
        chart_data: get_daily_chart()의 반환값
        current_price: 현재가
    
    Returns:
        포맷팅된 텔레그램 메시지 문자열
    """
    if not chart_data:
        return "일봉차트 정보를 가져올 수 없습니다."
    
    lines = []
    lines.append("📈 일봉차트 정보")
    lines.append("")
    
    # 당일 정보
    today_open = chart_data.get("today_open", 0)
    today_high = chart_data.get("today_high", 0)
    today_low = chart_data.get("today_low", 0)
    today_current = chart_data.get("today_current", current_price)
    
    lines.append("📊 당일:")
    lines.append(f"시가: {today_open:,.0f}원")
    if current_price > 0 and today_open > 0:
        diff = current_price - today_open
        pct = (diff / today_open * 100) if today_open > 0 else 0
        sign = "+" if diff >= 0 else ""
        lines.append(f"  현재가 대비: {sign}{diff:,.0f}원 ({sign}{pct:.2f}%)")
    
    lines.append(f"고가: {today_high:,.0f}원")
    if current_price > 0 and today_high > 0:
        diff = current_price - today_high
        pct = (diff / today_high * 100) if today_high > 0 else 0
        sign = "+" if diff >= 0 else ""
        lines.append(f"  현재가 대비: {sign}{diff:,.0f}원 ({sign}{pct:.2f}%)")
    
    lines.append(f"저가: {today_low:,.0f}원")
    if current_price > 0 and today_low > 0:
        diff = current_price - today_low
        pct = (diff / today_low * 100) if today_low > 0 else 0
        sign = "+" if diff >= 0 else ""
        lines.append(f"  현재가 대비: {sign}{diff:,.0f}원 ({sign}{pct:.2f}%)")
    
    lines.append(f"현재가: {today_current:,.0f}원")
    lines.append("")
    
    # 전일 정보
    yesterday_close = chart_data.get("yesterday_close", 0)
    yesterday_high = chart_data.get("yesterday_high", 0)
    yesterday_low = chart_data.get("yesterday_low", 0)
    
    lines.append("📉 전일:")
    lines.append(f"종가: {yesterday_close:,.0f}원")
    if current_price > 0 and yesterday_close > 0:
        diff = current_price - yesterday_close
        pct = (diff / yesterday_close * 100) if yesterday_close > 0 else 0
        sign = "+" if diff >= 0 else ""
        lines.append(f"  현재가 대비: {sign}{diff:,.0f}원 ({sign}{pct:.2f}%)")
    
    if yesterday_high > 0:
        lines.append(f"고가: {yesterday_high:,.0f}원")
        if current_price > 0:
            diff = current_price - yesterday_high
            pct = (diff / yesterday_high * 100) if yesterday_high > 0 else 0
            sign = "+" if diff >= 0 else ""
            lines.append(f"  현재가 대비: {sign}{diff:,.0f}원 ({sign}{pct:.2f}%)")
    
    if yesterday_low > 0:
        lines.append(f"저가: {yesterday_low:,.0f}원")
        if current_price > 0:
            diff = current_price - yesterday_low
            pct = (diff / yesterday_low * 100) if yesterday_low > 0 else 0
            sign = "+" if diff >= 0 else ""
            lines.append(f"  현재가 대비: {sign}{diff:,.0f}원 ({sign}{pct:.2f}%)")
    
    return "\n".join(lines)


if __name__ == "__main__":
    # 테스트 코드
    from kiwoom_token import get_token
    
    token = get_token()
    symbol = "081180"
    
    print("=" * 60)
    print(f"일봉차트 조회 테스트 - 종목코드: {symbol}")
    print("=" * 60)
    print()
    
    chart_data = get_daily_chart(token, symbol)
    
    if chart_data:
        print("✅ 일봉차트 조회 성공")
        print()
        print("📊 조회 결과:")
        for key, value in chart_data.items():
            print(f"  {key}: {value}")
        print()
        
        # 포맷팅 테스트 (일봉 cur_prc를 현재가로 사용)
        current_price = float(chart_data.get("today_current", 0))
        formatted = format_chart_info(chart_data, current_price)
        print("💬 텔레그램 메시지 포맷팅 예시:")
        print("-" * 60)
        print(formatted)
    else:
        print("❌ 일봉차트 조회 실패")
