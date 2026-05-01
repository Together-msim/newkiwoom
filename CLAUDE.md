# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Korean stock auto-trading system with two interfaces:
1. **Web UI** (`web_app.py`) - Multi-page SPA: Watchlist, Mode1, Mode2, Tradelog, 시황체크(Siwhang), 백테스트, Test
2. **Signal Listener** (`signal_listener.py`) - Telegram channel archiver + keyword filter

**Active strategies:**
- **Mode1**: 전일대비 급등 첫 조정 (분봉 그린라이트 조건)
- **Mode2**: 저항/지지 레벨 자동매매 ⭐ **최우선 기능**

Tactic1/2 (`bot_v3.py`)는 구형 기능으로 현재 미사용.

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
- `asyncio.gather()`로 전 종목 병렬 체크 (14개 종목 ~1초)
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
- `.data/news.db` — 뉴스/급등주 SQLite DB (tables: messages, filtered_messages, themes, saved_news, siwhang_results, backtest_sessions, backtest_picks, backtest_pnl)
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
| `backtest` | `/backtest [YYYY-MM-DD]` | 지정 날짜 급등주/뉴스 → 13 타임슬롯 AI 분석 → 종목 추천 → Oracle 저장 |

프롬프트 커스터마이징: `.claude/skills/<skill>/prompts/`

**⚠️ `.claude/` 디렉터리는 `.gitignore`에 등록됨 — git push로 배포 불가.**  
Oracle 서버에 스킬 파일 배포 시 scp 사용:
```bash
scp -i /Users/msim/Downloads/ssh-key-2026-04-26.key \
  -r .claude/skills/siwhang opc@152.67.207.143:~/newkiwoom/.claude/skills/
```

**시황체크 스킬 분석 기준 수정**: `.claude/skills/siwhang/prompts/analysis.md` 편집

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
- 하단 고정 탭바 (≤768px): Mode2, 시황체크, 감시리스트, Mode1, 시그널, 매매일지, 백테스트, Test
- 기본 시작 페이지: Mode2
- 가로모드 감지: `(max-height: 500px) and (orientation: landscape)`
- 시황체크 테이블: 카드별 개별 검색 입력 (`data-search` 속성 pre-compute)

### 백테스트 시스템 아키텍처
- DB: `backtest_sessions` (날짜별 세션) → `backtest_picks` (슬롯별 추천) → `backtest_pnl` (P&L 입력)
- `backtest_picks.note_source` 컬럼 — 향후 종목노트 소스 연결 예약 필드
- API: `GET/POST /api/backtest/sessions`, `GET /api/backtest/sessions/<id>`, `POST /api/backtest/picks`, `PUT /api/backtest/picks/<id>/pnl`
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
