"""
Enhanced Analysis - AI Agent용 핵심 인사이트 추출
"""
import pandas as pd
from typing import Dict, List, Optional, Tuple


def find_strong_rally_day(daily_df: pd.DataFrame,
                          volume_threshold: float = 500_0000_0000,
                          close_change_pct: float = 15.0) -> Optional[Dict]:
    """
    강한 상승일 탐지 (거래대금 + 종가 상승률)

    Args:
        daily_df: 일봉 DataFrame (trde_prica, cur_prc 필요)
        volume_threshold: 거래대금 임계값 (기본 500억)
        close_change_pct: 종가 상승률 임계값 (기본 15%)

    Returns:
        강한 상승일 정보 dict (없으면 None)
    """
    if daily_df.empty or len(daily_df) < 2:
        return None

    # 역순으로 탐색 (최근 날짜부터)
    for i in range(len(daily_df) - 1, 0, -1):
        current = daily_df.iloc[i]
        prev = daily_df.iloc[i - 1]

        # 거래대금 체크
        volume = current.get('trde_prica', 0)
        if volume < volume_threshold:
            continue

        # 종가 상승률 체크
        prev_close = prev['cur_prc']
        current_close = current['cur_prc']

        if prev_close == 0:
            continue

        close_change = ((current_close - prev_close) / prev_close * 100)

        if close_change >= close_change_pct:
            # 시가 상승률도 계산
            prev_close_for_open = prev['cur_prc']
            current_open = current['open_pric']
            open_change = ((current_open - prev_close_for_open) / prev_close_for_open * 100) if prev_close_for_open > 0 else 0

            # 며칠 전인지 계산
            days_ago = len(daily_df) - 1 - i

            return {
                'date': current['dt'].strftime('%Y-%m-%d') if hasattr(current['dt'], 'strftime') else str(current['dt']),
                'days_ago': days_ago,
                'volume': volume,
                'volume_billion': round(volume / 100000000, 1),  # 억원
                'close_change_pct': round(close_change, 2),
                'open_change_pct': round(open_change, 2),
                'prev_close': prev_close,
                'current_open': current_open,
                'current_high': current['high_pric'],
                'current_low': current['low_pric'],
                'current_close': current_close,
            }

    return None


def get_ma_price_alignment(daily_df: pd.DataFrame,
                           ma_periods: List[int] = [3, 5, 10, 15, 33, 45, 60]) -> Dict:
    """
    이동평균선과 현재가를 가격 순으로 정렬

    Args:
        daily_df: 일봉 DataFrame (ma3, ma5, ma10, ... 필요)
        ma_periods: 이동평균선 기간 리스트

    Returns:
        가격순 정렬 정보
    """
    if daily_df.empty:
        return {'error': 'Empty DataFrame'}

    current_row = daily_df.iloc[-1]
    current_price = current_row['cur_prc']

    # 이평선 값 수집
    items = []
    items.append(('현재가', current_price))

    for period in ma_periods:
        ma_col = f'ma{period}'
        if ma_col in daily_df.columns:
            ma_value = current_row[ma_col]
            if pd.notna(ma_value) and ma_value > 0:
                items.append((f'{period}일선', ma_value))

    # 가격 순으로 정렬 (내림차순)
    sorted_items = sorted(items, key=lambda x: x[1], reverse=True)

    # 현재가 위치 찾기
    current_price_index = next((i for i, (name, _) in enumerate(sorted_items) if name == '현재가'), -1)

    # 현재가보다 위에 있는 이평선
    above_mas = [name for name, _ in sorted_items[:current_price_index]]

    # 현재가보다 아래에 있는 이평선
    below_mas = [name for name, _ in sorted_items[current_price_index + 1:]]

    # 가격과 거리 계산
    ma_distances = {}
    for period in ma_periods:
        ma_col = f'ma{period}'
        if ma_col in daily_df.columns:
            ma_value = current_row[ma_col]
            if pd.notna(ma_value) and ma_value > 0:
                distance_pct = ((current_price - ma_value) / ma_value * 100)
                ma_distances[f'{period}일선'] = {
                    'value': float(ma_value),
                    'distance_pct': round(float(distance_pct), 2),
                    'position': 'above' if distance_pct > 0 else 'below'
                }

    return {
        'current_price': float(current_price),
        'sorted_by_price': [
            {'name': name, 'value': float(value)}
            for name, value in sorted_items
        ],
        'above_current': above_mas,  # 현재가보다 위
        'below_current': below_mas,  # 현재가보다 아래
        'ma_distances': ma_distances,
        'alignment_string': ' > '.join([f"{name}({value:,.0f})" for name, value in sorted_items])
    }


def check_bollinger_consolidation(daily_df: pd.DataFrame,
                                  bb_period: int = 20,
                                  bb_std: float = 2.0,
                                  squeeze_threshold_pct: float = 5.0,
                                  lookback_days: int = 5) -> Dict:
    """
    볼린저 밴드 기반 횡보 판정

    Args:
        daily_df: 일봉 DataFrame
        bb_period: 볼린저 밴드 기간 (기본 20)
        bb_std: 표준편차 배수 (기본 2.0)
        squeeze_threshold_pct: 밴드폭 임계값 (기본 5%)
        lookback_days: 연속 일수 (기본 5)

    Returns:
        횡보 판정 결과
    """
    if daily_df.empty or len(daily_df) < bb_period:
        return {'error': 'Insufficient data'}

    # 볼린저 밴드 계산
    close = daily_df['cur_prc']
    ma = close.rolling(bb_period).mean()
    sd = close.rolling(bb_period).std()

    upper_band = ma + (bb_std * sd)
    lower_band = ma - (bb_std * sd)

    # 밴드폭 % 계산
    bb_width_pct = ((upper_band - lower_band) / ma * 100)

    # 최근 N일 밴드폭
    recent_widths = bb_width_pct.tail(lookback_days)

    # 횡보 판정: 최근 N일 모두 임계값 이하
    is_consolidating = all(recent_widths <= squeeze_threshold_pct)

    # 현재 밴드 정보
    current_row = daily_df.iloc[-1]
    current_price = current_row['cur_prc']
    current_ma = ma.iloc[-1]
    current_upper = upper_band.iloc[-1]
    current_lower = lower_band.iloc[-1]
    current_width_pct = bb_width_pct.iloc[-1]

    # 현재가가 밴드 내 어디에 위치하는지
    band_position = 'middle'
    if current_price >= current_upper:
        band_position = 'above_upper'
    elif current_price <= current_lower:
        band_position = 'below_lower'
    elif current_price > current_ma:
        band_position = 'upper_half'
    else:
        band_position = 'lower_half'

    return {
        'is_consolidating': is_consolidating,
        'parameters': {
            'period': bb_period,
            'std': bb_std,
            'squeeze_threshold_pct': squeeze_threshold_pct,
            'lookback_days': lookback_days
        },
        'current': {
            'price': float(current_price),
            'middle_band': float(current_ma),
            'upper_band': float(current_upper),
            'lower_band': float(current_lower),
            'width_pct': round(float(current_width_pct), 2),
            'position': band_position
        },
        'recent_widths': [round(float(w), 2) for w in recent_widths],
        'avg_width_last_n_days': round(float(recent_widths.mean()), 2),
        'max_width_last_n_days': round(float(recent_widths.max()), 2),
        'min_width_last_n_days': round(float(recent_widths.min()), 2),
    }


def extract_key_insights(daily_df: pd.DataFrame,
                        volume_threshold: float = 500_0000_0000,
                        rally_pct: float = 15.0,
                        bb_period: int = 20,
                        bb_std: float = 2.0,
                        bb_squeeze_pct: float = 5.0) -> Dict:
    """
    핵심 인사이트 통합 추출

    Args:
        daily_df: 일봉 DataFrame (모든 지표 포함)
        volume_threshold: 거래대금 임계값
        rally_pct: 상승률 임계값
        bb_period: 볼린저 밴드 기간
        bb_std: 볼린저 밴드 표준편차
        bb_squeeze_pct: 밴드폭 임계값

    Returns:
        핵심 인사이트 dict
    """
    insights = {}

    # 1. 강한 상승일 탐지
    rally_day = find_strong_rally_day(daily_df, volume_threshold, rally_pct)
    insights['strong_rally_day'] = rally_day

    # 2. 이평선-현재가 위치
    ma_alignment = get_ma_price_alignment(daily_df, [3, 5, 10, 15, 33, 45, 60])
    insights['ma_price_alignment'] = ma_alignment

    # 3. 볼린저 밴드 횡보 판정
    bb_consolidation = check_bollinger_consolidation(
        daily_df, bb_period, bb_std, bb_squeeze_pct, lookback_days=5
    )
    insights['bollinger_consolidation'] = bb_consolidation

    return insights
