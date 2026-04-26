# 📡 Seeking Signal Minho - 종목 분석 모듈

단일 종목코드를 입력받아 일봉/분봉 기반 기술적 분석을 수행하고, 구조화된 리포트를 반환하는 Python 모듈입니다.

---

## ✨ 주요 기능

### 📊 타입1 분석 (강한 상승 후 눌림)
- 최근 60일 강한 상승 후 고점 대비 일정 범위 내 눌림
- BBWP 기반 변동성 수축 감지 (5일 연속)
- 이동평균선 정배열/역배열 판정
- 5, 8, 15, 33, 45, 60일 이동평균선 분석

### 📉 타입2 분석 (답보 중인 종목)
- 224일선 아래 + 100일선 위 (오랜 기간 횡보)
- 20일 변동폭 7% 이하 (타이트한 횡보)
- 거래량 감소 (최근 20일 < 과거 100일 × 50%)
- ADX 20 미만 (추세 부재)

### 💰 거래대금 스파이크 탐지
- 시총 구간별 계단식 임계값 적용
- 강한 거래대금 발생 시점 추적
- 신호 품질 분류: imminent(임박) / watch(관망) / dead(죽음)

### 🕐 분봉 마이크로 분석
- 3분봉 횡보 판정 (최근 10봉)
- 120분봉 추세선 위/아래 판정 (60분봉 리샘플링)
- 당일 추세 살아있음 여부

### 🎯 종합 판정
- **BUYABLE** (매수 가능): 신뢰도 70% 이상
- **WATCH** (관망): 신뢰도 40~70%
- **AVOID** (회피): 신뢰도 40% 미만

---

## 🚀 사용 방법

### 1️⃣ Python 모듈로 직접 사용

```python
from seeking_signal_minho import analyze

# 삼성전자 분석
report = analyze("005930")

# 판정 결과
print(f"종목: {report['meta']['stock_name']}")
print(f"판정: {report['summary']['verdict']}")
print(f"신뢰도: {report['summary']['confidence']:.0%}")

# 주요 신호
for signal in report['summary']['key_signals']:
    print(f"  ✓ {signal}")
```

### 2️⃣ 커스텀 파라미터로 분석

```python
from seeking_signal_minho import analyze_with_custom_params

report = analyze_with_custom_params(
    "005930",
    bbwp_threshold=20,           # BBWP 임계값 (기본 25)
    bbwp_consecutive_days=7,     # 연속 일수 (기본 5)
    pullback_max_pct=10,         # 고점대비 최대 하락% (기본 15)
    rally_min_pct=30,            # 60일 최소 상승% (기본 20)
    range_threshold_pct=5,       # 타입2 Range 임계% (기본 7)
    volume_ratio=0.4,            # 거래량 비율 (기본 0.5)
    adx_threshold=18,            # ADX 임계값 (기본 20)
)
```

### 3️⃣ 웹 UI 테스트 페이지

1. 웹 서버 시작:
```bash
source .venv/bin/activate
WEB_PORT=5002 python web_app.py
```

2. 브라우저에서 접속:
```
http://localhost:5002
```

3. **📡 Seeking Signal** 탭 클릭

4. 종목코드 입력 + 파라미터 조정 + **🚀 분석 실행**

---

## 📁 프로젝트 구조

```
seeking_signal_minho/
├── __init__.py              # 패키지 진입점
├── config.py                # 설정 및 상수
├── cache.py                 # 5일 TTL 파일 캐싱
├── api_client.py            # 키움 REST API 래퍼 (연속조회 지원)
├── indicators.py            # MA, ATR, ADX, BB, BBWP 계산
├── analyzers/
│   ├── __init__.py
│   ├── macro_type1.py       # 타입1 판정 로직
│   ├── macro_type2.py       # 타입2 판정 로직
│   ├── volume_spike.py      # 거래대금 스파이크
│   └── micro_minute.py      # 분봉 마이크로 분석
├── report.py                # 최종 리포트 조립
└── main.py                  # analyze() 단일 진입점
```

---

## ⚙️ 설정 파라미터

### 타입1 기본값 (`TYPE1_DEFAULTS`)
```python
{
    'bbwp_threshold': 25,           # BBWP 임계값
    'bbwp_consecutive_days': 5,     # 연속 일수
    'pullback_max_pct': 15,         # 고점대비 최대 하락%
    'rally_min_pct': 20,            # 60일 최소 상승%
}
```

### 타입2 기본값 (`TYPE2_DEFAULTS`)
```python
{
    'range_threshold_pct': 7,       # 20일 변동폭 임계%
    'volume_ratio': 0.5,            # 거래량 비율
    'adx_threshold': 20,            # ADX 임계값
}
```

### 시총 구간별 거래대금 임계값 (`VOLUME_THRESHOLDS`)
```python
[
    (1_000,       30_0000_0000,    80_0000_0000),   # ~1천억
    (2_000,       50_0000_0000,   150_0000_0000),   # 1~2천억
    (5_000,      100_0000_0000,   300_0000_0000),   # 2~5천억
    (20_000,     200_0000_0000,   500_0000_0000),   # 5천억~2조
    (float('inf'), 500_0000_0000, 1_500_0000_0000), # 2조 이상
]
```

---

## 📊 리포트 스키마

```python
{
  "meta": {
    "stock_code": "005930",
    "stock_name": "삼성전자",
    "base_date": "20260423",
    "market_cap_won": 450000,        # 억원
    "current_price": 72500,
    "analyzed_at": "2026-04-23T14:15:30+09:00"
  },

  "macro": {
    "type1": { ... },
    "type2": { ... },
    "dominant_type": "type1" | "type2" | "none" | "both"
  },

  "volume_spike": {
    "signal_quality": "imminent" | "watch" | "dead",
    "days_ago_strong": 2,
    "thresholds": { ... }
  },

  "micro": {
    "three_min_sideways": { ... },
    "above_120min_trend": true,
    "today_trend": { ... }
  },

  "summary": {
    "verdict": "buyable" | "watch" | "avoid",
    "confidence": 0.85,
    "key_signals": [ ... ],
    "risks": [ ... ]
  },

  "raw": { ... }
}
```

---

## 🧪 테스트

### CLI 테스트
```bash
python test_seeking_signal.py
```

### 웹 UI 테스트
1. http://localhost:5002 접속
2. **📡 Seeking Signal** 탭
3. 삼성전자(005930) 입력
4. 파라미터 조정 후 분석 실행

---

## 🔄 캐싱 시스템

- **TTL**: 5일
- **저장 위치**: `.data/cache/`
- **효과**: 같은 종목 재분석 시 API 호출 0회 (즉시 응답)
- **메모리**: 종목당 약 40KB (100종목 = 4MB)

### 캐시 관리
```python
from seeking_signal_minho.cache import get_cache

cache = get_cache()
cache.clear_expired()  # 만료된 캐시만 삭제
cache.clear_all()      # 전체 캐시 삭제
```

---

## 📝 주의사항

1. **키움 API 인증 필요**: `.env` 파일에 `KIWOOM_APPKEY`, `KIWOOM_SECRETKEY` 설정
2. **시총 단위**: 억원 (ka10001 API `mac` 필드)
3. **타입2 Range 임계값**: 한국 주식 특성상 3%는 거의 안 잡힘 → 7% 권장
4. **분봉 데이터**: 장중에만 조회 가능 (장 외 시간에는 `micro.error` 발생)
5. **연속조회**: Rate Limit 방지를 위해 0.25초 sleep 적용

---

## 🎯 활용 시나리오

### 백테스트
- 다양한 파라미터 조합으로 과거 데이터 분석
- 웹 UI에서 실시간 파라미터 조정 가능

### 스크리닝
- 여러 종목을 순회하며 `verdict == "buyable"` 필터링
- 신뢰도 순으로 정렬

### 알림 시스템
- `verdict == "buyable"` 종목 발견 시 텔레그램 알림 (추후 구현)

---

## 📌 Troubleshooting

### Q: 분석 실패 (API 에러)
**A**: `.env` 파일의 키움 API 인증 정보 확인
```bash
KIWOOM_APPKEY=...
KIWOOM_SECRETKEY=...
```

### Q: 분봉 분석 에러
**A**: 장중에만 분봉 데이터 조회 가능. 장 외 시간에는 `micro.error` 메시지 확인

### Q: 캐시 히트율이 낮음
**A**: TTL이 5일이므로 5일 이내 재분석 시에만 캐시 적중

### Q: 타입2 종목이 거의 안 잡힘
**A**: `range_threshold_pct`를 7% → 10%로 조정 시도

---

## 📚 참고 문서

- [seeking-signal-minho-service-spec.md](./seeking-signal-minho-service-spec.md) - 상세 명세서
- [CLAUDE.md](./CLAUDE.md) - 프로젝트 전체 가이드

---

**개발 완료일**: 2026-04-23  
**버전**: 1.0.0  
**개발자**: Claude Code + 사용자 협업
