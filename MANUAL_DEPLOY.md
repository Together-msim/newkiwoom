# GCP 수동 배포 가이드

SSH 연결 문제로 자동 배포가 안 되는 경우, GCP 콘솔에서 직접 배포하세요.

## 방법 1: GCP 콘솔 SSH 사용 (권장)

1. **GCP Console 접속**
   - https://console.cloud.google.com/compute/instances
   - 프로젝트: propane-library-247011
   - Zone: us-central1-b

2. **SSH 버튼 클릭**
   - instance-20251231-183226 옆의 "SSH" 버튼 클릭
   - 브라우저에서 SSH 터미널 열림

3. **배포 명령 실행**
```bash
# 프로젝트 디렉토리로 이동
cd newkiwoom

# 최신 코드 가져오기
git pull origin main

# 서비스 재시작
sudo systemctl restart newkiwoom-web.service

# 상태 확인
sudo systemctl status newkiwoom-web.service
```

4. **로그 확인**
```bash
# 실시간 로그 보기
sudo journalctl -u newkiwoom-web.service -f

# 최근 로그 50줄
sudo journalctl -u newkiwoom-web.service -n 50
```

## 방법 2: 로컬에서 gcloud 재인증

SSH 키 문제일 경우:

```bash
# SSH 키 재생성
gcloud compute config-ssh

# 다시 배포 시도
./quick_deploy.sh
```

## 배포 확인

1. **웹 UI 접속**
   - http://35.238.194.112:5000

2. **새 파일 확인**
   - server_scheduler.py
   - SERVER_CONTROL.md
   - test_server_scheduler.py

3. **봇 명령어 테스트** (텔레그램)
   - /start - 새 명령어 목록 확인
   - /server - 서버 상태 확인
   - /on - 서버 시작 (수동 모드)
   - /off - 서버 중지

## 텔레그램 봇 재시작 (필요시)

봇이 실행 중이 아니면:

```bash
# SSH로 서버 접속 후
cd newkiwoom
source .venv/bin/activate
python bot_v3.py
```

또는 systemd 서비스로 실행:

```bash
# 서비스 파일 생성 (아직 없다면)
sudo nano /etc/systemd/system/newkiwoom-bot.service
```

서비스 파일 내용:
```ini
[Unit]
Description=Newkiwoom Telegram Bot
After=network.target

[Service]
Type=simple
User=YOUR_USERNAME
WorkingDirectory=/home/YOUR_USERNAME/newkiwoom
Environment="PATH=/home/YOUR_USERNAME/newkiwoom/.venv/bin"
ExecStart=/home/YOUR_USERNAME/newkiwoom/.venv/bin/python bot_v3.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 서비스 시작
sudo systemctl daemon-reload
sudo systemctl enable newkiwoom-bot.service
sudo systemctl start newkiwoom-bot.service
sudo systemctl status newkiwoom-bot.service
```

## 트러블슈팅

### Git Pull 실패
```bash
# 변경사항이 있는 경우
git stash
git pull origin main
git stash pop
```

### 서비스 재시작 실패
```bash
# 로그 확인
sudo journalctl -u newkiwoom-web.service -n 100

# 수동 실행 테스트
cd newkiwoom
source .venv/bin/activate
python web_app.py
```

### 포트 이미 사용 중
```bash
# 5000 포트 사용 프로세스 확인
sudo lsof -i :5000

# 프로세스 종료
sudo kill -9 PID
```

## 현재 배포된 변경사항

✅ server_scheduler.py - GCP 서버 자동 제어
✅ bot_v3.py - /server, /on, /off 명령어 추가
✅ SERVER_CONTROL.md - 사용 가이드
✅ CLAUDE.md - 문서 업데이트
✅ .env.example - GCP 설정 추가

## 테스트 체크리스트

- [ ] 웹 UI 접속 확인 (http://35.238.194.112:5000)
- [ ] 텔레그램 봇 응답 확인 (/start)
- [ ] /server 명령어 - 서버 상태 표시
- [ ] /on 명령어 - 수동 시작 (시간 걸림)
- [ ] /off 명령어 - 수동 중지 (시간 걸림)
- [ ] 자동 스케줄 확인 (08:00, 15:30에 자동 ON/OFF)
