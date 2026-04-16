"""
서버 자동 스케줄링 및 제어
- 평일 08:00~15:30 자동 서버 ON
- 그 외 시간 자동 서버 OFF
- /on, /off 명령어로 수동 제어 가능
"""
import os
import logging
import subprocess
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo
import asyncio

logger = logging.getLogger(__name__)

# 서버 설정
GCP_INSTANCE_NAME = os.getenv("GCP_INSTANCE_NAME", "kiwoom-trading-bot")
GCP_ZONE = os.getenv("GCP_ZONE", "asia-northeast3-a")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")

# 한국 시간대
KST = ZoneInfo("Asia/Seoul")

# 운영 시간 (평일 08:00 ~ 15:30)
MARKET_START = time(8, 0)
MARKET_END = time(15, 30)

# 수동 제어 플래그 (파일 기반 상태 관리)
MANUAL_CONTROL_FILE = ".data/manual_server_control.txt"


class ServerScheduler:
    """서버 자동 스케줄링"""

    def __init__(self):
        self.is_running = False
        self.manual_mode = self._load_manual_mode()

    def _load_manual_mode(self) -> bool:
        """수동 제어 모드 로드"""
        if not os.path.exists(MANUAL_CONTROL_FILE):
            return False

        try:
            with open(MANUAL_CONTROL_FILE, 'r') as f:
                content = f.read().strip().lower()
                return content == 'on'
        except Exception as e:
            logger.error(f"수동 제어 상태 로드 실패: {e}")
            return False

    def _save_manual_mode(self, enabled: bool):
        """수동 제어 모드 저장"""
        try:
            os.makedirs(os.path.dirname(MANUAL_CONTROL_FILE), exist_ok=True)
            with open(MANUAL_CONTROL_FILE, 'w') as f:
                f.write('on' if enabled else 'off')
        except Exception as e:
            logger.error(f"수동 제어 상태 저장 실패: {e}")

    def should_be_running(self) -> bool:
        """현재 시간에 서버가 켜져 있어야 하는지 확인"""
        # 수동 제어 모드가 활성화된 경우
        if self.manual_mode:
            return True

        now = datetime.now(KST)

        # 주말 체크 (0=월, 6=일)
        if now.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False

        # 평일 08:00~15:30 체크
        current_time = now.time()
        return MARKET_START <= current_time <= MARKET_END

    def get_next_schedule(self) -> str:
        """다음 스케줄 시간 반환"""
        if self.manual_mode:
            return "수동 제어 모드 (자동 스케줄 비활성화)"

        now = datetime.now(KST)
        current_time = now.time()
        weekday = now.weekday()

        # 주말
        if weekday >= 5:
            # 다음 월요일 08:00
            days_until_monday = (7 - weekday) % 7 or 7
            return f"월요일 08:00 (D-{days_until_monday})"

        # 평일
        if current_time < MARKET_START:
            return f"오늘 08:00"
        elif current_time < MARKET_END:
            return f"오늘 15:30 (종료)"
        else:
            return f"내일 08:00"

    def _get_next_schedule_time(self) -> datetime | None:
        """다음 스케줄 시간 계산 (08:00 또는 15:30)"""
        if self.manual_mode:
            return None  # 수동 모드에서는 스케줄 없음

        now = datetime.now(KST)
        today = now.date()

        # 평일만 체크
        if now.weekday() >= 5:  # 주말
            # 다음 월요일 08:00
            days_until_monday = (7 - now.weekday()) % 7 or 7
            next_day = today + timedelta(days=days_until_monday)
            return datetime.combine(next_day, MARKET_START, tzinfo=KST)

        # 평일
        current_time = now.time()

        if current_time < MARKET_START:
            # 오늘 08:00
            return datetime.combine(today, MARKET_START, tzinfo=KST)
        elif current_time < MARKET_END:
            # 오늘 15:30
            return datetime.combine(today, MARKET_END, tzinfo=KST)
        else:
            # 내일 08:00
            if now.weekday() == 4:  # 금요일
                next_day = today + timedelta(days=3)  # 월요일
            else:
                next_day = today + timedelta(days=1)
            return datetime.combine(next_day, MARKET_START, tzinfo=KST)

    async def start_monitoring(self):
        """모니터링 시작 (특정 시간에만 실행)"""
        self.is_running = True
        logger.info("서버 스케줄러 시작")

        while self.is_running:
            try:
                # 다음 스케줄 시간 계산
                next_time = self._get_next_schedule_time()

                if next_time is None:
                    # 수동 모드: 10분마다 체크 (수동 모드 해제 감지용)
                    await asyncio.sleep(600)
                    continue

                now = datetime.now(KST)
                wait_seconds = (next_time - now).total_seconds()

                if wait_seconds > 0:
                    logger.info(f"다음 스케줄: {next_time.strftime('%Y-%m-%d %H:%M:%S')} (대기: {wait_seconds/60:.1f}분)")
                    await asyncio.sleep(wait_seconds)

                # 스케줄 실행
                await self._execute_schedule()

            except Exception as e:
                logger.error(f"스케줄러 오류: {e}")
                await asyncio.sleep(60)  # 에러 시 1분 대기

    async def _execute_schedule(self):
        """스케줄 실행 (서버 ON/OFF)"""
        if self.manual_mode:
            logger.info("수동 모드 활성화 - 자동 스케줄 건너뜀")
            return

        now = datetime.now(KST)
        current_time = now.time()
        is_running = await self.check_server_status()

        # 08:00 근처 - 서버 시작
        if abs((current_time.hour * 60 + current_time.minute) - (MARKET_START.hour * 60 + MARKET_START.minute)) < 2:
            if not is_running:
                logger.info("⏰ 장 시작 - 서버를 시작합니다...")
                await self.start_server()
            else:
                logger.info("서버가 이미 실행 중입니다")

        # 15:30 근처 - 서버 중지
        elif abs((current_time.hour * 60 + current_time.minute) - (MARKET_END.hour * 60 + MARKET_END.minute)) < 2:
            if is_running:
                logger.info("⏰ 장 마감 - 서버를 중지합니다...")
                await self.stop_server()
            else:
                logger.info("서버가 이미 중지되어 있습니다")

    def stop_monitoring(self):
        """모니터링 중지"""
        self.is_running = False
        logger.info("서버 스케줄러 중지")

    async def manual_start(self) -> tuple[bool, str]:
        """수동 서버 시작"""
        try:
            result = await self.start_server()
            if result:
                self.manual_mode = True
                self._save_manual_mode(True)
                return True, "✅ 서버를 시작했습니다 (수동 모드)"
            return False, "❌ 서버 시작 실패"
        except Exception as e:
            logger.error(f"수동 시작 실패: {e}")
            return False, f"❌ 오류: {str(e)}"

    async def manual_stop(self) -> tuple[bool, str]:
        """수동 서버 중지"""
        try:
            result = await self.stop_server()
            if result:
                self.manual_mode = False
                self._save_manual_mode(False)
                return True, "✅ 서버를 중지했습니다 (수동 모드 해제)"
            return False, "❌ 서버 중지 실패"
        except Exception as e:
            logger.error(f"수동 중지 실패: {e}")
            return False, f"❌ 오류: {str(e)}"

    async def check_server_status(self) -> bool:
        """GCP VM 인스턴스 상태 확인"""
        try:
            cmd = [
                "gcloud", "compute", "instances", "describe",
                GCP_INSTANCE_NAME,
                f"--zone={GCP_ZONE}",
                "--format=get(status)"
            ]

            if GCP_PROJECT_ID:
                cmd.append(f"--project={GCP_PROJECT_ID}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                status = result.stdout.strip()
                return status == "RUNNING"

            logger.error(f"서버 상태 확인 실패: {result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("서버 상태 확인 타임아웃")
            return False
        except Exception as e:
            logger.error(f"서버 상태 확인 오류: {e}")
            return False

    async def start_server(self) -> bool:
        """GCP VM 인스턴스 시작"""
        try:
            cmd = [
                "gcloud", "compute", "instances", "start",
                GCP_INSTANCE_NAME,
                f"--zone={GCP_ZONE}"
            ]

            if GCP_PROJECT_ID:
                cmd.append(f"--project={GCP_PROJECT_ID}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"서버 시작 완료: {GCP_INSTANCE_NAME}")
                return True

            logger.error(f"서버 시작 실패: {result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("서버 시작 타임아웃")
            return False
        except Exception as e:
            logger.error(f"서버 시작 오류: {e}")
            return False

    async def stop_server(self) -> bool:
        """GCP VM 인스턴스 중지"""
        try:
            cmd = [
                "gcloud", "compute", "instances", "stop",
                GCP_INSTANCE_NAME,
                f"--zone={GCP_ZONE}"
            ]

            if GCP_PROJECT_ID:
                cmd.append(f"--project={GCP_PROJECT_ID}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info(f"서버 중지 완료: {GCP_INSTANCE_NAME}")
                return True

            logger.error(f"서버 중지 실패: {result.stderr}")
            return False

        except subprocess.TimeoutExpired:
            logger.error("서버 중지 타임아웃")
            return False
        except Exception as e:
            logger.error(f"서버 중지 오류: {e}")
            return False

    def get_status_message(self) -> str:
        """현재 상태 메시지"""
        now = datetime.now(KST)
        should_run = self.should_be_running()

        mode = "🔧 수동 제어" if self.manual_mode else "⏰ 자동 스케줄"
        status = "✅ 운영 중" if should_run else "❌ 중지"
        next_schedule = self.get_next_schedule()

        return f"""
🖥 서버 상태

모드: {mode}
현재: {status}
다음: {next_schedule}

한국시간: {now.strftime('%Y-%m-%d %H:%M:%S')}
평일 자동 운영: 08:00~15:30
"""
