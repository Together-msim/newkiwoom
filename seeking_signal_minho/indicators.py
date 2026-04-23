"""
기술적 지표 계산 (MA, ATR, ADX, BB, BBWP)
"""
import pandas as pd
import numpy as np


def add_moving_averages(df: pd.DataFrame, windows: list[int],
                       price_col: str = 'cur_prc') -> pd.DataFrame:
    """
    이동평균선 추가

    Args:
        df: 일봉 DataFrame
        windows: 이동평균선 기간 리스트 (예: [5, 8, 15, 33, 45, 60, 100, 224])
        price_col: 가격 컬럼명

    Returns:
        ma{window} 컬럼이 추가된 DataFrame
    """
    out = df.copy()
    for w in windows:
        out[f'ma{w}'] = out[price_col].rolling(window=w).mean()
    return out


def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    ATR (Average True Range) 추가

    Args:
        df: 일봉 DataFrame
        period: ATR 기간 (기본 14)

    Returns:
        atr{period} 컬럼이 추가된 DataFrame
    """
    out = df.copy()
    high = out['high_pric']
    low = out['low_pric']
    close = out['cur_prc']

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)

    out[f'atr{period}'] = tr.rolling(period).mean()
    return out


def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """
    ADX (Average Directional Index) 추가 - Wilder 방식

    Args:
        df: 일봉 DataFrame
        period: ADX 기간 (기본 14)

    Returns:
        adx{period} 컬럼이 추가된 DataFrame
    """
    out = df.copy()
    high = out['high_pric']
    low = out['low_pric']
    close = out['cur_prc']

    # +DM, -DM 계산
    up = high.diff()
    down = -low.diff()
    plus_dm = np.where((up > down) & (up > 0), up, 0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)

    # True Range
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)

    # ATR
    atr = tr.rolling(period).mean()

    # +DI, -DI
    plus_di = 100 * pd.Series(plus_dm, index=df.index).rolling(period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr

    # DX
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)

    # ADX
    out[f'adx{period}'] = dx.rolling(period).mean()

    return out


def add_bbwp(df: pd.DataFrame, bb_period: int = 20, bb_std: float = 2.0,
            percentile_window: int = 126) -> pd.DataFrame:
    """
    볼린저밴드 폭(BBW) 및 BBWP(Bollinger Band Width Percentile) 추가

    Args:
        df: 일봉 DataFrame
        bb_period: 볼린저밴드 기간 (기본 20)
        bb_std: 표준편차 배수 (기본 2.0)
        percentile_window: 백분위 계산 기간 (기본 126일 = 약 6개월)

    Returns:
        bbw, bbwp 컬럼이 추가된 DataFrame
    """
    out = df.copy()
    close = out['cur_prc']

    # 볼린저밴드 계산
    ma = close.rolling(bb_period).mean()
    sd = close.rolling(bb_period).std()

    # BBW: (상단밴드 - 하단밴드) / 중간밴드 * 100
    bbw = (2 * bb_std * sd) / ma * 100
    out['bbw'] = bbw

    # BBWP: 최근 126일 중 백분위 (0~100)
    out['bbwp'] = bbw.rolling(percentile_window).rank(pct=True) * 100

    return out


def add_all_indicators(df: pd.DataFrame, ma_windows: list[int]) -> pd.DataFrame:
    """
    모든 지표를 한 번에 추가

    Args:
        df: 일봉 DataFrame
        ma_windows: 이동평균선 기간 리스트

    Returns:
        모든 지표가 추가된 DataFrame
    """
    df = add_moving_averages(df, ma_windows)
    df = add_atr(df, period=14)
    df = add_adx(df, period=14)
    df = add_bbwp(df, bb_period=20, bb_std=2.0, percentile_window=126)
    return df
