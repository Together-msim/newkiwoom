"""
타입2 매크로 분석 - 오랫동안 주목받지 못하고 답보 중인 종목
"""
import pandas as pd
from typing import Dict


def analyze_type2(df: pd.DataFrame, params: dict = None) -> Dict:
    """
    타입2 판정 로직

    대상: 오랫동안 주목받지 못하고 답보 중인 종목
    필요 컬럼: cur_prc, ma100, ma224, adx14, high_pric, low_pric, trde_qty

    Args:
        df: 일봉 DataFrame (260일 이상)
        params: 파라미터 오버라이드
            - range_threshold_pct: 20일 변동폭 임계% (기본 7)
            - volume_ratio: 거래량 비율 (기본 0.5)
            - adx_threshold: ADX 임계값 (기본 20)

    Returns:
        타입2 분석 결과 dict
    """
    from ..config import TYPE2_DEFAULTS

    # 파라미터 병합
    p = {**TYPE2_DEFAULTS, **(params or {})}

    if len(df) < 224:
        return {
            'type': 'type2',
            'applicable': False,
            'is_sideways': False,
            'error': 'Insufficient data (< 224 days)'
        }

    # 현재 값들
    current = df.iloc[-1]
    cur_price = current['cur_prc']

    # 필수 컬럼 체크
    required_cols = ['ma100', 'ma224', 'adx14']
    if not all(col in df.columns for col in required_cols):
        return {
            'type': 'type2',
            'applicable': False,
            'is_sideways': False,
            'error': 'Missing required indicators'
        }

    ma100 = current['ma100']
    ma224 = current['ma224']
    adx14 = current['adx14']

    # T2.A: below_224_above_100
    below_224_above_100 = cur_price < ma224 and cur_price > ma100

    # T2.B: tight_range_20d
    # 최근 20영업일 (고가 max - 저가 min) / 중간값 × 100 <= 7%
    if len(df) >= 20:
        recent_20d = df.tail(20)
        high_max = recent_20d['high_pric'].max()
        low_min = recent_20d['low_pric'].min()
        mid_price = (high_max + low_min) / 2
        range_pct = ((high_max - low_min) / mid_price * 100) if mid_price > 0 else 0
        tight_range = range_pct <= p['range_threshold_pct']
    else:
        range_pct = 100
        tight_range = False

    # T2.C: volume_dried
    # 최근 20일 거래량 평균 <= 과거 100일 거래량 평균 × 0.5
    if len(df) >= 100:
        recent_20_vol = df['trde_qty'].tail(20).mean()
        past_100_vol = df['trde_qty'].tail(100).mean()
        volume_ratio = (recent_20_vol / past_100_vol) if past_100_vol > 0 else 1.0
        volume_dried = volume_ratio <= p['volume_ratio']
    else:
        volume_ratio = 1.0
        volume_dried = False

    # T2.D: no_trend
    no_trend = adx14 < p['adx_threshold']

    # 최종 타입2 횡보 판정
    is_type2_sideways = (below_224_above_100 and
                        tight_range and
                        volume_dried and
                        no_trend)

    return {
        'type': 'type2',
        'applicable': below_224_above_100,  # 224밑/100위 조건 충족 시 타입2 후보
        'is_sideways': is_type2_sideways,
        'criteria_hits': {
            'below_224_above_100': below_224_above_100,
            'tight_range_20d': tight_range,
            'volume_dried': volume_dried,
            'no_trend': no_trend,
        },
        'metrics': {
            'range_pct_20d': round(range_pct, 2),
            'volume_ratio_recent_vs_longterm': round(volume_ratio, 3),
            'adx14': round(float(adx14), 2) if pd.notna(adx14) else 0,
        }
    }
