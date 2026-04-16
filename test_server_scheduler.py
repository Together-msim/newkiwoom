"""
서버 스케줄러 테스트 스크립트
"""
import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo
from server_scheduler import ServerScheduler

async def test_scheduler():
    scheduler = ServerScheduler()

    print("=" * 60)
    print("서버 스케줄러 테스트")
    print("=" * 60)

    # 현재 상태 확인
    now = datetime.now(ZoneInfo("Asia/Seoul"))
    print(f"\n현재 시간 (KST): {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"요일: {['월', '화', '수', '목', '금', '토', '일'][now.weekday()]}")

    # 서버 상태 확인
    print(f"\n수동 제어 모드: {scheduler.manual_mode}")
    print(f"서버 실행 여부: {scheduler.should_be_running()}")
    print(f"다음 스케줄: {scheduler.get_next_schedule()}")

    # 상태 메시지
    print("\n" + scheduler.get_status_message())

    # GCP 서버 상태 확인 (실제 gcloud 명령 실행)
    print("\n[GCP 서버 상태 확인 중...]")
    try:
        is_running = await scheduler.check_server_status()
        print(f"실제 서버 상태: {'🟢 RUNNING' if is_running else '🔴 STOPPED'}")
    except Exception as e:
        print(f"서버 상태 확인 실패: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_scheduler())
