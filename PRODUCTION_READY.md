# 🚀 실전 운영 가이드

**마지막 업데이트**: 2026-04-15
**작성자**: Claude Code

## ⚠️ 중요 안내

이 문서는 실제 매매에 시스템을 사용하기 전 **반드시** 확인해야 할 사항들을 정리한 것입니다.

---

## ✅ 필수 설정 체크리스트

### 1. 환경 변수 설정 (`.env`)

현재 설정 상태를 확인했습니다:

#### ✅ 완료된 설정
- [x] `TELEGRAM_BOT_TOKEN` - 텔레그램 봇 토큰 설정됨
- [x] `TELEGRAM_CHAT_ID` - 텔레그램 채팅 ID 설정됨
- [x] `KIWOOM_APPKEY` - 키움 앱키 설정됨
- [x] `KIWOOM_SECRETKEY` - 키움 시크릿키 설정됨
- [x] `KIWOOM_ACCOUNT_NO` - 계좌번호 설정됨
- [x] `KIWOOM_ACCOUNT_PW` - 계좌 비밀번호 설정됨
- [x] `MONITOR_INTERVAL=10` - 모니터링 주기 10초

#### ⚠️ 주의 필요한 설정

```bash
# 현재 상태
ORDER_SIMULATION_MODE=1  # 시뮬레이션 모드

# 실제 매매 시작 전 변경 필요
ORDER_SIMULATION_MODE=0  # 실제 주문 모드
```

**중요**: `ORDER_SIMULATION_MODE=1`일 때는 **실제 주문이 실행되지 않습니다**. 
알림만 받고 실제 주문은 수동으로 해야 합니다.

---

## 📋 실전 운영 전 체크리스트

### Step 1: 시스템 준비 확인

```bash
cd /Users/msim/Documents/newkiwoom

# 1. 가상환경 활성화
source .venv/bin/activate

# 2. 필수 파일 존재 확인
ls -la .env                          # 환경 변수
ls -la files/corp_master1.xlsx       # 종목 마스터
ls -la .data/mode1_watchers.json     # Mode1 데이터
ls -la .data/mode2_watchers.json     # Mode2 데이터
```

**확인 결과**: ✅ 모든 파일 존재

### Step 2: Kiwoom API 연결 테스트

```bash
# 웹 서버 실행
python web_app.py

# 브라우저에서 Test 페이지 접속
http://localhost:5000

# 테스트 항목:
1. "토큰 상태 확인" 버튼 클릭 → 토큰 유효성 확인
2. 종목 정보 조회 (예: 005930) → API 연결 확인
3. 보유 종목 조회 → 계좌 연동 확인
```

### Step 3: 텔레그램 알림 테스트

```bash
# 웹 서버 실행 (다른 터미널)
python web_app.py

# 텔레그램 테스트 실행
python test_telegram_notification.py

# 옵션 2 선택: 다중 시나리오 테스트
```

**기대 결과**: 텔레그램 앱에서 3개의 메시지 수신

### Step 4: 시뮬레이션 모드 테스트

**현재 설정**: `ORDER_SIMULATION_MODE=1` (안전 모드)

```bash
# 1. 웹 UI 실행
python web_app.py

# 2. Mode2 페이지에서 종목 등록
- 종목코드: 005930 (삼성전자)
- Budget: 100,000원 (소액 테스트)
- 매수타점: 현재가 근처
- 알림만 체크박스: 체크

# 3. 감시리스트에서 확인
- 모드: 🔔 알림 태그 확인
- Active: ON 상태 확인

# 4. 매수타점 도달 시 동작 확인
- 텔레그램 알림 수신 확인
- 실제 주문 실행되지 않음 (시뮬레이션 모드)
```

---

## 🎯 실전 매매 시작 방법

### 방법 1: 알림 전용 모드 (추천 - 초보자)

**특징**: 알림만 받고 수동으로 판단/주문

```bash
# .env 설정 (현재 상태 유지)
ORDER_SIMULATION_MODE=1  # 시뮬레이션 모드 유지

# Mode2 등록 시
- 🔔 알림만 체크박스: 체크
- 매수타점 도달 시 텔레그램 알림만 수신
- 수동으로 HTS/MTS에서 주문 실행
```

**장점**:
- ✅ 안전함 (실수로 주문 실행 안 됨)
- ✅ 최종 판단은 사람이 함
- ✅ 시스템 동작 학습 가능

**단점**:
- ⏱️ 수동 주문 필요 (타이밍 놓칠 수 있음)

---

### 방법 2: 자동매매 모드 (경험자)

**특징**: 조건 만족 시 자동으로 주문 실행

#### ⚠️ 실행 전 필수 확인

1. **소액으로 시작**
   ```
   Budget: 100,000원 ~ 500,000원
   종목: 안정적인 대형주 (삼성전자, SK하이닉스 등)
   ```

2. **.env 파일 수정**
   ```bash
   # 실제 주문 모드로 변경
   ORDER_SIMULATION_MODE=0
   ```

3. **재시작**
   ```bash
   # 웹 서버 재시작 (설정 적용)
   python web_app.py
   ```

4. **Mode2 등록**
   ```
   - 🔔 알림만 체크박스: 체크 해제 (자동매매 모드)
   - 매수타점: 신중하게 설정
   - 저항/지지 레벨: 명확하게 설정
   - Polling 주기: 10초 (기본값)
   ```

5. **모니터링**
   ```bash
   # 터미널에서 로그 확인
   python web_app.py
   
   # 텔레그램 알림 모니터링
   - 매수 시그널: [자동매매] 태그 확인
   - 체결 알림: 주문번호 확인
   ```

---

## 🛡️ 안전 장치

### 1. 시뮬레이션 모드
```bash
ORDER_SIMULATION_MODE=1
```
- 실제 주문 **실행되지 않음**
- 로그에만 기록
- 알림은 정상 전송

### 2. 알림 전용 모드
```
Mode2 등록 시 🔔 알림만 체크
```
- 시그널 발생 시 알림만
- 주문 실행 안 함
- 수동 판단 가능

### 3. Budget 제한
```
종목별 Budget 설정으로 최대 손실 제한
예: Budget 100,000원 → 최대 투입금 10만원
```

### 4. 익절/손절 자동 실행
```
Mode2 자동매매 모드:
- 1차/2차 저항: 자동 익절
- 1차/2차 지지: 자동 손절
```

---

## 📊 권장 시작 설정

### 초보자 (첫 1주일)

```yaml
모드: 알림 전용
ORDER_SIMULATION_MODE: 1
종목 수: 1~2개
종목: 대형주 (삼성전자, SK하이닉스)
Budget: 100,000원
Polling: 10초
```

### 경험자 (1주일 후)

```yaml
모드: 자동매매 (소액)
ORDER_SIMULATION_MODE: 0
종목 수: 2~3개
종목: 대형주 + 관심 종목
Budget: 500,000원
Polling: 10초
```

### 숙련자 (1개월 후)

```yaml
모드: 자동매매 (분산)
ORDER_SIMULATION_MODE: 0
종목 수: 5~10개
종목: 포트폴리오 분산
Budget: 종목별 차등
Polling: 종목별 최적화
```

---

## 🔍 실시간 모니터링 방법

### 1. 웹 UI 모니터링
```
http://localhost:5000

페이지:
- 📊 감시리스트: 전체 종목 상태
- 📈 Mode1: 분봉 조건 모니터링
- 📉 Mode2: 저항/지지 레벨 모니터링
- 💼 보유 종목: 실시간 수익률
```

### 2. 텔레그램 알림
```
알림 종류:
- 🔔 매수 시그널 (타점 도달)
- ✅ 매수 체결
- 💰 익절 시그널
- ⚠️ 손절 시그널
- ✅ 매도 체결
```

### 3. 터미널 로그
```bash
# 실시간 로그 확인
python web_app.py

로그 레벨:
- INFO: 주요 이벤트
- DEBUG: 상세 디버깅 (KIWOOM_DEBUG=1)
```

---

## ⚠️ 알려진 제한사항

### 1. 시간 제한
- **장 운영 시간**: 09:00 ~ 15:30
- 장외 시간에는 API 호출 실패 가능
- `IGNORE_MARKET_HOURS=1` 설정 시 24시간 작동 (테스트용)

### 2. API 호출 제한
- Kiwoom API 호출 제한: 초당 20회
- Polling 주기 최소 5초 권장
- 종목 수 증가 시 Polling 주기 조정 필요

### 3. 주문 체결
- **시장가 주문**: 즉시 체결 (가격 변동 가능)
- **지정가 주문**: 체결 지연 가능
- 체결 확인은 텔레그램 알림으로 확인

### 4. 보유수량 동기화
- 수동 매도 후 "보유수량 동기화" 버튼 클릭 필요
- 또는 감시리스트 페이지 재진입 (자동 동기화)

---

## 🆘 문제 해결

### Q1. 텔레그램 알림이 안 와요
```bash
# .env 확인
cat .env | grep TELEGRAM

# 테스트 실행
python test_telegram_notification.py

# 실패 시:
1. 봇 토큰 확인
2. 채팅 ID 확인
3. 봇과 대화 시작 (/start)
```

### Q2. 주문이 실행되지 않아요
```bash
# .env 확인
cat .env | grep ORDER_SIMULATION_MODE

# ORDER_SIMULATION_MODE=1 이면 시뮬레이션
# 실제 주문: ORDER_SIMULATION_MODE=0

# 웹 서버 재시작 필수!
```

### Q3. Kiwoom API 오류
```bash
# Test 페이지에서 확인
1. 토큰 상태 확인
2. 종목 정보 조회
3. 보유 종목 조회

# 실패 시:
- KIWOOM_APPKEY 재확인
- KIWOOM_SECRETKEY 재확인
- 계좌 정보 재확인
```

### Q4. 보유종목이 감시리스트에 반영 안 돼요
```bash
# 감시리스트 페이지에서
1. "🔄 보유수량 동기화" 버튼 클릭
2. 또는 페이지 새로고침 (자동 동기화)
```

---

## 📞 지원 및 피드백

### 버그 리포트
- GitHub Issues: https://github.com/anthropics/claude-code/issues
- 로그 파일 첨부 권장

### 기능 제안
- 실전 사용 경험 공유 환영
- 개선 아이디어 제안

---

## 🎓 추가 학습 자료

### 시스템 이해
```bash
# README.md
cat README.md

# CLAUDE.md (개발자용)
cat CLAUDE.md

# TODO.md (로드맵)
cat TODO.md
```

### 코드 이해
```
주요 파일:
- bot_v3.py: 텔레그램 봇
- web_app.py: 웹 서버
- price_monitor.py: 모니터링 엔진
- mode1_manager.py: Mode1 전략
- mode2_manager.py: Mode2 전략
- kiwoom_client.py: API 클라이언트
```

---

## ✨ 최종 확인

실전 매매 시작 전 마지막 체크:

- [ ] `.env` 파일 설정 확인
- [ ] `ORDER_SIMULATION_MODE` 설정 확인 (0=실제, 1=시뮬레이션)
- [ ] Kiwoom API 연결 테스트 완료
- [ ] 텔레그램 알림 테스트 완료
- [ ] 소액으로 시작 (10만원 ~ 50만원)
- [ ] 대형주로 시작 (삼성전자, SK하이닉스 등)
- [ ] 익절/손절 레벨 명확히 설정
- [ ] 웹 UI와 텔레그램 모니터링 준비
- [ ] HTS/MTS 병행 사용 준비 (수동 개입 가능)

**축하합니다! 실전 매매를 시작할 준비가 되었습니다.** 🎉

**Remember**: 
- 시작은 소액으로
- 알림 전용 모드로 시스템 학습
- 자동매매는 충분히 익숙해진 후
- 항상 손절선 설정
- 분산 투자 원칙 준수

**행운을 빕니다!** 🍀
