# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---

## 📑 목차

1. [Project Overview](#project-overview)
2. [🗺️ Quick Map — 작업별 참고 위치](#-quick-map--작업별-참고-위치)
3. [매매 스타일 3종 (개요)](#매매-스타일-3종-개요)
4. [⚠️ CRITICAL: Kiwoom API 코드 절대 함부로 수정 금지](#-critical-kiwoom-api-코드-절대-함부로-수정-금지)
5. [Architecture](#architecture)
6. [Core Services](#core-services)
7. [Mode1 Trading Logic](#mode1-trading-logic)
8. [Mode2 Trading Logic](#mode2-trading-logic)
9. [Style3 발라먹기 (전체 가이드)](#style3-발라먹기-전체-가이드)
10. [Essential Commands](#essential-commands)
11. [🌐 Production Environment (Oracle Cloud)](#-production-environment-oracle-cloud)
12. [Claude Code Skills](#claude-code-skills)
13. [Key Patterns](#key-patterns)
14. [📂 전체 코드 구조 리뷰](#-전체-코드-구조-리뷰)
15. [🖥️ Oracle 서버 부하 가이드](#-oracle-서버-부하-가이드)
16. [TODO](#todo-구현-대기)
17. [Known Issues & Lessons](#known-issues--lessons)

---

## Project Overview

Korean stock auto-trading system with two interfaces:
1. **Web UI** (`web_app.py`) - 두 URL로 분리된 SPA:
   - `/` (장중 실전): 실전, Mode2, 시황체크, 발라먹기(Style3), Mode1, 감시리스트, 매매일지
   - `/adminpage` (운영/분석): AI슬롯분석(백테스트), 종목마스터, Test
2. **Signal Listener** (`signal_listener.py`) - Telegram channel archiver + keyword filter

**Active strategies:**
- **Mode1**: 전일대비 급등 첫 조정 (분봉 그린라이트 조건)
- **Mode2**: 저항/지지 레벨 자동매매 ⭐ **최우선 기능**
- **Style3 (발라먹기 매매)**: 익절 후 재진입 — 거감음봉 조정 후 쌍바닥 지지 확인 → 재매수

Tactic1/2 (`bot_v3.py`)는 구형 기능으로 현재 미사용.

---

## 🗺️ Quick Map — 작업별 참고 위치

| 작업 유형 | 핵심 파일 | 문서 섹션 |
|---------|---------|---------|
| Mode2 매매 로직 수정 | `price_monitor.py:check_mode2_conditions` | [Mode2 Trading Logic](#mode2-trading-logic) |
| Mode1 분봉 조건 수정 | `price_monitor.py:check_mode1_conditions` | [Mode1 Trading Logic](#mode1-trading-logic) |
| Style3 시그널 수정 | `style3_signals.py` + `price_monitor.py:check_style3_conditions` | [Style3 발라먹기](#style3-발라먹기-전체-가이드) |
| Kiwoom API 호출 | `kiwoom_client.py` / `kiwoom_client_async.py` | [⚠️ CRITICAL](#-critical-kiwoom-api-코드-절대-함부로-수정-금지) |
| 백테스트 분석 변경 | `.claude/skills/backtest/prompts/analysis.md` | [Known Issues — 설계 원칙](#-설계-원칙-의사결정-배경) |
| 시황체크 분석 변경 | `.claude/skills/siwhang/prompts/analysis.md` | [Skills](#claude-code-skills) |
| Oracle 배포 | `start_https.sh`, scp 명령 | [Production Environment](#-production-environment-oracle-cloud) |
| DB 스키마 | `news_storage.py` | [DB 스키마 표](#db-스키마) |
| 핵심 API 호출 | `web_app.py` | [핵심 API](#-핵심-api-자주-사용) |
| 트러블슈팅 (자주 틀리는 포인트) | — | [Known Issues](#known-issues--lessons) |

---

## 매매 스타일 3종 (개요)

상세 시그널/구현은 각 모드 섹션 참고.

### Style1 — 눌림매매 (수동)
전일 대비 강하게 상승한 종목의 첫 조정 구간 매수. **Mode1**이 분봉 조건 알림 제공.

### Style2 — 대장주/연관주 매매 (백테스트→Mode2 등록)
급등주 메시지(`[SS⬆️]`/`[VI]`)에서 주도 테마 파악 → 아직 안 오른 연관주 선점.
`/backtest` 스킬로 타임슬롯별 분석 → 백테스트 페이지에서 "Mode2 등록" 버튼.

### Style3 — 발라먹기 매매 (익절 후 재진입) ⭐
강한 거래량 폭발로 급등한 종목 익절 이후, 변동성이 유지되면서 조정 구간을 주고 결국 고점을 뚫는 패턴. "잘 맞는 종목을 계속 발라먹는" 매매 스타일. → [상세](#style3-발라먹기-전체-가이드)

---

## ⚠️ CRITICAL: Kiwoom API 코드 절대 함부로 수정 금지

`kiwoom_client.py`, `kiwoom_chart.py`, `kiwoom_token.py`는 **프로덕션 실제 거래** 코드. 수정 시:
1. `ORDER_SIMULATION_MODE=1`로 로컬 테스트 먼저
2. 에러 핸들링 (try-except) 절대 제거 금지
3. Rate limit 주의 (초당 5회)

### Kiwoom 계좌 구조 (2026-05 현재)

- **서브계좌** (`account='sub'`, 기본): `KIWOOM_APPKEY`/`KIWOOM_SECRETKEY` — 자동매매 실행 계좌
- **메인계좌** (`account='main'`): `KIWOOM_MAIN_APPKEY`/`KIWOOM_MAIN_SECRETKEY` — **조회 전용**
  - 실제 Style3 수동 매매 이력이 있는 계좌
  - `ka10170` 전일 체결 이력 조회 → Track B Style3 종목 자동 등록 소스
  - `place_buy_order` / `place_sell_order` / `cancel_order` 호출 시 `PermissionError` 강제 차단 (`_assert_not_main_account()`)
  - **키 보관 정책**: 로컬 `.env`에만 키 저장. Oracle 서버 `.env`에는 빈값으로 추가됨 (Oracle에 키 올리지 않음)
  - Track B 흐름: **로컬 PC에서 직접 Kiwoom 조회** → Oracle `POST /api/trade-watchlist-draft` 전송

---

## Architecture

### Data Flow
```
Web UI → Flask API → Mode1/Mode2Manager → PriceMonitor → KiwoomClientAsync → Telegram
Telegram Channels → signal_listener (Pyrogram) → news.db → Web UI 시황체크
/siwhang skill → Oracle API (hotstock/parsed + news/today + watchlist) → AI 분석 → siwhang_results → Telegram
/backtest skill → Oracle API → 13 슬롯 AI 분석 → backtest_picks 저장 → 실전 페이지
Style3 폴링 (3분) → trade_watchlist watching + morning_watchlist 130개 → reentry_signals
```

---

## Core Services

**`web_app.py`** — Flask server + PriceMonitor 통합
- 웹서버 시작 시 PriceMonitor 백그라운드 자동 시작
- Basic Auth (`WEB_USERNAME` / `WEB_PASSWORD`)
- SSL: cert.pem/key.pem 존재 시 HTTPS, 없으면 HTTP
- 모든 fetch 호출에 `credentials: 'same-origin'` 필수

**`price_monitor.py`** — 비동기 모니터링 엔진
- `asyncio.gather()`로 전 종목 병렬 체크
- 종목별 polling_interval 독립 관리 (`mode2_last_check` dict)
- `last_notification` 필드로 중복 알림 방지
- `notify_only=True` 시 알림만, `False` 시 자동 주문 실행
- Style3 폴링: 3분 간격, C2 일봉 캐시(`style3_c2_cache`/`morning_c2_cache`)

**`kiwoom_client_async.py`** — 비동기 API wrapper (price_monitor에서 사용)
- aiohttp 기반, Rate limiting 초당 5회 내장

**`kiwoom_client.py`** — 동기 API wrapper (주문/계좌조회에서 사용)
- OAuth2 토큰 25분마다 자동 갱신 (TTL 30분)
- ka10003: 현재가 / kt10000: 매수 / kt10001: 매도 / ka01690: 보유종목

**`signal_listener.py`** — Pyrogram 텔레그램 채널 구독
- 급등주 채널(`-1003342481653`) + 뉴스 채널(`-1003239561368`) 구독
- 모든 메시지 → `news.db` 아카이빙 (필터 무관)
- 키워드 필터 통과 시 → 목적지 채널 포워딩 + `filtered_messages` 기록
- 키워드 핫리로드: `keywords.json` 30초 주기 감지

---

## Mode1 Trading Logic

분봉 polling 스케줄 (offset 3초):
- 1분봉: 사용자 설정 주기
- 3분봉: 3분 간격 + 3초 (xx:03, xx:06, ...)
- 5분봉: 5분 간격 + 3초
- 10분봉: 10분 간격 + 3초

**조건 체크** (`price_monitor.py:check_mode1_conditions`):
```
Step1: 전일 대비 급등 확인 (rise_threshold%)
Step2: 최고가 도달 확인 (high_threshold%)
Step3: 재반등 → n번째 봉 시가가 매수타점
  ↓
AND 조건 모두 충족 시 텔레그램 알림 (수동 매수)
```

---

## Mode2 Trading Logic

**매수**: `current_price <= buy_target_price` (±1% tolerance)

**매도 우선순위** (높은 것부터):
1. `resistance_2` → 전량 익절
2. `resistance_1` → 부분 익절 (profit_ratio 설정값%)
3. `trailing_exit` → 잔여 전량 익절 (resistance_1 익절 후 하락 시)
4. `support_2` → 심층 손절
5. `support_1` → 1차 손절 (또는 물타기)

**Budget**: 웹UI에서 만원 단위 입력 → 저장 시 ×10000 (API는 항상 원 단위).

### 트레일링 익절 로직

**컨셉**: 1차 저항에서 부분 익절 후 추가 상승이 아닌 하락 전환 시 잔여 포지션 전량 청산.

**트리거 가격 계산**:
```
trailing_trigger = resistance_1 - (resistance_1 - buy_target_price) / 4
예: 매수타점 100, 1차저항 200 → trailing_trigger = 200 - (200-100)/4 = 175원
예: 매수타점 50,000, 1차저항 60,000 → trailing_trigger = 57,500원
```

**활성 조건**: `'resistance_1' in sold_history` AND `'trailing_exit' not in sold_history`
- 1차 저항 익절이 실행된 이후에만 활성화
- 1차 저항 안 건드리고 바로 하락하면 비활성 (기존 지지/손절 로직만 동작)
- 비율(50%/25%/75% 등) 무관하게 동일 적용

**sold_history 흐름**: `resistance_1` 기록 → 하락 → `trailing_exit` 기록 → 전량 청산

### Mode2 Demark 자동계산
- 일봉 차트 로드 시(`loadWatcherChart`, `handleMode2Lookup`) 전일 OHLC → 디마크 자동계산 → `resistance_1_price`/`support_1_price` 자동 채움
- 디마크 공식: close<open → x=high+2*low+close; close>open → x=2*high+low+close; else → x=high+low+2*close; targetHigh=x/2-low, targetLow=x/2-high
- 디마크 섹션의 "1차 저항/지지 적용" 버튼으로 수동 재계산도 가능

### Mode2 청산 → Style3 자동 draft 등록 (2026-05-06)

Mode2 전량 매도(`record_sell` 후 `remaining_qty == 0`) 시 `trade_watchlist`에 `status='draft'`로 자동 삽입.

**가격 설정 규칙**:
- 익절(`reason`에 'resistance' 포함): `buy_price=bought_price`, `exit_price=매도가(저항선)`
- 손절: `buy_price=매도가(손절가)`, `exit_price=bought_price(원래 매수가)`

이미 watching/draft 상태인 종목은 중복 삽입 스킵. 웹 발라먹기 감시목록에 노란 배경 draft로 뜸 → "✓ 등록" 클릭 시 watching 전환.

---

## Style3 발라먹기 (전체 가이드)

### 1. 전제 조건과 레퍼런스 패턴

**핵심 패턴**: 강한 거래량 폭발로 급등한 종목 익절 이후, 변동성이 유지되면서 조정 구간을 주고 결국 고점을 뚫는 패턴.

**전제 조건 (이 종목을 왜 다시 볼 것인가)**:
1. 최근 강한 거래량 폭발(평균 대비 5배+) 이력이 있음
2. 내가 이미 익절한 종목 → 패턴 검증됨
3. 힘이 좋아서 결국 고점을 뚫어버리는 종목

**레퍼런스: 한컴위드 054920**
```
4/17 매수 6,190원 (강한 상승 초기)
4/20 익절 6,760원 (거래량 32.5M 폭발, 고가 7,980원)
  → 익절 직후 재진입 기회 3개:
  
  타입A (4/20 13:15): 당일 6,190원까지 재조정 → 매수가 존 터치 (분봉 포착 필요)
  타입B (4/20 13:48): 익절가 6,760원 재돌파 확인 → 6,900원 진입 (분봉 포착 필요)
  타입C2 (4/22 오전): 21~22일 거래량 감소 음봉(거감음봉) → 6,300원대 쌍바닥 확인
                       → 4/24 10:45, 11:21, 11:45 지속적 지지 확인 후 진입
  
4/27 거래량 19.8M 재폭발 → 고점 돌파
```

### 2. 시그널 타입 6종

| 타입 | 조건 | 기준 가격 | 타이밍 | 비고 |
|------|------|-----------|--------|------|
| **A** | 현재가 ≤ Mode2 매수타점 × 1.03 | `buy_target_price` | 익절 당일~수일 내 원가 복귀 | 당일 1회만 알림 |
| **A2** | 현재가 ≤ Mode2 1차저항 × 1.03 | `resistance_1_price` | 1차저항(익절가) 근처 복귀 | 익절가 지지선 전환 확인. 당일 1회만 |
| **B-r1** | 현재가 > 1차저항 × 1.02 (2%+ 돌파) | `resistance_1_price` | 재상승 확인 진입 | 같은 가격대 반복 방지 (±2%) |
| **B-r2** | 현재가 > 2차저항 × 1.02 (2%+ 돌파) | `resistance_2_price` | 강한 재상승 | confidence H |
| **C1** | 거감봉 진행 중 (거래량 < 평균 50%) | — | 조정 초기 | 모니터링 알림, 진입 아님. 2시간 쿨다운 |
| **C2** | 쌍바닥 지지 터치 (exit_date 이후 일봉 기준) | `support_price` | 거감봉 이후 | **핵심 타점** — `H+`: 지지가가 1차저항 ±2% 이내면 강한 지지 |
| **C3** | 거래량 급증(>평균 1.8배) 양봉 | — | 재상승 시작 신호 | 2시간 쿨다운 |

### 3. C2 쌍바닥 자동 계산 로직

`style3_signals.py: find_double_bottom()`:
- `exit_date` 이후 일봉에서 최저점(base) 탐색
- base × 1.04 이내에 저점 2개 이상 → 쌍바닥 확인
- `support_price = base × 1.005` (지지가 0.5% 위 진입)
- **H+ 등급**: `support_price`가 `resistance_1_price` ±2% 이내 → "익절가=지지선 전환" 강한 신호
- 터치 판정: `abs(close - support_price) / support_price < 0.008` (±0.8%)

### 4. 가격 체계 (Mode2 연동)

Mode2 watcher에서 `buy_target_price` / `resistance_1_price` / `resistance_2_price` 조회.
Mode2 미등록 시 `trade_watchlist`의 `buy_price` / `exit_price` fallback.

### 5. 등록 흐름 (draft → watching → Mode2)

**현행 2단계 파이프라인**:

```
[1단계: draft 등록]
저녁 루틴 /style3-register or Mode2 청산 자동 → POST /api/trade-watchlist-draft
  ↓ status='draft' (노란 배경)

[2단계: 웹UI 확인 후 watching 전환]
발라먹기 탭 → 감시목록 서브탭 → "✓ 등록" 버튼
  ↓ PUT /api/trade-watchlist/{id} status='watching' + Mode2 섹션 자동 생성

[3단계: 시그널 발생 시 Mode2 정식 등록]
시그널 알림 수신 → 발라먹기 탭 → "📊 Mode2 전환" 버튼 → 모달 입력
  ↓ POST /api/mode2/watchers
```

**Mode2 섹션 3종 구조** (매일 아침 기준):
- `YYYY-MM-DD 눌림매매 (Style1)` — 수동 등록
- `YYYY-MM-DD 종목추천매매 (Style2)` — 백테스트 페이지 "Mode2 등록" 버튼
- `YYYY-MM-DD Style3 발라먹기` (또는 `MM-DD 발라먹기`) — watching 전환 시 자동 생성
- Mode2 날짜 필터로 당일 3개 섹션만 필터링 가능

### 6. 실시간 폴링 아키텍처

**`price_monitor.py`** (3분 주기, 비동기 병렬):

| 함수 | 대상 | 알림 | 시그널 타입 |
|------|------|------|-----------|
| `check_style3_conditions()` | `trade_watchlist` watching 종목 | 텔레그램 + DB | A/A2/B-r1/B-r2/C1/C2/C3 |
| `check_morning_c_signals()` | `morning_watchlist.json` 130종목 | DB만 (웹 전용) | C1/C2 (매수가/저항가 미등록이라 A/B 없음) |

**공통 동작**:
- 3분봉(ka10080) 기반 장중 즉시 감지
- 단일가 매매일(봉 간격 25분+ > 50%) → `DANILGA` 태그 후 스킵
- C2 지지가 산출 후 시그널 감지
- 캐시: `style3_c2_cache` / `morning_c2_cache` — 종목별 일봉 1일 1회 조회 후 재사용
- 비동기 전환 효과: 150종목 처리 ~30초

**reentry_signals.source 컬럼**:
- `'watchlist'`: trade_watchlist watching 종목 시그널
- `'morning'`: 관심종목 130개 C시그널

### 7. 백테스트 모드

`POST /api/seeking-signal/reentry-check` (`backtest_mode=true`):
- `exit_time` (HH:MM) 입력 시 익절 당일 해당 시각 이후 3분봉도 분석 포함
- exit_date 다음날부터 최대 7거래일 3분봉 조회 (ka10080)
- 날짜+타입 기준 dedup (같은 날 같은 타입은 첫 감지 1개만)
- 단일가 매매일(봉 간격 25분+ 비율 > 50%) → `DANILGA` 태그로 표시 후 스킵
- 응답에 `support_price`, `bars_analyzed`, `trading_days`, `buy_target_price`, `resistance_1_price` 포함

**단기과열 억제 없음**: exit_date 다음날부터 즉시 시그널 감지. 단일가 매매일만 제외.

### 8. 저녁/장중 루틴 파이프라인

```
[저녁] /style3-register [날짜]
  → 익절 데이터 탐색 (april_trade_sets → kt00015 → 수동입력)
  → POST /api/trade-watchlist-draft
  → 웹 UI 발라먹기 탭 → ✓ 등록 (draft → watching)
  → (선택) /style3-backtest → 과거 시그널 패턴 확인

[장중] price_monitor가 3분 폴링으로 실시간 시그널 자동 감지
  → 텔레그램 알림 수신 (watchlist) / 웹UI 표시 (morning)

[시그널 발생 시] /style3-consult [종목코드]
  → 매크로(morning_report) + 시황(siwhang) + 뉴스 교차 분석
  → 진입 판단 컨설팅

[진입 결정 시] 웹 UI 발라먹기 탭 → 📊 Mode2 버튼 → 모달 등록
```

**스킬 요약**:
| 스킬 | 실행 시점 | 핵심 입력 | 핵심 출력 |
|------|---------|---------|---------|
| `/style3-register` | 저녁 (장마감 후) | 날짜 | draft 등록 |
| `/style3-backtest` | 장마감 후 검증용 | stock_code or all | 시그널 패턴 요약 |
| `/style3-consult` | 장중 시그널 발생 시 | stock_code | 진입 판단 |

**`/morning-style3` 스킬** (매일 아침 수동 실행):
- Track A: 관심종목 130개 → 시가±5%(09:15)/±7%(10:00) 필터 → C2 전용 등록 (buy_price=0)
- Track B: 메인계좌 전일 체결 → 매수타점+익절가 설정 → 전체 시그널 등록
- 현재는 메인계좌 키 미등록(Oracle)으로 서브계좌 기준으로만 동작

### 9. UI 구조 (서브탭)

**발라먹기 탭 내 서브탭**:
- **감시목록**: trade_watchlist 전체 (draft=노란배경, watching=흰배경, exited=필터링)
  - draft 행: "✓ 등록" + "✕" 버튼
  - watching 행: "📊 Mode2" + "삭제" 버튼
- **오늘 시그널**: `reentry_signals?date=오늘` (source='watchlist') — 장중 실시간 감지 결과
  - 각 카드에 "📊 Mode2 전환" 버튼 → `showS3Mode2Modal()` 팝업
- **관심종목 C**: `reentry/morning-signals?date=오늘` (source='morning') — 130종목 C시그널
  - 종목=행, 시그널 발생 시각=열 매트릭스 테이블
  - C2(쌍바닥)/C1(거감봉) 타입 + H/M/L 컨피던스 배지 + 지지가 표시
  - 텔레그램 알림 없음 (웹 전용)

**Mode2 전환 모달 (`s3Mode2Modal`)**:
- 매수타점, 1차저항(익절가 기본), 2차저항(선택)
- 1차지지 + 손절/물타기 select + 물타기 추가예산(hidden)
- 2차지지, 예산
- "💾 Mode2 등록" → `submitS3Mode2Modal()` → `POST /api/mode2/watchers`
- 기존 동일 종목 watcher 있으면 "덮어쓰기?" 확인 팝업

### 10. 관련 파일

- `style3_signals.py` — 시그널 감지 유틸 (web_app + price_monitor 공유)
- `news_storage.py` — `trade_watchlist` + `reentry_signals` 테이블
- `web_app.py` — `/api/trade-watchlist` CRUD + `/api/trade-watchlist-draft` + `/api/reentry/signals` + `/api/seeking-signal/reentry-check` + `/api/morning-watchlist`
- `price_monitor.py: check_style3_conditions()` / `check_morning_c_signals()` — 3분 폴링
- `kiwoom_client.py: get_daily_trades()` — ka10170 전일 매매일지 조회
- `.data/morning_watchlist.json` — Track A 관심종목 (9.csv+10.csv 기반 130종목)

### 11. 설계 원칙 (왜 이렇게 만들었나)

**일봉 기반 시그널 = 폐기**: 15:30 종가 확정 후 발생하는 시그널은 이미 기회가 지나간 것. 반드시 **장중 분봉(3분봉) 기반 실시간 감지**여야 의미 있음.

**C2 쌍바닥은 가격 패턴만**: 거감봉 카운트 불필요. 두 저점이 ±4% 이내에 있으면 충분. 한컴위드 4/22의 경우 미세 양봉(거래량만 감소)도 거감봉으로 처리했기 때문에 가격 패턴으로만 판단하는 것이 더 정확.

**단기과열 억제 폐기**: exit_date 다음날부터 즉시 시그널 허용. 단일가 매매일(30분 단위 단일가 거래)만 제외. 한컴위드 4/21~4/23이 단일가 구간이었음.

**단일가 매매일 감지**: 3분봉 조회 후 봉 간격 25분+ 비율이 50% 초과이면 단일가로 판단 → 스킵.

**overheat_date**: `exit_date`를 직접 사용 (자동탐지 폐기 — 전체 일봉에서 탐색하면 수년 전 폭등일 오탐 발생).

**C2 dedup**: 같은 `support_price` ±100원은 하루에 첫 감지만.

**가격 체계 전환 (2026-05)**: 기존 `buy_price`/`exit_price` → Mode2 `buy_target_price`/`resistance_1_price`/`resistance_2_price`. trade_watchlist에 Mode2가 없으면 fallback.

**Type B 조건**: +2% 이상 돌파 (이전 +5%). B-r1(1차저항), B-r2(2차저항)으로 분리. 같은 가격대(±2%) 반복 알림 방지.

---

## Essential Commands

```bash
source .venv/bin/activate

# 로컬 개발
WEB_PORT=5002 python web_app.py       # 웹서버만 (PriceMonitor 자동시작)
python signal_listener.py             # 뉴스 아카이빙 (최초 실행 시 Pyrogram 인증 필요)

# 테스트
python test_bot.py
python test_kiwoom.py                 # 실제 API 호출 (유효한 credentials 필요)
python test_mode2_monitoring.py

# 오라클 뉴스 DB 조회
cd ~/newkiwoom && source .venv/bin/activate && python3 -c "
from news_storage import NewsStorage; import datetime
ns = NewsStorage('.data/news.db')
msgs = ns.get_messages(source_type='news')
print(f'오늘 뉴스: {len(msgs)}건')
"
```

### Signal Listener 최초 인증 (1회만, 반드시 터미널 직접 실행)
```bash
python signal_listener.py
# → Enter phone number: +8210XXXXXXXX
# → Enter OTP: XXXXX
# signal_listener.session 파일 생성됨
```

---

## 🌐 Production Environment (Oracle Cloud)

- **Domain**: https://www.nomaddoklip.xyz
- **IP**: 152.67.207.143 / **User**: opc
- **SSH Key**: `/Users/msim/Downloads/ssh-key-2026-04-26.key`
- **Path**: ~/newkiwoom

**현재 운영 중인 서비스 (2개만):**
- `web_app.py` — sudo, WEB_PORT=443, HTTPS (cert.pem/key.pem)
- `signal_listener.py` — 뉴스/급등주 아카이빙

```bash
# SSH
ssh -i /Users/msim/Downloads/ssh-key-2026-04-26.key opc@152.67.207.143

# 서비스 상태 확인
ps aux | grep -E "python.*(web_app|signal_listener)" | grep -v grep
tail -f ~/newkiwoom/web_app.log
tail -f ~/newkiwoom/signal_listener.log

# 재시작 (긴급)
cd ~/newkiwoom && ./start_https.sh    # web_app만
# signal_listener는 별도:
source .venv/bin/activate && nohup python signal_listener.py > signal_listener.log 2>&1 &
```

**로컬 Admin UI로 관리**: `start_admin_oracle.command` 더블클릭 → http://localhost:8889
- 오라클 서버 시작/정지 버튼이 web_app + signal_listener 둘 다 제어함

### 배포 절차
```bash
# 로컬에서 변경 후
git add <files> && git commit -m "..." && git push origin main

# 오라클에서
ssh opc@152.67.207.143 'cd ~/newkiwoom && git pull origin main'
# 그 후 admin UI에서 서버 재시작 또는 start_https.sh + signal_listener 재시작
```

### Oracle 포트 설정 주의
포트 변경 시 iptables + Security List 둘 다 업데이트 필요:
```bash
sudo iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
sudo iptables-save | sudo tee /etc/sysconfig/iptables
```

### signal_listener.session 배포
`.gitignore`에 `*.session`이 있어 git으로 배포 불가. SCP로 직접 복사:
```bash
scp -i /Users/msim/Downloads/ssh-key-2026-04-26.key \
  signal_listener.session opc@152.67.207.143:~/newkiwoom/
```

### 로컬 PC에서 Oracle API 직접 호출 불가 (VPN 환경)
회사 VPN 환경에서 `https://www.nomaddoklip.xyz` 직접 호출은 DNS 타임아웃으로 실패. **SSH로 오라클 서버에 붙어서 localhost로 호출**해야 함.

```bash
# 올바른 패턴: SSH → Oracle 서버에서 localhost 호출
ssh -i /Users/msim/Downloads/ssh-key-2026-04-26.key opc@152.67.207.143 '
  source ~/newkiwoom/.venv/bin/activate
  export $(grep -v "^#" ~/newkiwoom/.env | xargs)
  curl -sk -u "$WEB_USERNAME:$WEB_PASSWORD" "https://localhost/api/news/today?date=2026-04-29"
'
```

### Environment Variables

```bash
# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Kiwoom API (서브계좌)
KIWOOM_HOST=https://api.kiwoom.com
KIWOOM_APPKEY=...
KIWOOM_SECRETKEY=...

# Kiwoom 메인계좌 (조회 전용, 로컬 .env에만)
KIWOOM_MAIN_APPKEY=...
KIWOOM_MAIN_SECRETKEY=...

# Web Server
WEB_PORT=443              # 프로덕션, 로컬은 5002
WEB_HOST=0.0.0.0
WEB_USERNAME=...
WEB_PASSWORD=...

# Order
ORDER_SIMULATION_MODE=1   # 1=시뮬, 0=실거래 (주의!)
MONITOR_INTERVAL=10

# Signal Listener
TG_API_ID=...
TG_API_HASH=...
SOURCE_CHAT_IDS=-1003342481653,-1003239561368
SOURCE_DEST_MAPPING=-1003342481653:-1003623684126,-1003239561368:-1003599721748
NEWS_DB_PATH=.data/news.db
KEYWORD_RELOAD_INTERVAL=30

# Style3
MORNING_WATCHLIST_PATH=.data/morning_watchlist.json  # (선택)

# Testing
TEST_LAST_PRICE=116000    # API 우회, 고정 가격 반환
IGNORE_MARKET_HOURS=1     # 시간 검증 스킵
```

---

## Claude Code Skills

`.claude/skills/` 디렉터리. **`.claude/`는 `.gitignore`에 등록됨 — git push로 배포 불가, scp 사용.**

```bash
scp -i /Users/msim/Downloads/ssh-key-2026-04-26.key \
  -r .claude/skills/siwhang opc@152.67.207.143:~/newkiwoom/.claude/skills/
```

### 활성 스킬

| 스킬 | 트리거 | 역할 |
|------|--------|------|
| `news-insight` | `/news-insight` | 마지막 실행 이후 신규 뉴스 증분 분석 |
| `news-insight-selected` | `/news-insight-selected` | 선택한 뉴스만 심층 분석 |
| `news-grouping` | `/news-grouping` | 테마별 그룹핑 + 강도(H/M/L) |
| `siwhang` | `/siwhang [1h\|2h]` | 급등주 시황 부합 여부 + 관심종목 매칭 AI 분석 → Oracle 저장 + 텔레그램 알림 |
| `siwhang-v2` | `/siwhang-v2 [1h\|2h]` | siwhang v2 — AI 분석 전 Kiwoom 현재가 스냅샷 → Entry Gate 필터 (등락률/RSI/VWAP/거래량) → `version='siwhang_v2'` 세션으로 A/B 비교 |
| `backtest` | `/backtest [YYYY-MM-DD] [--version v2] [--desc "설명"]` | 지정 날짜 급등주/뉴스 → 13 타임슬롯 AI 분석 → 종목 추천 → Oracle 저장 |
| `style3-register` | `/style3-register [YYYY-MM-DD]` | 저녁 루틴 — 익절 종목 → draft 등록 |
| `style3-backtest` | `/style3-backtest [stock_code]` | 장마감 후 — 익절 이후 재진입 패턴 분석 |
| `style3-consult` | `/style3-consult [stock_code]` | 장중 — 시그널 발생 시 매크로+시황 교차 → 진입 판단 |
| `signal-consult` | `/signal-consult [stock_code[,code2,...]]` | signalreport.co.kr 멤버십 페이지 크롤링 → 분석 |
| `dart-consult` | `/dart-consult [종목코드] [질문]` | DART 공시 원문 조회 → 질문 직접 답변 |
| `mode2-register` | `/mode2-register` | Mode2 알림모드 종목 일괄 등록 |
| `oracle-server` | `/oracle-server [stop\|start\|restart\|status]` 또는 자연어 ("서버 죽여줘" 등) | Oracle 서버 stop/start/restart/status |
| `live-backtest` | 자연어 ("실전추천종목 백테스트해줘봐", "추천종목 C시그널 확인해줘" 등) | 장마감 후 — 오늘 siwhang/v2 추천 picks 슬롯 이후 3분봉 C시그널 탐지 → Oracle DB 저장 → 실전 카드에 표시 |

### Deprecated 스킬

| 스킬 | 트리거 | 상태 |
|------|--------|------|
| `reentry` | `/reentry` | ⚠️ **구형 (일봉 기반)** — Style3 실시간 감지는 `price_monitor.py:check_style3_conditions()`로 대체됨. **사용 금지** |

프롬프트 커스터마이징: `.claude/skills/<skill>/prompts/`
- 시황체크: `.claude/skills/siwhang/prompts/analysis.md`
- 백테스트: `.claude/skills/backtest/prompts/analysis.md`

---

## Key Patterns

### Stock Code Normalization
`normalize_stock_code()` (utils/code.py) — 항상 사용:
- `"81180"` → `"081180"` (6자리 패딩)
- 전각 숫자 변환

### Status Flow
```
Mode1/Mode2: waiting_buy → waiting_sell → auto_sold | manual_sold
trade_watchlist: draft → watching 
```

### Watcher Data Files
- `.data/mode1_watchers.json` — Mode1 감시종목
- `.data/mode2_watchers.json` — Mode2 감시종목 (구조: `{sections:[...], watchers:{code: {...}}}`)
- `.data/news.db` — 뉴스/급등주 SQLite DB (스키마 표 아래 참고)
- `.data/news_keywords.json` — 뉴스 키워드 필터 (include/exclude 분리)
- `.data/hotstock_keywords.json` — 급등주 키워드 필터 (include만)
- `.data/keywords.json` — 구형 단일 키워드 파일 (하위호환용)
- `.data/watchlist.json` — 수동 추가 관심종목 (`[{"code":"005930","name":"삼성전자"}]`)
- `.data/morning_watchlist.json` — Style3 Track A 관심종목 (130개)
- `.data/corp_code_map.json` — DART corp_code 매핑
- `.data/stock_name_map.json` — 종목명 → stock_code 역방향 매핑

---

## 📂 전체 코드 구조 리뷰

### 파일별 역할 (2026-05 기준)

| 파일 | 줄 수 | 역할 |
|------|-------|------|
| `web_app.py` | ~3850 | Flask 서버 + 전체 API 라우터 |
| `price_monitor.py` | ~1370 | 비동기 종목 모니터링 엔진 |
| `kiwoom_client.py` | ~850 | Kiwoom REST API 동기 wrapper |
| `kiwoom_chart.py` | ~800 | 일봉/분봉 차트 조회 |
| `news_storage.py` | ~1370 | SQLite DB 전체 CRUD |
| `style3_signals.py` | ~175 | Style3 시그널 감지 유틸 (web_app + price_monitor 공유) |
| `mode2_manager.py` | ~650 | Mode2 감시종목 상태 관리 |
| `signal_listener.py` | ~380 | Pyrogram 텔레그램 채널 구독 |
| `mode1_manager.py` | ~320 | Mode1 감시종목 상태 관리 |
| `static/js/app.js` | ~9050 | 프론트엔드 전체 SPA 로직 |
| `templates/index.html` | ~1990 | 단일 HTML SPA 템플릿 |
| `static/css/style.css` | ~3100 | 전체 스타일 |

### DB 스키마

`.data/news.db` (SQLite):

| 테이블 | 역할 | 주요 컬럼 | 사용처 |
|--------|------|---------|-------|
| `messages` | 텔레그램 원본 아카이빙 | `source_type`, `received_at`(UTC), `date`(KST), `message_id` | signal_listener |
| `filtered_messages` | 키워드 통과분 | `keywords` | 시황체크 |
| `themes` | 테마 그룹핑 | `theme_name`, `strength` | news-grouping 스킬 |
| `saved_news` | 뉴스 스크랩 | `url`, `title` | 웹 UI |
| `siwhang_results` | AI 시황 분석 결과 | `confidence(H/M/L)`, `hot_stocks` | /siwhang 스킬 |
| `backtest_sessions` | 백테스트 세션 | `version`, `strategy_desc`, `date` | /backtest 스킬 |
| `backtest_picks` | 슬롯별 추천 종목 | `slot_time`, `confidence`, `catalyst`, `sources_json`, `note_source` | /backtest 스킬 |
| `backtest_pnl` | P&L 입력 | `pick_id`, `actual_pnl` | 웹 UI |
| `analysis_context` | 분석 컨텍스트 | `morning_report`, `interval_context`, `next_instruction` | /backtest 스킬 |
| `stock_master` | 종목 마스터 | `themes`, `note`, 재무캐시(시총/PER/ROE/...) | hover tooltip |
| `stock_siwhang_history` | 종목별 급등주 feed 이력 | `event_date`, `tag_type`, `theme` | hover tooltip |
| `trading_mottos` | 격언 | — | 웹 UI |
| `trade_watchlist` | Style3 감시 | `status(draft/watching/exited)`, `exit_date`, `buy_price`, `exit_price` | 발라먹기 탭 |
| `reentry_signals` | Style3 시그널 | `source(watchlist/morning)`, `signal_type`, `support_price` | 발라먹기 탭 |

### 🌟 핵심 API (자주 사용)

| 메서드 | 경로 | 용도 |
|--------|------|------|
| POST | `/api/mode2/watchers` | Mode2 등록. **필드명 주의**: `code`/`name` (NOT `stock_code`/`stock_name`). 필수: `code`, `buy_target_price`, `budget` |
| POST | `/api/trade-watchlist-draft` | Style3 일괄 draft 등록 (items 배열, 이미 watching/draft는 자동 스킵) |
| PUT | `/api/trade-watchlist/<id>` | draft → watching 전환 |
| POST | `/api/seeking-signal/reentry-check` | Style3 백테스트 (과거 3분봉 시그널 탐색) |
| GET | `/api/reentry/signals?date=` | 오늘 시그널 (source='watchlist') |
| GET | `/api/reentry/morning-signals?date=` | 관심종목 C시그널 (source='morning') |
| POST | `/api/backtest/picks` | 백테스트 추천 종목 저장 |
| GET | `/api/live/picks` | 실전 페이지용 오늘 picks |
| POST | `/api/siwhang/results` | 시황체크 결과 저장 |

### 부수 API (전체 목록)

#### Mode1 (`/api/mode1/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET/POST | `/api/mode1/watchers` | 감시종목 목록/추가 |
| GET/PUT/DELETE | `/api/mode1/watchers/<code>` | 개별 조회/수정/삭제 |
| PATCH | `/api/mode1/watchers/<code>/active` | 활성화 토글 |
| PATCH | `/api/mode1/watchers/<code>/status` | 상태 수동 변경 |

#### Mode2 (`/api/mode2/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET/POST | `/api/mode2/watchers` | 감시종목 목록/추가 |
| GET/PUT/DELETE | `/api/mode2/watchers/<code>` | 개별 조회/수정/삭제 |
| PATCH | `/api/mode2/watchers/<code>/active` | 활성화 토글 |
| PATCH | `/api/mode2/watchers/<code>/status` | 상태 수동 변경 |
| GET/POST | `/api/mode2/sections` | 섹션 목록/추가 (응답: `{"data": [...]}`, list) |
| PUT/DELETE | `/api/mode2/sections/<id>` | 섹션 수정/삭제 |
| POST | `/api/mode2/sections/reorder` | 섹션 순서 변경 |
| POST | `/api/mode2/sections/<id>/toggle-collapse` | 섹션 접기/펼치기 |
| POST | `/api/mode2/watchers/<code>/move-section` | 종목 섹션 이동 |
| POST | `/api/mode2/sections/<id>/reorder-watchers` | 섹션 내 종목 순서 |
| GET | `/api/mode2/sections/<id>/watchers` | 섹션별 종목 |

#### 주문/계좌 (`/api/order/`, `/api/account/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| POST | `/api/order/buy` | 매수 주문 |
| POST | `/api/order/sell` | 매도 주문 |
| GET | `/api/order/pending` | 미체결 조회 |
| POST | `/api/order/cancel` | 주문 취소 |
| GET | `/api/account/positions` | 보유종목 조회 |

#### 뉴스/키워드 (`/api/news/`, `/api/keywords/`, `/api/messages/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET | `/api/news/today` | 당일 뉴스 (`?date=` `?until=` 필터) |
| GET | `/api/hotstock/parsed` | 급등주 메시지 파싱 결과 (`?date=` `?until=`) |
| POST | `/api/news/save` | 뉴스 스크랩 저장 |
| GET | `/api/news/saved` | 스크랩 목록 |
| DELETE | `/api/news/saved/<id>` | 스크랩 삭제 |
| POST/DELETE | `/api/keywords/include` | 포함 키워드 (body: `{keyword, type: news\|hotstock}`) |
| POST/DELETE | `/api/keywords/exclude` | 제외 키워드 |
| POST | `/api/keywords/cleanup` | 날짜 기준 메시지 정리 (`{source_type: news\|hot_stock}`) |
| GET | `/api/keywords/status` | 현재 키워드 목록 |

#### 시황체크 (`/api/siwhang/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET | `/api/siwhang/results` | 분석 결과 목록 (`?date=`) |
| POST | `/api/siwhang/results` | 분석 결과 저장 (스킬에서 호출) |
| DELETE | `/api/siwhang/results/<id>` | 결과 삭제 |

#### 백테스트 (`/api/backtest/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET/POST | `/api/backtest/sessions` | 세션 목록/생성 |
| GET | `/api/backtest/sessions/<id>` | 세션 상세 (picks 포함) |
| POST | `/api/backtest/picks` | 추천 종목 저장 (스킬 호출) |
| PUT | `/api/backtest/picks/<id>/pnl` | P&L 입력/수정 |
| GET | `/api/backtest/compare` | 버전 A/B 비교 |
| POST | `/api/backtest/fix-stock-codes` | NULL stock_code 자동 복원 |

#### 분석 컨텍스트 (`/api/analysis/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET | `/api/analysis/context` | 당일 morning_report + interval_context 조회 |
| POST | `/api/analysis/morning-report` | 시황 가설 저장 |
| POST | `/api/analysis/instruction` | next_instruction 저장/삭제 |
| POST | `/api/analysis/interval-context` | 슬롯 분석 후 테마 흐름 업데이트 |
| POST | `/api/analysis/request` | 분석 트리거 플래그 세팅 (웹 UI '▶ 지금 분석') |
| GET | `/api/analysis/pending` | poll_trigger.py 폴링용 — pending 확인 + 자동 클리어 |

#### Style3 (`/api/trade-watchlist/`, `/api/reentry/`, `/api/seeking-signal/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET/POST | `/api/trade-watchlist` | 감시 목록 조회/등록 (`?status=watching`) |
| POST | `/api/trade-watchlist-draft` | 일괄 draft 등록 |
| PUT/DELETE | `/api/trade-watchlist/<id>` | 수정/삭제 (status 변경 포함) |
| GET | `/api/reentry/signals` | 날짜별 시그널 조회 (`?date=`) — source='watchlist' |
| GET | `/api/reentry/morning-signals` | 관심종목 C시그널 (`?date=`) — source='morning', 종목별 그룹핑 |
| POST | `/api/seeking-signal/reentry-check` | 백테스트 모드 |
| GET/POST | `/api/morning-watchlist` | 관심종목 (JSON or CSV 텍스트) |

#### 재무/종목/格言
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET | `/api/financial-info?stock_code=` | 재무정보 (Kiwoom ka10001 + DART) |
| GET | `/api/stock/search?q=` | 종목명 키워드 검색 |
| GET | `/api/stock-master/<code>` | 마스터 + 시황 히스토리 + finance_stale 여부 |
| POST | `/api/stock-master/<code>` | 테마/노트 수동 업데이트 |
| POST | `/api/stock-master/<code>/refresh-finance` | Kiwoom+DART 재무 강제 갱신 |
| POST | `/api/stock-master/<code>/history` | 시황 히스토리 추가 (백테스트 스킬) |
| GET/POST/PUT/DELETE | `/api/mottos` | 격언 CRUD |

### 핵심 동작 로직

#### Mode2 매매 판단 (`price_monitor.py:check_mode2_conditions`)
```
현재가 polling (kiwoom_client_async: ka10003)
  ↓
매수 조건: current_price <= buy_target_price (±1% tolerance)
  ↓
매도 우선순위: resistance_2 > resistance_1 > trailing_exit > support_2 > support_1
  ↓
notify_only=True: 텔레그램 알림만 / False: 자동 주문 실행
```

#### 급등주 분석 / 시황체크 (`/siwhang` 스킬)
```
/siwhang 스킬 (로컬 Claude Code)
  ↓
SSH → Oracle localhost API
  ├── GET /api/hotstock/parsed (SS⬆️/VI/SS 파싱 메시지)
  ├── GET /api/news/today (DART 공시 포함)
  └── GET /api/watchlist (관심종목)
  ↓
AI 분석 (analysis.md 프롬프트) → Confidence H/M/L
  ↓
POST /api/siwhang/results → Oracle DB 저장 + 텔레그램 알림
```

#### 백테스트 분석 (`/backtest` 스킬)
```
1. POST /api/backtest/sessions → session_id 생성
2. GET /api/analysis/context → morning_report + interval_context
3. DART 공시 전체 사전 수집 (1회)
4. GET /api/hotstock/parsed + /api/news/today (전체)
   ↓ 백필 여부 판단 (received_at 동일이면 message_id 기준 13등분)
5. 13슬롯 순회 (09:15 ~ 15:15):
   ├── 신규 메시지 분리
   ├── SS⬆️ catalyst 3소스 조사 (뉴스DB + Google RSS + DART)
   ├── AI 분석 → picks JSON
   ├── POST /api/analysis/interval-context 업데이트
   └── POST /api/backtest/picks 저장
```

#### 재무정보 조회 (`/api/financial-info`)
```
Kiwoom ka10001 → 시총/PER/PBR/ROE/EPS/BPS/영업이익/매출/순이익/유통비율
  +
DART fnlttSinglAcntAll → 부채비율/유동비율
  ↓
결합 응답
```

### 분석 프롬프트 파일 위치

| 프롬프트 | 경로 | 역할 |
|---------|------|------|
| 시황체크 분석 | `.claude/skills/siwhang/prompts/analysis.md` | Confidence H/M/L 기준 |
| 백테스트 분석 | `.claude/skills/backtest/prompts/analysis.md` | 슬롯별 추천, interval_context 형식 |

**프롬프트 수정 가이드**: Confidence 기준 / 슬롯별 전략 / 출력 JSON 형식 / 분석 우선순위는 해당 md 파일의 섹션을 직접 편집. SKILL.md의 저장 로직과 동기화 필수.

### corp_code 매핑 관리
- 파일: `.data/corp_code_map.json` (stock_code → corp_code/corp_name)
- 역방향: `.data/stock_name_map.json` (corp_name → stock_code)
- 갱신: `scp CORPCODE.xml → python 파싱 → 두 파일 재생성`
- 자동복원: `POST /api/backtest/fix-stock-codes`

---

## 🖥️ Oracle 서버 부하 가이드

### 서버 스펙 (Oracle Cloud Free Tier)
- CPU: 1 OCPU (1코어) / RAM: ~1GB / Storage: SSD / 국내망 무제한

### 현재 실행 중인 프로세스 부하

| 프로세스 | CPU | RAM | 비고 |
|---------|-----|-----|------|
| `web_app.py` (Flask) | 0~2% | ~140MB | 요청 시 spike |
| `signal_listener.py` (Pyrogram) | 0~1% | ~100MB | 상시 연결 유지 |
| `PriceMonitor` (web_app 내) | 1~5% | 포함 | 장중 14종목 polling |
| **합계** | **~5%** | **~250MB** | **여유 충분** |

### 모니터링 capa (트랙별 구분)

**Mode2 자동매매 트랙**:
- 동시 polling (asyncio.gather) — 실측 ~1초 처리
- polling_interval: 알림전용=180초, 자동매매=30초
- **권장 최대 종목 수: 30개** (30초 interval, CPU spike 5% 이내)
- 40개 이상 시 polling lag 발생 가능

**Style3 폴링 트랙** (별도 트랙, 3분 주기):
- watching 종목 + morning_watchlist 130개 동시 처리
- 비동기 전환(2026-05-05) 후 150종목 ~30초 처리
- C2 일봉 캐시로 부하 분산

### 분석 capa (백테스트 / 시황체크)

**Oracle 서버 부하와 무관 — 로컬 PC에서 실행**:
- `/backtest`: 13슬롯 × 2 API 호출 = ~26 HTTP 요청. 5~15분 소요
- `/siwhang`: 1회 1~3분
- 동시 실행 제한: Oracle API rate limit 없음. Kiwoom API만 초당 5회 제한

### 메모리/DB 한계
- 자유 메모리 ~250MB
- SQLite 동시 write 경합 가능 (signal_listener + web_app)
- WAL 모드 미사용 (대량 write 시 lock 대기 가능)

### 부하 모니터링 명령
```bash
ssh opc@152.67.207.143
free -m
top -bn1 | head -20
ps aux | grep python | grep -v grep
du -sh ~/newkiwoom/.data/news.db
tail -100 ~/newkiwoom/web_app.log | grep -i "error\|warn\|kill\|oom"
```

### 최적화 권고
1. **뉴스 DB 주기 정리**: 매주 `/api/keywords/cleanup` 7일 이상 메시지 삭제
2. **Mode2 30개 이상 시**: polling_interval 180초로 (알림 전용)
3. **백테스트 실행 중 서버 재시작 금지**
4. **corp_code_map 갱신**: CORPCODE.xml SCP → 로컬 파싱 → fix-stock-codes
5. **SQLite WAL 모드** (선택): `PRAGMA journal_mode=WAL`

---

## TODO (구현 대기)

### High Priority
1. **매매일지 페이지** — 확정 손익 내역, 통계, Date filter
2. **계좌 polling** — 보유종목 주기 조회, 수동매도 자동 감지

### 선택
3. **시황체크 고도화**: 1일 자동 삭제 (매일 자정)
4. **백테스트 고도화**: 종목노트 소스 추가 (`note_source` 컬럼 준비 완료), 종목별 일봉 차트 + 추천 시점 마커

---

## Known Issues & Lessons

### 🔧 API/통신 이슈

#### kiwoom_chart.py get_minute_chart() return_code 체크 주의
Kiwoom ka10080 API는 응답에 `return_code` 필드를 반환하지 않음. `data.get("return_code") != 0` 체크를 넣으면 `None != 0 = True`이므로 **항상 실패** 처리됨. 성공 판정은 `stk_min_pole_chart_qry` 키 존재 여부로 해야 함.

#### ka10170 일별 매매일지 API 필수 파라미터
- 필수 파라미터: `ottks_tp` (0=전체), `ch_crd_tp` (0=현금+신용) — 둘 다 없으면 `return_code=2`
- 응답 리스트 키: `tdy_trde_diary` (기존 추측 `cts_acnt_dtls` 아님)
- 응답 구조: 종목당 **1행**에 매수+매도 통합
  - `buy_avg_pric` / `buy_qty`: 매수
  - `sel_avg_pric` / `sell_qty`: 매도 (0이면 매도 없음)
  - `pl_amt`: 당일 실현손익
- `strt_dt`/`end_dt`는 **체결일(cntr_dt)** 기준 (결제일 trde_dt +2영업일과 혼동 금지)

#### kt00015 메인계좌 조회 — 자주 틀리는 포인트
```python
client = KiwoomClient(account='main')
result = client._call_api('kt00015', {
    'acnt_no': client.account_no,
    'acnt_prdt_cd': client.account_product_code,
    'strt_dt': 'YYYYMMDD',
    'end_dt': 'YYYYMMDD',
    'ottks_tp': '0',    # ← 필수
    'ch_crd_tp': '0',   # ← 필수
})
trades = result.get('data', {}).get('tdy_trde_diary', [])
# sell_qty > 0 인 행만 익절 종목
```
- Oracle 서버에 메인계좌 키 없음 → **반드시 로컬 PC에서 실행**

#### Oracle SSH 복합 명령어 exit 255
SSH에서 `kill && restart` 같은 복합 명령은 간혹 exit 255로 실패.  
→ kill과 start를 **별도 SSH 호출로 분리**하고 ps aux로 확인.

#### Oracle 서버 SSH에서 Python f-string 중첩 따옴표 오류
SSH heredoc 안에서 `f"...{m.get("key")}..."` 형태는 파이썬 3.11 이하 SyntaxError.  
→ 해결책 1: f-string 대신 문자열 연결 (`"prefix" + var + "suffix"`)  
→ 해결책 2: `python3 << 'PYEOF' ... PYEOF` heredoc 패턴

#### Oracle API 인증 — 환경변수 미로드 시 401
Oracle SSH 내 Python에서 `os.environ.get("WEB_USERNAME")` 빈값이면 401.
```python
# 올바른 패턴
WU = "smh8857"; WP = "Saturday06.!chltnfus"

# 틀린 패턴 (Oracle SSH에서 환경변수 미로드)
WU = os.environ.get("WEB_USERNAME", "")  # → "" → 401
```

### 🗄️ DB/데이터 이슈

#### UTC vs KST 날짜 불일치
`messages.received_at`은 UTC 저장. `messages.date`는 KST 날짜 저장.  
당일 데이터 조회 시 `since=<UTC_ISO>` 대신 `date=YYYY-MM-DD` 파라미터 사용.

#### 백테스트 백필 데이터 타임슬롯 문제
signal_listener가 다운됐다가 Pyrogram history API로 백필한 데이터는 **모든 received_at이 백필 시각으로 동일**.  
→ `until` UTC 파라미터로 시간대별 필터 불가.  
→ 해결: `message_id`(텔레그램 채널 순번) 기준으로 13슬롯 균등 분배.  
→ 실시간 수집 데이터는 `until` 정상 동작.

#### 단위 변환
Budget: UI 입력/표시는 만원 단위, API 저장은 원 단위. 변환은 프론트엔드에서만.

#### Mode2 watcher API 필드명 (자주 틀림)
```python
# 올바른 필드명
{"code": "059090", "name": "미코", "buy_target_price": ..., "budget": ...}

# 틀린 필드명 (400 에러)
{"stock_code": "059090", "stock_name": "미코", ...}
```
필수 3개: `code`, `buy_target_price`, `budget`

#### Mode2 섹션 API 응답 구조
`GET /api/mode2/sections` 응답: `{"data": [{id, name, collapsed, order}, ...]}`
- `data`가 list (dict 아님) → `.get("sections")` 하면 None
- 섹션 id는 문자열: `"section_8_1777976873"` 형태

#### Mode2 watcher 등록 시 section_id 무시됨
`POST /api/mode2/watchers`에 `section_id` 포함해도 등록 후 `uncategorized`로 들어감.
→ 등록 후 반드시 `POST /api/mode2/watchers/{code}/move-section` 별도 호출 필요.
```python
api("POST", "/api/mode2/watchers", {..., "section_id": SID})  # section_id 무시됨
api("POST", "/api/mode2/watchers/090460/move-section", {"section_id": SID})  # 이걸로 이동
```

#### `/api/trade-watchlist-draft` POST 날짜 형식
- `buy_date`, `exit_date`: 반드시 `YYYY-MM-DD` (하이픈 포함)
- april_trade_sets.json의 date(YYYYMMDD) → 변환: `date[:4]+"-"+date[4:6]+"-"+date[6:]`

#### CSV HTS 관심종목 파일 파싱
- 인코딩: **CP949**
- 종목코드 컬럼: 마지막 컬럼, 값 앞 `'` 접두어
- `lstrip("'").zfill(6)` 처리 필요
- BLANK 행 필터링: `row[0].strip() == 'BLANK'` 또는 종목명 빈값 스킵

#### `/api/morning-watchlist` 업로드 방식
- **JSON**: `{"items": [{"code": "005930", "name": "삼성전자"}, ...]}`
- **CSV 텍스트**: `{"csv": "종목코드,종목명\n005930,삼성전자\n..."}`
- 파일 위치: `.data/morning_watchlist.json` (`MORNING_WATCHLIST_PATH` 오버라이드)

#### style3_signals.py 배포 누락 주의
web_app.py + price_monitor.py 양쪽에서 import하는 공유 모듈. 수정 후 git add 빠뜨리면 Oracle에 구버전이 남아 `signal_time` 같은 필드가 없는 상태로 실행됨. 반드시 커밋 전 `git diff style3_signals.py` 확인.

### 🚀 배포/운영 이슈

#### 텔레그램 봇 충돌
같은 TELEGRAM_BOT_TOKEN을 여러 서버에서 동시 실행하면 Conflict 에러. 현재 오라클 1곳에서만 web_app.py 실행.

#### signal_listener 포워딩 실패
`Chat not found` 에러가 나와도 **DB 아카이빙은 정상 동작**. 포워딩 실패는 목적지 채널 접근권한 문제.

#### Test endpoint vs 실제 로직 일치
`web_app.py` test endpoint 조건 로직은 `price_monitor.py`와 **완전 동일**해야 함. 경계값 (`<` vs `<=`) 특히 주의.

#### web_app.py 새 함수 작성 시 import 주의
`web_app.py`에는 `import json`이 원래 없었음. `news_storage` 등 다른 모듈이 먼저 로드되면서 side-effect로 `json`이 전역에 들어와 기존 코드는 동작했으나, 함수 구조를 바꾸는 순간 `name 'json' is not defined` 에러 발생.
→ **새 함수에서 json/datetime 등 표준 라이브러리 사용 시 반드시 파일 상단 import 명시 확인.**
→ `import json`은 현재 상단 2번째 줄에 추가돼 있음.

#### except Exception: pass — 절대 사용 금지
`_load_morning_settings`에서 `except Exception: pass`로 에러를 조용히 삼켜, `json is not defined` 에러가 발생해도 기본값(빈 목록)을 반환했고 원인 파악에 30분 이상 소요됨.
→ **except 블록에는 반드시 `logger.error(f"... {e}")` 포함.** 조용한 swallow는 디버깅을 극도로 어렵게 만듦.

#### morning_settings.json API 저장 불안정 이슈 (2026-05-07)
`POST /api/morning-settings/focus` 응답이 success여도 파일이 디스크에 안 저장되는 경우 있었음. 원인: `import json` 누락으로 `_save_morning_settings` 내부에서 실패해도 `except Exception: pass`가 삼킴.
→ **포커스 종목 등록은 스킬에서 파일 직접 write 방식 사용** (`/api` 호출 안 함). 경로: `/home/opc/newkiwoom/.data/morning_settings.json`

#### Oracle 서버 보안 강화 (2026-04-27)
대량 취약점 스캔 공격 (170.64.180.74 등 phpunit/ThinkPHP 패턴) 방어:

**KR IP Only (ipset)**:
```bash
# /etc/update_kr_ips.sh — 매주 일요일 02:00 cron 자동 업데이트
ipset create KR_IPS hash:net
for cidr in $(curl -s https://www.ipdeny.com/ipblocks/data/countries/kr.zone); do
  ipset add KR_IPS $cidr
done
iptables -I INPUT 1 -p tcp --dport 443 -m set --match-set KR_IPS src -j ACCEPT
iptables -I INPUT 2 -p tcp --dport 443 -j DROP
iptables -I INPUT 1 -p tcp --dport 443 -s 127.0.0.1 -j ACCEPT
```

**취약점 URL 패턴 차단**:
```bash
sudo iptables -I INPUT 1 -p tcp --dport 443 -m string --string "phpunit" --algo bm -j DROP
sudo iptables -I INPUT 1 -p tcp --dport 443 -m string --string "eval-stdin" --algo bm -j DROP
sudo iptables -I INPUT 1 -p tcp --dport 443 -m string --string "invokefunction" --algo bm -j DROP
```

**fail2ban 미적용 이유**: Oracle Linux 9 SELinux Enforcing에서 fail2ban-server 소켓 생성 실패. werkzeug failregex `<HOST>` 캡처 어려움. iptables string match로 대체.

**SSH 22번 포트는 KR IP 제한 없이 유지** (별도 관리).

### 💡 설계 원칙 (의사결정 배경)

#### 백테스트 분석 — 급등주 메시지 중심
AI 분석 소스 우선순위:
- **뉴스 DB는 노이즈 많아 분석 소스로 부적합** — 급등주 메시지(`[SS⬆️]`/`[VI]`/`[SS]`)가 핵심
- **일반 뉴스는 Tier3 (스킵)** — 시황 리포트, 증권사 리포트 제외
- **DART 공시는 Tier1 (항상)** — 당일 신규 공시 or 분석 종목 관련
- **Google News는 Tier2 (SS⬆️ catalyst 전용)**

**슬롯 시간대별 분석 역할**:
| 슬롯 | 역할 | 전략 |
|------|------|------|
| 09:15~09:45 | 테마 주도주 선점 | morning_report 가설 검증 |
| 10:15~11:45 | 연관주/확산주 발굴 | 주도주 관련주 중 안 오른 것 |
| 12:15~13:45 | 신규 테마 or 눌림목 | 오전 테마 눌림 + 새 시황 |
| 14:15~15:15 | 보수적 | H 확신 종목만, 고점 추격 금지 |

**원칙**: "이미 오른 종목 추종"이 아닌 "아직 안 오른 연관주/눌림목/신규 테마 선점". `already_picked` 중복 추천 금지. 슬롯당 최대 3종목.

#### 백테스트 종목 추천 기준 (슬롯당 최대 3종목)
```
Confidence H: SS⬆️(상한가) + 뉴스 교차확인 + 복합 테마(3개 이상)
Confidence M: VI발동 or 명확한 촉매 1개
Confidence L: SS만 있거나 단독 뉴스 (보통 미추천)

우선순위: SS⬆️ > VI(복합테마) > SS(watchlist_match만) > 뉴스 교차
SS 종목은 watchlist_match 있는 것만 분석 대상 (토큰 절약)
```

#### 백테스트 catalyst 조사: v1 vs v2
- **v1**: 내부 뉴스 DB + 급등주 메시지만. catalyst는 AI 추론값. sources 배열 비어 있음.
- **v2+**: SS⬆️ 종목에 대해 3소스 실조회:
  1. 내부 뉴스 DB (종목명 grep)
  2. Google News RSS (`종목명 상한가 OR 특징주 OR 급등`)
  3. DART 공시 API (`bgn_de=end_de=RUN_DATE`)
- 같은 날짜 v1/v2 재실행 후 웹UI 비교 패널에서 A/B 교차 확인 가능

#### 백테스트 버전 관리 전략
| 버전 | 전략 | 핵심 변경 |
|------|------|-----------|
| v1 | SS⬆️+VI 테마 강도 기반 | 기본: 테마 복합도 + 뉴스 교차 (AI 추론) |
| v2 | catalyst 우선 (3소스 실조회) | Google+DART 실조회, 확인된 것만 H |
| v3 | VI 확장 (watchlist 없어도 복합테마 3개↑) | VI 분석 범위 확대 |

#### 분석 컨텍스트 시스템 (`analysis_context`)
백테스트 분석 품질 향상용 구조화된 컨텍스트 시스템.

**DB 테이블 컬럼**:
- `context_date` (UNIQUE) — 날짜별 1개
- `morning_report` (JSON) — 해외증시, 예측 테마, 주요 내용
- `interval_context` (JSON) — 슬롯별 누적 테마 흐름 (confirmed/new/faded/already_picked)
- `next_instruction` — 사용자 1회성 추가 분석 지시
- `instruction_used` — 인스트럭션 소비 여부 (1회만 사용 후 null)

**스킬 사용 흐름**:
1. `/backtest` 실행 전 웹UI에서 morning_report 입력 + (선택) next_instruction
2. 스킬이 context 조회 → next_instruction consume (슬롯 시작 전 1회)
3. 각 슬롯 분석 후 interval_context 업데이트 → 다음 슬롯이 이전 테마 흐름 인지

**주의**: 새 날짜에 먼저 morning_report 입력 필수. DB 테이블 미생성 시:
```bash
python3 -c "from news_storage import NewsStorage; NewsStorage('.data/news.db')"
```

#### 시황체크 (Siwhang) 아키텍처
- AI 분석은 로컬 PC (Claude Code 스킬), 데이터는 Oracle API 조회
- `/siwhang` 스킬: `last_run.txt` 기준 증분 → Oracle fetch → AI 분석 → Oracle POST 저장 → 텔레그램
- `[SS]` 종목은 watchlist_match 있는 것만 분석 (토큰 절약)
- 결과: `siwhang_results` 테이블 + 웹UI `#siwhang` 섹션

#### 키워드 관리 (뉴스/급등주 분리)
- 뉴스(`news`)와 급등주(`hotstock`) 키워드 파일 완전 분리
- 급등주: `[SS⬆️]`(상한가) / `[VI]`(VI발동)는 키워드 필터 없이 무조건 표시
- `[SS]`만 키워드 필터 적용

#### 급등주 메시지 파싱 (hotstock regex)
- `[SS⬆️]` = 상한가, `[VI]` = VI 발동, `[SS]` = 급등 조짐 (confirmed surge 아님)
- `테마 : 테마명` 줄에서 테마 추출
- `Y 테마명 : 종목A, 종목B` 줄에서 관련주 추출
- 관심종목 매칭은 메인종목 + 관련주 전체 대상으로 비교

#### 백테스트 → 실전 연결 (Mode2 감시 등록)
- 백테스트 카드 하단 "📊 Mode2 등록" 버튼: 매수/익절/손절가 + 예산 → `POST /api/mode2/watchers`
- `notify_only: true` 기본값 — 알림만, 자동주문 실행 안 함
- stock_code 없는 종목은 버튼 미표시

#### 실전 트레이딩 페이지 + 분석 트리거
**실전 페이지 (`livePage`)**: 오늘 날짜 최신 backtest session picks (`GET /api/live/picks`)
- 모바일: 캐로셀 (1종목씩, 좌우 스와이프), 일봉 차트 lazy load
- 데스크탑: 스크롤 리스트
- 슬롯 탭바 (09:15~15:15), 현재 시간대 자동 선택

**분석 트리거 (A+B 조합)**:
- A (웹 수동): "▶ 지금 분석" → `POST /api/analysis/request`
- B (자동 폴링): `poll_trigger.py` 30초 주기 → `GET /api/analysis/pending` → pending이면 `claude --print "/siwhang"` 실행
- `get_and_clear_analysis_request()`: read + null clear atomically — 중복 실행 방지

**poll_trigger.py 실행**:
```bash
source .venv/bin/activate && python poll_trigger.py
# 장시간 외 자동 스킵 (09:00~15:35), IGNORE_MARKET_HOURS=1로 오버라이드
```

#### stock_master + 종목 Hover Tooltip
Mode2 감시종목 카드에서 종목명 hover 시 팝업.

**Hover 동작 흐름**:
1. 종목명 셀 `onmouseenter` → `showStockTooltip()`
2. 5분 클라이언트 캐시 → 없으면 `/api/stock-master/<code>` fetch
3. 툴팁 표시: 테마 태그 + 재무 6개 + 시황 히스토리 최근 10개
4. `finance_stale: true` 이면 "🔄 재무 갱신" 버튼 → `refresh-finance` 호출

**재무 stale 기준**: `finance_updated_at` 24시간 초과.
**테마 입력**: 현재 UI 없음 — `POST /api/stock-master/<code>` 직접 호출 또는 향후 노트 모달 연동 예정.

### 📱 UI 이슈

#### 모바일 UI
- 실전 페이지 (`/`) 하단 탭바: 실전, Mode2, 시황체크, 발라먹기, Mode1, 감시리스트, 매매일지
- 어드민 페이지 (`/adminpage`) 하단 탭바: AI슬롯분석, 종목마스터, Test
- 기본 시작 페이지: Mode2
- 가로모드 감지: `(max-height: 500px) and (orientation: landscape)`
- 시황체크 테이블: 카드별 개별 검색 입력 (`data-search` pre-compute)

#### 백테스트 시스템 UI
- DB: `backtest_sessions` (날짜별 세션) → `backtest_picks` (슬롯별 추천) → `backtest_pnl` (P&L 입력)
- `version` + `strategy_desc` — 같은 날짜 복수 전략 A/B 비교
- `catalyst` — 상한가 종목 시황/재료/뉴스 요약
- `sources_json` — `[{type, time, text}]` 근거 목록 (hotstock/news/google/dart)
- `note_source` — 향후 종목노트 소스 연결 예약 필드
- `get_messages()` `until_utc` 파라미터 (백필 데이터는 received_at 동일해서 무효)

---

## 2026-05-10 작업 — Lessons Learned

### siwhang v2 스킬 신설 (Entry Gate 필터)

**배경**: 추천 종목이 이미 급등 이후여서 "고점 판독기" 문제 발생. 5가지 구조적 문제 파악:
1. 텔레그램 채널 메시지 수신 자체가 후행 (이미 급등 후)
2. related_stocks 현재가 미확인 (채널 미등장 ≠ 덜 오름)
3. 뉴스 매칭이 후행지표 (많이 오른 종목일수록 뉴스 언급 ↑ → confidence 상향 역설)
4. 가격 레벨 정보 없음
5. 시간대별 전략 없음

**구현**: `.claude/skills/siwhang-v2/` — v1 그대로 두고 Entry Gate 단계 추가.
- `entry_gate_data.py`: ka10081(일봉) + ka10080(5분봉) → 등락률/갭/RSI/VWAP/거래량비율
- Gate 판정: PASS(0개 실패) / WARN(1개) / BLOCK(2개+)
- BLOCK 종목은 confidence=L 강제, picks 저장 제외
- DB 버전: `siwhang_v2` → 실전 페이지에서 v1과 A/B 탭 비교

**실전 페이지 A/B 탭**: `_version` 필드로 picks 구분. v2 data 있을 때만 버전 탭 노출.
카드에 gate 정보 블록 표시 (✅ PASS / ⚠️ WARN / 🚫 BLOCK + 실패 지표 목록).

### manual_focus — morning_report 수동 관련주 등록

**배경**: `[SS]` 급등조짐 종목은 관심종목(watchlist/Mode2) 매칭인 것만 분석했는데, 오늘 아침 특정 뉴스 관련주를 임시로 분석 대상에 올리고 싶어도 방법이 없었음.

**구현**: 실전 페이지 시황설정 > 주요 내용(자유입력)에 아래 형식으로 입력:
```
뉴스 제목
관련주: 종목A, 종목B, 종목C
다른 뉴스 제목
관련주: 종목D, 종목E
```

**파싱 규칙** (v1/v2 공통, SKILL.md Step 2):
- `관련주:` 로 시작하는 줄 → 콤마 split → 각 토큰 strip
- 직전 비어있지 않은 줄 = `source_news` (뉴스-종목 1:1 연결)
- 같은 종목이 여러 뉴스에 속하면 `source_news` 배열에 누적
- 결과: `[{stock_name, source_news: [...]}]`

**[SS] 필터 확장 (AND 조건)**:
- 기존: `[SS]` && `watchlist_match` 있는 것
- 변경: `[SS]` && (`watchlist_match` 있음 OR `manual_focus`에 본인/related_stocks 포함)
- 즉 `[SS]`로 등장했다는 게 필수 전제(AND 왼쪽), 관심종목 OR 수동지정이 우측 조건

**AI 분석 반영**: `source_news`를 1차 촉매로 간주 → `has_news_match=true`. analysis_text에 `[수동지정]` 태그.

**파싱 검증**: `관련주:` 다음 줄이 다른 뉴스 제목이면 정확히 분리됨. 줄 중간 종목명 잘림(AP\n시스템) 방지 위해 사용자가 같은 종목은 줄바꿈 없이 입력.

### backtest_picks 가격 스냅샷 추가

**배경**: 추천 카드에 "얼마일 때 추천했는지"가 없어 사후 검증 불가.

**신규 DB 컬럼** (backtest_picks, ALTER TABLE 마이그레이션):
- `price_at_signal` REAL — [SS/VI] 메시지 수신 시점 3분봉 종가
- `prev_close` REAL — 전일 종가
- `today_open` REAL — 당일 시가

**수집 스크립트**: `.claude/skills/siwhang/price_snapshot.py`
- 인자: `종목코드:signal_hhmmss(KST6자리)` (예: `230240:091345`)
- ka10081(일봉) → prev_close, today_open
- ka10080(3분봉, count=80) → signal 시각 포함 봉 종가 = price_at_signal, 최신 봉 = price_at_slot
- 1분봉 대신 3분봉 선택 이유: 노이즈 감소 + price_monitor와 동일 API + 최대 3분 오차 허용 범위

**스킬 실행 순서**: Step 4(AI 분석) 완료 후 → Step 4-B(가격 수집) → Step 5(picks 저장 시 필드 포함)

**카드 UI** (app.js `renderLivePickCard`):
- `prev_close` 있을 때만 타임라인 블록 표시 (null이면 숨김 — 구버전 데이터 호환)
- 표시 형식:
  ```
  [SS/VI] 09:13  15,400원  전일比+2.1%  시가比+0.8%
  분석 09:15     15,650원  전일比+3.7%  시가比+2.3%
  ```
- signal 시각: `received_at`(UTC) → KST 변환 (별도 컬럼 없이 프론트에서 계산)
- signal == slot 동일 봉이면 1줄 표시 생략 (중복 방지)

**주의**: 기능 추가 이전(~2026-05-09) picks는 가격 필드 전부 null → 카드에 타임라인 미표시. 소급 적용 불가.

### watchlist_match 소스 범위 (중요)
`/api/hotstock/parsed` 에서 계산되는 `watchlist_match`는 **2개 소스만**:
1. `.data/watchlist.json` (감시리스트 탭 수동 등록)
2. Mode2 watchers (Mode2 탭 등록 종목)

**포함되지 않는 것**: morning_watchlist 130종목, trade_watchlist(발라먹기 watching)
→ `[SS]` 필터 통과 여부는 위 2개 소스 기준. manual_focus는 별도 경로로 추가됨.

---

## 2026-05-12 작업 — Lessons Learned

### siwhang v1/v2 cron 분리 + 메시지 헤더 개선

**현상**: cron `14,44 * * 1-5`로 v2 자동 실행 중인데, 같은 시간대에 v1도 따로 돌아 텔레그램이 두 번 옴 (12:23 v1 / 12:31 v2). 헤더 표기 "(12:09 기준)"이 분석 시각인지 fetch 시작점인지 불분명.

**원인**:
- v1과 v2가 **last_run 파일을 따로 관리** (`siwhang/prompts/last_run.txt` vs `siwhang-v2/prompts/last_run_v2.txt`) → fetch 윈도우 어긋남.
- v2가 13:05에 끝났을 때 직전 v2 실행이 12:32였다면 윈도우 33분짜리로 거슬러 올라감 → 헤더 "12:32 기준"은 정상 동작이지만 사용자 입장에선 "왜 이전 시간을?" 의문.

**조치**:
- 메시지 헤더 형식을 **`(HH:MM~HH:MM 분석)`**으로 변경 (fetch 윈도우 시작~분석 시점). v1/v2 SKILL.md 동시 수정 후 Oracle SCP 배포.
- v1/v2 같은 시간대 cron 충돌은 별도 cron 정리 필요 (이번 세션에선 v2만 살림). v1 cron은 다른 Claude Code 세션에서 등록됐을 수 있어 그쪽에서 `CronDelete` 필요.

**왜 자동 실행이 17분 걸리나**: cron 트리거 12:14 → 발송 12:31 = 17분. 분해 추정:
- fetch 1~2분 + AI catalyst 조사(Google RSS + DART + 뉴스 grep) 5~10분 + Entry Gate(Oracle SSH) 1~2분 + 저장+텔레그램 1분.
- 30분 cron 주기와 거의 겹쳐서 다음 실행과 시간이 가까워질 위험 있음. 종목 수 많으면 더 오래.

### Entry Gate `vol_ratio` 기준 재검토 필요 (잠재 이슈)

**관찰**: 2026-05-12 오후 분석 결과 24종목 중 거의 전부가 vol_ratio < 1.2로 WARN/BLOCK 처리됨. 평균 +5~10% 상승 종목들조차 거래량이 "최근 1봉 / 직전 5봉 평균" 기준으로 0.0~0.7 사이에 분포.

**원인 추정**: SKILL.md 4-2의 vol_ratio 정의가 "현재 봉 vs 5봉 평균"이라, 5분봉 한가운데에 시간이 끼면 현재 봉 거래량이 아직 누적 중이라 항상 낮게 잡힘. 점심시간 직후/오후 후반 등 활동성 떨어지는 시간대도 모두 fail.

**대응 방향(미적용)**: 시간대별 가중 평균(전일 동시간 대비)으로 변경하거나, 진짜 모멘텀 죽음만 잡도록 임계 0.5로 완화. 현재는 vol_ratio 기준이 "WARN을 양산하는 노이즈 게이트"가 됨.

### `received_at` 컬럼 추가 (가격 카드 시각 표시)

**배경**: `[SS/VI]` 카드에 가격은 보였지만 **수신 시각이 안 보였음**. v1 코드(app.js:8270~)는 `p.received_at`을 UTC ISO로 변환해서 `12:13` 표시하게 작성됐지만, **`backtest_picks`에 `received_at` 컬럼 자체가 없어** 응답에 안 실림.

**조치 (A안 채택)**:
- `news_storage.py`에 `ALTER TABLE backtest_picks ADD COLUMN received_at TEXT` 마이그레이션 추가
- `save_backtest_pick()`에 `received_at` 파라미터 추가
- `web_app.py /api/backtest/picks` 페이로드에 `received_at` 통과
- **KST 문자열로 저장** (`"YYYY-MM-DD HH:MM:SS"`). UTC 저장 + 프론트 변환은 사용자 요청에 따라 거부 — DB 직접 조회 시 KST가 더 직관적.
- `static/js/app.js` 카드 코드: KST 문자열에서 `HH:MM` regex로 직접 추출 (UTC 변환 코드 제거)
- siwhang/siwhang-v2 SKILL.md에 picks 저장 시 `received_at` 필드 포함 지시 추가

**변환 패턴** (메시지의 `received_at`은 UTC stored이므로 KST로 변환 후 저장):
```python
from datetime import datetime, timezone, timedelta
KST = timezone(timedelta(hours=9))
dt_utc = datetime.fromisoformat(received_at.replace(' ','T')).replace(tzinfo=timezone.utc)
received_at_kst = dt_utc.astimezone(KST).strftime("%Y-%m-%d %H:%M:%S")
```

**주의**: `messages.received_at`은 여전히 UTC 저장 (signal_listener 로직). picks 테이블만 KST. 이 불일치를 인지할 것.

### 실전 페이지 슬롯 매핑 한계 (미해결)

**현상**: cron 분이 `14,44`라 분석 종료가 23~33분 사이 떨어지면 picks의 `slot_time`이 `13:23` 같은 비정형 시각이 됨. 프론트 `_LIVE_SLOTS`는 30분 그리드(`09:15, 09:45, ...`)만 가짐 → `_hhmmToNearestSlot`이 가장 가까운 이전 슬롯에 매핑.

예: `slot_time=12:09` pick은 11:45 슬롯 카드로, `slot_time=13:23` pick은 12:45 슬롯에 매핑됨 → 사용자가 12:15 슬롯 탭을 보면 비어있는 카드.

**해결 옵션 (미적용)**:
- A. cron 분 조정 (`14,44` → `15,45` 또는 `05,35`) — 분석 시작/종료를 정형 슬롯에 맞춤. 가장 작은 변경.
- B. 실전 페이지 한정 동적 슬롯 — picks의 `run_at` distinct 시각을 그대로 탭으로 노출. 백테스트 페이지의 13슬롯 모델과 분리.

추천 B (사용자 의견 수렴 후 결정).

### 권한 자동 실행 설정

**배경**: 30분 cron 자동 실행 중 권한 prompt가 뜨면 분석이 멈춤. SKILL.md "절대 묻지 않는다" 원칙과 충돌.

**조치**: `.claude/settings.json` 신설 (프로젝트 공유 설정, settings.local.json과 별도):
```json
{
  "permissions": {
    "allow": [
      "Bash(ssh *)", "Bash(scp *)", "Bash(.venv/bin/python3 *)",
      "Bash(python3 *)", "Bash(curl *)", "Bash(git *)",
      "Write(/Users/msim/Documents/newkiwoom/**)",
      "Edit(/Users/msim/Documents/newkiwoom/**)",
      "Read(/Users/msim/Documents/newkiwoom/**)",
      "Read(/tmp/**)",
      ...
    ]
  }
}
```

**주의**:
- `Bash(ssh *)` / `Bash(python3 *)` 등은 임의 코드 실행을 가능케 함 — 보안 트레이드오프. 자동화 우선.
- `.claude/`는 `.gitignore`에 등록돼 있어 settings.json은 공유되지 않음. SCP로 Oracle 등 다른 환경에 별도 배포 필요 시 주의.
- settings.json은 **세션 시작 시점**에 로드. 변경 후 즉시 적용 안 될 수 있음 — 다음 세션부터 완전 적용.

**fewer-permission-prompts skill 정책 우회 사유**: skill은 `python3 *`, `ssh *` 와일드카드를 거부하지만, 사용자가 cron 자동화 우선으로 요청 → 명시적 우회.

### siwhang-v2 manual_focus 활용 사례 (2026-05-12 오후)

**상황**: 12:13 [SS]엑스게이트 → 12:14 cron v2 트리거 → 분석 진행. 엑스게이트는 watchlist_match 비어있지만 morning_report `관련주:` 목록에 등록돼 있어 manual_focus 매칭으로 분석 대상 진입.

**확인된 흐름**:
1. signal_listener → DB messages 적재 (UTC received_at)
2. `[SS]` AND (`watchlist_match` OR `manual_focus 매칭`) 필터 통과
3. Entry Gate: stock_name_map → 코드 조회 → Oracle entry_gate_data.py 실행
4. AI 분석 → confidence M (PQC 정부 실증 + manual_focus)
5. backtest_picks (session id=13, slot_time=12:09) + siwhang_results 동시 저장
6. 텔레그램 발송 → `last_run_v2.txt` 갱신

**검증된 picks 가격 필드 (id=392)**: `price_at_signal=16,260` / `price_at_slot=16,260` / `prev_close=15,300` / `today_open=17,600`. entry_gate_data.py의 snapshot 결과 재활용.

### 자동 실행 원칙 강화

stage가 끝날 때마다 사용자에 묻지 않고 자동 진행:
- fetch 결과 0건 → "분석 대상 없음" 텔레그램 + last_run 갱신 후 종료
- Kiwoom 토큰 인증 실패 → catalyst에 경고 표기 후 picks 저장 진행 (price 필드 null)
- SSH/저장/텔레그램 어느 단계든 실패해도 last_run 반드시 갱신 (다음 cron이 같은 윈도우 재처리 방지)

이 원칙은 v1/v2 SKILL.md "⚡ 자동 실행 원칙" 섹션에 명시. 권한 prompt 회피 패턴(권한 트리거 회피 — 명령 작성 규칙)도 SKILL.md에 명시.

### ⚠️ scp 후 반드시 web_app 재시작 확인

**현상**: `web_app.py`/`news_storage.py`를 scp로 Oracle에 올리고 admin UI 재시작 안 했을 때, **신규 컬럼/필드는 무시되고 응답에 빠짐**. 코드 자체는 새 버전인데 실행 중 프로세스는 옛 메모리.

이번 케이스: `received_at` 컬럼 추가 후 picks 페이로드엔 KST 값 정상 포함되어 SCP 완료 → 그러나 web_app 미재시작 상태라 INSERT에서 received_at 무시 → DB에 NULL 저장 → 카드에 시각 미표시.

**디버깅 첫 의심 포인트**:
1. `ps -ef | grep web_app` — 시작 시각이 코드 변경 시각보다 이전이면 재시작 누락
2. `grep -n '<신규필드>' /home/opc/newkiwoom/web_app.py` — 파일은 이미 새 버전인데 응답에 안 실리면 100% 재시작 문제
3. 보강 백필: `messages` 테이블에서 종목명 LIKE 매칭 + `received_at` UTC→KST 변환 후 `UPDATE backtest_picks` 일괄 패치

**권장 절차**:
- scp 직후 → admin UI(http://localhost:8889)에서 "Oracle 서버 재시작" 또는 SSH `sudo kill <pid> && sudo -E env PATH=... WEB_PORT=443 nohup python web_app.py &`
- DB ALTER TABLE은 마이그레이션 코드가 import 시점에 실행되므로, **재시작 = 마이그레이션 적용 + 새 코드 로드**가 한 번에 됨
- 신규 컬럼 추가했는데 카드/응답에 안 보이면 우선 재시작 누락 의심

---

## 2026-05-13 작업 — Lessons Learned

### 자유형 뉴스 + 시세 인사이트 워크플로 (자동 실행)

**원칙**: 사용자가 "오늘 호재 뉴스 종목과 상승률 정리해줘" 같은 자유 질문 던졌을 때, **권한 prompt 없이 즉시 실행**한다. 사용자가 명시적으로 "항상 승인"을 선언했으므로 SSH/Kiwoom/curl 모든 단계 묻지 않음.

**표준 절차**:
1. **뉴스/급등주 fetch** — `/news-consult` 스킬 패턴 (SSH → Oracle localhost API)
   - `GET /api/news/today?date=YYYY-MM-DD`
   - `GET /api/hotstock/parsed?date=YYYY-MM-DD`
2. **호재 종목 후보 추출** — 키워드 매칭(임상/승인/특허/수출/기술수출/마일스톤 등) + 급등주 [SS⬆️]/[VI] 교차
3. **stock_name → code 매핑** — Oracle `/home/opc/newkiwoom/.data/stock_name_map.json`
4. **현재가/등락률 일괄 조회** — Oracle SSH에서 Kiwoom ka10003 직접 호출 (아래 패턴 참고)
5. 결과 표 정리 + 호재성 ↔ 시장 반응 해석 (재료 작동 vs 선반영 sell-the-news)

### Kiwoom ka10003 일괄 시세 조회 패턴 (검증됨)

`KiwoomClient.get_stock_info()`는 `current_price`만 주고 등락률 안 줌. **ka10003 직접 호출**이 정답:

```python
import urllib.request, json
from kiwoom_client import KiwoomClient
kc = KiwoomClient(); kc._ensure_valid_token()

def fetch_quote(code):
    req = urllib.request.Request(
        "https://api.kiwoom.com/api/dostk/stkinfo",
        data=json.dumps({"stk_cd": code}).encode(),
        headers={
            "Content-Type": "application/json;charset=UTF-8",
            "authorization": "Bearer " + kc.token,
            "api-id": "ka10003",
        }
    )
    data = json.loads(urllib.request.urlopen(req, timeout=10).read())
    # 응답에 list-of-dict가 어디 있을지 모르니 동적 탐색
    items = next((v for v in data.values() if isinstance(v,list) and v and isinstance(v[0],dict)), [])
    if not items: return None
    latest = items[0]  # 첫 행 = 가장 최신 체결
    return {
        "cur": latest.get("cur_prc","").lstrip("+-"),  # 부호 제거
        "chg_pct": latest.get("pre_rt"),               # 등락률 (예: "+12.92")
        "chg_amt": latest.get("pred_pre"),             # 전일대비 금액
        "tm": latest.get("tm"),                         # HHMMSS
        "vol": latest.get("acc_trde_qty"),             # 누적거래량
    }
```

**주의**:
- `cur_prc` 등 가격 필드는 `+` 또는 `-` 부호 prefix가 붙어있음 → 표시할 때 `.lstrip("+-")`
- 응답 list 키 이름이 종목/시점에 따라 달라질 수 있어 `next((v for v in data.values() if isinstance(v,list) ...))` 패턴이 안전
- 호출 간격 0.2초+ (rate limit 5/sec 여유)

### Oracle 원격 Python 실행 패턴 (heredoc 함정 회피)

heredoc 안에 f-string 중첩 따옴표 / 이모지 / 한글 등 들어가면 SyntaxError 자주 남. **로컬에서 .py 작성 → SCP → Oracle에서 실행**이 가장 안정적:

```bash
# 1. 로컬에서 작성
Write /tmp/myscript.py

# 2. SCP
scp -i $SSH_KEY /tmp/myscript.py opc@152.67.207.143:/tmp/myscript.py

# 3. Oracle에서 newkiwoom 디렉터리로 옮긴 뒤 실행 (cwd 의존 import 때문)
ssh -i $SSH_KEY opc@152.67.207.143 'cp /tmp/myscript.py ~/newkiwoom/_tmp.py && cd ~/newkiwoom && source .venv/bin/activate && python3 _tmp.py && rm _tmp.py'
```

**왜 ~/newkiwoom 안에서 실행해야 하나**: `kiwoom_client.py` 등 프로젝트 모듈이 `sys.path` 기준 cwd에 있어야 import됨. `/tmp`에서 그냥 돌리면 `ModuleNotFoundError`.

### siwhang-v2 entry_gate_data.py 재활용

자유형 인사이트 요청에서 등락률만 필요하면 ka10003으로 충분하지만, **추가 지표(RSI/VWAP/거래량비율/갭) 필요하면 siwhang-v2의 `entry_gate_data.py` 재사용 가능**.

```bash
# .claude/skills/siwhang-v2/entry_gate_data.py 가 이미 일봉+5분봉+RSI/VWAP/거래량비율 한번에 계산
ssh -i $SSH_KEY opc@152.67.207.143 'cd ~/newkiwoom && source .venv/bin/activate && python3 .claude/skills/siwhang-v2/entry_gate_data.py 078160 196170 950220'
```

출력은 `{code: {change_pct, gap_pct, rsi, vwap_gap_pct, vol_ratio, gate_pass}}` JSON.

자유 질의 답변에 깊이가 필요할 때(눌림목 진입 가능성, 추격 위험 평가 등)는 entry_gate_data 결과를 같이 보여줄 것.

### 호재 → 주가 해석 프레임 (자유 인사이트용)

추천 패턴이 아니라 **재료와 시장 반응을 교차 해석**:

| 패턴 | 등락률 | 해석 |
|------|--------|------|
| 호재 + 상한가/SS⬆️ | +25%~30% | 재료 작동 — 추격 위험 (이미 반응) |
| 호재 + 강세 (+10~20%) | 보통 [VI] 동반 | 진행 중 — 눌림 대기 가능 |
| 호재 + 약세/혼조 (-2~+3%) | — | 선반영 또는 시장이 호재로 안 받음 |
| 호재 + 폭락 (-10%↓) | — | sell the news 또는 다른 악재 동시 발생. 메디포스트 5/13 카티스템 임상3상 성공 발표 → -16.89% 사례 |

답변 표에 등락률만 나열하지 말고 **"재료 작동" / "선반영" / "sell the news"** 한 줄 해석을 같이 줄 것.

### 권한 자동 승인 항목 (사용자 명시적 사전 승인)

다음 작업들은 **항상 묻지 않고 즉시 실행**:
- Oracle SSH 임의 명령 (`ssh ... '...'` 모든 형태)
- Oracle SCP 파일 전송 (양방향)
- Kiwoom API 임의 호출 (시세/차트/계좌조회 — 단, 주문 API는 제외)
- Oracle localhost API 호출 (Basic Auth + curl)
- `/tmp` `~/.claude/projects/.../tool-results/` 임시 파일 작성/조회
- 뉴스 fetch + 종목 코드 매핑 + 시세 일괄 조회 워크플로 전체

**계속 사용자 확인이 필요한 작업** (이 자동 승인에서 제외):
- 실거래 매수/매도 주문 (`place_buy_order`/`place_sell_order`)
- Oracle 서버 재시작/중단 (`oracle-server` 스킬 호출은 OK, 직접 kill은 사용자 의도 확인)
- git push, force-push
- DB DROP/DELETE 류 destructive 쿼리

---

## 2026-05-14 작업 — Lessons Learned

### Mode2 watcher entry에 빈 code 발생 → UI 삭제 안 됨

**현상**: `mode2_watchers.json`의 watchers dict에 `key=""`(빈 문자열) entry가 들어가는 경우 UI 삭제 버튼이 동작하지 않음.

**원인**: UI 삭제는 `DELETE /api/mode2/watchers/<code>` 호출 → `code=""`이면 URL이 `/api/mode2/watchers/` 가 되어 라우트 미매칭. 결과적으로 무반응.

**근본 원인 (추정)**: 등록 흐름 어딘가에서 종목코드 정규화 누락 또는 API 페이로드 검증 누락. **재발 방지를 위해 watcher 등록 API에 `code` 빈 값 거부 검증을 추가하는 것이 좋음** (현재 미적용).

**복구 절차**:
```python
# /home/opc/newkiwoom/.data/mode2_watchers.json — root 소유라 sudo 필요
ws = d["watchers"]
for code in list(ws.keys()):
    if code == "" or not code:
        del ws[code]
# sections[].watchers 리스트에서도 "" 제거
```
백업: `mode2_watchers.json.bak_YYYYMMDD` 생성 후 진행. **수정 후 web_app 재시작 필수** (메모리상 dict가 디스크 덮어쓰기 방지).

### Mode2 벌크등록 — 종목명 입력 지원 (`static/js/app.js: executeBulkAdd`)

**변경**: 첫 컬럼이 **숫자만**이면 종목코드(6자리 zero-pad), 그 외는 종목명으로 간주 → `/api/stock/search` 조회. 헤더 alias도 `종목코드`/`종목명`/`종목` 모두 `'stock'` 으로 통합.

**API 응답 키 함정** (이전 버그):
- `/api/stock/search` 응답: `{success, results: [{stock_code, stock_name}]}`
- 잘못된 코드: `srData.data` / `.code` 사용 → 종목명 입력 시 항상 실패
- 올바른 패턴: `srData.results || srData.data` 폴백 + `pick.stock_code || pick.code` 폴백

**정확 일치 우선 + 후보 다수 시 실패 처리**:
- 정확히 같은 이름이 있으면 그것 사용
- 정확 일치 없고 후보 여러 개면 실패 목록에 후보 3개까지 표시 (사용자 재시도)
- 자동으로 첫 번째 후보 채택하지 않음 (오등록 방지)

**같은 패턴이 적용된 다른 화면**: 시황체크 관심종목 입력 (`addWatchlistItems`, `saveWatchlistEdit`) — 공통 헬퍼 `_resolveWatchlistTokens()` 추가.

### Mode2 인라인 편집 budget 단위 변환 누락

**증상**: 종목 행 budget cell을 편집하면 만원 단위 변환이 안 돼서 입력값이 원 단위로 저장됨. UI 표시 "10만" → 편집 input "10" → blur 시 `data.budget = 10` PUT → DB 10원 저장.

**원인 — 인라인 편집 경로가 2개**:
1. **셀 더블클릭** (`enableCellEdit`) — 단건 cell 편집, blur/Enter 저장
2. **연필 아이콘 → 행 편집 모드** (`enterEditMode` + `saveWatcherRow` + `saveSectionWatchers`) — 행 단위 일괄 ✓ 저장

`enableCellEdit`은 budget 단위 변환 코드가 있었지만, **2번 경로(`enterEditMode`)와 섹션 일괄 저장(`saveSectionWatchers`)에는 단위 변환 로직이 없었음**. 사용자가 주로 쓰는 경로가 2번이라 문제 발생.

**수정 패턴**:
- 셀 렌더 시 `data-raw="${w.budget}"` 속성으로 원본 원 단위 값 저장
- 편집 모드 진입 시 `parseInt(data-raw) / 10000` 으로 만원 표시
- 저장 시 `data[field] = isBudget ? (parseInt(input) * 10000 || 0) : (parseInt(input) || 0)` 변환

**같은 함수 안 다른 함정 — `isNote` 변수 누락**:
`enableCellEdit`에서 `isNote` 변수 선언 없이 참조 → ReferenceError 발생 → blur 핸들러가 saveEdit 진입 첫 줄에서 throw → "Enter/blur 저장 안 됨" 증상. 콘솔 빨간 에러 확인이 첫 디버깅 단계.

### Mode2 인라인 편집 — 셀 안 이모지/단위 문자열 함정

**증상**: 1차지지 셀을 행 편집 모드(연필→✓)로 저장하면 가격이 0으로 덮어써짐.

**원인**: 1차지지 셀 안에 가격 + 이모지(📥 물타기 / ✂️ 손절)가 함께 들어있음. `enterEditMode`가 `cell.textContent` 를 그대로 input value로 넣음 → `<input type="number">` 가 `"22,425 📥"` 같은 비숫자 문자열을 거부 → input 빈 값 → ✓ 저장 시 `parseInt("") || 0 = 0` PUT.

**수정**: 가격 셀에서 input 값 추출 시 정규식 `/-?\d+/` 으로 **숫자만** 추출. `enterEditMode` (행 편집)와 `enableCellEdit` (셀 더블클릭) 양쪽 다 적용.

**연쇄 영향**: 사용자가 1차지지 안 건드리고 다른 필드만 행 단위 저장해도 1차지지가 0으로 덮어써짐. 즉 행 편집 모드 진입 자체가 버그 트리거.

### Mode2 1차지지 셀 — 물타기 모드 시각화

**변경**: `support_1_mode === '물타기'` AND `support_1_price > 0` 조건일 때 셀 배경 `rgba(173, 216, 230, 0.35)` (투명 하늘색). 손절 모드 또는 가격 미설정 시 배경 변화 없음. 글씨/이모지 가독성 유지.

### 시황체크 관심종목 — 종목명 입력 지원 + 표시 보정

**변경 1 (프론트, `app.js`)**: `addWatchlistItems` / `saveWatchlistEdit` 가 공통 헬퍼 `_resolveWatchlistTokens()` 사용. 토큰별로 숫자 → 코드, 그 외 → `/api/stock/search` 조회.

**변경 2 (백엔드, `web_app.py`)**:
- `POST /api/watchlist` 와 `POST /api/watchlist/bulk` 가 종목코드 저장 시 `_load_corp_code_map()` 으로 종목명 조회해서 `name` 필드 채움 (이전엔 `name=code` 로 저장됨)
- `GET /api/watchlist` 응답에서 `name == code` 또는 빈 값이면 corp_map으로 보정해서 반환 → **기존에 잘못 저장된 manual 항목도 자동 표시 보정** (DB/JSON 마이그레이션 불필요)

**왜 백엔드까지 손대야 했나**: 프론트에서 종목명 → 코드 변환만 했더니 manual 항목이 `{code: "035720", name: "035720"}` 으로 저장돼 UI에 `035720(035720)` 표시됨. 코드 → 종목명 lookup이 백엔드에 있어야 일관성 유지.

### scp 후 web_app 재시작 — Python 코드 변경은 반드시 재시작

**규칙**: `web_app.py` / `news_storage.py` / `mode2_manager.py` 등 **Python 모듈** 변경 시 항상 재시작 필요. JS/HTML/CSS만 변경한 경우 재시작 불필요 (사용자 측 Cmd+Shift+R 만으로 충분).

**재시작 절차** (검증된 패턴):
```bash
ssh -i $KEY opc@$HOST "sudo pkill -f 'web_app.py'"
ssh -i $KEY opc@$HOST "ps aux | grep web_app | grep -v grep"  # exit 1 = 종료 확인
ssh -i $KEY opc@$HOST "cd ~/newkiwoom && bash start_https.sh"
ssh -i $KEY opc@$HOST 'curl -sk -o /dev/null -w "%{http_code}" -u "$WU:$WP" "https://localhost/api/analysis/context?date=$(date +%Y-%m-%d)"'  # 200 확인
```

**SSH 복합 명령 exit 255 회피** (CLAUDE.md 기존 항목 재확인): `kill && start` 한 줄에 묶지 말고 **별도 SSH 호출로 분리**. `sudo pkill -f 'web_app.py' 2>/dev/null; pkill -f 'signal_listener.py' 2>/dev/null; sleep 1; echo done` 같은 복합 형태도 exit 255 자주 발생.

---
