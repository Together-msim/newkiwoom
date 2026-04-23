"""
분봉 마이크로 판단
"""
import pandas as pd
from typing import Dict


def analyze_micro(df3: pd.DataFrame, df60: pd.DataFrame,
                 snapshot: dict, daily_df: pd.DataFrame,
                 params: dict = None) -> Dict:
    """
    분봉 기반 마이크로 추세 분석

    Args:
        df3: 3분봉 DataFrame
        df60: 60분봉 DataFrame
        snapshot: 현재 스냅샷 (ka10001 응답)
        daily_df: 일봉 DataFrame
        params: 파라미터 오버라이드

    Returns:
        마이크로 분석 결과
    """
    from ..config import MICRO_DEFAULTS

    p = {**MICRO_DEFAULTS, **(params or {})}

    result = {
        'three_min_sideways': None,
        'above_120min_trend': False,
        'today_trend': None,
        'price_comparison': None,
        'minute_120_data': None,  # 120분봉 원시 데이터
    }

    # 3분봉 횡보 판정
    if not df3.empty and len(df3) >= p['sideways_bars']:
        result['three_min_sideways'] = is_3min_sideways(
            df3,
            bars=p['sideways_bars'],
            range_threshold_pct=p['sideways_range_pct']
        )

    # 120분봉 추세 (60분봉에서 합성)
    if not df60.empty and len(df60) >= 5:
        cur_price = float(snapshot.get('cur_prc', 0))
        df120 = resample_60_to_120(df60)
        result['above_120min_trend'] = is_above_120min_trend_from_df(df120, cur_price)

        # 120분봉 원시 데이터 (최근 10개) 및 5봉 MA 포함
        if not df120.empty:
            result['minute_120_data'] = extract_120min_data(df120)

    # 당일 추세
    if snapshot:
        result['today_trend'] = is_today_trending_up(snapshot)

    # 가격 비교 그래프 데이터
    if not daily_df.empty and len(daily_df) >= 2:
        result['price_comparison'] = build_price_comparison(snapshot, daily_df)

    return result


def is_3min_sideways(df3: pd.DataFrame, bars: int = 10,
                    range_threshold_pct: float = 1.0) -> Dict:
    """
    3분봉 횡보 판정

    Args:
        df3: 3분봉 DataFrame
        bars: 최근 N개 봉 (기본 10 = 30분)
        range_threshold_pct: 변동폭 임계% (기본 1.0%)

    Returns:
        횡보 판정 결과
    """
    recent = df3.tail(bars)
    high_max = recent['high_pric'].max()
    low_min = recent['low_pric'].min()
    last_close = df3['cur_prc'].iloc[-1]

    range_pct = ((high_max - low_min) / last_close * 100) if last_close > 0 else 0

    # 거래량 동반 수축 조건 (진짜 횡보)
    avg_vol_today = df3['trde_qty'].mean()
    recent_vol_avg = recent['trde_qty'].mean()
    vol_contracted = recent_vol_avg <= avg_vol_today * 0.7

    is_sideways = range_pct <= range_threshold_pct and vol_contracted

    return {
        'is_sideways': is_sideways,
        'range_pct': round(range_pct, 3),
        'volume_contracted': vol_contracted,
        'bars_analyzed': bars,
    }


def resample_60_to_120(df60: pd.DataFrame) -> pd.DataFrame:
    """
    60분봉을 120분봉으로 리샘플링

    Args:
        df60: 60분봉 DataFrame

    Returns:
        120분봉 DataFrame
    """
    if df60.empty:
        return pd.DataFrame()

    df = df60.copy().set_index('cntr_tm').sort_index()

    # 한국장 09:00 시작 기준으로 120분 집계
    df120 = df.resample('120min', origin='start_day', offset='9h').agg({
        'open_pric': 'first',
        'high_pric': 'max',
        'low_pric': 'min',
        'cur_prc': 'last',
        'trde_qty': 'sum',
    }).dropna()

    return df120.reset_index()


def is_above_120min_trend(df60: pd.DataFrame, current_price: float) -> bool:
    """
    120분봉 5개 이동평균선 위에 있는지 판정

    Args:
        df60: 60분봉 DataFrame
        current_price: 현재가

    Returns:
        120분봉 추세 위 여부
    """
    df120 = resample_60_to_120(df60)
    return is_above_120min_trend_from_df(df120, current_price)


def is_above_120min_trend_from_df(df120: pd.DataFrame, current_price: float) -> bool:
    """
    120분봉 DataFrame으로부터 추세 위 여부 판정

    Args:
        df120: 120분봉 DataFrame
        current_price: 현재가

    Returns:
        120분봉 추세 위 여부
    """
    if df120.empty or len(df120) < 5:
        return False

    # 120분봉 5개 이동평균 (약 10시간)
    ma5_120 = df120['cur_prc'].tail(5).mean()

    return current_price > ma5_120


def extract_120min_data(df120: pd.DataFrame) -> Dict:
    """
    120분봉 원시 데이터 추출 (차트용)

    Args:
        df120: 120분봉 DataFrame

    Returns:
        차트용 120분봉 데이터
    """
    if df120.empty:
        return None

    # 최근 10개 봉
    recent = df120.tail(10).copy()

    # 5봉 이동평균 계산
    recent['ma5'] = recent['cur_prc'].rolling(window=5, min_periods=1).mean()

    # JSON 직렬화 가능한 형태로 변환
    candles = []
    for _, row in recent.iterrows():
        candles.append({
            'time': row['cntr_tm'].strftime('%Y-%m-%d %H:%M:%S') if hasattr(row['cntr_tm'], 'strftime') else str(row['cntr_tm']),
            'open': float(row['open_pric']),
            'high': float(row['high_pric']),
            'low': float(row['low_pric']),
            'close': float(row['cur_prc']),
            'volume': int(row['trde_qty']) if 'trde_qty' in row else 0,
            'ma5': float(row['ma5']) if pd.notna(row['ma5']) else None,
        })

    return {
        'candles': candles,
        'count': len(candles),
    }


def is_today_trending_up(snapshot: dict) -> Dict:
    """
    당일 추세가 살아있는지 판정

    Args:
        snapshot: 현재 스냅샷 (ka10001 응답)

    Returns:
        당일 추세 판정 결과
    """
    cur = float(snapshot.get('cur_prc', 0))
    today_open = float(snapshot.get('open_pric', 0))
    prev_close = float(snapshot.get('base_pric', 0))

    above_today_open = cur > today_open
    above_prev_close = cur > prev_close
    alive = above_today_open and above_prev_close

    return {
        'above_today_open': above_today_open,
        'above_prev_close': above_prev_close,
        'alive': alive,
    }


def build_price_comparison(snapshot: dict, daily_df: pd.DataFrame) -> Dict:
    """
    전일/당일 가격 비교 데이터 생성

    Args:
        snapshot: 현재 스냅샷
        daily_df: 일봉 DataFrame

    Returns:
        가격 비교 데이터
    """
    if len(daily_df) < 2:
        return {}

    prev_row = daily_df.iloc[-2]  # 전일

    return {
        'prev_open': float(prev_row['open_pric']),
        'prev_close': float(snapshot.get('base_pric', 0)),
        'prev_high': float(prev_row['high_pric']),
        'prev_low': float(prev_row['low_pric']),
        'today_open': float(snapshot.get('open_pric', 0)),
        'today_high': float(snapshot.get('high_pric', 0)),
        'today_low': float(snapshot.get('low_pric', 0)),
        'current_price': float(snapshot.get('cur_prc', 0)),
    }
