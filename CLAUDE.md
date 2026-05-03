# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## 매매 스타일 3종

### Style1 — 눌림매매 (수동)
전일 대비 강하게 상승한 종목의 첫 조정 구간 매수. Mode1이 분봉 조건 알림 제공.

### Style2 — 대장주/연관주 매매 (백테스트→Mode2 등록)
급등주 메시지([SS⬆️]/[VI])에서 주도 테마 파악 → 아직 안 오른 연관주 선점.
`/backtest` 스킬로 타임슬롯별 분석 → 백테스트 페이지에서 "Mode2 등록" 버튼.

### Style3 — 발라먹기 매매 (익절 후 재진입) ⭐

**핵심 패턴**: 강한 거래량 폭발로 급등한 종목 익절 이후, 변동성이 유지되면서 조정 구간을 주고 결국 고점을 뚫는 패턴. "잘 맞는 종목을 계속 발라먹는" 매매 스타일.

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

**시그널 타입 5종**:

| 타입 | 조건 | 타이밍 | 비고 |
|------|------|--------|------|
| **A** | 현재가 ≤ 매수가 × 1.03 | 익절 당일~수일 내 원가 복귀 | 난이도 높음, 빠른 대응 필요 |
| **B** | 현재가 > 익절가 × 1.02 (2%+ 돌파) | 익절 당일~익일 | 재상승 확인 진입 |
| **C1** | 거감봉 1봉+ 진행 중 | 조정 초기 | 모니터링 알림, 진입 아님 |
| **C2** | 쌍바닥 지지 터치 (과열 이후 봉 기준) | 거감봉 2봉+ 이후 | **핵심 타점** — `H+`: 지지가가 익절가 ±2% 이내면 강한 지지 |
| **C3** | 거감봉 이후 거래량 급증 양봉 | 재상승 시작 신호 | 진입 or 보유 확인용 |

**C2 쌍바닥 자동 계산 로직** (`style3_signals.py: find_double_bottom()`):
- **과열기간(exit_date+3거래일) 이후 일봉**에서 최저점(base) 탐색 (과열기간 저가 제외)
- base × 1.04 이내에 저점 2개 이상 → 쌍바닥 확인
- `support_price = base × 1.005` (지지가 0.5% 위 진입)
- **H+ 등급**: `support_price`가 익절가 ±2% 이내 → "익절가=지지선 전환" 강한 신호
- 터치 판정: `abs(close - support_price) / support_price < 0.008` (±0.8%)

**백테스트 모드** (`/api/seeking-signal/reentry-check`, `backtest_mode=true`):
- `exit_time` (HH:MM) 입력 시 익절 당일 해당 시각 이후 3분봉도 분석 포함
- 과열기간 이후 최대 5거래일치 3분봉 조회 (ka10080)
- 날짜+타입 기준 dedup (같은 날 같은 타입은 첫 감지 1개만)
- 응답에 `support_price`, `bars_analyzed`, `trading_days` 포함

**단기과열 억제**: `exit_date` 이후 3거래일 내 → 모든 시그널 차단 (변동성 과열 구간)

**실시간 폴링**: `price_monitor.py: check_style3_conditions()` — 3분마다 `trade_watchlist watching` 종목 체크
- 3분봉(ka10080) 기반 장중 즉시 감지
- 단기과열 억제 → C2 지지가 산출 → 시그널 감지 → 텔레그램 즉시 알림 + DB 저장

**등록 방식 (현재)**:
- 실전 페이지(`/`) → 발라먹기 탭 → 개별 필드 입력 (종목코드/종목명/매수날짜/매수가/익절날짜/익절가/손절가/예산)
  - 종목명 자동완성 (`/api/stock/search`), 날짜는 date picker
- "💾 감시등록 + Mode2" 버튼 → `trade_watchlist` 저장 + Mode2 섹션 자동 생성 + watcher 등록
- 섹션명: `YYYY-MM-DD Style3 발라먹기` (Mode2 날짜 필터로 조회 가능)
- 실전 체크("⚡ 지금 확인") 버튼 → 현재 3분봉 기준 즉시 시그널 체크

**Kiwoom 계좌 제약**:
- 현재 연결: **부계좌** (실제 Style3 매매 이력 없음)
- 실제 Style3 매매: **메인계좌** (미연결)
- 향후 메인계좌 연결 시 `ka10170` 체결 이력 → `trade_watchlist` 자동 등록 예정

**관련 파일**:
- `style3_signals.py` — 시그널 감지 유틸 (web_app.py + price_monitor.py 공유)
- `news_storage.py` — `trade_watchlist` + `reentry_signals` 테이블
- `web_app.py` — `/api/trade-watchlist` CRUD + `/api/reentry/signals` + `/api/seeking-signal/reentry-check`
- `price_monitor.py: check_style3_conditions()` — 3분 폴링 실시간 체크

**Mode2 섹션 3종 구조** (매일 아침 기준):
- `YYYY-MM-DD 눌림매매 (Style1)` — 수동 등록
- `YYYY-MM-DD 종목추천매매 (Style2)` — 백테스트 페이지 "Mode2 등록" 버튼
- `YYYY-MM-DD Style3 발라먹기` — 감시 등록 버튼으로 자동 생성
- Mode2 날짜 필터로 당일 3개 섹션만 필터링 가능

## ⚠️ CRITICAL: Kiwoom API 코드 절대 함부로 수정 금지

`kiwoom_client.py`, `kiwoom_chart.py`, `kiwoom_token.py`는 **프로덕션 실제 거래** 코드. 수정 시:
1. `ORDER_SIMULATION_MODE=1`로 로컬 테스트 먼저
2. 에러 핸들링 (try-except) 절대 제거 금지
3. Rate limit 주의

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

## Architecture

### Data Flow
```
Web UI → Flask API → Mode1/Mode2Manager → PriceMonitor → KiwoomClientAsync → Telegram
Telegram Channels → signal_listener (Pyrogram) → news.db → Web UI 시황체크
/siwhang skill → Oracle API (hotstock/parsed + news/today + watchlist) → AI 분석 → siwhang_results → Telegram
```

### Core Services

**`web_app.py`** — Flask server + PriceMonitor 통합
- 웹서버 시작 시 PriceMonitor 백그라운드 자동 시작
- Basic Auth (`WEB_USERNAME` / `WEB_PASSWORD`)
- SSL: cert.pem/key.pem 존재 시 HTTPS, 없으면 HTTP
- 모든 fetch 호출에 `credentials: 'same-origin'` 필수

**`price_monitor.py`** — 비동기 모니터링 엔진
- `asyncio.gather()`로 전 종목 병렬 체크 (~1초에 처리)
- 종목별 polling_interval 독립 관리 (`mode2_last_check` dict)
- `last_notification` 필드로 중복 알림 방지
- `notify_only=True` 시 알림만, `False` 시 자동 주문 실행

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

### Mode2 Trading Logic

**매수**: `current_price <= buy_target_price` (±1% tolerance)
**매도 우선순위** (위에서부터):
1. resistance_2 → 전량 익절
2. resistance_1 → 부분 익절
3. support_2 → 심층 손절
4. support_1 → 1차 손절

Budget은 웹UI에서 만원 단위 입력 → 저장 시 ×10000 (API는 항상 원 단위).

### Mode1 Trading Logic

분봉 polling 스케줄 (offset 3초):
- 1분봉: 사용자 설정 주기
- 3분봉: 3분 간격 + 3초 (xx:03, xx:06, ...)
- 5분봉: 5분 간격 + 3초
- 10분봉: 10분 간격 + 3초

모든 조건 AND 만족 시 → 텔레그램 알림 (수동 매수).

## Key Patterns

### Stock Code Normalization
`normalize_stock_code()` (utils/code.py) — 항상 사용:
- `"81180"` → `"081180"` (6자리 패딩)
- 전각 숫자 변환

### Status Flow
```
Mode1/Mode2: waiting_buy → waiting_sell → auto_sold | manual_sold
```

### Watcher Data Files
- `.data/mode1_watchers.json` — Mode1 감시종목
- `.data/mode2_watchers.json` — Mode2 감시종목 (구조: `{sections:[...], watchers:{code: {...}}}`)
- `.data/news.db` — 뉴스/급등주 SQLite DB (tables: messages, filtered_messages, themes, saved_news, siwhang_results, backtest_sessions, backtest_picks, backtest_pnl, analysis_context, stock_master, stock_siwhang_history, trading_mottos, **trade_watchlist**, **reentry_signals**)
- `.data/news_keywords.json` — 뉴스 키워드 필터 (include/exclude 분리)
- `.data/hotstock_keywords.json` — 급등주 키워드 필터 (include만)
- `.data/keywords.json` — 구형 단일 키워드 파일 (하위호환용)
- `.data/watchlist.json` — 수동 추가 관심종목 (`[{"code":"005930","name":"삼성전자"}]`)

## Environment Variables

```bash
# Telegram
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...

# Kiwoom API
KIWOOM_HOST=https://api.kiwoom.com
KIWOOM_APPKEY=...
KIWOOM_SECRETKEY=...

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

# Testing
TEST_LAST_PRICE=116000    # API 우회, 고정 가격 반환
IGNORE_MARKET_HOURS=1     # 시간 검증 스킵
```

## Claude Code Skills (`.claude/skills/`)

| 스킬 | 트리거 | 역할 |
|------|--------|------|
| `news-insight` | `/news-insight` | 마지막 실행 이후 신규 뉴스 증분 분석 |
| `news-insight-selected` | `/news-insight-selected` | 선택한 뉴스만 심층 분석 |
| `news-grouping` | `/news-grouping` | 테마별 그룹핑 + 강도(H/M/L) |
| `siwhang` | `/siwhang [1h\|2h]` | 급등주 시황 부합 여부 + 관심종목 매칭 AI 분석 → Oracle 저장 + 텔레그램 알림 |
| `backtest` | `/backtest [YYYY-MM-DD] [--version v2] [--desc "설명"]` | 지정 날짜 급등주/뉴스 → 13 타임슬롯 AI 분석 → 종목 추천 → Oracle 저장. 같은 날짜 재실행 시 버전 태그로 구분, 웹UI에서 A/B 비교 가능 |
| `reentry` | `/reentry` | ⚠️ **구형 (일봉 기반, 사실상 미사용)** — Style3 실시간 감지는 `price_monitor.py:check_style3_conditions()`로 대체됨 |

프롬프트 커스터마이징: `.claude/skills/<skill>/prompts/`

**⚠️ `.claude/` 디렉터리는 `.gitignore`에 등록됨 — git push로 배포 불가.**  
Oracle 서버에 스킬 파일 배포 시 scp 사용:
```bash
scp -i /Users/msim/Downloads/ssh-key-2026-04-26.key \
  -r .claude/skills/siwhang opc@152.67.207.143:~/newkiwoom/.claude/skills/
```

**시황체크 스킬 분석 기준 수정**: `.claude/skills/siwhang/prompts/analysis.md` 편집

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

---

### web_app.py API 엔드포인트 전체 목록

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
| GET/POST | `/api/mode2/sections` | 섹션 목록/추가 |
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
| POST/DELETE | `/api/keywords/include` | 포함 키워드 추가/삭제 |
| POST/DELETE | `/api/keywords/exclude` | 제외 키워드 추가/삭제 |
| POST | `/api/keywords/cleanup` | 날짜 기준 메시지 정리 |
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

#### 실전 트레이딩 (`/api/live/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET | `/api/live/picks` | 오늘 날짜 최신 backtest session의 picks (실전 페이지용) |

#### Style3 발라먹기 (`/api/trade-watchlist/`, `/api/reentry/`, `/api/seeking-signal/`)
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET/POST | `/api/trade-watchlist` | 감시 목록 조회/등록 (?status=watching) |
| PUT/DELETE | `/api/trade-watchlist/<id>` | 수정/삭제 |
| GET | `/api/reentry/signals` | 날짜별 시그널 조회 (?date=) |
| POST | `/api/seeking-signal/reentry-check` | 백테스트 모드 — 과거 3분봉 기반 시그널 탐색 |

#### 재무/종목 정보
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET | `/api/financial-info` | 재무정보 (Kiwoom ka10001 + DART) |
| GET | `/api/stock/search` | 종목명 키워드 검색 |

#### 格言
| 메서드 | 경로 | 역할 |
|--------|------|------|
| GET/POST | `/api/mottos` | 목록/추가 |
| PUT/DELETE | `/api/mottos/<id>` | 수정/삭제 |
| POST | `/api/mottos/reorder` | 순서 변경 |

---

### 핵심 동작 로직

#### Mode2 매매 판단 (`price_monitor.py:check_mode2_conditions`)
```
check_mode2_conditions(code, watcher)
  ↓
현재가 polling (kiwoom_client_async: ka10003)
  ↓
매수 조건: current_price <= buy_target_price (±1% tolerance)
  ↓
매도 우선순위 (높은 것부터):
  resistance_2  → 전량 익절
  resistance_1  → 부분 익절 (profit_ratio 설정값%)
  support_2     → 심층 손절
  support_1     → 1차 손절 (또는 물타기)
  ↓
notify_only=True: 텔레그램 알림만
notify_only=False: 자동 주문 실행 (kiwoom_client.buy/sell)
```

#### Mode1 매매 판단 (`price_monitor.py:check_mode1_conditions`)
```
분봉 polling 스케줄 (3초 offset): 1분/3분/5분/10분봉
  ↓
Step1: 전일 대비 급등 확인 (rise_threshold%)
Step2: 최고가 도달 확인 (high_threshold%)
Step3: 재반등 → n번째 봉 시가가 매수타점
  ↓
AND 조건 모두 충족 시 텔레그램 알림 (수동 매수)
```

#### 급등주 분석 / 시황체크 (`/siwhang` 스킬)
```
/siwhang 스킬 실행 (로컬 Claude Code)
  ↓
SSH → Oracle localhost API
  ├── GET /api/hotstock/parsed (SS⬆️/VI/SS 파싱 메시지)
  ├── GET /api/news/today (DART 공시 포함)
  └── GET /api/watchlist (관심종목)
  ↓
AI 분석 (analysis.md 프롬프트):
  - SS⬆️: 상한가 + catalyst 조사 (뉴스DB + Google RSS + DART)
  - VI: 발동 종목 + 테마 강도
  - SS: watchlist_match 있는 것만
  - 수급 (기관/외인) + 거래량 전일비교 + 재료FEED × 당일뉴스 연결성
  → Confidence H/M/L 판단
  ↓
POST /api/siwhang/results → Oracle DB 저장
POST 텔레그램 알림
```

#### 백테스트 분석 (`/backtest` 스킬)
```
/backtest YYYY-MM-DD --version v2 실행
  ↓
1. POST /api/backtest/sessions → session_id 생성
2. GET /api/analysis/context → morning_report + interval_context
3. DART 공시 전체 사전 수집 (1회)
4. GET /api/hotstock/parsed + /api/news/today (전체)
   ↓ 백필 여부 판단
   백필(received_at 동일): message_id 기준 13등분
   실시간: until UTC 파라미터로 슬롯 슬라이싱
5. 13슬롯 순회 (09:15 ~ 15:15):
   ├── 신규 메시지 분리
   ├── SS⬆️ catalyst 3소스 조사 (뉴스DB + Google RSS + DART)
   ├── AI 분석 (analysis.md) → picks JSON
   ├── POST /api/analysis/interval-context 업데이트
   └── POST /api/backtest/picks 저장
6. 완료 요약
```

#### 뉴스 아카이빙 (`signal_listener.py`)
```
Pyrogram → 급등주 채널(-1003342481653) + 뉴스 채널(-1003239561368) 구독
  ↓
모든 메시지 → messages 테이블 (source_type: hotstock/news)
  ↓
키워드 필터 통과 시:
  - 목적지 채널 포워딩
  - filtered_messages 테이블 기록
  ↓
급등주: [SS⬆️]/[VI] → 키워드 무관 무조건 저장
         [SS] → hotstock_keywords.json 필터 적용
```

#### 재무정보 조회 (`/api/financial-info`)
```
GET /api/financial-info?stock_code=005930
  ↓
Kiwoom ka10001 (주식기본정보조회):
  시가총액(mac), PER, PBR, ROE, EPS, BPS
  영업이익(bus_pro), 매출(sale_amt), 순이익(cup_nga)
  유통비율(dstr_rt)
  ↓
DART fnlttSinglAcntAll (전년 사업보고서):
  stock_code → corp_code (.data/corp_code_map.json 캐시)
  자산총계, 부채총계, 자본총계, 유동자산, 유동부채
  → 부채비율(부채/자본×100), 유동비율(유동자산/유동부채×100)
  ↓
결합 응답 반환
```

---

### 분석 프롬프트 파일 위치

| 프롬프트 | 경로 | 역할 |
|---------|------|------|
| 시황체크 분석 | `.claude/skills/siwhang/prompts/analysis.md` | Confidence H/M/L 판단 기준, 수급/거래량/재료FEED 조건 |
| 백테스트 분석 | `.claude/skills/backtest/prompts/analysis.md` | 슬롯별 종목 추천, interval_context 업데이트 형식 |

**프롬프트 수정 가이드:**
- Confidence 기준 바꾸고 싶을 때 → `## Confidence 기준` 섹션 수정
- 슬롯별 전략 바꾸고 싶을 때 → `## 슬롯 시간대별 역할` 테이블 수정
- 출력 JSON 형식 바꾸고 싶을 때 → `## 출력 형식` 섹션 수정 (SKILL.md의 저장 로직과 동기화 필수)
- 분석 대상 우선순위 바꾸고 싶을 때 → `## 분석 절차 Step 2~3` 수정

---

### corp_code 매핑 관리

- **파일**: `.data/corp_code_map.json` (stock_code → corp_code/corp_name)
- **파일**: `.data/stock_name_map.json` (corp_name → stock_code, 역방향)
- **갱신**: `scp CORPCODE.xml → python 파싱 → 두 파일 재생성`
- **자동복원**: `POST /api/backtest/fix-stock-codes` — NULL stock_code를 종목명으로 자동 매핑
- **종목명 검색**: `GET /api/stock/search?q=삼성` — 자동완성용

---

## 🖥️ Oracle 서버 부하 가이드

### 서버 스펙 (Oracle Cloud Free Tier)
- CPU: 1 OCPU (1코어)
- RAM: ~1GB 실제 사용 가능 (1GB 할당, 시스템 예약 제외)
- Storage: SSD (충분)
- Network: 국내 트래픽 제한 없음

### 현재 실행 중인 프로세스 부하

| 프로세스 | CPU | RAM | 비고 |
|---------|-----|-----|------|
| `web_app.py` (Flask) | 0~2% | ~140MB | 요청 시 spike |
| `signal_listener.py` (Pyrogram) | 0~1% | ~100MB | 상시 연결 유지 |
| `PriceMonitor` (web_app 내) | 1~5% | 포함 | 장중 14종목 polling |
| **합계** | **~5%** | **~250MB** | **여유 충분** |

### 분석 capa (백테스트 / 시황체크)

**`/backtest` 스킬 (로컬 실행):**
- 분석 자체는 로컬 PC (Claude Code) — Oracle 서버에 부하 없음
- Oracle 서버는 API 응답만 담당 (13슬롯 × 2 API 호출 = ~26 HTTP 요청)
- 총 실행 시간: 5~15분 (Opus 4.7 기준, API 응답 속도에 따라 다름)
- **동시 실행 제한**: Oracle API rate limit 없음, 단 Kiwoom API는 초당 5회 제한

**`/siwhang` 스킬 (로컬 실행):**
- 마찬가지로 로컬 분석, Oracle은 데이터 제공만
- 1회 실행: 약 1~3분

**결론: 백테스트/시황 분석은 Oracle 서버 부하와 무관. 로컬 PC 성능/API 토큰 소비가 병목.**

### 실시간 모니터링 capa

**현재 Mode2 감시종목:**
- 동시 polling (asyncio.gather) — 실측 ~1초에 처리
- polling_interval: 알림전용=180초, 자동매매=30초
- **권장 최대 종목 수: 30개** (30초 interval 기준, CPU spike 5% 이내 유지)
- 40개 이상 시 polling lag 발생 가능 (간헐적 1~2초 delay)

**메모리 한계:**
- 현재 250MB 사용, 자유 메모리 ~250MB
- 종목 50개, 뉴스 DB 10만 건 이상 누적 시 OOM 위험
- `/api/keywords/cleanup` 주기적 호출 권장 (30일 이상 메시지 정리)

**DB 부하:**
- SQLite 동시 write 경합 가능 (signal_listener + web_app 동시 write)
- 현재는 WAL 모드 미사용 → 대량 write 시 lock 대기 발생 가능
- 하루 뉴스 수신량 ~수백 건 → 현재 수준에서 문제 없음

### 부하 모니터링 명령

```bash
ssh opc@152.67.207.143

# 실시간 메모리/CPU
free -m
top -bn1 | head -20

# 프로세스별 상세
ps aux | grep python | grep -v grep

# DB 크기
du -sh ~/newkiwoom/.data/news.db

# 로그 에러 확인
tail -100 ~/newkiwoom/web_app.log | grep -i "error\|warn\|kill\|oom"
```

### 최적화 권고

1. **뉴스 DB 주기 정리**: 매주 `/api/keywords/cleanup`으로 7일 이상 메시지 삭제
2. **Mode2 30개 이상 등록 시**: polling_interval 180초로 설정 (알림 전용)
3. **백테스트 실행 중 서버 재시작 금지**: 스킬은 로컬에서 실행되지만 API 요청이 많음
4. **corp_code_map 갱신**: CORPCODE.xml 받아서 로컬 파싱 후 SCP → `fix-stock-codes` 호출
5. **SQLite WAL 모드 적용** (선택, 향후): `PRAGMA journal_mode=WAL` — 동시 write 성능 향상

---

## TODO (구현 대기)

### High Priority
1. **매매일지 페이지** — 확정 손익 내역, 통계, Date filter

2. **계좌 polling** — 보유종목 주기 조회, 수동매도 자동 감지

3. **시황체크 고도화** (선택)
   - 1일 자동 삭제 (매일 자정)

4. **백테스트 고도화** (선택)
   - 종목노트 소스 추가 (`note_source` 컬럼 준비 완료)
   - 종목별 일봉 차트 + 추천 시점 마커 (현재 카드 형태만)

## Known Issues & Lessons

### 텔레그램 봇 충돌
같은 TELEGRAM_BOT_TOKEN을 여러 서버에서 동시 실행하면 Conflict 에러 발생. 현재 오라클 1곳에서만 web_app.py 실행 (bot_v3.py는 미사용).

### signal_listener 포워딩 실패
`Chat not found` 에러가 나와도 **DB 아카이빙은 정상 동작**. 포워딩 실패는 목적지 채널 접근권한 문제.

### Test endpoint vs 실제 로직 일치
`web_app.py` test endpoint의 조건 로직은 `price_monitor.py`와 **완전 동일**해야 함. 경계값 처리 (`<` vs `<=`) 특히 주의.

### 단위 변환
Budget: UI 입력/표시는 만원 단위, API 저장은 원 단위. 변환은 프론트엔드에서만.

### UTC vs KST 날짜 불일치
`messages.received_at`은 UTC 저장. `messages.date`는 KST 날짜 저장.  
당일 데이터 조회 시 `since=<UTC_ISO>` 대신 `date=YYYY-MM-DD` 파라미터 사용.  
예: 20:39 KST 저장 → `received_at` UTC로는 다음날이 될 수 있음.

### Oracle SSH 복합 명령어 exit 255
SSH에서 `kill && restart` 같은 복합 명령은 간혹 exit 255로 실패.  
→ kill과 start를 **별도 SSH 호출로 분리**하고 ps aux로 확인.

### 급등주 메시지 파싱 (hotstock regex)
`[SS⬆️]` / `[VI]` / `[SS]` 태그별 파싱:
- `[SS⬆️]` = 상한가, `[VI]` = VI 발동, `[SS]` = 급등 조짐 (confirmed surge 아님)
- `테마 : 테마명` 줄에서 테마 추출
- `Y 테마명 : 종목A, 종목B` 줄에서 관련주 추출
- 관심종목 매칭은 메인종목 + 관련주 전체 대상으로 비교

### 로컬 PC에서 Oracle API 직접 호출 불가 (VPN 환경)
로컬 개발 PC에서 `https://www.nomaddoklip.xyz` 직접 호출은 **회사 VPN 환경에서 DNS 타임아웃**으로 실패함.  
→ Claude Code 스킬 등에서 Oracle API 데이터가 필요할 때는 **SSH로 오라클 서버에 붙어서 localhost로 호출**해야 함.

```bash
# 올바른 패턴: SSH → Oracle 서버에서 localhost 호출
ssh -i /Users/msim/Downloads/ssh-key-2026-04-26.key opc@152.67.207.143 '
  source ~/newkiwoom/.venv/bin/activate
  export $(grep -v "^#" ~/newkiwoom/.env | xargs)
  curl -sk -u "$WEB_USERNAME:$WEB_PASSWORD" "https://localhost/api/news/today?date=2026-04-29"
'

# 잘못된 패턴 (VPN 환경에서 실패)
curl -u "..." "https://www.nomaddoklip.xyz/api/..."
```

### 시황체크 (Siwhang) 아키텍처
- AI 분석은 로컬 PC (Claude Code 스킬)에서 실행, 데이터는 Oracle API 조회
- `/siwhang` 스킬: `last_run.txt` 기준 증분 → Oracle fetch → AI 분석 → Oracle POST 저장 → 텔레그램
- `[SS]` 종목은 watchlist_match 있는 것만 분석 (토큰 절약)
- 분석 결과는 `siwhang_results` 테이블 + 웹UI `#siwhang` 섹션에서 확인

### 키워드 관리 (뉴스/급등주 분리)
- 뉴스(`news`)와 급등주(`hotstock`) 키워드 파일 완전 분리
- 급등주: `[SS⬆️]`(상한가) / `[VI]`(VI발동) 는 키워드 필터 없이 무조건 표시, `[SS]`만 키워드 필터 적용
- API: `/api/keywords/include` POST/DELETE, `/api/keywords/exclude` POST/DELETE — body에 `{"keyword": "...", "type": "news"|"hotstock"}`
- `/api/keywords/cleanup` POST `{"source_type": "news"|"hot_stock"}` — 오늘 이전 메시지 삭제

### Mode2 Demark 자동계산
- 일봉 차트 로드 시(`loadWatcherChart`, `handleMode2Lookup`) 전일 OHLC → 디마크 자동계산 → `resistance_1_price`/`support_1_price` 자동 채움
- 디마크 공식: close<open → x=high+2*low+close; close>open → x=2*high+low+close; else → x=high+low+2*close; targetHigh=x/2-low, targetLow=x/2-high
- 디마크 섹션의 "1차 저항/지지 적용" 버튼으로 수동 재계산도 가능

### 모바일 UI
- **실전 페이지 (`/`)** 하단 탭바: 실전, Mode2, 시황체크, 발라먹기, Mode1, 감시리스트, 매매일지
- **어드민 페이지 (`/adminpage`)** 하단 탭바: AI슬롯분석, 종목마스터, Test
- 기본 시작 페이지: Mode2
- 가로모드 감지: `(max-height: 500px) and (orientation: landscape)`
- 시황체크 테이블: 카드별 개별 검색 입력 (`data-search` 속성 pre-compute)

### 백테스트 시스템 아키텍처
- DB: `backtest_sessions` (날짜별 세션) → `backtest_picks` (슬롯별 추천) → `backtest_pnl` (P&L 입력)
- `backtest_sessions.version` + `strategy_desc` — 같은 날짜 복수 전략 A/B 비교용
- `backtest_picks.catalyst` — 상한가 종목의 시황/재료/뉴스 요약 (1~3문장)
- `backtest_picks.sources_json` — `[{type, time, text}]` 형태 근거 목록 (hotstock/news/google/dart). UI 카드에 시각+내용 표시
- `backtest_picks.note_source` 컬럼 — 향후 종목노트 소스 연결 예약 필드
- API: `GET/POST /api/backtest/sessions`, `GET /api/backtest/sessions/<id>`, `POST /api/backtest/picks`, `PUT /api/backtest/picks/<id>/pnl`, `GET /api/backtest/compare?session_a=&session_b=`
- `get_messages()` — `until_utc` 파라미터로 시각 기준 필터 (백필 데이터는 received_at 동일해서 무효)
- `/api/hotstock/parsed`, `/api/news/today` — `until` 쿼리파라미터 추가됨

### 백테스트 백필 데이터 타임슬롯 문제
signal_listener가 다운되었다가 Pyrogram history API로 백필한 데이터는 **모든 received_at이 백필 시각으로 동일**하게 찍힘.  
→ `until` UTC 파라미터로 시간대별 필터가 불가.  
→ 해결책: `message_id`(텔레그램 채널 순번) 기준으로 총 건수를 13슬롯에 균등 분배해 시간 근사.  
→ 실시간 수집 데이터는 `until` 파라미터 정상 동작.

### 백테스트 종목 추천 기준 (슬롯당 최대 3종목)
```
Confidence H: SS⬆️(상한가) + 뉴스 교차확인 + 복합 테마(3개 이상)
Confidence M: VI발동 or 명확한 촉매 1개
Confidence L: SS만 있거나 단독 뉴스 (보통 미추천)

우선순위: SS⬆️ > VI(복합테마) > SS(watchlist_match만) > 뉴스 교차
SS 종목은 watchlist_match 있는 것만 분석 대상 (토큰 절약)
```

### Oracle 서버 SSH에서 Python f-string 중첩 따옴표 오류
SSH heredoc 안에서 Python f-string 사용 시 `f"...{m.get("key")}..."` 형태는 파이썬 3.11 이하에서 SyntaxError.  
→ 해결책 1: f-string 대신 문자열 연결 (`"prefix" + var + "suffix"`) 사용  
→ 해결책 2: `python3 << 'PYEOF' ... PYEOF` heredoc 패턴으로 스크립트 전달

### 백테스트 catalyst 조사: v1 vs v2 구분
- **v1**: 내부 뉴스 DB + 급등주 메시지만 사용. catalyst는 AI 추론값 (실조회 아님). sources 배열 비어 있음.
- **v2+**: SS⬆️ 종목에 대해 3소스 실조회 → catalyst + sources 배열 채움:
  1. 내부 뉴스 DB (종목명 grep)
  2. Google News RSS (`종목명 상한가 OR 특징주 OR 급등`)
  3. DART 공시 API (`bgn_de=end_de=RUN_DATE`, key: `c77a3bdb4d1b8bdf50792863473f716db261d989`)
- 같은 날짜를 v1/v2로 재실행 후 웹UI 비교 패널에서 A/B 교차 확인 가능

### 백테스트 → 실전 연결 (Mode2 감시 등록)
- 백테스트 카드 하단의 "📊 Mode2 등록" 버튼: 매수/익절/손절가 + 예산 입력 후 `POST /api/mode2/watchers` 호출
- `notify_only: true` 기본값 — 알림만, 자동주문 실행 안 함
- stock_code 없는 종목은 버튼 미표시

### 실전 트레이딩 페이지 + 분석 트리거 시스템

**실전 페이지 (`livePage`)**:
- 오늘 날짜 최신 backtest session의 picks 표시 (`GET /api/live/picks`)
- **모바일**: 캐로셀 방식 (1종목씩, 좌우 스와이프/버튼), 일봉 차트 lazy load
- **데스크탑**: 기존 스크롤 리스트 방식
- 슬롯 탭바 (09:15~15:15), 현재 시간대 자동 선택
- 카드마다 매수가 + 예산 입력 후 "📊 Mode2 등록" → `POST /api/mode2/watchers` 직접 호출
- 일봉 차트: `POST /api/test/daily-chart` + `drawCandlestickChart()` 재사용

**분석 트리거 (A+B 조합)**:
- A (웹 수동 트리거): "▶ 지금 분석" 버튼 → `POST /api/analysis/request` → analysis_context.analysis_request에 ISO timestamp 저장
- B (자동 폴링): `poll_trigger.py` 30초 주기 → `GET /api/analysis/pending` → pending이면 `claude --print "/siwhang"` 실행
- `get_and_clear_analysis_request()`: read + null clear atomically — 중복 실행 방지

**poll_trigger.py 실행**:
```bash
source .venv/bin/activate && python poll_trigger.py
# 장시간 외 자동 스킵 (09:00~15:35), IGNORE_MARKET_HOURS=1로 오버라이드
```

**macOS launchd 자동시작**: `poll_trigger.py` 상단 주석에 plist 예시 포함.

### 백테스트 버전 관리 전략
| 버전 | 전략 | 핵심 변경 |
|------|------|-----------|
| v1 | SS⬆️+VI 테마 강도 기반 | 기본: 테마 복합도 + 뉴스 교차 (AI 추론) |
| v2 | catalyst 우선 (3소스 실조회) | Google+DART 실조회, 확인된 것만 H 부여 |
| v3 | VI 확장 (watchlist 없어도 복합테마 3개↑) | VI 분석 범위 확대 |

### 분석 컨텍스트 시스템 (analysis_context)
백테스트 분석 품질 향상을 위한 구조화된 컨텍스트 시스템.

**DB 테이블** (`analysis_context`):
- `context_date` (UNIQUE) — 날짜별 1개
- `morning_report` (JSON) — 해외증시, 예측 테마, 주요 내용
- `interval_context` (JSON) — 슬롯별 누적 테마 흐름 (confirmed/new/faded/already_picked)
- `next_instruction` — 사용자 1회성 추가 분석 지시
- `instruction_used` — 인스트럭션 소비 여부 (1회만 사용 후 null)

**API (4개)**:
- `GET /api/analysis/context?date=` — 전체 컨텍스트 조회
- `POST /api/analysis/morning-report` — 시황 가설 저장
- `POST /api/analysis/instruction` — next_instruction 저장 (null이면 삭제)
- `POST /api/analysis/interval-context` — 슬롯 분석 후 테마 흐름 업데이트

**웹UI**: 백테스트 탭 우상단 "📋 시황 설정" 버튼 → 패널 토글

**스킬 사용 흐름**:
1. `/backtest` 실행 전 웹UI에서 morning_report 입력 + (선택) next_instruction 입력
2. 스킬이 context 조회 → next_instruction consume (슬롯 시작 전 1회)
3. 각 슬롯 분석 후 interval_context 업데이트 → 다음 슬롯이 이전 테마 흐름 인지

**주의**: 새 날짜에 먼저 morning_report 입력 필수.  
DB 테이블 미생성 시: `python3 -c "from news_storage import NewsStorage; NewsStorage('.data/news.db')"` 직접 실행.

### stock_master + 종목 Hover Tooltip
Mode2 감시종목 카드에서 종목명에 마우스 올리면 팝업 툴팁 표시.

**DB 테이블** (`stock_master`, `stock_siwhang_history`):
- `stock_master`: stock_code PK, themes(콤마구분), note, 재무캐시(시가총액/PER/ROE/부채비율/유동비율/영업이익/전년분기비교), finance_updated_at
- `stock_siwhang_history`: 종목별 급등주 feed 이력 (event_date, tag_type, theme, feed_text), 최근 10개 표시

**API (4개)**:
- `GET /api/stock-master/<code>` — 마스터 조회 + 시황 히스토리 + finance_stale 여부
- `POST /api/stock-master/<code>` — 테마/노트 수동 업데이트 (body: {themes, note})
- `POST /api/stock-master/<code>/refresh-finance` — Kiwoom+DART 재무 강제 갱신
- `POST /api/stock-master/<code>/history` — 시황 히스토리 추가 (백테스트 스킬에서 호출)

**Hover 동작 흐름**:
1. 종목명 셀 `onmouseenter` → `showStockTooltip()` 호출
2. 5분 클라이언트 캐시 확인 → 없으면 `/api/stock-master/<code>` 비동기 fetch
3. 툴팁 표시: 테마 태그 + 재무 6개 지표 + 시황 히스토리 최근 10개
4. `finance_stale: true` 이면 "🔄 재무 갱신" 버튼 표시 → `refresh-finance` 호출

**재무 stale 기준**: `finance_updated_at`에서 24시간 초과 시.
**재무 미입력 상태**: 테마/히스토리만 표시, 재무는 "-" 처리.
**테마 입력**: 현재 UI 없음 — `POST /api/stock-master/<code>` 직접 호출 또는 향후 노트 모달 연동 예정.

### Oracle 서버 보안 강화 (2026-04-27)
대량 취약점 스캔 공격 (170.64.180.74 등에서 phpunit/ThinkPHP 패턴) 방어:

**KR IP Only (ipset)**:
```bash
# /etc/update_kr_ips.sh — 매주 일요일 02:00 cron 자동 업데이트
ipset create KR_IPS hash:net
for cidr in $(curl -s https://www.ipdeny.com/ipblocks/data/countries/kr.zone); do
  ipset add KR_IPS $cidr
done
iptables -I INPUT 1 -p tcp --dport 443 -m set --match-set KR_IPS src -j ACCEPT
iptables -I INPUT 2 -p tcp --dport 443 -j DROP
# localhost 반드시 허용
iptables -I INPUT 1 -p tcp --dport 443 -s 127.0.0.1 -j ACCEPT
```

**취약점 URL 패턴 차단 (iptables string match)**:
```bash
sudo iptables -I INPUT 1 -p tcp --dport 443 -m string --string "phpunit" --algo bm -j DROP
sudo iptables -I INPUT 1 -p tcp --dport 443 -m string --string "eval-stdin" --algo bm -j DROP
sudo iptables -I INPUT 1 -p tcp --dport 443 -m string --string "invokefunction" --algo bm -j DROP
```

**fail2ban 미적용 이유**: Oracle Linux 9 SELinux Enforcing에서 fail2ban-server 소켓 생성 실패.  
werkzeug 로그 포맷과 failregex `<HOST>` 캡처그룹 매칭 어려움. iptables string match로 대체.

**VPN 환경 개발 PC에서 SSH 접속**: 443 포트 SSH 터널로 우회 가능.
```bash
ssh -i /Users/msim/Downloads/ssh-key-2026-04-26.key -p 22 opc@152.67.207.143
# 22번 포트는 KR IP 제한 없이 유지 (SSH는 별도 관리)
```

### 백테스트 분석 설계 원칙 (급등주 메시지 중심)
AI 분석 소스 우선순위 결정 원칙:
- **뉴스 DB는 노이즈가 많아 분석 소스로 부적합** — 급등주 메시지(`[SS⬆️]`/`[VI]`/`[SS]`)가 핵심 소스
- **일반 뉴스는 Tier3 (스킵)** — 시황 리포트, 증권사 리포트 제외
- **DART 공시는 Tier1 (항상)** — 당일 신규 공시 or 분석 종목 관련 공시
- **Google News는 Tier2 (SS⬆️ catalyst 전용)** — 상한가 종목의 촉매 확인용만

**슬롯 시간대별 분석 역할**:
| 슬롯 | 역할 | 전략 |
|------|------|------|
| 09:15~09:45 | 테마 주도주 선점 | morning_report 가설 검증, 빠른 진입 |
| 10:15~11:45 | 연관주/확산주 발굴 | 주도주 관련주 중 아직 안 오른 것 |
| 12:15~13:45 | 신규 테마 포착 or 눌림목 | 오전 테마 눌림 + 새 시황 |
| 14:15~15:15 | 보수적 | H 확신 종목만, 당일 고점 추격 금지 |

**추가 상승여력 관점**: "이미 오른 종목 추종"이 아닌 "아직 안 오른 연관주/눌림목/신규 테마 선점" 목적.  
`already_picked` 중복 추천 금지. 슬롯당 최대 3종목. 확신 없으면 추천하지 않음.

### Style3 시그널 감지 설계 원칙

**일봉 기반 시그널 = 폐기**: 15:30 종가 확정 후 발생하는 시그널은 이미 기회가 지나간 것. 반드시 **장중 분봉(3분봉) 기반 실시간 감지**여야 의미 있음.

**C2 쌍바닥은 가격 패턴만**: 거감봉 카운트 불필요. 두 저점이 ±4% 이내에 있으면 충분. 한컴위드 4/22의 경우 미세 양봉(거래량만 감소)도 거감봉으로 처리했기 때문에 가격 패턴으로만 판단하는 것이 더 정확.

**단기과열 억제 기준**: `exit_date` = 폭등일 직접 사용. `all_bars` 전체 탐색하면 과거 폭등일 오탐 발생.

**C2 dedup**: 같은 `support_price` ±100원은 하루에 첫 감지만. 반복 알림 방지.

**overheat_period 계산**: 주말 스킵 단순 계산(공휴일 미처리). 3거래일 이후부터 시그널 허용.

**C2 지지가 계산 기준**: 과열기간(exit_date+3거래일) **이후** 봉만 사용해야 함. 과열기간 저가를 포함하면 실제 재진입 구간 가격과 동떨어진 지지가가 나옴. 한컴위드 예시: 4/21~4/23 과열기간 저가 6,280원 → 지지가 6,311원 산출됐지만 실제 4/24 장중 가격은 6,840~6,990원대. 과열 이후 봉(4/24~) 기준으로 계산해야 실제 거래 가격과 맞음.

**Type B 조건**: 익절가 +2% 이상 돌파 (이전 +5%). +5%는 너무 늦음 — 재돌파 타이밍을 놓침. 한컴위드 4/20 13:48 B시그널이 +5% 기준에서는 잡히지 않았음.

**백테스트 trading_dates 설계**: `exit_date` 이후 5일이 아니라 과열 억제 이후 5거래일이어야 함. 과열 3일을 포함해서 자르면 실질 분석 가능일이 2일뿐.

### kiwoom_chart.py get_minute_chart() return_code 체크 주의
Kiwoom ka10080 API는 응답에 `return_code` 필드를 반환하지 않음. `data.get("return_code") != 0` 체크를 넣으면 `None != 0 = True`이므로 **항상 실패** 처리됨. 성공 판정은 `stk_min_pole_chart_qry` 키 존재 여부로 해야 함.

### style3_signals.py 배포 누락 주의
`style3_signals.py`는 web_app.py와 price_monitor.py 양쪽에서 import하는 공유 모듈. 수정 후 git add 빠뜨리면 Oracle에 구버전이 남아서 `signal_time` 같은 필드가 없는 상태로 실행됨. 반드시 커밋 전 `git diff style3_signals.py` 확인.
