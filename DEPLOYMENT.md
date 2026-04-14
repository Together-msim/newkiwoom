# 🚀 GCP Compute Engine 배포 가이드

**대상 서버**: `instance-20251231-183226` (us-central1-b)

---

## 📋 배포 전 체크리스트

### 로컬에서 준비
- [x] GitHub에 코드 푸시 완료
- [ ] `.env` 파일 내용 백업 (로컬에서 복사)
- [ ] 서버 SSH 접속 테스트

### 서버 요구사항
- Python 3.8 이상
- 최소 1GB RAM (권장: 2GB)
- 최소 10GB 디스크
- 인터넷 연결 (Kiwoom API, Telegram API)

---

## 🔧 Step 1: 서버 접속 및 환경 확인

```bash
# 로컬에서 서버 접속
gcloud compute ssh instance-20251231-183226 --zone us-central1-b

# 서버에서 실행
# OS 및 Python 버전 확인
cat /etc/os-release
python3 --version

# 디스크 공간 확인
df -h

# 메모리 확인
free -h
```

**예상 결과**:
- Ubuntu 20.04/22.04 또는 Debian
- Python 3.8+
- 10GB+ 여유 공간

---

## 📦 Step 2: 필수 패키지 설치

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# Python 및 필수 도구 설치
sudo apt install -y python3 python3-pip python3-venv git curl

# Git 설정 (선택)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

---

## 🔽 Step 3: 프로젝트 클론

```bash
# 홈 디렉토리로 이동
cd ~

# GitHub에서 클론
git clone https://github.com/Together-msim/newkiwoom.git

# 프로젝트 디렉토리 이동
cd newkiwoom

# 파일 확인
ls -la
```

---

## 🔐 Step 4: 환경 변수 설정

### 방법 1: 로컬 .env 파일 업로드 (추천)

**로컬 컴퓨터에서 실행**:
```bash
# .env 파일 업로드
gcloud compute scp /Users/msim/Documents/newkiwoom/.env \
  instance-20251231-183226:~/newkiwoom/.env \
  --zone us-central1-b
```

### 방법 2: 서버에서 직접 생성

**서버에서 실행**:
```bash
cd ~/newkiwoom

# 템플릿 복사
cp .env.example .env

# 편집기로 열기
nano .env

# 또는
vim .env
```

**필수 값 입력**:
```bash
TELEGRAM_BOT_TOKEN=your_actual_token
TELEGRAM_CHAT_ID=your_actual_chat_id
KIWOOM_APPKEY=your_actual_appkey
KIWOOM_SECRETKEY=your_actual_secretkey
KIWOOM_ACCOUNT_NO=your_account_number
KIWOOM_ACCOUNT_PW=your_account_password

# 중요: 실제 주문 모드 설정
ORDER_SIMULATION_MODE=1  # 처음에는 1로 시작 (안전)

# 웹 서버 설정
WEB_PORT=5000
WEB_HOST=0.0.0.0  # 외부 접속 허용
```

---

## 🐍 Step 5: Python 환경 설정

```bash
cd ~/newkiwoom

# 가상환경 생성
python3 -m venv .venv

# 가상환경 활성화
source .venv/bin/activate

# 패키지 설치
pip install --upgrade pip
pip install -r requirements.txt

# 설치 확인
pip list
```

---

## 🧪 Step 6: 동작 테스트

```bash
# 시스템 체크
python check_system.py

# 텔레그램 테스트
python test_telegram_notification.py
# 옵션 1 선택 → 텔레그램 앱에서 메시지 확인

# 웹 서버 테스트 (잠깐만 실행)
python web_app.py
# Ctrl+C로 종료
```

---

## 🔥 Step 7: 방화벽 설정 (웹 UI 접속용)

### GCP 방화벽 규칙 생성

**로컬 컴퓨터에서 실행**:
```bash
# 웹 UI 포트 (5000) 오픈
gcloud compute firewall-rules create allow-newkiwoom-web \
  --allow tcp:5000 \
  --source-ranges 0.0.0.0/0 \
  --description "Allow web UI access for newkiwoom"

# 규칙 확인
gcloud compute firewall-rules list | grep newkiwoom
```

**또는 GCP 콘솔에서**:
1. VPC Network → Firewall
2. Create Firewall Rule
3. Name: `allow-newkiwoom-web`
4. Targets: All instances in network
5. Source IP ranges: `0.0.0.0/0`
6. Protocols and ports: `tcp:5000`
7. Create

---

## 🔄 Step 8: systemd 서비스 설정 (자동 시작)

### 서비스 파일 생성

```bash
# 서비스 파일 생성
sudo nano /etc/systemd/system/newkiwoom-web.service
```

**내용**:
```ini
[Unit]
Description=Newkiwoom Web Server
After=network.target

[Service]
Type=simple
User=msim
WorkingDirectory=/home/msim/newkiwoom
Environment="PATH=/home/msim/newkiwoom/.venv/bin"
ExecStart=/home/msim/newkiwoom/.venv/bin/python web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**주의**: `User=msim` 부분을 실제 사용자명으로 변경하세요!

### 텔레그램 봇 서비스 생성 (선택사항)

```bash
sudo nano /etc/systemd/system/newkiwoom-bot.service
```

**내용**:
```ini
[Unit]
Description=Newkiwoom Telegram Bot
After=network.target

[Service]
Type=simple
User=msim
WorkingDirectory=/home/msim/newkiwoom
Environment="PATH=/home/msim/newkiwoom/.venv/bin"
ExecStart=/home/msim/newkiwoom/.venv/bin/python bot_v3.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 서비스 활성화 및 시작

```bash
# 서비스 파일 리로드
sudo systemctl daemon-reload

# 서비스 활성화 (부팅 시 자동 시작)
sudo systemctl enable newkiwoom-web.service
sudo systemctl enable newkiwoom-bot.service  # 봇 사용 시

# 서비스 시작
sudo systemctl start newkiwoom-web.service
sudo systemctl start newkiwoom-bot.service  # 봇 사용 시

# 상태 확인
sudo systemctl status newkiwoom-web.service
sudo systemctl status newkiwoom-bot.service
```

### 서비스 관리 명령어

```bash
# 로그 확인
sudo journalctl -u newkiwoom-web.service -f

# 재시작
sudo systemctl restart newkiwoom-web.service

# 중지
sudo systemctl stop newkiwoom-web.service

# 비활성화 (자동 시작 해제)
sudo systemctl disable newkiwoom-web.service
```

---

## 🌐 Step 9: 웹 UI 접속

### 외부 IP 확인

**로컬에서 실행**:
```bash
gcloud compute instances describe instance-20251231-183226 \
  --zone us-central1-b \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)'
```

**또는 서버에서 실행**:
```bash
curl ifconfig.me
```

### 브라우저에서 접속

```
http://[외부IP]:5000
```

예: `http://34.123.45.67:5000`

**확인 사항**:
- [ ] 감시리스트 페이지 로드
- [ ] Mode2 페이지에서 종목 등록
- [ ] 텔레그램 알림 수신

---

## 🔒 Step 10: 보안 강화 (선택사항)

### 1. SSH 키 기반 인증만 허용

```bash
# SSH 설정 편집
sudo nano /etc/ssh/sshd_config

# 변경 사항
PasswordAuthentication no
PermitRootLogin no

# SSH 재시작
sudo systemctl restart sshd
```

### 2. 방화벽 IP 제한

특정 IP만 웹 UI 접속 허용:
```bash
gcloud compute firewall-rules update allow-newkiwoom-web \
  --source-ranges [내IP]/32
```

### 3. HTTPS 설정 (권장)

Nginx + Let's Encrypt 사용:
```bash
# Nginx 설치
sudo apt install -y nginx certbot python3-certbot-nginx

# 도메인이 있다면 SSL 인증서 발급
sudo certbot --nginx -d your-domain.com
```

### 4. 환경 변수 파일 권한 설정

```bash
cd ~/newkiwoom
chmod 600 .env
chmod 700 .data/
```

---

## 📊 Step 11: 모니터링 설정

### 1. 로그 확인 스크립트

```bash
# 로그 확인 스크립트 생성
nano ~/check_logs.sh
```

**내용**:
```bash
#!/bin/bash
echo "=== Web Service Status ==="
sudo systemctl status newkiwoom-web.service --no-pager

echo ""
echo "=== Recent Logs (last 20 lines) ==="
sudo journalctl -u newkiwoom-web.service -n 20 --no-pager

echo ""
echo "=== Disk Usage ==="
df -h /home/msim/newkiwoom

echo ""
echo "=== Memory Usage ==="
free -h
```

```bash
chmod +x ~/check_logs.sh
./check_logs.sh
```

### 2. Cron 작업 설정 (일일 재시작)

```bash
crontab -e
```

**추가**:
```bash
# 매일 새벽 4시 서비스 재시작
0 4 * * * sudo systemctl restart newkiwoom-web.service

# 매주 일요일 새벽 3시 시스템 업데이트
0 3 * * 0 sudo apt update && sudo apt upgrade -y
```

---

## 🔄 Step 12: 코드 업데이트 방법

### GitHub에서 최신 코드 가져오기

```bash
cd ~/newkiwoom

# 서비스 중지
sudo systemctl stop newkiwoom-web.service
sudo systemctl stop newkiwoom-bot.service

# 최신 코드 pull
git pull origin main

# 가상환경 활성화
source .venv/bin/activate

# 패키지 업데이트 (필요시)
pip install -r requirements.txt --upgrade

# 서비스 재시작
sudo systemctl start newkiwoom-web.service
sudo systemctl start newkiwoom-bot.service

# 상태 확인
sudo systemctl status newkiwoom-web.service
```

### 자동 업데이트 스크립트

```bash
nano ~/update_newkiwoom.sh
```

**내용**:
```bash
#!/bin/bash
set -e

echo "=== Newkiwoom 업데이트 시작 ==="

cd ~/newkiwoom

# 서비스 중지
echo "서비스 중지..."
sudo systemctl stop newkiwoom-web.service

# Git pull
echo "최신 코드 가져오기..."
git pull origin main

# 가상환경 활성화 및 패키지 업데이트
echo "패키지 업데이트..."
source .venv/bin/activate
pip install -r requirements.txt --upgrade

# 서비스 시작
echo "서비스 시작..."
sudo systemctl start newkiwoom-web.service

echo "=== 업데이트 완료 ==="
sudo systemctl status newkiwoom-web.service --no-pager
```

```bash
chmod +x ~/update_newkiwoom.sh
./update_newkiwoom.sh
```

---

## 🆘 트러블슈팅

### 문제 1: 웹 UI 접속 안 됨

```bash
# 서비스 상태 확인
sudo systemctl status newkiwoom-web.service

# 로그 확인
sudo journalctl -u newkiwoom-web.service -n 50

# 포트 확인
sudo netstat -tlnp | grep 5000

# 방화벽 확인
gcloud compute firewall-rules list | grep 5000
```

### 문제 2: 텔레그램 알림 안 옴

```bash
# 서버에서 테스트
cd ~/newkiwoom
source .venv/bin/activate
python test_telegram_notification.py

# .env 파일 확인
cat .env | grep TELEGRAM
```

### 문제 3: 메모리 부족

```bash
# 메모리 사용량 확인
free -h

# 스왑 파일 생성 (2GB)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 영구 설정
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 문제 4: Kiwoom API 연결 실패

```bash
# 서버 시간 확인 (한국 시간과 동기화)
timedatectl

# 타임존 변경 (한국 시간)
sudo timedatectl set-timezone Asia/Seoul

# 확인
date
```

---

## 📈 성능 최적화

### 1. 프로세스 수 제한

```bash
# .env 파일 수정
MONITOR_INTERVAL=15  # 10초 → 15초로 증가
```

### 2. 로그 로테이션

```bash
sudo nano /etc/logrotate.d/newkiwoom
```

**내용**:
```
/home/msim/newkiwoom/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0640 msim msim
}
```

---

## 🎯 배포 완료 체크리스트

- [ ] 서버 접속 확인
- [ ] Python 및 필수 패키지 설치
- [ ] GitHub에서 프로젝트 클론
- [ ] .env 파일 설정
- [ ] 가상환경 생성 및 패키지 설치
- [ ] 시스템 체크 및 텔레그램 테스트
- [ ] 방화벽 규칙 생성
- [ ] systemd 서비스 설정 및 시작
- [ ] 웹 UI 접속 확인
- [ ] 감시 종목 등록 테스트
- [ ] 텔레그램 알림 수신 확인
- [ ] 자동 재시작 설정
- [ ] 모니터링 스크립트 설정

---

## 📞 유지보수

### 일일 체크
```bash
# 서비스 상태
sudo systemctl status newkiwoom-web.service

# 최근 로그
sudo journalctl -u newkiwoom-web.service -n 20

# 리소스 사용량
htop  # 또는 top
```

### 주간 체크
```bash
# 디스크 공간
df -h

# .data 디렉토리 정리
cd ~/newkiwoom/.data
ls -lh

# 시스템 업데이트
sudo apt update && sudo apt upgrade -y
```

---

## 🎉 배포 완료!

서버가 24시간 운영됩니다:
- ✅ 웹 UI 항상 접속 가능
- ✅ 가격 모니터링 지속
- ✅ 텔레그램 알림 실시간
- ✅ 자동 재시작 설정
- ✅ 시스템 재부팅 시 자동 시작

**웹 UI 접속**: `http://[서버IP]:5000`

**다음 단계**: 
1. 알림 전용 모드로 1주일 테스트
2. 자동매매 모드 전환 (.env에서 ORDER_SIMULATION_MODE=0)
3. 종목 추가 및 포트폴리오 확장

행운을 빕니다! 🍀
