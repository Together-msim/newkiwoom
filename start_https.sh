#!/bin/bash
# HTTPS로 웹 서버 시작 (443 포트)

cd ~/newkiwoom

# 가상환경 활성화
source .venv/bin/activate

# 기존 프로세스 종료
pkill -f "python.*web_app.py" 2>/dev/null
sleep 2

# 로그 백업
[ -f web_app.log ] && mv web_app.log web_app.log.$(date +%Y%m%d_%H%M%S)

# 443 포트로 시작 (sudo 필요)
sudo WEB_PORT=443 $(which python) web_app.py > web_app.log 2>&1 &

echo "✅ HTTPS 서버 시작 완료 (포트 443)"
echo "접속: https://nomaddoklip.xyz"

# 프로세스 확인
sleep 3
ps aux | grep "python.*web_app.py" | grep -v grep
