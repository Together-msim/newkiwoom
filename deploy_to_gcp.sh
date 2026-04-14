#!/bin/bash

# GCP Compute Engine 자동 배포 스크립트
# 사용법: ./deploy_to_gcp.sh

set -e  # 에러 발생 시 중단

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 설정
INSTANCE_NAME="instance-20251231-183226"
ZONE="us-central1-b"
PROJECT_DIR="newkiwoom"

echo -e "${GREEN}=== GCP Compute Engine 배포 시작 ===${NC}"
echo ""

# Step 1: .env 파일 확인
echo -e "${YELLOW}[1/5] .env 파일 확인...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ .env 파일이 없습니다!${NC}"
    echo "먼저 .env 파일을 생성하고 실행하세요."
    exit 1
fi
echo -e "${GREEN}✓ .env 파일 존재${NC}"

# Step 2: .env 파일 업로드
echo ""
echo -e "${YELLOW}[2/5] .env 파일 서버로 업로드...${NC}"
gcloud compute scp .env ${INSTANCE_NAME}:~/ --zone ${ZONE}
echo -e "${GREEN}✓ .env 업로드 완료${NC}"

# Step 3: 서버에서 프로젝트 클론 및 설정
echo ""
echo -e "${YELLOW}[3/5] 서버에 프로젝트 설정...${NC}"
gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} --command "
    set -e

    # Python 및 필수 도구 설치
    echo '>>> Python 및 필수 패키지 설치...'
    sudo apt update -qq
    sudo apt install -y python3 python3-pip python3-venv git curl > /dev/null 2>&1

    # 기존 프로젝트 디렉토리 삭제 (있다면)
    if [ -d ${PROJECT_DIR} ]; then
        echo '>>> 기존 프로젝트 백업...'
        mv ${PROJECT_DIR} ${PROJECT_DIR}.backup.\$(date +%Y%m%d_%H%M%S)
    fi

    # 프로젝트 클론
    echo '>>> GitHub에서 프로젝트 클론...'
    git clone https://github.com/Together-msim/newkiwoom.git

    # .env 파일 이동
    echo '>>> .env 파일 복사...'
    mv ~/.env ${PROJECT_DIR}/.env

    # 가상환경 생성 및 패키지 설치
    echo '>>> 가상환경 생성 및 패키지 설치...'
    cd ${PROJECT_DIR}
    python3 -m venv .venv
    source .venv/bin/activate
    pip install --upgrade pip > /dev/null 2>&1
    pip install -r requirements.txt > /dev/null 2>&1

    echo '>>> 설정 완료'
"
echo -e "${GREEN}✓ 서버 설정 완료${NC}"

# Step 4: systemd 서비스 설정
echo ""
echo -e "${YELLOW}[4/5] systemd 서비스 설정...${NC}"

# 현재 사용자명 가져오기
REMOTE_USER=\$(gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} --command "whoami" 2>/dev/null)

# 서비스 파일 생성 및 업로드
cat > /tmp/newkiwoom-web.service <<EOF
[Unit]
Description=Newkiwoom Web Server
After=network.target

[Service]
Type=simple
User=${REMOTE_USER}
WorkingDirectory=/home/${REMOTE_USER}/${PROJECT_DIR}
Environment="PATH=/home/${REMOTE_USER}/${PROJECT_DIR}/.venv/bin"
ExecStart=/home/${REMOTE_USER}/${PROJECT_DIR}/.venv/bin/python web_app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

gcloud compute scp /tmp/newkiwoom-web.service ${INSTANCE_NAME}:/tmp/ --zone ${ZONE}

gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} --command "
    sudo mv /tmp/newkiwoom-web.service /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable newkiwoom-web.service
    sudo systemctl start newkiwoom-web.service
"
echo -e "${GREEN}✓ systemd 서비스 설정 완료${NC}"

# Step 5: 방화벽 설정
echo ""
echo -e "${YELLOW}[5/5] 방화벽 설정 확인...${NC}"

# 방화벽 규칙 존재 확인
if gcloud compute firewall-rules describe allow-newkiwoom-web &>/dev/null; then
    echo -e "${GREEN}✓ 방화벽 규칙 이미 존재${NC}"
else
    echo ">>> 방화벽 규칙 생성 중..."
    gcloud compute firewall-rules create allow-newkiwoom-web \
        --allow tcp:5000 \
        --source-ranges 0.0.0.0/0 \
        --description "Allow web UI access for newkiwoom" \
        --quiet
    echo -e "${GREEN}✓ 방화벽 규칙 생성 완료${NC}"
fi

# 외부 IP 확인
echo ""
echo -e "${GREEN}=== 배포 완료! ===${NC}"
echo ""

EXTERNAL_IP=\$(gcloud compute instances describe ${INSTANCE_NAME} \
    --zone ${ZONE} \
    --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo -e "${GREEN}웹 UI 접속 주소: ${YELLOW}http://${EXTERNAL_IP}:5000${NC}"
echo ""

# 서비스 상태 확인
echo -e "${YELLOW}서비스 상태 확인:${NC}"
gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} --command "
    sudo systemctl status newkiwoom-web.service --no-pager -l
"

echo ""
echo -e "${GREEN}배포가 완료되었습니다! 🎉${NC}"
echo ""
echo "다음 단계:"
echo "1. 웹 브라우저에서 http://${EXTERNAL_IP}:5000 접속"
echo "2. Mode2 페이지에서 종목 등록"
echo "3. 텔레그램 알림 확인"
echo ""
echo "로그 확인: gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE}"
echo "           sudo journalctl -u newkiwoom-web.service -f"
echo ""
