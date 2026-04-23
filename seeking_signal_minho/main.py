"""
Seeking Signal Minho - 단일 진입점

Usage:
    from seeking_signal_minho import analyze
    report = analyze("005930")
"""
from datetime import datetime
from typing import Dict, Optional

from .config import MA_WINDOWS_ALL
from .api_client import SeekingSignalClient
from .indicators import add_all_indicators
from .analyzers import analyze_type1, analyze_type2, find_last_volume_spike, analyze_micro
from .report import assemble_report
from .enhanced_analysis import extract_key_insights


def analyze(stock_code: str, base_date: str = None, params: dict = None) -> Dict:
    """
    단일 종목 분석

    Args:
        stock_code: 6자리 종목코드 (예: "005930")
        base_date: 조사 기준일 YYYYMMDD (None이면 오늘)
        params: 파라미터 오버라이드
            - type1: 타입1 파라미터 dict
            - type2: 타입2 파라미터 dict
            - micro: 분봉 마이크로 파라미터 dict

    Returns:
        AnalysisReport dict

    Example:
        >>> report = analyze("005930")
        >>> print(report['summary']['verdict'])
        'buyable'
        >>> print(report['summary']['confidence'])
        0.85
    """
    # 종목코드 검증
    if not stock_code or len(stock_code) != 6 or not stock_code.isdigit():
        return {
            'error': 'Invalid stock code. Must be 6-digit string.',
            'stock_code': stock_code,
        }

    # 파라미터 추출
    params = params or {}
    type1_params = params.get('type1')
    type2_params = params.get('type2')
    micro_params = params.get('micro')

    # API 클라이언트
    client = SeekingSignalClient()

    try:
        # 1. 종목 기본정보
        stock_info = client.get_stock_info(stock_code)
        if not stock_info:
            return {
                'error': 'Failed to fetch stock info',
                'stock_code': stock_code,
            }

        # 시가총액 (억원)
        market_cap = float(stock_info.get('mac', 0))

        # 2. 일봉 차트 조회 (260일 이상)
        daily_df = client.get_daily_chart(stock_code, base_date)
        if daily_df.empty:
            return {
                'error': 'Failed to fetch daily chart',
                'stock_code': stock_code,
            }

        # 3. 기술 지표 계산
        daily_df = add_all_indicators(daily_df, MA_WINDOWS_ALL)

        # 4. 타입1 분석
        type1_result = analyze_type1(daily_df, type1_params)

        # 5. 타입2 분석
        type2_result = analyze_type2(daily_df, type2_params)

        # 6. 거래대금 스파이크
        volume_spike = find_last_volume_spike(daily_df, market_cap)

        # 7. 분봉 마이크로 분석
        micro_result = None
        try:
            df3 = client.get_minute_chart(stock_code, tic_scope=3, min_bars=120)
            df60 = client.get_minute_chart(stock_code, tic_scope=60, min_bars=40)
            micro_result = analyze_micro(df3, df60, stock_info, daily_df, micro_params)
        except Exception as e:
            print(f"분봉 분석 실패 (비장시간일 수 있음): {e}")
            # 분봉 없어도 가격 비교는 일봉+현재가로 생성 가능
            from .analyzers.micro_minute import build_price_comparison
            micro_result = {
                'error': str(e),
                'three_min_sideways': None,
                'above_120min_trend': False,
                'today_trend': None,
                'price_comparison': build_price_comparison(stock_info, daily_df),
                'minute_120_data': None,
            }

        # 8. 핵심 인사이트 추출 (Enhanced Analysis)
        key_insights = extract_key_insights(
            daily_df,
            volume_threshold=params.get('volume_threshold', 500_0000_0000),
            rally_pct=params.get('rally_pct', 15.0),
            bb_period=params.get('bb_period', 20),
            bb_std=params.get('bb_std', 2.0),
            bb_squeeze_pct=params.get('bb_squeeze_pct', 5.0)
        )

        # 9. 최종 리포트 조립
        analyzed_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%S+09:00')
        report = assemble_report(
            stock_code=stock_code,
            stock_info=stock_info,
            daily_df=daily_df,
            type1_result=type1_result,
            type2_result=type2_result,
            volume_spike=volume_spike,
            micro_result=micro_result,
            analyzed_at=analyzed_at,
        )

        # Enhanced Insights 추가
        report['key_insights'] = key_insights

        return report

    except Exception as e:
        return {
            'error': f'Analysis failed: {str(e)}',
            'stock_code': stock_code,
        }


def analyze_with_custom_params(stock_code: str, **kwargs) -> Dict:
    """
    커스텀 파라미터로 분석 (웹 UI용)

    Args:
        stock_code: 종목코드
        **kwargs: 파라미터 오버라이드
            - bbwp_threshold: BBWP 임계값
            - bbwp_consecutive_days: 연속 일수
            - pullback_max_pct: 고점대비 최대 하락%
            - rally_min_pct: 60일 최소 상승%
            - range_threshold_pct: 타입2 Range 임계%
            - volume_ratio: 거래량 비율
            - adx_threshold: ADX 임계값
            - volume_threshold: 거래대금 임계값 (Enhanced)
            - rally_pct: 상승률 임계값 (Enhanced)
            - bb_period: 볼린저 밴드 기간 (Enhanced)
            - bb_std: 볼린저 밴드 표준편차 (Enhanced)
            - bb_squeeze_pct: 밴드폭 임계값 (Enhanced)

    Returns:
        AnalysisReport dict
    """
    # 파라미터 분류
    type1_keys = ['bbwp_threshold', 'bbwp_consecutive_days', 'pullback_max_pct', 'rally_min_pct']
    type2_keys = ['range_threshold_pct', 'volume_ratio', 'adx_threshold']
    micro_keys = ['sideways_bars', 'sideways_range_pct']
    enhanced_keys = ['volume_threshold', 'rally_pct', 'bb_period', 'bb_std', 'bb_squeeze_pct']

    type1_params = {k: v for k, v in kwargs.items() if k in type1_keys}
    type2_params = {k: v for k, v in kwargs.items() if k in type2_keys}
    micro_params = {k: v for k, v in kwargs.items() if k in micro_keys}
    enhanced_params = {k: v for k, v in kwargs.items() if k in enhanced_keys}

    params = {}
    if type1_params:
        params['type1'] = type1_params
    if type2_params:
        params['type2'] = type2_params
    if micro_params:
        params['micro'] = micro_params

    # Enhanced params를 루트 레벨에 추가
    params.update(enhanced_params)

    return analyze(stock_code, params=params)
