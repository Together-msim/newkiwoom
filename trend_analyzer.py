"""
추세 분석 유틸리티
분봉 데이터를 분석하여 추세 전환을 감지합니다.
"""
from typing import List, Dict, Any


def is_bullish(candle: Dict[str, Any]) -> bool:
    """
    양봉 판단: 종가 > 시가

    Args:
        candle: {"open": float, "close": float, ...}

    Returns:
        True if bullish candle
    """
    open_price = float(candle.get("open", 0))
    close_price = float(candle.get("close", 0))
    return close_price > open_price


def is_bearish(candle: Dict[str, Any]) -> bool:
    """
    음봉 판단: 종가 < 시가

    Args:
        candle: {"open": float, "close": float, ...}

    Returns:
        True if bearish candle
    """
    open_price = float(candle.get("open", 0))
    close_price = float(candle.get("close", 0))
    return close_price < open_price


def count_consecutive_candles(candles: List[Dict[str, Any]], trend: str, from_end: bool = True) -> int:
    """
    연속 양봉/음봉 개수 카운트

    Args:
        candles: 분봉 리스트 (시간 순서대로 정렬된 상태)
        trend: "상승" or "하락"
        from_end: True이면 최신 봉부터 역순으로 카운트 (기본값)

    Returns:
        연속된 봉 개수
    """
    if not candles:
        return 0

    check_func = is_bullish if trend == "상승" else is_bearish
    count = 0

    # 최신 봉부터 역순으로 체크
    if from_end:
        for candle in reversed(candles):
            if check_func(candle):
                count += 1
            else:
                break
    # 오래된 봉부터 순방향으로 체크
    else:
        for candle in candles:
            if check_func(candle):
                count += 1
            else:
                break

    return count


def check_condition_satisfied(candles: List[Dict[str, Any]], trend: str, required_count: int) -> bool:
    """
    조건 만족 여부 체크

    Args:
        candles: 분봉 리스트
        trend: "상승" or "하락"
        required_count: 요구되는 연속 봉 개수

    Returns:
        True if condition is satisfied
    """
    consecutive_count = count_consecutive_candles(candles, trend, from_end=True)
    return consecutive_count >= required_count


def format_candles_summary(candles: List[Dict[str, Any]], limit: int = 5) -> str:
    """
    최신 N개 봉 요약 (디버깅용)

    Args:
        candles: 분봉 리스트
        limit: 표시할 봉 개수

    Returns:
        포맷팅된 문자열
    """
    if not candles:
        return "봉 데이터 없음"

    recent = candles[-limit:] if len(candles) > limit else candles
    lines = []

    for candle in recent:
        time = candle.get("time", "")
        open_price = candle.get("open", 0)
        close_price = candle.get("close", 0)

        if is_bullish(candle):
            trend_icon = "🔴"  # 양봉
            trend_text = "상승"
        elif is_bearish(candle):
            trend_icon = "🔵"  # 음봉
            trend_text = "하락"
        else:
            trend_icon = "⚪"  # 도지
            trend_text = "도지"

        lines.append(f"{trend_icon} {time} {trend_text} (O:{open_price:.0f} C:{close_price:.0f})")

    return "\n".join(lines)
