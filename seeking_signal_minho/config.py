"""
설정 및 상수 정의
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# 키움 API 설정
KIWOOM_APP_KEY = os.getenv('KIWOOM_APPKEY')
KIWOOM_SECRET_KEY = os.getenv('KIWOOM_SECRETKEY')
KIWOOM_BASE_URL = os.getenv('KIWOOM_HOST', 'https://api.kiwoom.com')

# 조회 기간 설정
DAILY_LOOKBACK_DAYS = 260          # 일봉 조회 최소 일수 (224일선 + 여유)
MINUTE_3_LOOKBACK = 120            # 3분봉 조회 개수 (약 6시간)
MINUTE_60_LOOKBACK = 40            # 60분봉 조회 개수 (약 1주일)

# 캐시 설정
CACHE_DIR = Path(__file__).parent.parent / '.data' / 'cache'
CACHE_TTL_DAYS = 5                 # 캐시 TTL (5일)

# 타입1 기본 파라미터
TYPE1_DEFAULTS = {
    'bbwp_threshold': 25,           # BBWP 임계값
    'bbwp_consecutive_days': 5,     # 연속 일수
    'pullback_max_pct': 15,         # 고점대비 최대 하락%
    'rally_min_pct': 20,            # 60일 최소 상승%
}

# 타입2 기본 파라미터
TYPE2_DEFAULTS = {
    'range_threshold_pct': 7,       # 20일 변동폭 임계%
    'volume_ratio': 0.5,            # 거래량 비율
    'adx_threshold': 20,            # ADX 임계값
}

# 분봉 마이크로 파라미터
MICRO_DEFAULTS = {
    'sideways_bars': 10,            # 3분봉 횡보 판정 봉 개수
    'sideways_range_pct': 1.0,      # 횡보 범위 임계%
}

# 시총 구간별 거래대금 임계값 (단위: 원)
# 각 구간: (시총 상한(억원), 관심 거래대금(원), 강한 신호 거래대금(원))
VOLUME_THRESHOLDS = [
    (1_000,       30_0000_0000,    80_0000_0000),   # ~1천억
    (2_000,       50_0000_0000,   150_0000_0000),   # 1~2천억
    (5_000,      100_0000_0000,   300_0000_0000),   # 2~5천억
    (20_000,     200_0000_0000,   500_0000_0000),   # 5천억~2조
    (float('inf'), 500_0000_0000, 1_500_0000_0000), # 2조 이상
]

# 이동평균선 윈도우
MA_WINDOWS_TYPE1 = [5, 8, 15, 33, 45, 60]
MA_WINDOWS_TYPE2 = [100, 224]
MA_WINDOWS_ALL = [3, 5, 8, 10, 15, 33, 45, 60, 100, 224]  # 3일선, 10일선 추가
