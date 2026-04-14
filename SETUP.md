# 설치 및 설정 가이드

## 1️⃣ 텔레그램 봇 생성

### BotFather로 봇 생성하기

1. 텔레그램에서 [@BotFather](https://t.me/BotFather) 검색
2. `/newbot` 명령어 입력
3. 봇 이름 입력 (예: "단타 트레이딩 봇")
4. 봇 사용자명 입력 (예: "daanta_trading_bot")
5. 생성된 **Bot Token**을 복사해두기

### Chat ID 확인하기

1. 생성한 봇과 대화 시작 (아무 메시지나 전송)
2. 브라우저에서 다음 URL 접속:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
3. `"chat":{"id": 숫자}` 부분의 숫자가 **Chat ID**

## 2️⃣ 프로젝트 설정

### 환경 변수 설정

```bash
# .env.example 복사
cp .env.example .env

# .env 파일 편집
nano .env
```

`.env` 파일 내용:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz  # BotFather에서 받은 토큰
```

### 가상환경 생성 및 의존성 설치

```bash
# 가상환경 생성
python -m venv .venv

# 가상환경 활성화 (macOS/Linux)
source .venv/bin/activate

# 가상환경 활성화 (Windows)
.venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```

## 3️⃣ 테스트 실행

### 기본 기능 테스트

```bash
python test_bot.py
```

성공적으로 실행되면 다음과 같은 출력을 볼 수 있습니다:
```
==================================================
Tactic Manager 테스트
==================================================

1. Tactic1 종목 추가 테스트
추가된 종목: ['005930', '000660']
...
✅ 테스트 완료!
```

### 봇 실행

```bash
python bot.py
```

성공적으로 실행되면:
```
2026-04-10 16:45:00 - __main__ - INFO - 단타 전략 봇을 시작합니다...
2026-04-10 16:45:01 - __main__ - INFO - 봇이 실행되었습니다. Ctrl+C로 종료할 수 있습니다.
```

## 4️⃣ 텔레그램에서 봇 사용하기

1. 생성한 봇과 대화 시작
2. `/start` 명령어로 도움말 확인
3. `/list` 명령어로 감시 리스트 확인

### 예제 사용법

```
# 도움말
/start

# Tactic1 전략 등록
/tactic1 005930

# 옵션과 함께 등록
/tactic1 000660 익절=8% 손절=-5%

# 감시 리스트 확인
/list

# 자연어 명령
감시 중인 종목 알려줘
종목코드(005930) 삭제
```

## 🐛 문제 해결

### Bot Token 오류
```
ValueError: TELEGRAM_BOT_TOKEN 환경 변수가 설정되지 않았습니다.
```
→ `.env` 파일에 `TELEGRAM_BOT_TOKEN` 값이 올바르게 설정되어 있는지 확인

### 모듈 import 오류
```
ModuleNotFoundError: No module named 'telegram'
```
→ 가상환경이 활성화되어 있는지 확인하고 `pip install -r requirements.txt` 재실행

### 봇이 응답하지 않음
1. 봇이 실행 중인지 확인 (`python bot.py`)
2. 봇 토큰이 올바른지 확인
3. 봇과 대화를 시작했는지 확인 (Start 버튼 클릭)

## 📚 다음 단계

- [ ] 키움 API 연동
- [ ] 실시간 가격 감시 구현
- [ ] 자동 매수/매도 로직 구현
- [ ] 체결 알림 추가

## 💡 팁

- 개발 중에는 테스트 봇을 별도로 만들어 사용하는 것을 권장합니다
- `.env` 파일은 절대 Git에 커밋하지 마세요 (`.gitignore`에 이미 추가됨)
- 봇 로그는 `bot.log` 파일에서 확인할 수 있습니다
