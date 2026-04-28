#!/bin/bash
# Flask 웹 서버 자동 재시작 스크립트 (Oracle 서버용)
# 매일 새벽 3시에 실행 (cron 등록 필요)

LOG_FILE=~/newkiwoom/restart.log
WEB_LOG=~/newkiwoom/web_app.log

echo "======================================" >> $LOG_FILE
echo "$(date '+%Y-%m-%d %H:%M:%S') - 서버 재시작 시작" >> $LOG_FILE

# 기존 Flask 프로세스 종료
echo "$(date '+%Y-%m-%d %H:%M:%S') - 기존 프로세스 종료 중..." >> $LOG_FILE
sudo pkill -9 -f "python.*web_app.py"
sleep 3

# 프로세스 확인
REMAINING=$(ps aux | grep -E "python.*web_app.py" | grep -v grep | wc -l)
if [ $REMAINING -gt 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 경고: 프로세스가 남아있음 ($REMAINING 개)" >> $LOG_FILE
fi

# 가상환경 경로
cd ~/newkiwoom
source .venv/bin/activate

# Flask 서버 재시작 (HTTPS 443 포트)
echo "$(date '+%Y-%m-%d %H:%M:%S') - Flask 서버 시작 중..." >> $LOG_FILE
sudo -E env PATH=$PATH WEB_PORT=443 nohup python web_app.py > $WEB_LOG 2>&1 &

sleep 5

# 시작 확인
NEW_PID=$(ps aux | grep -E "python.*web_app.py" | grep -v grep | awk '{print $2}' | head -1)
if [ -n "$NEW_PID" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✓ 서버 시작 성공 (PID: $NEW_PID)" >> $LOG_FILE

    # PriceMonitor 로그 확인 (10초 대기)
    sleep 10
    MONITOR_CHECK=$(tail -20 $WEB_LOG | grep "PriceMonitor" | wc -l)
    if [ $MONITOR_CHECK -gt 0 ]; then
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ✓ PriceMonitor 작동 확인" >> $LOG_FILE
    else
        echo "$(date '+%Y-%m-%d %H:%M:%S') - ⚠️ PriceMonitor 로그 없음" >> $LOG_FILE
    fi
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - ✗ 서버 시작 실패" >> $LOG_FILE
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') - 재시작 완료" >> $LOG_FILE
echo "" >> $LOG_FILE
