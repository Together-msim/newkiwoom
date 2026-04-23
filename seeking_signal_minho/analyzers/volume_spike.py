"""
거래대금 스파이크 탐지
"""
import pandas as pd
from typing import Dict


def find_last_volume_spike(daily_df: pd.DataFrame, market_cap_won: float) -> Dict:
    """
    시총 구간에 맞는 임계값으로 최근 스파이크 날짜 찾기

    Args:
        daily_df: 일봉 DataFrame (trde_prica 컬럼 필요)
        market_cap_won: 시가총액 (억원)

    Returns:
        거래대금 스파이크 분석 결과
    """
    from ..config import VOLUME_THRESHOLDS

    # 시총 구간에서 임계값 찾기
    interest_threshold, strong_threshold = None, None
    for cap_limit, interest, strong in VOLUME_THRESHOLDS:
        if market_cap_won <= cap_limit:
            interest_threshold = interest
            strong_threshold = strong
            break

    # 기본값 (매우 큰 시총)
    if interest_threshold is None:
        interest_threshold = 500_0000_0000
        strong_threshold = 1_500_0000_0000

    # 역순으로 스파이크 찾기 (today=0일 전)
    days_ago_interest = None
    days_ago_strong = None

    for i, (idx, row) in enumerate(daily_df[::-1].iterrows()):
        trde_prica = row.get('trde_prica', 0)

        if days_ago_strong is None and trde_prica >= strong_threshold:
            days_ago_strong = i
        if days_ago_interest is None and trde_prica >= interest_threshold:
            days_ago_interest = i

        if days_ago_strong is not None and days_ago_interest is not None:
            break

    # 신호 품질 분류
    signal_quality = _classify_signal(days_ago_strong)

    return {
        'market_cap_won': market_cap_won,
        'thresholds': {
            'interest': interest_threshold,
            'strong': strong_threshold,
        },
        'days_ago_interest': days_ago_interest,
        'days_ago_strong': days_ago_strong,
        'signal_quality': signal_quality,
    }


def _classify_signal(days_ago_strong: int | None) -> str:
    """
    신호 품질 분류

    Args:
        days_ago_strong: 강한 거래대금 발생 일수 (0=오늘)

    Returns:
        'imminent' (돌파 임박) | 'watch' (관망) | 'dead' (죽은 종목)
    """
    if days_ago_strong is None:
        return 'dead'
    if days_ago_strong <= 3:
        return 'imminent'  # 돌파 임박
    if days_ago_strong <= 30:
        return 'watch'  # 관망
    return 'dead'  # 죽은 종목
