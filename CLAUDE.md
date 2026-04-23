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
- Mode2 active=true 종목은 **10초마다 자동 체크**
- 매수타점/저항/지지 도달 시 **즉시 주문 실행**
- Telegram bot 없이도 **웹 서버만으로 완전 동작**

## Essential Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all services (Telegram bot + Web UI)
python run_all.py

# Run individually
python bot_v3.py          # Telegram bot only
python web_app.py         # Web UI only (default port 5000)

# Run tests
python test_bot.py        # Basic functionality
python test_kiwoom.py     # Kiwoom API integration
python test_mode2_monitoring.py  # Mode2 monitoring test
```

## Web UI Structure (Multi-Page)

### Page Navigation
The web interface has 5 main pages accessed via top navigation:

1. **📊 감시리스트 (Watchlist)** - Default page
   - Unified view of all Mode1 + Mode2 stocks
   - Filters: Mode, Status, Date (UI ready, backend pending)
   - Displays: code, name, registration date, status, **bought_quantity**, current price, bought_price, profit rate
   - Actions:
     - **💼 보유 종목 조회**: Opens modal showing full account summary and holdings
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
   - Input form: 종목코드 (종목명 자동 조회), Budget, Polling 주기 (5/10/15/20/30초), **🔔 알림만 체크박스**
   - 5 core inputs: 매수타점, 2차저항, 1차저항, 1차지지, 2차지지 (각각 가격 + 익절/손절 %)
   - **2가지 모드**:
     - **🔔 알림 전용** (`notify_only=true`): 매수타점 도달 시 텔레그램 알림만, 주문 실행 X
     - **🤖 자동매매** (`notify_only=false`): 알림 + 자동 주문 실행
   - **Row 체크박스**: 선택 시 폼에 데이터 auto-fill → 수정 후 저장 (CREATE/UPDATE)
   - **Full inline editing**: 테이블에서 모든 필드 직접 수정 가능 (종목명, 매수타점, Budget, Polling, 레벨)
   - **모드 태그 클릭**: 테이블에서 모드 태그 클릭으로 알림/자동 전환
   - Auto-calculation: quantity = budget / buy_target_price
   - **Polling 최적화**: 종목별 마지막 체크 시간 기록, polling_interval만큼 경과 후 체크

4. **💰 매매일지 (Tradelog)** - 구현 대기
   - 확정 손익만 표시 (auto_sold, manual_sold)
   - Stats cards: 총 거래, 총 수익, 평균 수익률
   - Date range filter
   - 계좌 polling으로 자동 상태 변경

5. **🧪 Test** - Kiwoom API 테스트 (완료)
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

### Shared Components

1. **price_monitor.py** - Unified monitoring engine
   - Monitors Tactic1/2, Mode1, Mode2 simultaneously
   - Mode2 logic: checks buy_target_price, resistance (익절), support (손절)
   - **Polling 최적화**: mode2_last_check dict로 종목별 마지막 체크 시간 기록
     - 각 종목의 polling_interval만큼 경과 후에만 체크
     - 불필요한 API 호출 방지
   - **알림 전용 모드**: `notify_only=True`일 때 알림만 전송, 주문 실행 X
   - Auto-executes orders via KiwoomClient when signals trigger (notify_only=False일 때)
   - Sends Telegram notifications for all trades (모드 태그 포함)
   - Runs as asyncio background task

2. **kiwoom_client.py** - Kiwoom API wrapper
   - Auto-refreshes OAuth2 token every 25 minutes (TTL: 30min)
   - `get_last_price(symbol)`: Uses ka10003 API for current price
   - `get_stock_info(symbol)`: Returns code, name, current_price
   - `place_buy_order()` / `place_sell_order()`: Order execution (currently simulation)
   - Test mode: set TEST_LAST_PRICE env var to bypass API calls

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
- **run_all.py** - Unified launcher (bot + web server in parallel)
- **server_scheduler.py** - GCP server auto-scheduling (평일 08:00~15:30)
- **mode1_manager.py** - Mode1 watchlist manager (완료)
- **mode2_manager.py** - Mode2 watchlist manager (완료)
- **price_monitor.py** - Unified monitoring engine (Tactic1/2 + Mode1 + Mode2) (완료)
- **kiwoom_client.py** - Kiwoom API wrapper with order execution
- **kiwoom_chart.py** - Daily + minute chart data retrieval (ka10081, ka10080 API)
- **trend_analyzer.py** - Candle trend analysis (양봉/음봉, 연속 카운트)
- **symbol_resolver.py** - Stock name/code converter
- **tactic_manager.py** - Tactic1/2 watchlist manager

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

**Remember**: 
- Kiwoom API 호출 코드는 금전적 손실과 직결
- 의심스러우면 수정하지 말고 사용자에게 먼저 확인
- 테스트 없이 프로덕션 코드 배포 금지
- 실수는 학습 기회 → CLAUDE.md에 즉시 기록
