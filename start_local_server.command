#!/bin/bash
# 로컬 서버 시작 스크립트 (더블클릭 실행 가능)

cd "$(dirname "$0")"

echo "🚀 로컬 서버 시작 중..."
echo ""

# 포트 정리
lsof -ti:5002 | xargs kill -9 2>/dev/null

# 가상환경 활성화 및 서버 시작
source .venv/bin/activate
WEB_PORT=5002 python web_app.py &

# PID 저장
echo $! > .local_server.pid

sleep 3

echo ""
echo "✅ 로컬 서버 시작 완료!"
echo ""
echo "접속: http://localhost:5002"
echo "Username: smh8857"
echo ""
echo "종료: stop_local_server.command 실행"
echo ""
echo "이 창을 닫지 마세요..."
echo ""

# 로그 출력
tail -f web_app.log 2>/dev/null || sleep infinity
