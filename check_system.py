"""
시스템 준비 상태 체크 스크립트
실전 운영 전 필수 확인 사항 점검
"""
import os
import json
from dotenv import load_dotenv

load_dotenv()

def check_env_vars():
    """환경 변수 체크"""
    print("\n" + "=" * 60)
    print("📋 환경 변수 체크")
    print("=" * 60)

    required_vars = {
        'TELEGRAM_BOT_TOKEN': '텔레그램 봇 토큰',
        'TELEGRAM_CHAT_ID': '텔레그램 채팅 ID',
        'KIWOOM_APPKEY': 'Kiwoom 앱키',
        'KIWOOM_SECRETKEY': 'Kiwoom 시크릿키',
        'KIWOOM_ACCOUNT_NO': '계좌번호',
        'KIWOOM_ACCOUNT_PW': '계좌 비밀번호',
    }

    all_ok = True
    for var, desc in required_vars.items():
        value = os.getenv(var)
        if value and value != 'your_appkey' and value != 'your_secretkey':
            # 민감한 정보는 일부만 표시
            if 'TOKEN' in var or 'KEY' in var or 'PW' in var:
                display = value[:10] + '...' if len(value) > 10 else '***'
            else:
                display = value
            print(f"  ✅ {desc}: {display}")
        else:
            print(f"  ❌ {desc}: 설정 필요!")
            all_ok = False

    return all_ok


def check_operation_mode():
    """운영 모드 체크"""
    print("\n" + "=" * 60)
    print("⚙️  운영 모드 체크")
    print("=" * 60)

    sim_mode = os.getenv('ORDER_SIMULATION_MODE', '1')

    if sim_mode == '1':
        print("  ⚠️  시뮬레이션 모드: ON")
        print("     → 실제 주문 실행되지 않음 (안전)")
        print("     → 알림만 전송됨")
        print("     → 테스트 및 학습용")
        print("\n  💡 실전 매매 시작하려면:")
        print("     1. .env 파일에서 ORDER_SIMULATION_MODE=0 으로 변경")
        print("     2. 웹 서버 재시작")
        return 'simulation'
    else:
        print("  🚀 실제 주문 모드: ON")
        print("     → 실제 주문이 실행됩니다!")
        print("     → 조건 만족 시 자동 매매")
        print("     → 신중하게 사용하세요")
        return 'real'


def check_files():
    """필수 파일 체크"""
    print("\n" + "=" * 60)
    print("📁 필수 파일 체크")
    print("=" * 60)

    required_files = {
        '.env': '환경 변수 파일',
        'files/corp_master1.xlsx': '종목 마스터 데이터',
        '.data/mode1_watchers.json': 'Mode1 감시리스트',
        '.data/mode2_watchers.json': 'Mode2 감시리스트',
    }

    all_ok = True
    for file_path, desc in required_files.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✅ {desc}: {size:,} bytes")
        else:
            print(f"  ❌ {desc}: 파일 없음!")
            all_ok = False

    return all_ok


def check_watchers():
    """등록된 감시 종목 체크"""
    print("\n" + "=" * 60)
    print("📊 등록된 감시 종목")
    print("=" * 60)

    # Mode1
    try:
        with open('.data/mode1_watchers.json', 'r') as f:
            mode1_data = json.load(f)
            mode1_count = len(mode1_data)
            print(f"\n  📈 Mode1 (분봉 기반): {mode1_count}개")
            if mode1_count > 0:
                for code, watcher in list(mode1_data.items())[:3]:
                    status = '🟢' if watcher.get('active') else '🔴'
                    print(f"     {status} {code}: {watcher.get('name', '?')}")
                if mode1_count > 3:
                    print(f"     ... 외 {mode1_count - 3}개")
    except Exception as e:
        print(f"  ❌ Mode1 데이터 읽기 실패: {e}")

    # Mode2
    try:
        with open('.data/mode2_watchers.json', 'r') as f:
            mode2_data = json.load(f)
            mode2_count = len(mode2_data)
            print(f"\n  📉 Mode2 (레벨 기반): {mode2_count}개")
            if mode2_count > 0:
                for code, watcher in list(mode2_data.items())[:3]:
                    status = '🟢' if watcher.get('active') else '🔴'
                    notify_mode = '🔔' if watcher.get('notify_only') else '🤖'
                    print(f"     {status} {notify_mode} {code}: {watcher.get('name', '?')}")
                if mode2_count > 3:
                    print(f"     ... 외 {mode2_count - 3}개")
    except Exception as e:
        print(f"  ❌ Mode2 데이터 읽기 실패: {e}")


def check_monitoring_settings():
    """모니터링 설정 체크"""
    print("\n" + "=" * 60)
    print("⏱️  모니터링 설정")
    print("=" * 60)

    interval = os.getenv('MONITOR_INTERVAL', '10')
    web_port = os.getenv('WEB_PORT', '5000')

    print(f"  ⏰ 가격 체크 주기: {interval}초")
    print(f"  🌐 웹 서버 포트: {web_port}")
    print(f"  📱 텔레그램 알림: 활성화")


def print_next_steps(mode, all_checks_ok):
    """다음 단계 안내"""
    print("\n" + "=" * 60)
    print("🎯 다음 단계")
    print("=" * 60)

    if not all_checks_ok:
        print("\n  ⚠️  일부 설정이 누락되었습니다.")
        print("     → .env 파일을 확인하세요")
        print("     → PRODUCTION_READY.md 문서를 참조하세요")
        return

    if mode == 'simulation':
        print("\n  ✅ 시스템 준비 완료! (시뮬레이션 모드)")
        print("\n  🚀 지금 바로 시작하기:")
        print("     1. 웹 서버 실행: python web_app.py")
        print("     2. 브라우저: http://localhost:5000")
        print("     3. Mode2에서 종목 등록")
        print("     4. 🔔 알림만 체크박스 체크")
        print("     5. 텔레그램 알림 확인")
        print("\n  💡 참고 문서:")
        print("     - QUICKSTART.md: 5분 빠른 시작")
        print("     - PRODUCTION_READY.md: 실전 전환 가이드")
    else:
        print("\n  ⚠️  실제 주문 모드 활성화됨!")
        print("\n  🛡️  안전 체크:")
        print("     - [ ] 소액으로 시작 (10만원 이하)")
        print("     - [ ] 대형주로 시작 (삼성전자, SK하이닉스)")
        print("     - [ ] 익절/손절 레벨 명확히 설정")
        print("     - [ ] 텔레그램 알림 모니터링 준비")
        print("     - [ ] HTS/MTS 병행 사용 준비")
        print("\n  🚀 실행:")
        print("     1. 웹 서버 실행: python web_app.py")
        print("     2. 브라우저: http://localhost:5000")
        print("     3. 감시리스트 확인")
        print("     4. 실시간 모니터링")


def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("🔍 단타 전략 시스템 준비 상태 체크")
    print("=" * 60)
    print("날짜:", os.popen('date "+%Y-%m-%d %H:%M:%S"').read().strip())

    # 체크 실행
    env_ok = check_env_vars()
    mode = check_operation_mode()
    files_ok = check_files()
    check_watchers()
    check_monitoring_settings()

    all_ok = env_ok and files_ok

    # 다음 단계 안내
    print_next_steps(mode, all_ok)

    # 최종 요약
    print("\n" + "=" * 60)
    if all_ok:
        print("✅ 시스템 체크 완료 - 준비됨!")
    else:
        print("⚠️  시스템 체크 완료 - 일부 설정 필요")
    print("=" * 60)

    # 추가 테스트 제안
    print("\n💡 추가 테스트:")
    print("   - 텔레그램 알림: python test_telegram_notification.py")
    print("   - 웹 UI: python web_app.py → http://localhost:5000")
    print("\n")


if __name__ == "__main__":
    main()
