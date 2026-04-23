"""
타입1 매크로 분석 - 최근 강한 상승 후 눌림/숨고르기 중인 종목
"""
import pandas as pd
from typing import Dict


def analyze_type1(df: pd.DataFrame, params: dict = None) -> Dict:
    """
    타입1 판정 로직

    대상: 최근 강한 상승 후 눌림/숨고르기 중인 종목
    필요 컬럼: cur_prc, ma5, ma8, ma15, ma33, ma45, ma60, bbwp, high_pric

    Args:
        df: 일봉 DataFrame (260일 이상)
        params: 파라미터 오버라이드
            - bbwp_threshold: BBWP 임계값 (기본 25)
            - bbwp_consecutive_days: 연속 일수 (기본 5)
            - pullback_max_pct: 고점대비 최대 하락% (기본 15)
            - rally_min_pct: 60일 최소 상승% (기본 20)

    Returns:
        타입1 분석 결과 dict
    """
    from ..config import TYPE1_DEFAULTS

    # 파라미터 병합
    p = {**TYPE1_DEFAULTS, **(params or {})}

    if len(df) < 60:
        return {
            'type': 'type1',
            'applicable': False,
            'is_sideways': False,
            'error': 'Insufficient data (< 60 days)'
        }

    # 현재 값들
    current = df.iloc[-1]
    cur_price = current['cur_prc']

    # 필수 컬럼 체크
    required_cols = ['ma5', 'ma8', 'ma15', 'ma33', 'ma45', 'ma60', 'bbwp']
    if not all(col in df.columns for col in required_cols):
        return {
            'type': 'type1',
            'applicable': False,
            'is_sideways': False,
            'error': 'Missing required indicators'
        }

    # MA 값 추출
    ma5 = current['ma5']
    ma8 = current['ma8']
    ma15 = current['ma15']
    ma33 = current['ma33']
    ma45 = current['ma45']
    ma60 = current['ma60']

    # T1.A: above_5_8
    above_5_8 = cur_price > ma5 and cur_price > ma8

    # T1.B: above_15
    above_15 = cur_price > ma15

    # T1.C: rebound_zone
    rebound_zone = (cur_price < ma15 and
                   cur_price > ma33 and
                   cur_price > ma45 and
                   cur_price > ma60)

    # T1.D: had_strong_rally_60d
    # 최근 60일 고가 >= 60일 전 종가 × 1.20
    if len(df) >= 60:
        high_60d = df['high_pric'].tail(60).max()
        close_60d_ago = df['cur_prc'].iloc[-61] if len(df) > 60 else df['cur_prc'].iloc[0]
        rally_60d_pct = ((high_60d - close_60d_ago) / close_60d_ago * 100) if close_60d_ago > 0 else 0
        had_strong_rally = rally_60d_pct >= p['rally_min_pct']
    else:
        rally_60d_pct = 0
        had_strong_rally = False

    # T1.E: near_recent_high
    # (60일 고가 - 현재가) / 60일 고가 <= 0.15
    if len(df) >= 60:
        high_60d = df['high_pric'].tail(60).max()
        pullback_pct = ((high_60d - cur_price) / high_60d * 100) if high_60d > 0 else 0
        near_recent_high = pullback_pct <= p['pullback_max_pct']
    else:
        pullback_pct = 100
        near_recent_high = False

    # T1.F: bb_squeeze_sustained
    # 최근 5일 연속 bbwp <= 25
    if len(df) >= p['bbwp_consecutive_days']:
        last_n_bbwp = df['bbwp'].tail(p['bbwp_consecutive_days'])
        bb_squeeze = all(last_n_bbwp <= p['bbwp_threshold'])
        bbwp_last_5d_max = last_n_bbwp.max()
    else:
        bb_squeeze = False
        bbwp_last_5d_max = 0

    # 정배열/역배열 판정
    ma_list = [ma5, ma8, ma15, ma33, ma45, ma60]
    is_perfect_bull = all(a > b for a, b in zip(ma_list, ma_list[1:])) if all(pd.notna(ma_list)) else False
    is_perfect_bear = all(a < b for a, b in zip(ma_list, ma_list[1:])) if all(pd.notna(ma_list)) else False

    # MA 값 정렬 (가격 내림차순)
    ma_values_sorted = sorted(
        [('ma5', ma5), ('ma8', ma8), ('ma15', ma15),
         ('ma33', ma33), ('ma45', ma45), ('ma60', ma60)],
        key=lambda x: x[1] if pd.notna(x[1]) else 0,
        reverse=True
    )

    # 최종 타입1 횡보 판정
    is_type1_sideways = had_strong_rally and near_recent_high and bb_squeeze

    # 타입1 후보 여부 (강한 상승이 있었는지)
    is_type1_candidate = had_strong_rally

    return {
        'type': 'type1',
        'applicable': is_type1_candidate,
        'is_sideways': is_type1_sideways,
        'ma_position': {
            'above_5_8': above_5_8,
            'above_15': above_15,
            'rebound_zone': rebound_zone,
        },
        'ma_values_sorted': ma_values_sorted,
        'is_perfect_bull': is_perfect_bull,
        'is_perfect_bear': is_perfect_bear,
        'metrics': {
            'bbwp_today': float(current['bbwp']) if pd.notna(current['bbwp']) else 0,
            'bbwp_last_5d_max': float(bbwp_last_5d_max) if pd.notna(bbwp_last_5d_max) else 0,
            'pullback_from_60d_high_pct': round(pullback_pct, 2),
            'rally_60d_pct': round(rally_60d_pct, 2),
        },
        'criteria_hits': {
            'had_strong_rally_60d': had_strong_rally,
            'near_recent_high': near_recent_high,
            'bb_squeeze_sustained': bb_squeeze,
        }
    }
