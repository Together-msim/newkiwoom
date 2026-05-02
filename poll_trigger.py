#!/usr/bin/env python3
"""
실전 분석 트리거 폴러.

웹 UI '▶ 지금 분석' 버튼 클릭 → Oracle DB에 플래그 → 이 스크립트가 감지 → /siwhang 실행.

실행 방법:
    source .venv/bin/activate
    python poll_trigger.py

macOS 로그인 시 자동시작 (launchd):
    ~/Library/LaunchAgents/xyz.nomaddoklip.poll_trigger.plist 에 아래 내용 저장 후
    launchctl load ~/Library/LaunchAgents/xyz.nomaddoklip.poll_trigger.plist

    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
    <plist version="1.0"><dict>
        <key>Label</key><string>xyz.nomaddoklip.poll_trigger</string>
        <key>ProgramArguments</key><array>
            <string>/Users/msim/Documents/newkiwoom/.venv/bin/python</string>
            <string>/Users/msim/Documents/newkiwoom/poll_trigger.py</string>
        </array>
        <key>WorkingDirectory</key><string>/Users/msim/Documents/newkiwoom</string>
        <key>RunAtLoad</key><true/>
        <key>KeepAlive</key><true/>
        <key>StandardOutPath</key><string>/tmp/poll_trigger.log</string>
        <key>StandardErrorPath</key><string>/tmp/poll_trigger_err.log</string>
    </dict></plist>
"""

import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
import base64
import json
from pathlib import Path
from datetime import datetime

# .env 로드
_env_path = Path(__file__).parent / '.env'
if _env_path.exists():
    for line in _env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, _, v = line.partition('=')
            os.environ.setdefault(k.strip(), v.strip())

BASE_URL = os.environ.get('POLL_TARGET_URL', 'http://localhost:5002')
USERNAME = os.environ.get('WEB_USERNAME', '')
PASSWORD = os.environ.get('WEB_PASSWORD', '')
POLL_INTERVAL = int(os.environ.get('POLL_INTERVAL', '30'))

# 장 운영 시간 체크 (09:00~15:35 KST)
MARKET_START = (9, 0)
MARKET_END = (15, 35)
IGNORE_HOURS = os.environ.get('IGNORE_MARKET_HOURS', '0') == '1'


def _auth_header():
    creds = base64.b64encode(f"{USERNAME}:{PASSWORD}".encode()).decode()
    return f"Basic {creds}"


def _is_market_hours() -> bool:
    if IGNORE_HOURS:
        return True
    now = datetime.now()
    h, m = now.hour, now.minute
    start = MARKET_START[0] * 60 + MARKET_START[1]
    end = MARKET_END[0] * 60 + MARKET_END[1]
    current = h * 60 + m
    return start <= current <= end


def check_pending() -> bool:
    """pending 여부 확인 (자동 클리어 포함). True면 분석 트리거 실행."""
    url = f"{BASE_URL}/api/analysis/pending"
    try:
        req = urllib.request.Request(url)
        req.add_header("Authorization", _auth_header())
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get('pending', False)
    except urllib.error.URLError as e:
        print(f"[poll_trigger] 연결 실패: {e.reason}", flush=True)
        return False
    except Exception as e:
        print(f"[poll_trigger] 오류: {e}", flush=True)
        return False


def run_siwhang():
    """claude --print '/siwhang' 실행."""
    print(f"[poll_trigger] {datetime.now().strftime('%H:%M:%S')} → /siwhang 실행 시작", flush=True)
    try:
        result = subprocess.run(
            ['claude', '--print', '/siwhang'],
            cwd=str(Path(__file__).parent),
            timeout=600,  # 10분 타임아웃
        )
        print(f"[poll_trigger] 완료 (returncode={result.returncode})", flush=True)
    except FileNotFoundError:
        print("[poll_trigger] ERROR: 'claude' 명령어를 찾을 수 없음. PATH 확인 필요.", flush=True)
    except subprocess.TimeoutExpired:
        print("[poll_trigger] TIMEOUT: /siwhang 10분 초과", flush=True)
    except Exception as e:
        print(f"[poll_trigger] 실행 실패: {e}", flush=True)


def main():
    print(f"[poll_trigger] 시작 — {BASE_URL} 폴링 {POLL_INTERVAL}초 간격", flush=True)
    print(f"[poll_trigger] 장시간 체크: {'OFF (IGNORE_MARKET_HOURS=1)' if IGNORE_HOURS else 'ON (09:00~15:35)'}", flush=True)

    while True:
        try:
            if _is_market_hours() and check_pending():
                run_siwhang()
        except KeyboardInterrupt:
            print("\n[poll_trigger] 종료", flush=True)
            sys.exit(0)
        except Exception as e:
            print(f"[poll_trigger] 루프 오류: {e}", flush=True)

        time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
