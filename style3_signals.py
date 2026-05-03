"""
Style3 발라먹기 매매 — 시그널 감지 유틸리티

web_app.py (백테스트/수동 체크)와 price_monitor.py (실시간 폴링) 공유.
"""
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional, Tuple


def count_weak_bars(bars_slice: List[Dict]) -> int:
    """거감봉(거래량 감소 약세봉) 연속 카운트 (최신봉부터 역순).
    - 음봉(close < open) + 거래량 < 평균 50%
    - 양봉이어도 거래량 < 평균 45% 이면 포함
    """
    if not bars_slice:
        return 0
    vol_avg = sum(b['volume'] for b in bars_slice) / len(bars_slice)
    count = 0
    for b in reversed(bars_slice):
        is_bearish = b['close'] < b['open']
        is_weak_vol = b['volume'] < vol_avg * 0.50
        if (is_bearish and is_weak_vol) or (is_weak_vol and b['volume'] < vol_avg * 0.45):
            count += 1
        else:
            break
    return count


def find_double_bottom(bars_slice: List[Dict], tolerance: float = 0.04) -> Optional[Tuple]:
    """쌍바닥 탐지: 저점 2개가 tolerance(4%) 이내.
    반환: (저점가격, 첫번째저점날짜, 두번째저점날짜) or None
    """
    lows = [(b['low'], b['date']) for b in bars_slice if b['low'] > 0]
    if len(lows) < 2:
        return None
    min_low = min(lows, key=lambda x: x[0])
    base = min_low[0]
    bottoms = [(v, d) for v, d in lows if v <= base * (1 + tolerance)]
    if len(bottoms) >= 2:
        bottoms_sorted = sorted(bottoms, key=lambda x: x[1])
        return (base, bottoms_sorted[0][1], bottoms_sorted[-1][1])
    return None


def is_overheat_period(exit_date_str: str, reference_date: Optional[date] = None) -> bool:
    """exit_date 이후 3거래일 내이면 True (단기과열 억제).
    거래일 = 주말 제외 단순 계산 (공휴일 미처리).
    """
    if not exit_date_str:
        return False
    try:
        exit_dt = datetime.strptime(exit_date_str, '%Y-%m-%d').date()
    except ValueError:
        return False
    today = reference_date or date.today()
    # exit_date 이후 3거래일 계산
    trading_days = 0
    cursor = exit_dt
    while cursor < today:
        cursor += timedelta(days=1)
        if cursor.weekday() < 5:  # 월~금
            trading_days += 1
    return trading_days <= 3


def calc_c2_support(daily_bars: List[Dict], exit_date_str: str) -> Optional[float]:
    """exit_date 이후 일봉에서 쌍바닥 지지가 계산.
    반환: entry_price (지지가 * 1.005) or None
    """
    exit_compact = exit_date_str.replace('-', '') if exit_date_str else ''
    after_exit = [b for b in daily_bars if b['date'] > exit_compact] if exit_compact else daily_bars
    if len(after_exit) < 2:
        return None
    result = find_double_bottom(after_exit[-8:], tolerance=0.04)
    if result:
        bottom_price = result[0]
        return int(bottom_price * 1.005)
    return None


def _fmt_time(raw: str) -> str:
    """HHMMSS → HH:MM 변환."""
    if not raw or len(raw) < 4:
        return raw or ''
    return f"{raw[:2]}:{raw[2:4]}"


def scan_style3_signals(
    bars: List[Dict],
    buy_price: float,
    exit_price: float,
    support_price: Optional[float] = None,
) -> List[Dict]:
    """3분봉 배열에서 Style3 시그널 탐지.
    bars: 시간 오름차순 (oldest→newest), 각 bar에 'time'(HHMMSS) 필드 있음
    반환: 시그널 리스트 [{type, signal_time, entry_price, support_price, confidence, reason}, ...]
    """
    if len(bars) < 3:
        return []

    last = bars[-1]
    prev = bars[:-1]
    vol_avg = sum(b['volume'] for b in prev) / max(len(prev), 1)
    close = last['close']
    if not close:
        return []

    signal_time = _fmt_time(str(last.get('time', '')))
    found = []

    # Type A: 현재가 ≤ 매수가 × 1.03
    if close <= buy_price * 1.03:
        found.append({
            'type': 'A',
            'signal_time': signal_time,
            'entry_price': close,
            'support_price': 0,
            'confidence': 'M',
            'reason': f"현재가({close:,}원) ≤ 매수가({int(buy_price):,}원) 존 터치",
        })

    # Type C2: 쌍바닥 지지 터치 (support_price 미리 계산된 값 사용)
    if support_price and abs(close - support_price) / support_price < 0.008:
        # 쌍바닥 지지가가 익절가 ±2% 이내이면 "익절가 지지" 프리미엄 시그널
        near_exit = (exit_price and abs(support_price - exit_price) / exit_price <= 0.02)
        c2_confidence = 'H+' if near_exit else 'H'
        near_exit_note = f" ★ 익절가({int(exit_price):,}원) 근처 지지 — 강한 지지선" if near_exit else ""
        found.append({
            'type': 'C2',
            'signal_time': signal_time,
            'entry_price': close,
            'support_price': support_price,
            'confidence': c2_confidence,
            'reason': f"쌍바닥 지지선({int(support_price):,}원) 터치 확인 — 현재가 {close:,}원{near_exit_note}",
        })

    # Type C1: 거감봉 진행 중
    is_weak_vol = last['volume'] < vol_avg * 0.50
    is_bearish = close < last.get('open', close)
    if is_weak_vol and is_bearish:
        found.append({
            'type': 'C1',
            'signal_time': signal_time,
            'entry_price': close,
            'support_price': 0,
            'confidence': 'L',
            'reason': f"거감봉 진행 중 (거래량 {last['volume']:,} / 평균 {int(vol_avg):,}, {last['volume']/vol_avg:.1f}배)",
        })

    # Type C3: 거래량 급증 양봉 (재상승)
    is_vol_up = last['volume'] > vol_avg * 1.8
    is_bullish = close >= last.get('open', close)
    if is_vol_up and is_bullish:
        found.append({
            'type': 'C3',
            'signal_time': signal_time,
            'entry_price': last.get('open', close),
            'support_price': support_price or 0,
            'confidence': 'H' if last['volume'] > vol_avg * 3.0 else 'M',
            'reason': f"거래량 급증 양봉 ({last['volume']:,} / 평균대비 {last['volume']/vol_avg:.1f}배) — 재상승 시작",
        })

    # Type B: 익절가 5%+ 돌파 (기록용)
    if exit_price and close > exit_price * 1.05:
        found.append({
            'type': 'B',
            'signal_time': signal_time,
            'entry_price': int(exit_price * 1.01),
            'support_price': 0,
            'confidence': 'M',
            'reason': f"익절가({int(exit_price):,}원) +{(close/exit_price-1)*100:.0f}% 돌파 — 기록용",
        })

    return found
