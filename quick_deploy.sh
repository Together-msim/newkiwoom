#!/bin/bash
# 빠른 배포 스크립트 (기존 프로젝트 업데이트)

set -e

INSTANCE_NAME="instance-20251231-183226"
ZONE="us-central1-b"

echo "=== Quick Deploy to GCP ==="
echo ""

# 1. Git Pull
echo "[1/3] Updating code from GitHub..."
gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} --command "
    cd newkiwoom
    git pull origin main
    echo '✓ Code updated'
"

# 2. Restart service
echo ""
echo "[2/3] Restarting web service..."
gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} --command "
    sudo systemctl restart newkiwoom-web.service
    echo '✓ Service restarted'
"

# 3. Check status
echo ""
echo "[3/3] Checking service status..."
gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE} --command "
    sudo systemctl status newkiwoom-web.service --no-pager -l | head -20
"

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Web UI: http://35.238.194.112:5000"
echo ""
echo "Logs: gcloud compute ssh ${INSTANCE_NAME} --zone ${ZONE}"
echo "      sudo journalctl -u newkiwoom-web.service -f"
echo ""
