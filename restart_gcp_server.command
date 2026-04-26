#!/bin/bash
# GCP 서버 재시작 스크립트 (더블클릭 실행 가능)

cd "$(dirname "$0")"

echo "🔄 GCP 서버 재시작 중..."
echo ""

INSTANCE_NAME="instance-20251231-183226"
ZONE="us-central1-b"

# 1. 코드 업데이트
echo "[1/3] GitHub에서 최신 코드 가져오기..."
gcloud compute ssh smh8857@${INSTANCE_NAME} --zone ${ZONE} --command "
    cd newkiwoom &&
    git pull origin main
"

# 2. 웹 서비스 재시작
echo ""
echo "[2/3] 웹 서비스 재시작..."
gcloud compute ssh smh8857@${INSTANCE_NAME} --zone ${ZONE} --command "
    pkill -f 'python web_app.py' || true
    cd newkiwoom &&
    source .venv/bin/activate &&
    nohup python web_app.py > web_app.log 2>&1 &
    sleep 3
"

# 3. 봇 재시작
echo ""
echo "[3/3] 텔레그램 봇 재시작..."
gcloud compute ssh smh8857@${INSTANCE_NAME} --zone ${ZONE} --command "
    pkill -f 'python bot_v3.py' || true
    cd newkiwoom &&
    source .venv/bin/activate &&
    nohup python bot_v3.py > bot.log 2>&1 &
    sleep 3
"

echo ""
echo "✅ GCP 서버 재시작 완료!"
echo ""
echo "웹 UI: http://35.238.194.112:5000"
echo ""
echo "5초 후 창이 닫힙니다..."
sleep 5
