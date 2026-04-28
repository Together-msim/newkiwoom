# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A dual-interface auto-trading system for Korean stocks via Kiwoom API:
1. **Telegram bot** - Conversational interface for Tactic1/2 strategies
2. **Web UI** - Multi-page browser interface with 5 sections (Watchlist, Mode1, Mode2, Tradelog, Test)

**Trading strategies:**
- **Tactic1**: Gap-up first pullback trades (당일 시가 7%↑ 갭상승 → 첫 조정 매수)
- **Tactic2**: Split buying at support levels (지지선 분할 매수)
- **Mode1**: 전일대비 급등 첫 조정 노리기 (분봉 기반, 그린라이트 조건) - 완료
- **Mode2**: Resistance/Support level-based swing trading (완료) ⭐ **최우선 기능**

## ⚠️ CRITICAL: Mode2 자동매매 최우선

**Mode2는 가장 중요한 기능입니다. 항상 정상 동작해야 합니다.**

- Web server (web_app.py) 실행 시 **PriceMonitor 자동 시작**
- Mode2 active=true 종목은 **polling_interval마다 자동 체크** (기본 10초)
- 매수타점/저항/지지 도달 시 **즉시 주문 실행**
- Telegram bot 없이도 **웹 서버만으로 완전 동작**

### 🚀 2026-04-27 비동기 최적화 완료
- **비동기 병렬 처리**: `kiwoom_client_async.py` + `asyncio.gather()`
- **성능**: 11개 종목 1초 처리 (기존 110초 → 99% 개선)
- **안정성**: CPU 2%, MEM 124MB, 에러 0건
- **확장성**: 50개 종목까지 가능
- **도메인**: https://nomaddoklip.xyz (443 포트, SSL)

## Essential Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all services (Telegram bot + Web UI + Signal Listener)
python run_all.py

# Run individually
python bot_v3.py            # Telegram bot only
python web_app.py           # Web UI only (default port 5000)
python signal_listener.py   # 뉴스/급등주 아카이빙 서비스 (최초 실행 시 Pyrogram 인증 필요)

# Run tests
python test_bot.py        # Basic functionality
python test_kiwoom.py     # Kiwoom API integration
python test_mode2_monitoring.py  # Mode2 monitoring test

# 뉴스 DB 조회 (빠른 확인)
sqlite3 .data/news.db "SELECT source_type, text, received_at FROM messages ORDER BY received_at DESC LIMIT 10;"
```

### ⚠️ Signal Listener 최초 실행 (1회만)
```bash
# 반드시 터미널에서 직접 실행 (전화번호 인증 필요)
python signal_listener.py
# → Enter phone number: +8210XXXXXXXX
# → Enter OTP: XXXXX
# 인증 완료 시 signal_listener.session 파일 생성됨
# 이후 run_all.py에서 자동 시작
```

## 🌐 Production Environment

### Oracle Cloud Server
- **IP**: 152.67.207.143
- **Domain**: https://nomaddoklip.xyz
- **Port**: 443 (HTTPS with SSL)
- **User**: opc
- **Path**: ~/newkiwoom
- **SSH Key**: `/Users/msim/Downloads/ssh-key-2026-04-26.key`

### Production Commands
```bash
# SSH 접속
ssh -i /Users/msim/Downloads/ssh-key-2026-04-26.key opc@152.67.207.143

# HTTPS 서버 시작 (443 포트)
cd ~/newkiwoom && ./start_https.sh

# 로그 확인
tail -f ~/newkiwoom/web_app.log

# 프로세스 확인
ps aux | grep 'python.*web_app.py'
ps aux | grep 'python.*signal_listener.py'

# 서버 재시작 (긴급)
~/newkiwoom/restart_web_oracle.sh

# 오늘 뉴스 수신 현황 확인
sqlite3 ~/newkiwoom/.data/news.db "SELECT source_type, COUNT(*) FROM messages WHERE date=date('now') GROUP BY source_type;"
```

### Performance Metrics (2026-04-28 기준)
- **처리 속도**: 14개 종목 1.0초 내외 (비동기 병렬 처리)
- **CPU**: 2.2% (매우 낮음)
- **메모리**: 144MB (안정)
- **에러**: 0건
- **확장성**: 50개 종목까지 가능
- **중복 알림**: last_notification 필드로 완전 방지

## Web UI Structure (Multi-Page)

### Page Navigation
The web interface has 5 main pages accessed via top navigation:

1. **📊 감시리스트 (Watchlist)** - Default page
   - Unified view of all Mode1 + Mode2 stocks
   - Filters: Mode, Status, Date (UI ready, backend pending)
   - Displays: code, name, registration date, status, **bought_quantity**, current price, bought_price, profit rate
   - Actions:
     - **💼 보유 종목 조회**: Opens modal showing full account summary and holdings
       - **📊 Mode2 편입**: 보유 종목을 Mode2 감시 종목으로 추가 (모바일 친화적 모달)
         - 자동 입력: 종목코드, 종목명, 매수가, 수량, Budget
         - 사용자 입력: 1차 저항(익절), 1차 지지(손절)만
         - 상태: `waiting_sell` (이미 매수 완료)
     - **🔄 보유수량 동기화**: Fetches holdings from Kiwoom (ka01690) and updates bought_quantity for all watchers
     - **매도 버튼** (only when status=waiting_sell AND bought_quantity>0): 
       - Modal inputs: quantity (blank=full), order_type (market/limit), price
       - Calls /api/order/sell which executes order AND calls manager.record_sell()
       - Status auto-updates to manual_sold on success
     - **ON/OFF toggle**: Activates/deactivates monitoring
     - **Delete**: Removes watcher from list

2. **📈 Mode1** - 전일대비 급등 첫 조정 전략 (완료)
   - 종목 추가 폼 with 종목명 자동 조회
   - 모니터링 가격 설정
   - 동적 조건 추가/삭제 (분봉 종류: 1/3/5/10분, 추세: 상승/하락, 횟수)
   - 기대 수익률 설정
   - Polling 주기 설정 (페이지 전역 + 종목별)
   - Status: 매수대기 / 매도대기 / 자동매도 / 수동매도
   - 인사이트 표시 영역 (모니터링 결과)

3. **📉 Mode2** - 저항/지지 레벨 전략 (완료)
   - Chart-based input UI with mode2_chart.png
   - Input form: 종목코드 (종목명 자동 조회), **Budget (만원 단위)**, Polling 주기 (5/10/15/20/30초), **🔔 알림만 체크박스**
   - **Budget picklist**: 0만, 10만, 20만, 30만, 60만, 100만, 수동입력 (테이블 표시: "30만")
   - 5 core inputs: 매수타점, 2차저항, 1차저항, 1차지지, 2차지지 (각각 가격 + 익절/손절 %)
   - **익절/손절 % picklist**: 0%, 25%, 50%, 75%, 100% (합=100 자동 계산)
   - **2가지 모드**:
     - **🔔 알림 전용** (`notify_only=true`): 매수타점 도달 시 텔레그램 알림만, 주문 실행 X
     - **🤖 자동매매** (`notify_only=false`): 알림 + 자동 주문 실행
   - **섹션 내 정렬**: 자동매매 종목이 위로, 알림전용 종목이 아래로
   - **Row 체크박스**: 선택 시 폼에 데이터 auto-fill → 수정 후 저장 (CREATE/UPDATE)
   - **Full inline editing**: 테이블에서 모든 필드 직접 수정 가능 (종목명, 매수타점, Budget, Polling, 레벨)
   - **모드 태그 클릭**: 테이블에서 모드 태그 클릭으로 알림/자동 전환
   - Auto-calculation: quantity = budget / buy_target_price
   - **Polling 최적화**: 종목별 마지막 체크 시간 기록, polling_interval만큼 경과 후 체크
   - **중복 알림 방지**: `last_notification` 필드로 상태 변화 시에만 알림 발송

4. **💰 매매일지 (Tradelog)** - 구현 대기
   - 확정 손익만 표시 (auto_sold, manual_sold)
   - Stats cards: 총 거래, 총 수익, 평균 수익률
   - Date range filter
   - 계좌 polling으로 자동 상태 변경

5. **📰 뉴스필터 (NewsFilter)** - 완료 ✅
   - 오늘 전체 뉴스 / 급등주 테이블 (날짜 선택 가능)
   - 필터링된 뉴스 테이블 (체크박스 선택 → 선택 인사이트 스킬 연동)
   - 키워드 관리: Include / Exclude / AND그룹 / loose·strict 모드 토글
   - 테마 라이브러리: 급등주 채널에서 자동 누적 + 수동 추가/삭제/토글

6. **🧪 Test** - Kiwoom API 테스트 (완료)
   - 종목 정보 조회 (code → name, current_price)
   - 일봉차트 조회 (종목명/코드 → 당일/전일 가격 정보)
   - 분봉 차트 조회 (1/3/5/10분)
   - 토큰 상태 확인

### Web UI Architecture

```
templates/index.html
├─ Navigation (top bar)
├─ Page Container
│  ├─ Watchlist Page (default active)
│  ├─ Mode1 Page
│  ├─ Mode2 Page
│  ├─ Tradelog Page
│  ├─ NewsFilter Page ← NEW
│  └─ Test Page
└─ static/
   ├─ css/style.css (responsive, multi-page layout)
   ├─ js/app.js (page switching, API calls)
   └─ img/mode2_chart.png
```

## Architecture

### Telegram Bot Interface (Tactic1/2)

1. **bot_v3.py** - Telegram bot with ConversationHandler-based flows
   - Multi-step dialogs for registering/updating tactics
   - Commands: /tactic1, /tactic2, /list, /start_monitoring, /stop_monitoring
   - **Server control**: /server (status), /on (manual start), /off (manual stop)
   - Integrates with PriceMonitor for background monitoring
   - Integrates with ServerScheduler for automatic server control

2. **tactic_manager.py** - Watchlist persistence and management
   - Stores tactics in `.data/watchers.json`
   - Each watcher tracks: code, tactic type, config, status, buy info

### Web UI Interface (Mode1/Mode2)

1. **web_app.py** - Flask REST API server + PriceMonitor ⭐
   - Mode1 endpoints: GET/POST/PUT/DELETE /api/mode1/watchers + PATCH for status/active
   - Mode2 endpoints: GET/POST/PUT/DELETE /api/mode2/watchers + PATCH for status/active
   - Test endpoints: /api/test/stock-info, /api/test/chart, /api/test/daily-chart, /api/test/token
   - Order mode endpoints: GET/PUT /api/config/order-mode (simulation/real toggle)
   - **PriceMonitor 통합**: 웹 서버 시작 시 자동으로 백그라운드 모니터링 시작
   - **독립 실행 가능**: Telegram bot 없이도 Mode1/Mode2 자동매매 완전 동작
   - Serves static HTML/CSS/JS frontend
   - Default port: 5000 (configurable via WEB_PORT, currently running on 5002)

2. **mode1_manager.py** - Mode1 watchlist manager (완료)
   - Stores Mode1 strategies in `.data/mode1_watchers.json`
   - Data structure:
     ```python
     {
       "code": str,
       "name": str,
       "monitoring_price": float,
       "monitoring_conditions": [
         {"interval": "1분/3분/5분/10분", "trend": "상승/하락", "count": int}
       ],
       "expected_profit_rate": float,
       "polling_interval": int (default: 20 seconds),
       "greenlight_status": {},  # Each condition's satisfaction status
       "insight": str,  # Monitoring insight message
       "buy_price": float,
       "status": "waiting_buy/waiting_sell/auto_sold/manual_sold",
       "active": bool,
       "bought_price": float,
       "bought_quantity": int,
       "bought_at": ISO datetime
     }
     ```
   - Methods: add_watcher, update_watcher, delete_watcher, set_active, update_status, update_insight, update_greenlight_status, record_buy, record_sell

3. **mode2_manager.py** - Mode2 watchlist manager (완료)
   - Stores Mode2 strategies in `.data/mode2_watchers.json`
   - Data structure:
     ```python
     {
       "code": str,
       "name": str,
       "buy_target_price": int,
       "budget": int,
       "quantity": int (auto-calc: budget // buy_target_price),
       "resistance_1_price": int,
       "resistance_1_profit_pct": float,
       "resistance_2_price": int,
       "resistance_2_profit_pct": float,
       "support_1_price": int,
       "support_1_loss_pct": float,
       "support_2_price": int,
       "support_2_loss_pct": float,
       "polling_interval": int (default: 10 seconds),
       "notify_only": bool (default: False, True=알림만/False=자동매매),
       "status": "waiting_buy/waiting_sell/auto_sold/manual_sold",
       "active": bool,
       "bought_price": float,
       "bought_quantity": int,
       "bought_at": ISO datetime
     }
     ```
   - Methods: add_watcher, update_watcher, delete_watcher, set_active, record_buy, record_sell

### News Filter Service (뉴스/급등주 아카이빙) ✅ NEW 2026-04-28

1. **signal_listener.py** - Pyrogram 기반 텔레그램 채널 구독 서비스
   - Source 1 (급등주 `-1003342481653`) → Target (`-1003623684126`) 포워딩
   - Source 2 (뉴스 `-1003239561368`) → Target (`-1003599721748`) 포워딩
   - 모든 수신 메시지를 `news.db`에 아카이빙 (필터 통과 여부 무관)
   - 급등주 채널에서 테마 자동 추출 → `themes` 테이블에 누적
   - 키워드 필터링 통과 시 포워딩 + `filtered_messages` 테이블 기록
   - `signal_listener.session` 파일 필요 (최초 1회 Pyrogram 인증)

2. **news_storage.py** - SQLite 기반 뉴스/급등주/테마 저장소
   - `messages` 테이블: 전체 수신 메시지 (source_type: news / hot_stock)
   - `filtered_messages` 테이블: 필터링 통과 메시지
   - `themes` 테이블: 테마 라이브러리 (자동 누적)
   - DB 경로: `.data/news.db`

3. **keyword_storage.py** - 키워드 설정 JSON 저장소 (portalocker 기반)
   - 저장 경로: `.data/keywords.json`
   - Include 키워드 / Exclude 키워드 / AND 그룹 / loose·strict 모드

4. **keyword_filter.py** - 키워드 필터링 로직
   - loose 모드: include 키워드 하나라도 매칭 → 포워딩
   - strict 모드: include 키워드 모두 매칭 → 포워딩
   - AND 그룹: 그룹 내 모두 매칭 → 포워딩 (그룹 간 OR)
   - 중복 방지: MD5 해시 → `message_hashes.txt`
   - 키워드 핫리로드: 파일 변경 감지 (30초 주기)

### Claude Code 스킬 (`.claude/skills/`) ✅ NEW 2026-04-28

| 스킬 | 트리거 | 역할 |
|------|--------|------|
| `news-grouping` | `/news-grouping` | 오늘 뉴스를 테마별 그룹핑 + 강도(H/M/L) |
| `news-insight` | `/news-insight` | 마지막 실행 이후 신규 뉴스 증분 분석 |
| `news-insight-selected` | `/news-insight-selected` | 체크박스로 선택한 뉴스만 심층 분석 |

- 프롬프트 파일 수정으로 분석 기준 커스터마이징 가능
  - `.claude/skills/news-grouping/prompts/grouping.md`
  - `.claude/skills/news-insight/prompts/insight.md`

### Shared Components

1. **price_monitor.py** - Unified monitoring engine ⭐ 2026-04-27 비동기 최적화
   - Monitors Tactic1/2, Mode1, Mode2 simultaneously
   - Mode2 logic: checks buy_target_price, resistance (익절), support (손절)
   - **비동기 병렬 처리**: `asyncio.gather()` 사용으로 11개 종목 1초 처리
   - **Polling 최적화**: mode2_last_check dict로 종목별 마지막 체크 시간 기록
     - 각 종목의 polling_interval만큼 경과 후에만 체크
     - 불필요한 API 호출 방지 (95% 절감)
   - **알림 전용 모드**: `notify_only=True`일 때 알림만 전송, 주문 실행 X
   - Auto-executes orders via KiwoomClient when signals trigger (notify_only=False일 때)
   - Sends Telegram notifications for all trades (모드 태그 포함)
   - Runs as asyncio background task

2. **kiwoom_client.py** - Kiwoom API wrapper (동기 버전)
   - Auto-refreshes OAuth2 token every 25 minutes (TTL: 30min)
   - `get_last_price(symbol)`: Uses ka10003 API for current price
   - `get_stock_info(symbol)`: Returns code, name, current_price
   - `place_buy_order()` / `place_sell_order()`: Order execution (currently simulation)
   - Test mode: set TEST_LAST_PRICE env var to bypass API calls

2-1. **kiwoom_client_async.py** - 비동기 Kiwoom API wrapper ⭐ NEW
   - **aiohttp 기반**: 비동기 HTTP 클라이언트 (블로킹 제거)
   - **Rate limiting 내장**: 초당 5회 제한
   - **병렬 호출 가능**: 여러 종목 동시 API 호출
   - **성능**: 11개 종목 1.033초 (동기 110초 → 99% 개선)
   - 동일 인터페이스: 기존 코드와 호환

3. **kiwoom_chart.py** - Daily chart data (copied from kiwoom-min)
   - `get_daily_chart(token, symbol)`: Uses ka10081 API
   - Returns: today_open, today_high, today_low, today_current, yesterday_close, yesterday_high, yesterday_low
   - `format_chart_info(chart_data, current_price)`: Formats for display
   - Used by Test page for daily chart queries

4. **symbol_resolver.py** - Stock name/code converter
   - `resolve_symbol(symbol)`: Converts stock name ↔ code
   - Uses `files/corp_master1.xlsx` (Excel file with stock master data)
   - Returns: { stock_code, corp_name, dart_corp_code }
   - Handles exact match and partial match
   - Required for Test page daily chart feature

5. **server_scheduler.py** - GCP server auto-scheduling and control
   - Auto ON: Weekdays (Mon-Fri) 08:00 KST (market open)
   - Auto OFF: Weekdays 15:30 KST (market close)
   - Auto OFF: Weekends (all day)
   - Manual override: `/on` or `/off` commands
   - Manual mode persists until turned off
   - Uses gcloud CLI to control GCP VM instance
   - **Efficient scheduling**: Sleeps until next scheduled time (08:00 or 15:30), not constant polling

**Data flow:**
```
Web UI → Flask API → Manager (mode1/mode2) → PriceMonitor → KiwoomClient → Telegram Notification
```

## Key Patterns

### Stock Code Normalization (utils/code.py)
- Always use `normalize_stock_code()` before storing or querying
- Pads numeric codes to 6 digits: "81180" → "081180"
- Handles mixed alphanumeric: "KQ178920" → "KQ178920"
- Converts fullwidth chars: "０８１１８０" → "081180"

### Stock Name Resolution (symbol_resolver.py)
- Use `resolve_symbol()` to convert stock name to code
- Reads from `files/corp_master1.xlsx`
- Handles Korean stock names (정확 일치 및 부분 일치)
- Returns None if not found

### Token Management
- Kiwoom OAuth2 tokens expire in 30 minutes
- Client auto-refreshes at 25min via `_ensure_valid_token()`
- If refresh fails, continues with existing token (fallback strategy)

### Status Tracking
Each watcher maintains a `status` field:
- **Tactic1**: `waiting` → `bought` → `sold`
- **Tactic2**: `waiting_1st` → `bought_1st` → `bought_2nd` → `sold`
- **Mode1**: `waiting_buy` → `waiting_sell` → `auto_sold` / `manual_sold`
- **Mode2**: `waiting_buy` → `waiting_sell` → `auto_sold` / `manual_sold`

### Mode2 Trading Logic

**Entry (매수):**
- Triggers when current price reaches buy_target_price (±1% tolerance)
- Quantity auto-calculated: `budget // buy_target_price`

**Exit (익절/손절):**
Priority order (checked top to bottom):
1. **2차 저항 (resistance_2_price)** - Full exit at highest target
2. **1차 저항 (resistance_1_price)** - Partial profit taking
3. **2차 지지 (support_2_price)** - Deep stop loss
4. **1차 지지 (support_1_price)** - First stop loss

PriceMonitor checks these levels every MONITOR_INTERVAL and auto-executes orders via KiwoomClient.

### Mode1 Trading Logic (완료)

**Monitoring:**
- 분봉 데이터 조회: ka10080 API 사용 (`get_minute_chart()`)
- 시간 기반 polling 스케줄:
  - **1분봉**: 사용자 설정 주기 (기본 20초)
  - **3분봉**: 00:03, 03:03, 06:03, 09:03, ... (3분 간격 + 3초 offset)
  - **5분봉**: 00:03, 05:03, 10:03, 15:03, ... (5분 간격 + 3초 offset)
  - **10분봉**: 00:03, 10:03, 20:03, 30:03, ... (10분 간격 + 3초 offset)
- 추세 분석:
  - **양봉**: `종가 > 시가`
  - **음봉**: `종가 < 시가`
  - **연속 N개**: 최신 봉부터 역순으로 카운트
- 그린라이트 조건: **모든 조건이 AND로 만족**되면 알림

**Entry (매수):**
- 그린라이트 조건 만족 시 텔레그램 알림 (수동 매수)
- 알림 내용: 종목명, 모니터링가, 기대수익률, 조건 상태, 최근 분봉 요약

**Monitoring Conditions:**
각 조건은 4개 필드로 구성:
```python
{
  "interval": "1분/3분/5분/10분",    # 분봉 종류
  "trend": "상승/하락",              # 추세 방향
  "count": int,                    # 연속 봉 개수
  "candle_count": int              # 조회할 총 봉 개수 (최대 200)
}
```

## Environment Variables

Critical settings in `.env`:
```bash
# Telegram
TELEGRAM_BOT_TOKEN=...       # Required
TELEGRAM_CHAT_ID=...         # For notifications

# Kiwoom API
KIWOOM_HOST=https://api.kiwoom.com
KIWOOM_APPKEY=...
KIWOOM_SECRETKEY=...

# Web Server
WEB_PORT=5000                # Flask web UI port (default: 5000, current: 5002)
WEB_HOST=0.0.0.0             # Bind address

# Monitoring
MONITOR_INTERVAL=10          # Price check interval (seconds)

# Order Settings
ORDER_SIMULATION_MODE=1      # 1=Simulation, 0=Real orders (CAUTION!)
KIWOOM_DEBUG=0               # 1=Debug mode

# GCP Server Control
GCP_INSTANCE_NAME=kiwoom-trading-bot  # GCP VM instance name
GCP_ZONE=asia-northeast3-a            # GCP Zone (Seoul)
GCP_PROJECT_ID=                       # GCP Project ID (optional, uses default if empty)

# Testing
TEST_LAST_PRICE=116000       # Bypass API, return fixed price
IGNORE_MARKET_HOURS=1        # Skip time validation

# 뉴스 필터링 서비스 (Signal Listener)
TG_API_ID=...                # Telegram User API ID (my.telegram.org)
TG_API_HASH=...              # Telegram User API Hash
SOURCE_CHAT_IDS=-1003342481653,-1003239561368   # 소스 채널 (급등주, 뉴스)
SOURCE_DEST_MAPPING=-1003342481653:-1003623684126,-1003239561368:-1003599721748
DEST_CHAT_ID=-1003623684126  # 기본 목적지
NEWS_DB_PATH=.data/news.db   # 뉴스 아카이브 DB 경로
KEYWORD_RELOAD_INTERVAL=30   # 키워드 핫리로드 주기 (초)
```

## Testing Strategy

- **test_bot.py**: TacticManager CRUD operations, no API calls
- **test_kiwoom.py**: Live token fetch and price queries (requires valid credentials)
- **test_mode2_monitoring.py**: Mode2 monitoring logic with mock price
- **TEST_LAST_PRICE**: For testing bot logic outside market hours
- **Web UI Test Page**: Interactive API testing (stock info, daily chart, token status)
- Never commit `.env` file (already in .gitignore)

## File Structure

### Current Production Files
- **bot_v3.py** - Telegram bot (Tactic1/2) with monitoring + server control
- **web_app.py** - Flask REST API + multi-page static file server
- **run_all.py** - Unified launcher (bot + web server + signal_listener)
- **server_scheduler.py** - GCP server auto-scheduling (평일 08:00~15:30)
- **mode1_manager.py** - Mode1 watchlist manager (완료)
- **mode2_manager.py** - Mode2 watchlist manager (완료)
- **price_monitor.py** - Unified monitoring engine (Tactic1/2 + Mode1 + Mode2) (완료)
- **kiwoom_client.py** - Kiwoom API wrapper with order execution
- **kiwoom_chart.py** - Daily + minute chart data retrieval (ka10081, ka10080 API)
- **trend_analyzer.py** - Candle trend analysis (양봉/음봉, 연속 카운트)
- **symbol_resolver.py** - Stock name/code converter
- **tactic_manager.py** - Tactic1/2 watchlist manager
- **signal_listener.py** - Pyrogram 채널 구독 + 아카이빙 + 포워딩 ✅ NEW
- **news_storage.py** - SQLite 뉴스/급등주/테마 저장소 ✅ NEW
- **keyword_storage.py** - 키워드 설정 JSON 저장소 ✅ NEW
- **keyword_filter.py** - 키워드 필터링 엔진 ✅ NEW
- **keyword_config.py** - 키워드 파일 경로 설정 ✅ NEW
- **admin_server_oracle.py** - 오라클 서버 관리 UI (signal_listener 상태 포함)

### Frontend Files
- **templates/index.html** - Multi-page SPA structure
- **static/css/style.css** - Responsive multi-page layout
- **static/js/app.js** - Page switching, API calls, event handling
- **static/img/mode2_chart.png** - Mode2 strategy visual guide

### Data Files
- `.data/watchers.json` - Tactic1/2 watchlist
- `.data/mode1_watchers.json` - Mode1 watchlist
- `.data/mode2_watchers.json` - Mode2 watchlist
- `.data/manual_server_control.txt` - Manual server control state (on/off)
- `.data/news.db` - 뉴스/급등주 아카이브 SQLite DB ✅ NEW
- `.data/keywords.json` - 키워드 필터링 설정 ✅ NEW
- `.data/message_hashes.txt` - 중복 방지 해시 목록 ✅ NEW
- `signal_listener.session` - Pyrogram 인증 세션 (최초 1회 생성) ✅ NEW
- `files/corp_master1.xlsx` - Stock master data (종목코드, 종목명, DART 코드)

### Legacy Files (Reference Only)
- `bot.py` - Initial version (basic commands)
- `bot_v2.py` - Enhanced parsing

Always use `bot_v3.py` or `run_all.py` for development.

## API Endpoints

### Mode1 API
- `GET /api/mode1/watchers` - List all Mode1 watchers
- `POST /api/mode1/watchers` - Create new watcher (종목명 auto-lookup)
- `GET /api/mode1/watchers/:code` - Get specific watcher
- `PUT /api/mode1/watchers/:code` - Update watcher
- `DELETE /api/mode1/watchers/:code` - Delete watcher
- `PATCH /api/mode1/watchers/:code/active` - Toggle active status
- `PATCH /api/mode1/watchers/:code/status` - Update status

### Mode2 API
- `GET /api/mode2/watchers` - List all Mode2 watchers
- `POST /api/mode2/watchers` - Create new watcher (종목명 auto-lookup)
- `GET /api/mode2/watchers/:code` - Get specific watcher
- `PUT /api/mode2/watchers/:code` - Update watcher
- `DELETE /api/mode2/watchers/:code` - Delete watcher
- `PATCH /api/mode2/watchers/:code/active` - Toggle active status
- `PATCH /api/mode2/watchers/:code/status` - Update status

### Test API
- `GET /api/test/stock-info/:code` - Get stock info (code, name, price)
- `GET /api/test/chart/:code?interval=1` - Get minute chart (1/3/5/10)
- `POST /api/test/daily-chart` - Get daily chart (accepts stock name or code)
- `GET /api/test/token` - Check token status
- `POST /api/test/telegram` - Send telegram test message
  - Body: { message: str }
  - Uses TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID from .env
  - Returns: { success, message }

### Account API
- `GET /api/account/positions` - Get account holdings (보유 종목 조회)
  - Returns: summary (total_value, total_profit, total_profit_rate, deposit_balance)
  - Returns: positions array (code, name, quantity, buy_price, current_price, profit, profit_rate, eval_amount)

### Order API
- `POST /api/order/buy` - Place buy order (매수 주문 - kt10000)
  - Body: { code, quantity, order_type: "market"|"limit", price }
  - Returns: { success, order_no, message }
- `POST /api/order/sell` - Place sell order (매도 주문 - kt10001)
  - Body: { code, quantity (optional, null=all), order_type: "market"|"limit", price, mode: "mode1"|"mode2" }
  - On success: Calls manager.record_sell(code, is_auto=False) to update status
  - Returns: { success, order_no, message }

### Watchlist API
- `POST /api/watchlist/sync-holdings` - Sync holdings from account to watchlist (보유수량 동기화)
  - Fetches account positions via kiwoom_client.get_positions()
  - Updates bought_quantity for all Mode1/Mode2 watchers
  - Sets bought_quantity=0 for watchers not in account
  - Returns: { success, message, holdings_count }

### News Filter API ✅ NEW
- `GET /api/news/today?date=YYYY-MM-DD` - 오늘 전체 뉴스 (생략 시 오늘)
- `GET /api/news/filtered?date=YYYY-MM-DD` - 필터링된 뉴스
- `GET /api/hotstock/today?date=YYYY-MM-DD` - 오늘 전체 급등주
- `GET /api/hotstock/filtered?date=YYYY-MM-DD` - 필터링된 급등주
- `GET /api/keywords` - 키워드 설정 전체 조회
- `POST /api/keywords/include` - include 키워드 추가 `{ keyword }`
- `DELETE /api/keywords/include` - include 키워드 삭제 `{ keyword }`
- `POST /api/keywords/exclude` - exclude 키워드 추가 `{ keyword }`
- `DELETE /api/keywords/exclude` - exclude 키워드 삭제 `{ keyword }`
- `POST /api/keywords/group` - AND 그룹 추가 `{ keywords: [] }`
- `DELETE /api/keywords/group` - AND 그룹 삭제 `{ keywords: [] }`
- `PATCH /api/keywords/mode` - 모드 변경 `{ mode: "loose"|"strict" }`
- `GET /api/themes` - 테마 목록
- `POST /api/themes` - 테마 수동 추가 `{ name }`
- `PATCH /api/themes/<id>` - 테마 활성화 토글
- `DELETE /api/themes/<id>` - 테마 삭제

## TODO / 구현 대기

### Completed ✅
1. **Mode1 구현 완료** ✅
   - ✅ `mode1_manager.py` 작성 완료
   - ✅ Mode1 REST API 엔드포인트 추가 완료
   - ✅ Mode1 페이지 UI 연동 완료 (동적 조건 추가/삭제, 조회 봉 개수 입력)
   - ✅ 분봉 데이터 조회 API 구현 (`get_minute_chart()` - ka10080)
   - ✅ 추세 분석 로직 (`trend_analyzer.py` - 음봉/양봉 감지, 연속 카운트)
   - ✅ 그린라이트 조건 체크 로직 (price_monitor.py에 통합)
   - ✅ 시간 기반 polling 스케줄러 (1/3/5/10분봉)
   - ✅ 텔레그램 알림 (수동 매수)

2. **계좌 보유 종목 조회** ✅
   - ✅ `get_positions()` 구현 (ka01690 API)
   - ✅ `/api/account/positions` 엔드포인트
   - ✅ 감시리스트 페이지에 "보유 종목 조회" 버튼
   - ✅ 계좌 요약 (총 평가금액, 손익, 수익률, 예수금)
   - ✅ 보유 종목 상세 테이블

3. **실제 주문 API** ✅
   - ✅ `place_buy_order()` 실제 구현 (kt10000)
   - ✅ `place_sell_order()` 실제 구현 (kt10001)
   - ✅ 보유수량 자동 조회 (`_get_holding_qty()` - kt00018)
   - ✅ 시뮬레이션 모드 (`ORDER_SIMULATION_MODE=1`)
   - ✅ Test 페이지 주문 테스트 UI
   - ✅ `/api/order/buy`, `/api/order/sell` 엔드포인트

### High Priority
1. **매매일지 페이지**
   - 확정 손익 내역 조회 API
   - 통계 계산 (총 거래, 총 수익, 평균 수익률)
   - Date range filter

2. **계좌 polling 및 자동 상태 변경**
   - 주기적으로 보유 종목 조회
   - 감시리스트와 비교하여 자동 상태 업데이트
   - 수동 매도 감지 (waiting_sell → manual_sold)

### Medium Priority
4. **실제 주문 API 연동**
   - `place_buy_order()` / `place_sell_order()` 실제 구현
   - 현재는 시뮬레이션 모드
   - 주문 체결 확인 로직

5. **감시리스트 필터링**
   - Mode, Status, Date 필터 동작 구현
   - 정렬 기능 추가

6. **Mode2 테이블 inline editing**
   - 현재 Budget만 가능
   - 모든 필드 inline editing 완성

## Lessons from kiwoom-min Project

This codebase integrates patterns from a previous validated project (`~/Documents/kiwoom-min`):
- Token auto-refresh (25min interval)
- ka10003 API for reliable price data (extracts from `cntr_infr` list)
- ka10081 API for daily chart data
- Stock code normalization (critical for Kiwoom API compatibility)
- Stock name resolution via corp_master.xlsx
- Error handling with fallback mechanisms
- Telegram bot checkprice/checkprices commands

Key files copied from kiwoom-min:
- `kiwoom_chart.py` (일봉차트 조회)
- `files/corp_master1.xlsx` (종목 마스터 데이터)

See CHANGES.md for detailed integration notes.

---

## ⚠️ Common Mistakes & Prevention Guide

### 🚨 CRITICAL: Kiwoom API 호출 코드는 절대 함부로 수정 금지!

Kiwoom REST API를 호출하는 모든 서비스는 **프로덕션 환경에서 실제 거래**를 실행합니다. 
코드 수정으로 인한 임팩트가 발생하면 금전적 손실로 직결됩니다.

**절대 수정 금지 코드**:
- `kiwoom_client.py` - 토큰 발급, 주문 실행, 계좌 조회
- `kiwoom_chart.py` - 차트 데이터 조회
- `kiwoom_token.py` - OAuth2 토큰 관리

**수정 시 반드시 지켜야 할 규칙**:
1. **로컬 테스트 필수**: 변경 후 로컬에서 충분히 검증
2. **시뮬레이션 모드 우선**: `ORDER_SIMULATION_MODE=1`로 테스트
3. **API 호출 횟수 체크**: 과도한 호출로 Rate Limit 방지
4. **에러 핸들링 유지**: 기존 try-except 구조 절대 제거 금지
5. **로그 확인**: 변경 후 web_app.log 확인

### 🔐 Authentication 관련 실수 방지

**실수 1: Basic Auth 추가 후 fetch에 credentials 누락**
```javascript
// ❌ 잘못된 예
fetch('/api/endpoint')

// ✅ 올바른 예
fetch('/api/endpoint', {
    credentials: 'same-origin'
})
```

**해결책**: 
- 모든 fetch 호출에 `credentials: 'same-origin'` 필수
- 새로운 API 엔드포인트 추가 시 템플릿 참고

**실수 2: .env 파일 문법 오류**
```bash
# ❌ 잘못된 예
WEB_USERNAME==admin  # 등호 2개

# ✅ 올바른 예
WEB_USERNAME=admin   # 등호 1개
```

**해결책**:
- .env 파일 수정 후 반드시 검증
- `grep "==" .env` 실행해서 이중 등호 체크

### 📊 데이터 구조 변경 시 주의사항

**실수 3: 기존 데이터 구조 변경 시 마이그레이션 미고려**

Mode1을 `monitoring_conditions` → `step1/step2/step3` 구조로 변경할 때:
- 기존 `.data/mode1_watchers.json` 파일과 호환성 체크 필요
- 기존 데이터가 있다면 마이그레이션 스크립트 제공

**해결책**:
- 데이터 구조 변경 전 기존 파일 백업
- 호환성 유지 또는 명시적 마이그레이션 제공
- 변경 사항 CHANGELOG에 기록

### 🌐 Web Server 수정 시 체크리스트

**before_request 같은 글로벌 훅 수정 시**:
- static 파일 접근 가능 여부 확인
- API 엔드포인트 전체 영향 검토
- 브라우저 콘솔에서 401/403 에러 확인

**Frontend 변경 시**:
- 브라우저 캐시 클리어 (`Cmd+Shift+R`)
- 개발자 도구 Network 탭으로 API 호출 확인
- 콘솔 에러 확인

### 🧪 변경 후 필수 확인 사항

**API 변경 시**:
```bash
# 1. 서버 로그 확인
tail -50 web_app.log

# 2. API 테스트
curl -s -u $USERNAME:$PASSWORD http://localhost:5002/api/test-endpoint

# 3. 에러 체크
grep ERROR web_app.log
```

**데이터베이스(JSON 파일) 변경 시**:
```bash
# 백업
cp .data/mode1_watchers.json .data/mode1_watchers.json.backup

# 검증
python -c "import json; json.load(open('.data/mode1_watchers.json'))"
```

### 📝 코드 수정 전 체크리스트

- [ ] 이 코드가 Kiwoom API를 직접 호출하는가?
- [ ] 이 변경이 실제 거래에 영향을 주는가?
- [ ] 로컬에서 테스트 완료했는가?
- [ ] 시뮬레이션 모드로 검증했는가?
- [ ] 에러 핸들링이 유지되는가?
- [ ] 기존 데이터와 호환되는가?
- [ ] .env 파일 문법이 올바른가?
- [ ] fetch에 credentials가 포함되어 있는가?

### 🔄 Rollback 방법

**문제 발생 시 즉시 롤백**:
```bash
# 1. Git으로 되돌리기
git log --oneline -10
git revert <commit-hash>

# 2. 서버 재시작
lsof -ti:5002 | xargs kill -9
source .venv/bin/activate && WEB_PORT=5002 python web_app.py

# 3. 백업 데이터 복원
cp .data/*.json.backup .data/

# 4. 로그 확인
tail -100 web_app.log
```

### 💡 Best Practices

1. **작은 단위로 변경**: 한 번에 하나의 기능만 수정
2. **로그 먼저 확인**: 변경 후 반드시 로그 체크
3. **테스트 페이지 활용**: /Test 페이지에서 API 직접 테스트
4. **사용자 피드백 반영**: 같은 실수 반복 시 CLAUDE.md 업데이트
5. **문서화**: 중요한 변경사항은 CHANGES.md에 기록

---

### 🤖 Telegram Bot Conflicts - CRITICAL LESSON (2026-04-27)

**문제**: 텔레그램 봇이 "Conflict: terminated by other getUpdates request" 에러 발생

**근본 원인**:
- **같은 텔레그램 봇 토큰**을 여러 서버/프로세스에서 동시 사용
- 텔레그램 API는 **1개 봇 토큰당 1개 인스턴스만** 허용
- 2개 이상에서 동시 실행 시 충돌 발생

**발생 사례**:
```
오라클 서버: run_all.py (텔레그램 봇 포함)
GCP 서버: web_app.py (PriceMonitor 내 텔레그램 봇 포함)
→ 같은 TELEGRAM_BOT_TOKEN 사용 → Conflict 에러
```

**해결 방법**:
1. **서버 간 중복 실행 방지**: 
   - 프로덕션 서버 1곳에서만 텔레그램 봇 실행
   - 다른 서버는 정지 또는 `bot_application=None` 설정

2. **프로세스 확인**:
   ```bash
   # 오라클 서버
   ssh opc@152.67.207.143 'ps aux | grep "python.*bot_v3\|python.*run_all"'
   
   # GCP 서버
   gcloud compute ssh instance-name --command 'ps aux | grep python'
   ```

3. **충돌 디버깅 순서**:
   - 모든 서버에서 봇 프로세스 확인
   - GCP/오라클/로컬 맥 모두 체크
   - 텔레그램 API 상태 클리어: `curl "https://api.telegram.org/bot<TOKEN>/getUpdates?offset=-1"`
   - 1개 프로세스만 남기고 나머지 정리

4. **예방책**:
   - **배포 전 반드시 확인**: 다른 서버에서 봇 실행 중인지 체크
   - **run_all.py 우선**: 웹서버 + 텔레그램 봇 통합 실행 권장
   - **별도 실행 시**: web_app.py는 `bot_application=None`, bot_v3.py는 별도 실행

**프로덕션 체크리스트**:
- [ ] 오라클 서버에서만 run_all.py 실행 중?
- [ ] GCP 서버 정지 또는 봇 비활성화?
- [ ] 로컬 맥에서 봇 실행 안 함?
- [ ] 텔레그램 getUpdates "200 OK" 응답?

**현재 운영 상태** (2026-04-28):
- ✅ 오라클 서버: web_app.py (웹서버 443 + 텔레그램 알림)
- ✅ GCP 서버: 정지됨
- ✅ 도메인: https://nomaddoklip.xyz
- ✅ 텔레그램 알림: 정상 동작

---

### 📊 2026-04-28 주요 업데이트

#### 1. Mode2 매수 조건 수정 (`<=` 연산자)
**문제**: Test 페이지에서 현재가(22,800원) > 매수타점(22,110원)인데 매수 시그널 발생
**원인**: `web_app.py` test endpoint에서 `current_price >= buy_target` 로직 사용 (반대)
**해결**: 
- `price_monitor.py`: `current_price <= target_price` ✅ (올바름)
- `web_app.py` test endpoint: `current_price < buy_target` → `current_price <= buy_target`로 통일

**Lesson Learned**:
- 같은 로직을 여러 곳에서 구현할 때 **일관성 체크 필수**
- Test endpoint는 실제 모니터링 로직과 **완전히 동일**해야 함
- `<` vs `<=` 같은 경계값 처리는 **사양 문서에 명확히 기록** 필요

#### 2. 텔레그램 알림 누락 해결
**문제**: 475580 종목 매수 성공했으나 텔레그램 알림 미발송
**원인**: `web_app.py`에서 PriceMonitor 초기화 시 `bot_application=None`
**해결**: 
```python
# web_app.py 추가
from telegram.ext import Application
bot_application = Application.builder().token(telegram_token).build()
price_monitor = PriceMonitor(..., bot_application=bot_application)
```

**Lesson Learned**:
- **웹 서버 단독 실행** 시나리오 고려 필요
- 텔레그램 봇을 2가지 방식으로 통합 가능:
  1. `run_all.py` - 별도 프로세스로 bot_v3.py 실행
  2. `web_app.py` - Application 객체만 생성 (알림 전송용)
- 프로덕션에서는 **방법 2 권장** (단일 프로세스, 간단한 배포)

#### 3. Oracle Cloud iptables 설정
**문제**: 서버 재시작 후 https://nomaddoklip.xyz 접속 불가
**원인**: 443 포트가 iptables에 등록되지 않음 (5000 포트만 존재)
**해결**:
```bash
sudo iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
sudo iptables-save | sudo tee /etc/sysconfig/iptables
```

**Lesson Learned**:
- **firewalld vs iptables**: 둘 다 확인 필요
  - `firewall-cmd --list-all` (firewalld)
  - `iptables -L -n` (iptables)
- Oracle Cloud는 **iptables가 우선**
- 포트 변경 시 **Security List + iptables 모두 설정** 필요
- 설정 후 반드시 **저장**(iptables-save) 해야 재부팅 시에도 유지됨

#### 4. Mode2 Budget 만원 단위 입력
**요구사항**: Budget을 만원 단위로 입력/표시 (10 입력 = 100,000원)
**구현**:
- Picklist: 0만, 10만, 20만, 30만, 60만, 100만, 수동입력
- 테이블 표시: "30만" 형식
- Inline 편집: 만원 단위로 입력 → 저장 시 × 10,000

**Lesson Learned**:
- **UI 단위 변환**은 프론트엔드에서만 처리
- 백엔드 API는 **항상 원화(원) 단위** 저장
- 변환 로직 위치:
  - 폼 submit: `budgetValue = parseInt(input) * 10000`
  - 테이블 표시: `${(w.budget / 10000).toFixed(0)}만`
  - Inline 편집: 입력받은 값 × 10000 후 API 전송

#### 5. Mode2 섹션 내 정렬 (자동매매 우선)
**요구사항**: 섹션 클릭 시 자동매매 종목이 위로, 알림전용 종목이 아래로
**구현**:
```javascript
watchersBySection[sectionId].sort((a, b) => {
    // 1순위: notify_only (false가 true보다 우선)
    const notifyA = a.notify_only ? 1 : 0;
    const notifyB = b.notify_only ? 1 : 0;
    if (notifyA !== notifyB) return notifyA - notifyB;
    
    // 2순위: display_order
    return (a.display_order || 9999) - (b.display_order || 9999);
});
```

**Lesson Learned**:
- **복합 정렬**: 1순위 → 2순위 순서로 비교
- Boolean 값 정렬: `false=0, true=1`로 변환
- 사용자 수동 정렬(display_order)과 **자동 정렬 병행** 가능

#### 6. 계좌 보유 종목 → Mode2 편입 기능
**요구사항**: 
- 보유 종목을 Mode2로 편입
- 자동 입력: 종목코드, 종목명, 매수가, 수량, Budget
- 사용자 입력: 1차 저항, 1차 지지만
- 모바일 친화적 UI

**구현**:
- "📊 Mode2" 버튼 → 모달 팝업
- 큰 터치 영역 (14px padding, 16px font)
- 유효성 검사: 1차 지지 < 매수가 < 1차 저항
- `status: 'waiting_sell'` (이미 매수 완료 상태)

**Lesson Learned**:
- **모바일 고려 필수**: 
  - 버튼 최소 크기 44×44px
  - 폰트 최소 16px (자동 줌 방지)
  - 모달 외부 클릭으로 닫기
- **복잡한 폼 → 모달 분리**로 UX 개선
- 보유 종목은 **바로 waiting_sell 상태**로 시작

#### 7. 중복 알림 방지 (최종 해결)
**문제**: 에이비엘바이오(298380) 매수 시그널이 매 polling마다 반복 발송
**원인 1**: 중복 체크 로직 없음
**해결 1**: `last_notification` 필드 추가
```python
if last_notification == 'buy_signal':
    return None  # 이미 알림 보냄, 스킵
```

**원인 2**: AttributeError - `'PriceMonitor' object has no attribute 'mode2_manager'`
**해결 2**: `self.mode2_manager` → `self.mode2_mgr` 오타 수정

**Lesson Learned** ⭐ **중요**:
- **에러 로그 확인 필수**: 기능이 작동 안 하면 **반드시 로그부터 확인**
- 변수명 오타는 **실행 시점에만 발견**됨 (정적 분석 어려움)
  - `__init__`에서 `self.mode2_mgr` 저장
  - 실제 사용 시 `self.mode2_manager` 호출 → AttributeError
- **일관된 네이밍**: 약어 사용 시 **프로젝트 전체에 통일**
  - `mode2_mgr` vs `mode2_manager` → 하나로 통일 필요
- **중복 방지 패턴**:
  1. 상태 플래그 저장 (`last_notification`)
  2. 조건 만족 시 플래그 확인 → 이미 알림 보냈으면 스킵
  3. 조건 불만족 시 플래그 리셋 (재사용 가능하도록)

#### 8. 트러블슈팅 실수 모음
1. **속성명 오타 간과**: `self.mode2_manager` vs `self.mode2_mgr`
   - **예방**: 클래스 초기화 시 속성 리스트 주석으로 정리
   - **탐지**: 에러 로그에서 `AttributeError` 즉시 확인

2. **로직 불일치**: Test endpoint와 실제 모니터링 로직 차이
   - **예방**: 공통 함수로 추출, 중복 구현 최소화
   - **검증**: Test 페이지로 실제 시나리오 테스트

3. **환경 차이**: 로컬(brew firewall) vs Oracle(iptables)
   - **예방**: 배포 전 서버 환경 체크리스트 작성
   - **디버깅**: 서버 내부 테스트(`curl localhost`) → 외부 테스트

4. **단위 변환 혼동**: 만원 단위 입력 vs 원 단위 저장
   - **예방**: API 문서에 단위 명시
   - **검증**: 저장된 값 직접 확인 (JSON 파일 또는 로그)

---

**Remember**: 
- Kiwoom API 호출 코드는 금전적 손실과 직결
- 의심스러우면 수정하지 말고 사용자에게 먼저 확인
- 테스트 없이 프로덕션 코드 배포 금지
- 실수는 학습 기회 → CLAUDE.md에 즉시 기록
- **텔레그램 봇은 반드시 1곳에서만 실행** - 서버 간 중복 실행 절대 금지
