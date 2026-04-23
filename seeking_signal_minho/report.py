"""
최종 리포트 조립 및 판정
"""
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np


def convert_to_native_types(obj):
    """NumPy/Pandas 타입을 Python 네이티브 타입으로 변환 (JSON 직렬화용)"""
    if isinstance(obj, dict):
        return {k: convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_to_native_types(item) for item in obj]
    elif isinstance(obj, (np.bool_, np.bool8)):
        return bool(obj)
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        return float(obj)
    elif isinstance(obj, (np.ndarray,)):
        return convert_to_native_types(obj.tolist())
    elif pd.isna(obj):
        return None
    else:
        return obj


def assemble_report(stock_code: str, stock_info: dict, daily_df: pd.DataFrame,
                   type1_result: dict, type2_result: dict,
                   volume_spike: dict, micro_result: dict,
                   analyzed_at: str) -> Dict:
    """
    최종 분석 리포트 조립

    Args:
        stock_code: 종목코드
        stock_info: 종목 기본정보
        daily_df: 일봉 DataFrame
        type1_result: 타입1 분석 결과
        type2_result: 타입2 분석 결과
        volume_spike: 거래대금 스파이크 결과
        micro_result: 분봉 마이크로 결과
        analyzed_at: 분석 시간

    Returns:
        AnalysisReport dict
    """
    # 메타 정보
    meta = {
        'stock_code': stock_code,
        'stock_name': stock_info.get('stk_nm', ''),
        'base_date': daily_df['dt'].iloc[-1].strftime('%Y%m%d') if not daily_df.empty else '',
        'market_cap_won': float(stock_info.get('mac', 0)),  # 억원
        'current_price': float(stock_info.get('cur_prc', 0)),
        'analyzed_at': analyzed_at,
    }

    # dominant_type 판정
    t1_applicable = type1_result.get('applicable', False)
    t2_applicable = type2_result.get('applicable', False)

    if t1_applicable and t2_applicable:
        dominant_type = 'both'
    elif t1_applicable:
        dominant_type = 'type1'
    elif t2_applicable:
        dominant_type = 'type2'
    else:
        dominant_type = 'none'

    # 매크로 분석
    macro = {
        'type1': type1_result,
        'type2': type2_result,
        'dominant_type': dominant_type,
    }

    # verdict 및 summary 생성
    verdict, confidence = decide_verdict(type1_result, type2_result, volume_spike, micro_result)
    summary = generate_summary(verdict, confidence, type1_result, type2_result,
                              volume_spike, micro_result, daily_df)

    # 원시 데이터
    raw = extract_raw_data(daily_df)

    report = {
        'meta': meta,
        'macro': macro,
        'volume_spike': volume_spike,
        'micro': micro_result,
        'summary': summary,
        'raw': raw,
    }

    # NumPy/Pandas 타입을 Python 네이티브 타입으로 변환 (JSON 직렬화용)
    return convert_to_native_types(report)


def decide_verdict(type1_result: dict, type2_result: dict,
                  volume_spike: dict, micro_result: dict) -> Tuple[str, float]:
    """
    종합 판정 (buyable / watch / avoid)

    Args:
        type1_result: 타입1 결과
        type2_result: 타입2 결과
        volume_spike: 거래대금 스파이크
        micro_result: 분봉 마이크로

    Returns:
        (verdict, confidence)
    """
    score = 0
    total = 0

    # [타입1 점수] (최대 5점)
    t1 = type1_result
    if t1.get('applicable'):
        total += 5
        if t1.get('ma_position', {}).get('above_5_8'):
            score += 1
        if t1.get('ma_position', {}).get('above_15'):
            score += 1
        if t1.get('ma_position', {}).get('rebound_zone'):
            score += 1
        if t1.get('is_sideways'):
            score += 2

    # [타입2 점수] (최대 4점)
    t2 = type2_result
    if t2.get('applicable'):
        total += 4
        if t2.get('is_sideways'):
            score += 3
        if t2.get('criteria_hits', {}).get('volume_dried'):
            score += 1

    # [거래대금 스파이크] (최대 3점)
    total += 3
    q = volume_spike.get('signal_quality', 'dead')
    if q == 'imminent':
        score += 3
    elif q == 'watch':
        score += 1

    # [분봉 추세] (최대 2점)
    if micro_result:
        total += 2
        if micro_result.get('today_trend', {}).get('alive'):
            score += 1
        if micro_result.get('above_120min_trend'):
            score += 1

    # 비율 계산
    ratio = score / total if total > 0 else 0

    if ratio >= 0.7:
        return 'buyable', ratio
    if ratio >= 0.4:
        return 'watch', ratio
    return 'avoid', ratio


def generate_summary(verdict: str, confidence: float,
                    type1_result: dict, type2_result: dict,
                    volume_spike: dict, micro_result: dict,
                    daily_df: pd.DataFrame) -> Dict:
    """
    사람이 읽는 요약 생성

    Returns:
        summary dict with verdict, confidence, key_signals, risks
    """
    key_signals = []
    risks = []

    # 타입1 신호
    t1 = type1_result
    if t1.get('applicable'):
        rally = t1.get('metrics', {}).get('rally_60d_pct', 0)
        pullback = t1.get('metrics', {}).get('pullback_from_60d_high_pct', 0)
        key_signals.append(f"타입1 후보: 60일 상승 +{rally:.1f}% 후 -{pullback:.1f}% 눌림")

        if t1.get('is_sideways'):
            bbwp = t1.get('metrics', {}).get('bbwp_today', 0)
            key_signals.append(f"BBWP {bbwp:.1f} → 변동성 수축 중")

        if not t1.get('ma_position', {}).get('above_15'):
            risks.append("15일선 이탈 — 당일 종가 중요")

    # 타입2 신호
    t2 = type2_result
    if t2.get('applicable'):
        range_pct = t2.get('metrics', {}).get('range_pct_20d', 0)
        key_signals.append(f"타입2 후보: 20일 변동폭 {range_pct:.1f}% (횡보 중)")

        if t2.get('is_sideways'):
            key_signals.append("타입2 횡보 확정 (224선 아래 + 거래량 감소)")

    # 거래대금 스파이크
    vs = volume_spike
    days_strong = vs.get('days_ago_strong')
    if days_strong is not None:
        if vs['signal_quality'] == 'imminent':
            key_signals.append(f"강한 거래대금 {days_strong}일 전 발생 → 돌파 임박")
        elif vs['signal_quality'] == 'watch':
            key_signals.append(f"강한 거래대금 {days_strong}일 전 발생 → 관망")
    else:
        risks.append("최근 거래대금 스파이크 없음")

    # 분봉 추세
    if micro_result:
        sideways = micro_result.get('three_min_sideways')
        if sideways and sideways.get('is_sideways'):
            range_pct = sideways.get('range_pct', 0)
            key_signals.append(f"3분봉 최근 30분 {range_pct:.1f}% 횡보 중")

        today_trend = micro_result.get('today_trend', {})
        if today_trend.get('alive'):
            key_signals.append("분봉 추세 살아있음 (시가/전일종가 위)")

        if not micro_result.get('above_120min_trend'):
            risks.append("120분봉 추세선 이탈")

    return {
        'verdict': verdict,
        'confidence': round(confidence, 2),
        'key_signals': key_signals,
        'risks': risks,
    }


def extract_raw_data(daily_df: pd.DataFrame) -> Dict:
    """
    원시 데이터 추출 (디버깅/차트용)

    Args:
        daily_df: 일봉 DataFrame

    Returns:
        raw data dict
    """
    if daily_df.empty:
        return {}

    # 최근 10일 OHLCV
    last_10 = daily_df.tail(10).to_dict('records')

    # 최신 일자의 MA 값
    current = daily_df.iloc[-1]
    ma_today = {
        col: float(current[col]) if pd.notna(current[col]) else None
        for col in daily_df.columns if col.startswith('ma')
    }

    # 최신 지표
    indicators_today = {}
    for col in ['atr14', 'adx14', 'bbwp', 'bbw']:
        if col in daily_df.columns:
            indicators_today[col] = float(current[col]) if pd.notna(current[col]) else None

    # 최근 10일의 각 이평선 값 추출 (차트용)
    ma_history = {}
    for col in daily_df.columns:
        if col.startswith('ma'):
            ma_values = daily_df[col].tail(10).tolist()
            ma_history[col] = [float(v) if pd.notna(v) else None for v in ma_values]

    return {
        'daily_last_10': last_10,
        'ma_today': ma_today,
        'ma_history': ma_history,  # 추가: 차트 오버레이용
        'indicators_today': indicators_today,
    }
