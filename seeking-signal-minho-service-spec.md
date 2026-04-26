# Seeking Signal Minho — 단일 종목 분석 모듈 개발 명세서

> **목적**: 단일 종목코드(6자리)를 입력받아 키움 REST API를 호출하고,
> 일봉 매크로(타입1 / 타입2) + 분봉 마이크로 판단을 수행한 뒤
> 구조화된 분석 리포트(JSON + 사람이 읽는 요약)를 반환하는 Python 모듈을 구현한다.
>
> **대상**: Claude Code (본 문서를 그대로 프롬프트/컨텍스트로 사용)
> **입력**: `stock_code: str` (예: `"005930"`)
> **출력**: `AnalysisReport` (dict, 스키마는 §7 참조)

---

## 0. 작업 범위 및 비포함 사항

### 포함
- 키움 REST API (`ka10001`, `ka10081`, `ka10080`) 호출 래퍼
- 이동평균선, ATR, ADX, 볼린저밴드, BBWP 등 모든 기술 지표 **직접 계산**
- 타입1 / 타입2 횡보 판정 로직
- 거래대금 스파이크 탐지 (시총 구간별 계단식 임계값)
- 분봉(3분/60분) 기반 마이크로 추세 판단
- 최종 종합 리포트 생성

### 비포함 (이번 작업 아님)
- 종목명 → 종목코드 변환 (이미 구현됨, 입력으로 6자리 코드가 들어온다고 가정)
- OCR / 이미지 처리
- 웹서비스 레이어(FastAPI 등) — 순수 파이썬 함수로만 작성
- 실제 주문 집행 (조회만)
- 백테스팅 프레임워크

---

## 1. 기술 스택 / 의존성

```
python >= 3.10
pandas >= 2.0
numpy >= 1.24
requests >= 2.31
pydantic >= 2.0      # 응답 스키마 검증용 (선택)
python-dotenv        # 앱키/시크릿키 로드
```

설치:
```bash
pip install pandas numpy requests pydantic python-dotenv
```

---

## 2. 프로젝트 구조

```
seeking_signal_minho/
├── __init__.py
├── config.py               # 환경변수, 상수
├── auth.py                 # 접근토큰 발급/갱신 (au10001)
├── api_client.py           # 키움 REST API 호출 래퍼
├── indicators.py           # MA, ATR, ADX, BB, BBWP 계산
├── analyzers/
│   ├── __init__.py
│   ├── macro_type1.py      # 타입1 (5,8,15,33,45,60선 기반)
│   ├── macro_type2.py      # 타입2 (100,224선 기반)
│   ├── micro_minute.py     # 분봉 마이크로 판단
│   └── volume_spike.py     # 거래대금 스파이크 탐지
├── report.py               # 최종 리포트 조립
└── main.py                 # 단일 진입점: analyze(stock_code) 함수
```

---

## 3. 설정 (config.py)

```python
# 환경변수 (.env)
KIWOOM_APP_KEY = "..."
KIWOOM_SECRET_KEY = "..."
KIWOOM_BASE_URL = "https://api.kiwoom.com"        # 실전
# KIWOOM_BASE_URL = "https://mockapi.kiwoom.com"  # 모의 (KRX만 가능)

# 상수 (config.py 내부에 정의)
DAILY_LOOKBACK_DAYS = 260          # 일봉 조회 최소 일수 (224일선 + 여유)
MINUTE_3_LOOKBACK = 120            # 3분봉 조회 개수 (약 6시간)
MINUTE_60_LOOKBACK = 40            # 60분봉 조회 개수 (약 1주일)

# 시총 구간별 거래대금 임계값 (단위: 원)
# 각 구간: (시총 상한, 관심 거래대금, 강한 신호 거래대금)
VOLUME_THRESHOLDS = [
    (1_000_0000_0000,       30_0000_0000,    80_0000_0000),   # ~1천억
    (2_000_0000_0000,       50_0000_0000,   150_0000_0000),   # 1~2천억
    (5_000_0000_0000,      100_0000_0000,   300_0000_0000),   # 2~5천억
    (20_000_0000_0000,     200_0000_0000,   500_0000_0000),   # 5천억~2조
    (float('inf'),         500_0000_0000, 1_500_0000_0000),   # 2조 이상
]
```

> ⚠️ **숫자 리터럴 주의**: 파이썬에서 `1_000_0000_0000`은 1조 원. 언더스코어는 가독성용. 꼭 단위 테스트로 검증할 것.

---

## 4. 키움 REST API 래퍼 (api_client.py)

### 4.1 공통 호출 규격

- **Method**: `POST`
- **URL**: `{BASE_URL}/api/dostk/{카테고리}` (차트는 `/api/dostk/chart`, 기본정보는 `/api/dostk/stkinfo` 등)
- **Headers** (공통):
  ```python
  {
      'Content-Type': 'application/json;charset=UTF-8',
      'authorization': f'Bearer {access_token}',
      'cont-yn': 'N',       # 연속조회 여부
      'next-key': '',       # 연속조회 키
      'api-id': 'ka10081',  # TR명
  }
  ```
- **연속조회**: 응답 헤더 `cont-yn == 'Y'`면 `next-key`를 다음 요청에 세팅

### 4.2 필요한 API 3종 스펙

#### (A) `au10001` — 접근토큰 발급
- **URL**: `POST /oauth2/token`
- **Body**:
  ```json
  { "grant_type": "client_credentials",
    "appkey": "...", "secretkey": "..." }
  ```
- **Response**: `token`, `token_type`, `expires_dt`(YYYYMMDDHHMMSS)
- **캐싱**: 메모리에 `(token, expires_dt)` 저장, 만료 5분 전 자동 재발급

#### (B) `ka10001` — 주식기본정보요청
- **URL**: `POST /api/dostk/stkinfo`
- **Body**: `{"stk_cd": "005930"}` (또는 `"005930_NX"` 등 거래소 접미사)
- **사용 필드**:
  - `cur_prc` (현재가), `open_pric` (시가), `high_pric` (고가), `low_pric` (저가)
  - `base_pric` (전일종가)
  - `mac` (시가총액, 단위 확인 필요 — 보통 억원)
  - `stk_nm` (종목명)

#### (C) `ka10081` — 주식일봉차트조회
- **URL**: `POST /api/dostk/chart`
- **Body**:
  ```json
  { "stk_cd": "005930",
    "base_dt": "20260422",    // 조사 당일 (YYYYMMDD)
    "upd_stkpc_tp": "1" }     // 수정주가 반드시 1
  ```
- **Response 리스트 필드**: `stk_dt_pole_chart_qry[]`
  - `dt`, `open_pric`, `high_pric`, `low_pric`, `cur_prc`(=종가),
    `trde_qty`, `trde_prica`
- **주의**: 한 번 호출당 몇 일치 주는지 문서에 미명시 →
  **260일 확보될 때까지 연속조회 루프**

#### (D) `ka10080` — 주식분봉차트조회
- **URL**: `POST /api/dostk/chart`
- **Body**:
  ```json
  { "stk_cd": "005930",
    "tic_scope": "3",         // 3 또는 60만 사용 (120은 불가)
    "upd_stkpc_tp": "1" }
  ```
- **`tic_scope` 허용값**: `1, 3, 5, 10, 15, 30, 45, 60` (최대 60분)
- **⚠️ 120분봉은 직접 조회 불가** → 60분봉을 받아 `pandas.resample('120min')` 으로 합성
- **Response 리스트 필드**: `stk_min_pole_chart_qry[]`
  - `cntr_tm` (체결시간 YYYYMMDDHHMMSS),
    `open_pric`, `high_pric`, `low_pric`, `cur_prc`, `trde_qty`

### 4.3 래퍼 함수 시그니처

```python
class KiwoomClient:
    def __init__(self, app_key: str, secret_key: str, base_url: str): ...

    def _ensure_token(self) -> str: ...           # 내부 토큰 자동 관리

    def get_stock_info(self, stock_code: str) -> dict:
        """ka10001. 시가총액, 현재가, 종목명 등 반환."""

    def get_daily_chart(self, stock_code: str,
                        base_dt: str,
                        min_days: int = 260) -> pd.DataFrame:
        """ka10081. 연속조회로 min_days 이상 확보하여 DataFrame 반환.
        컬럼: dt(datetime), open_pric, high_pric, low_pric, cur_prc,
              trde_qty, trde_prica (모두 numeric)
        정렬: 날짜 오름차순, 인덱스 reset"""

    def get_minute_chart(self, stock_code: str,
                         tic_scope: int,
                         min_bars: int = 120) -> pd.DataFrame:
        """ka10080. 컬럼: cntr_tm(datetime), open_pric, high_pric,
        low_pric, cur_prc, trde_qty. 시간 오름차순 정렬."""
```

### 4.4 데이터 정제 필수 규칙
1. 키움 응답의 숫자 필드는 **모두 String**으로 내려옴 → `pd.to_numeric(errors='coerce')`로 변환
2. 가격 필드는 종종 **음수 부호(`-`)** 가 붙어서 내려올 수 있음(전일대비 표시용 관습) → `.abs()` 적용
3. `dt` / `cntr_tm`은 `pd.to_datetime` 으로 변환
4. 연속조회 루프에서 `time.sleep(0.25)` 삽입 (Rate limit 방어)

---

## 5. 기술 지표 계산 (indicators.py)

### 5.1 이동평균선 (SMA)

```python
def add_moving_averages(df: pd.DataFrame,
                        windows: list[int],
                        price_col: str = 'cur_prc') -> pd.DataFrame:
    """df에 ma{window} 컬럼 추가. 원본을 변형하지 말고 copy 반환."""
    out = df.copy()
    for w in windows:
        out[f'ma{w}'] = out[price_col].rolling(window=w).mean()
    return out
```

**타입1용 windows**: `[5, 8, 15, 33, 45, 60]`
**타입2용 windows**: `[100, 224]`
**한 번에 전부 계산 권장**: `[5, 8, 15, 33, 45, 60, 100, 224]`

### 5.2 ATR (14)

```python
def add_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = df.copy()
    high, low, close = out['high_pric'], out['low_pric'], out['cur_prc']
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)
    out[f'atr{period}'] = tr.rolling(period).mean()
    return out
```

### 5.3 ADX (14) — Wilder 방식

```python
def add_adx(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    out = df.copy()
    high, low, close = out['high_pric'], out['low_pric'], out['cur_prc']

    up = high.diff()
    down = -low.diff()
    plus_dm  = np.where((up > down) & (up > 0),   up,   0.0)
    minus_dm = np.where((down > up) & (down > 0), down, 0.0)

    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low - close.shift()).abs(),
    ], axis=1).max(axis=1)

    atr = tr.rolling(period).mean()
    plus_di  = 100 * pd.Series(plus_dm,  index=df.index).rolling(period).mean() / atr
    minus_di = 100 * pd.Series(minus_dm, index=df.index).rolling(period).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    out[f'adx{period}'] = dx.rolling(period).mean()
    return out
```

### 5.4 볼린저밴드 폭 & BBWP

```python
def add_bbwp(df: pd.DataFrame,
             bb_period: int = 20,
             bb_std: float = 2.0,
             percentile_window: int = 126) -> pd.DataFrame:
    """BBW: 밴드폭(%).  BBWP: 최근 126일 중 백분위(0~100)."""
    out = df.copy()
    close = out['cur_prc']
    ma = close.rolling(bb_period).mean()
    sd = close.rolling(bb_period).std()
    bbw = (2 * bb_std * sd) / ma * 100
    out['bbw'] = bbw
    out['bbwp'] = bbw.rolling(percentile_window).rank(pct=True) * 100
    return out
```

---

## 6. 분석 로직

### 6.1 타입1 판정 (analyzers/macro_type1.py)

**대상 종목 조건**: 최근 강한 상승 후 눌림/숨고르기 중인 종목

**입력**: 일봉 DataFrame (260일 이상, `ma5, ma8, ma15, ma33, ma45, ma60, bbwp, adx14` 포함)

**판정 항목** (모두 개별 bool 반환):

| 코드 | 판정명 | 로직 |
|---|---|---|
| T1.A | `above_5_8` | 현재가 > ma5 AND 현재가 > ma8 |
| T1.B | `above_15` | 현재가 > ma15 |
| T1.C | `rebound_zone` | 현재가 < ma15 AND 현재가 > ma33 AND 현재가 > ma45 AND 현재가 > ma60 |
| T1.D | `had_strong_rally_60d` | 최근 60일 고가 ≥ 60일 전 종가 × 1.20 |
| T1.E | `near_recent_high` | (60일 고가 - 현재가) / 60일 고가 ≤ 0.15 |
| T1.F | `bb_squeeze_sustained` | 최근 5일 연속 bbwp ≤ 25 |

**정배열/역배열 판정**:
```python
ma_list = [df['ma5'].iloc[-1], df['ma8'].iloc[-1], df['ma15'].iloc[-1],
           df['ma33'].iloc[-1], df['ma45'].iloc[-1], df['ma60'].iloc[-1]]
is_perfect_bull = all(a > b for a, b in zip(ma_list, ma_list[1:]))
is_perfect_bear = all(a < b for a, b in zip(ma_list, ma_list[1:]))
```

**최종 타입1 횡보 판정**:
```python
is_type1_sideways = T1.D and T1.E and T1.F
# 즉: 강한 상승 있었고 + 고점 근처 + 변동성 수축 5일 연속
```

**반환값 (dict)**:
```python
{
    'type': 'type1',
    'applicable': is_type1_candidate,     # 이 종목이 타입1로 볼 수 있는가
    'is_sideways': is_type1_sideways,     # 타입1 횡보 중인가
    'ma_position': {
        'above_5_8': bool,
        'above_15': bool,
        'rebound_zone': bool,
    },
    'ma_values_sorted': [('ma5', 70000), ('ma8', 69500), ...],  # 가격 내림차순
    'is_perfect_bull': bool,
    'is_perfect_bear': bool,
    'metrics': {
        'bbwp_today': float,
        'bbwp_last_5d_max': float,
        'pullback_from_60d_high_pct': float,
        'rally_60d_pct': float,
    }
}
```

### 6.2 타입2 판정 (analyzers/macro_type2.py)

**대상 종목 조건**: 오랫동안 주목받지 못하고 답보 중인 종목

**입력**: 일봉 DataFrame (260일 이상, `ma100, ma224, adx14` 포함)

**판정 항목**:

| 코드 | 판정명 | 로직 |
|---|---|---|
| T2.A | `below_224_above_100` | 현재가 < ma224 AND 현재가 > ma100 |
| T2.B | `tight_range_20d` | 최근 20영업일 (고가 max - 저가 min) / 중간값 × 100 ≤ **7%** |
| T2.C | `volume_dried` | 최근 20일 거래량 평균 ≤ 과거 100일 거래량 평균 × 0.5 |
| T2.D | `no_trend` | adx14 < 20 |

**최종 타입2 횡보 판정**:
```python
is_type2_sideways = T2.A and T2.B and T2.C and T2.D
```

> 💬 **사용자 원안의 3%는 한국 주식 특성상 거의 잡히지 않아 7%로 조정됨**. 사용자가 원하면 `TYPE2_RANGE_THRESHOLD_PCT` 상수로 외부 조정 가능하게 작성할 것.

**반환값 (dict)**:
```python
{
    'type': 'type2',
    'applicable': T2.A,                    # 224밑/100위 조건 충족 시 타입2 후보
    'is_sideways': is_type2_sideways,
    'criteria_hits': {
        'below_224_above_100': bool,
        'tight_range_20d': bool,
        'volume_dried': bool,
        'no_trend': bool,
    },
    'metrics': {
        'range_pct_20d': float,
        'volume_ratio_recent_vs_longterm': float,  # 최근20/과거100 평균비율
        'adx14': float,
    }
}
```

### 6.3 거래대금 스파이크 탐지 (analyzers/volume_spike.py)

**입력**:
- 일봉 DataFrame (`trde_prica` 컬럼)
- 시가총액 (ka10001의 `mac` 필드, 단위 확인 필수)

**로직**:
```python
def find_last_volume_spike(daily_df: pd.DataFrame,
                           market_cap_won: float) -> dict:
    """시총 구간에 맞는 임계값으로 최근 스파이크 날짜 찾기."""

    # 1. 시총 구간에서 임계값 찾기
    interest_threshold, strong_threshold = None, None
    for cap_limit, interest, strong in VOLUME_THRESHOLDS:
        if market_cap_won <= cap_limit:
            interest_threshold = interest
            strong_threshold = strong
            break

    # 2. 역순으로 스파이크 찾기 (today=0일 전)
    today_idx = len(daily_df) - 1
    days_ago_interest, days_ago_strong = None, None

    for i, row in daily_df[::-1].reset_index(drop=True).iterrows():
        if days_ago_strong is None and row['trde_prica'] >= strong_threshold:
            days_ago_strong = i
        if days_ago_interest is None and row['trde_prica'] >= interest_threshold:
            days_ago_interest = i
        if days_ago_strong is not None and days_ago_interest is not None:
            break

    return {
        'market_cap_won': market_cap_won,
        'thresholds': {
            'interest': interest_threshold,
            'strong': strong_threshold,
        },
        'days_ago_interest': days_ago_interest,   # None if never
        'days_ago_strong': days_ago_strong,
        'signal_quality': _classify(days_ago_strong),  # 'imminent'|'watch'|'dead'
    }

def _classify(days_ago_strong: int | None) -> str:
    if days_ago_strong is None: return 'dead'
    if days_ago_strong <= 3:    return 'imminent'   # 돌파 임박
    if days_ago_strong <= 30:   return 'watch'      # 관망
    return 'dead'                                    # 죽은 종목
```

### 6.4 분봉 마이크로 판단 (analyzers/micro_minute.py)

**모든 종목에 공통 적용** (타입1/2 무관).

#### 입력
- 3분봉 DataFrame (120봉 = 약 6시간)
- 60분봉 DataFrame (40봉, 120분봉 합성용)
- 스냅샷 (ka10001): `cur_prc`, `open_pric`, `base_pric`(전일종가), `high_pric`, `low_pric`

#### 6.4.1 3분봉 횡보 판정
```python
def is_3min_sideways(df3: pd.DataFrame,
                     bars: int = 10,                # 최근 10봉 (30분)
                     range_threshold_pct: float = 1.0) -> dict:
    recent = df3.tail(bars)
    high_max = recent['high_pric'].max()
    low_min  = recent['low_pric'].min()
    last_close = df3['cur_prc'].iloc[-1]
    range_pct = (high_max - low_min) / last_close * 100

    # 거래량 동반 수축 조건 (진짜 횡보)
    avg_vol_today = df3['trde_qty'].mean()
    recent_vol_avg = recent['trde_qty'].mean()
    vol_contracted = recent_vol_avg <= avg_vol_today * 0.7

    return {
        'is_sideways': range_pct <= range_threshold_pct and vol_contracted,
        'range_pct': round(range_pct, 3),
        'volume_contracted': vol_contracted,
        'bars_analyzed': bars,
    }
```

#### 6.4.2 120분봉 합성 & 마이크로 추세
```python
def resample_60_to_120(df60: pd.DataFrame) -> pd.DataFrame:
    df = df60.set_index('cntr_tm').sort_index()
    # 한국장 09:00 시작 기준으로 120분 집계
    df120 = df.resample('120min', origin='start_day', offset='9h').agg({
        'open_pric': 'first',
        'high_pric': 'max',
        'low_pric':  'min',
        'cur_prc':   'last',
        'trde_qty':  'sum',
    }).dropna()
    return df120.reset_index()

def is_above_120min_trend(df60: pd.DataFrame, current_price: float) -> bool:
    df120 = resample_60_to_120(df60)
    # 120분봉 5개 이동평균 (약 10시간)
    ma5_120 = df120['cur_prc'].tail(5).mean()
    return current_price > ma5_120
```

#### 6.4.3 당일 추세 살아있음
```python
def is_today_trending_up(snapshot: dict) -> dict:
    cur = float(snapshot['cur_prc'])
    today_open = float(snapshot['open_pric'])
    prev_close = float(snapshot['base_pric'])
    return {
        'above_today_open': cur > today_open,
        'above_prev_close': cur > prev_close,
        'alive': cur > today_open and cur > prev_close,
    }
```

#### 6.4.4 가격 비교 그래프 데이터 생성
```python
def build_price_comparison(snapshot: dict, daily_df: pd.DataFrame) -> dict:
    prev_row = daily_df.iloc[-2]  # 전일
    return {
        'prev_close':     float(snapshot['base_pric']),
        'prev_high':      float(prev_row['high_pric']),
        'prev_low':       float(prev_row['low_pric']),
        'today_open':     float(snapshot['open_pric']),
        'today_high':     float(snapshot['high_pric']),
        'today_low':      float(snapshot['low_pric']),
        'current_price':  float(snapshot['cur_prc']),
    }
```

---

## 7. 최종 리포트 스키마 (report.py)

### 7.1 단일 진입점 함수

```python
# main.py
def analyze(stock_code: str, base_date: str | None = None) -> dict:
    """단일 종목을 분석해 종합 리포트 반환.

    Args:
        stock_code: 6자리 종목코드 (예: "005930")
        base_date: 조사 기준일 YYYYMMDD. None이면 오늘.

    Returns:
        AnalysisReport dict (§7.2 스키마)
    """
```

### 7.2 AnalysisReport 스키마

```python
{
  "meta": {
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "base_date": "20260422",
    "market_cap_won": 450_0000_0000_0000,   # 450조
    "current_price": 72500,
    "analyzed_at": "2026-04-22T10:15:30+09:00"
  },

  # 일봉 매크로
  "macro": {
    "type1": { /* §6.1 반환값 */ },
    "type2": { /* §6.2 반환값 */ },
    "dominant_type": "type1" | "type2" | "none" | "both",
    # 설명: type1.applicable과 type2.applicable 중 맞는 것.
    # 둘 다 해당 안 되면 "none", 드물게 둘 다면 "both".
  },

  # 거래대금 스파이크
  "volume_spike": { /* §6.3 반환값 */ },

  # 분봉 마이크로
  "micro": {
    "three_min_sideways": { /* §6.4.1 */ },
    "above_120min_trend": bool,
    "today_trend": { /* §6.4.3 */ },
    "price_comparison": { /* §6.4.4 */ }
  },

  # 사람이 읽는 요약
  "summary": {
    "verdict": "buyable" | "watch" | "avoid",
    "confidence": 0.0 ~ 1.0,
    "key_signals": [
        "타입1 후보: 60일 상승 +25% 후 -8% 눌림",
        "BBWP 5일 연속 20 이하 → 변동성 수축 확정",
        "강한 거래대금(500억+) 2일 전 발생 → 돌파 임박",
        "3분봉 최근 30분 0.7% 횡보 중",
        "분봉 추세 살아있음 (시가/전일종가 위)",
    ],
    "risks": [
        "15일선 살짝 이탈 — 당일 종가 중요",
    ]
  },

  # 원시 데이터 (옵션, 디버깅/차트용)
  "raw": {
    "daily_last_10": [...],           # 최근 10일 OHLCV
    "ma_today": {"ma5": 72000, "ma8": 71800, ...},
    "indicators_today": {"atr14": 1200, "adx14": 18.5, "bbwp": 15.3}
  }
}
```

### 7.3 verdict 산정 규칙

```python
def decide_verdict(report: dict) -> tuple[str, float]:
    score = 0
    total = 0

    # [타입1 점수]
    t1 = report['macro']['type1']
    if t1['applicable']:
        total += 5
        if t1['ma_position']['above_5_8']:     score += 1
        if t1['ma_position']['above_15']:      score += 1
        if t1['ma_position']['rebound_zone']:  score += 1
        if t1['is_sideways']:                  score += 2

    # [타입2 점수]
    t2 = report['macro']['type2']
    if t2['applicable']:
        total += 4
        if t2['is_sideways']:                  score += 3
        if t2['criteria_hits']['volume_dried']: score += 1

    # [거래대금 스파이크]
    total += 3
    q = report['volume_spike']['signal_quality']
    if q == 'imminent': score += 3
    elif q == 'watch':  score += 1

    # [분봉 추세]
    total += 2
    if report['micro']['today_trend']['alive']:      score += 1
    if report['micro']['above_120min_trend']:        score += 1

    ratio = score / total if total else 0
    if ratio >= 0.7:   return 'buyable', ratio
    if ratio >= 0.4:   return 'watch',   ratio
    return 'avoid', ratio
```

---

## 8. 에러 처리 규칙

1. **토큰 만료**: `expires_dt` 확인 후 자동 재발급. 재시도 최대 2회.
2. **일봉 < 224일**: 신규상장 종목. `type2.applicable = False`로 설정하고 warning 로그. 타입1만 진행.
3. **분봉 0개**: 휴장일이거나 장 시작 전. `micro` 섹션을 `null`로 두고 `summary.risks`에 기록.
4. **API 4xx/5xx**: 최대 3회 재시도 (exponential backoff: 1s → 2s → 4s).
5. **Rate Limit**: 연속조회 루프 내 `time.sleep(0.25)` 필수.
6. **종목코드 포맷 검증**: 6자리 숫자가 아니면 `ValueError`. (예: "005930", "000660")
7. **거래정지 종목**: `cur_prc == 0` 또는 `trde_qty == 0`이 연속 → warning 후 분석은 진행.

---

## 9. 단위 테스트 체크리스트

- [ ] `add_moving_averages`가 알려진 입력에 대해 정확한 SMA 반환 (예: `[1,2,3,4,5]`의 3일 SMA 마지막 값 = 4)
- [ ] `add_bbwp`가 BBWP 0~100 범위로 반환
- [ ] `add_adx` 값이 0~100 범위
- [ ] 60분봉 → 120분봉 리샘플 시 봉수가 절반 (±1)
- [ ] `find_last_volume_spike`에서 시총 2500억 종목이 3번째 구간 임계값을 쓰는지
- [ ] 타입1 판정: mock 데이터로 "고점대비 -10% + BBWP 낮음" 시 `is_sideways=True`
- [ ] 타입2 판정: "224 아래 + 100 위 + 20일 변동폭 5%" 시 `is_sideways` 판정 정확
- [ ] 신규상장(일봉 50개) 입력 시 크래시 없이 `type2.applicable=False` 반환
- [ ] `analyze("005930")` end-to-end 실행 성공 (실제 API 호출 / 모의투자 환경)

---

## 10. 구현 순서 (권장)

1. `config.py` + `.env` 세팅
2. `auth.py` + `api_client.py` 뼈대 → `get_stock_info("005930")`로 토큰/호출 검증
3. `get_daily_chart` 구현 + 연속조회 루프 + **실제로 260일 확보되는지 확인**
4. `indicators.py` 전체 구현 + 단위테스트
5. `analyzers/macro_type1.py` → `macro_type2.py` → `volume_spike.py` 순
6. `get_minute_chart` + `micro_minute.py`
7. `report.py`에서 전체 조립
8. `main.py`의 `analyze()` 단일 함수 노출
9. 실제 종목 3~5개로 end-to-end 검증 (예: 삼성전자 / 바이오 중소형주 / 이미 꾸준히 오른 테마주)

---

## 11. 사용 예시 (완성된 모듈의 최종 호출 모습)

```python
from seeking_signal_minho.main import analyze

report = analyze("005930")  # 삼성전자

print(f"종목: {report['meta']['stock_name']}")
print(f"판정: {report['summary']['verdict']} "
      f"(신뢰도 {report['summary']['confidence']:.0%})")
print("\n[주요 신호]")
for signal in report['summary']['key_signals']:
    print(f"  ✓ {signal}")

print("\n[타입1 분석]")
t1 = report['macro']['type1']
print(f"  적용 가능: {t1['applicable']}")
print(f"  횡보 중: {t1['is_sideways']}")
print(f"  이평 정배열: {t1['is_perfect_bull']}")

print("\n[거래대금 스파이크]")
vs = report['volume_spike']
print(f"  마지막 강한 거래: {vs['days_ago_strong']}일 전")
print(f"  신호 품질: {vs['signal_quality']}")
```

---

## 12. 중요 주의사항 요약

| 항목 | 내용 |
|---|---|
| **수정주가** | `upd_stkpc_tp='1'` 반드시. 액면분할/권리락 종목 이평선 오염 방지 |
| **120분봉 합성** | 키움 API 직접 제공 X → 60분봉 리샘플링 필수 |
| **이동평균선 계산** | API 제공 X → pandas `rolling().mean()` 로 직접 계산 |
| **224일선 NaN** | 최소 224일 이상 데이터 필요. 연속조회로 260일+ 확보 |
| **시총 단위** | ka10001의 `mac` 단위를 디버깅으로 반드시 재확인 (억원인지 원인지) |
| **음수 부호** | 가격 응답에 `-` 부호 섞여올 수 있음 → `.abs()` 처리 |
| **문자열 응답** | 모든 수치 필드 String → `pd.to_numeric` 변환 필수 |
| **Rate Limit** | API 호출 간 `time.sleep(0.25)` |
| **타입2 3% → 7%** | 한국 주식 특성상 3%는 거의 안 잡힘. 7% 권장(상수로 조정 가능) |
| **BBWP 기준** | 20 이하가 스퀴즈 표준. 판정은 "최근 5일 연속"으로 지속성 확인 |

---

**끝.** 이 문서를 Claude Code에 프롬프트로 주고
`"이 명세에 따라 seeking_signal_minho 패키지 전체를 구현해줘"`
라고 지시하면 바로 개발 가능합니다.
