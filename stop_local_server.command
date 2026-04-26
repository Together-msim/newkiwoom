#!/bin/bash
# 로컬 서버 중지 스크립트

cd "$(dirname "$0")"

echo "🛑 로컬 서버 중지 중..."

# PID 파일에서 프로세스 종료
if [ -f .local_server.pid ]; then
    kill $(cat .local_server.pid) 2>/dev/null
    rm .local_server.pid
fi

# 포트 5002 프로세스 모두 종료
lsof -ti:5002 | xargs kill -9 2>/dev/null

echo "✅ 로컬 서버 중지 완료"
echo ""
echo "3초 후 창이 닫힙니다..."
sleep 3
