"""
가격 모니터링 엔진
"""
import os
import asyncio
import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo
from dotenv import load_dotenv

from kiwoom_chart import get_minute_chart
from kiwoom_token import get_token
from trend_analyzer import check_condition_satisfied, format_candles_summary

load_dotenv()

logger = logging.getLogger(__name__)
KST = ZoneInfo("Asia/Seoul")


class PriceMonitor:
    """가격 모니터링"""

    def __init__(self, tactic_manager, kiwoom_client, bot_application=None, mode1_manager=None, mode2_manager=None):
        self.tactic_mgr = tactic_manager
        self.mode1_mgr = mode1_manager
        self.mode2_mgr = mode2_manager
        self.kiwoom = kiwoom_client
        self.bot_app = bot_application
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.interval = int(os.getenv("MONITOR_INTERVAL", "10"))
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        # Mode2 종목별 마지막 체크 시간 기록 (polling 최적화)
        self.mode2_last_check = {}

    def start(self):
        """모니터링 시작"""
        if self.is_monitoring:
            logger.warning("이미 모니터링 중입니다")
            return False

        self.is_monitoring = True
        logger.info(f"가격 모니터링 시작 (간격: {self.interval}초)")
        return True

    def stop(self):
        """모니터링 중지"""
        if not self.is_monitoring:
            logger.warning("모니터링이 실행 중이 아닙니다")
            return False

        self.is_monitoring = False
        logger.info("가격 모니터링 중지")
        return True

    async def send_notification(self, message: str):
        """텔레그램 알림 전송"""
        if self.bot_app and self.chat_id:
            try:
                await self.bot_app.bot.send_message(
                    chat_id=self.chat_id,
                    text=message
                )
            except Exception as e:
                logger.error(f"알림 전송 실패: {e}")

    async def check_tactic1_conditions(self, code: str, watcher: dict):
        """Tactic1 조건 체크"""
        try:
            # 현재가 조회
            current_price = self.kiwoom.get_last_price(code)

            # TODO: 실제 매매 로직 구현
            # - 첫 조정 감지
            # - 반등 지점 확인
            # - 매수 시그널 발생

            # 현재는 간단히 가격만 로그
            logger.debug(f"T1 | {code} | {current_price:,}원")

            return None  # 매수 시그널이 발생하면 dict 반환

        except Exception as e:
            logger.error(f"T1 체크 실패 ({code}): {e}")
            return None

    async def check_tactic2_conditions(self, code: str, watcher: dict):
        """Tactic2 조건 체크"""
        try:
            current_price = self.kiwoom.get_last_price(code)
            config = watcher['config']
            status = watcher['status']

            # 1차 매수 대기 중
            if status == 'waiting_1st':
                target_price = config['1차_매수가']
                if abs(current_price - target_price) / target_price < 0.01:  # 1% 이내
                    logger.info(f"T2 | {code} | 1차 매수 타이밍: {current_price:,}원")
                    await self.send_notification(
                        f"🔔 T2 매수 시그널\n"
                        f"종목: {code}\n"
                        f"1차 매수: {target_price:,}원\n"
                        f"현재가: {current_price:,}원"
                    )
                    return {'action': '1st_buy', 'price': current_price}

            # 2차 매수 대기 중
            elif status == 'bought_1st':
                support_price = config['2차_지지선']
                if current_price <= support_price:
                    logger.info(f"T2 | {code} | 2차 매수 타이밍: {current_price:,}원")
                    await self.send_notification(
                        f"🔔 T2 2차 매수 시그널\n"
                        f"종목: {code}\n"
                        f"지지선: {support_price:,}원\n"
                        f"현재가: {current_price:,}원"
                    )
                    return {'action': '2nd_buy', 'price': current_price}

            return None

        except Exception as e:
            logger.error(f"T2 체크 실패 ({code}): {e}")
            return None

    async def check_mode2_conditions(self, code: str, watcher: dict):
        """Mode2 조건 체크 (저항/지지 레벨 기반)"""
        try:
            current_price = self.kiwoom.get_last_price(code)
            status = watcher['status']
            notify_only = watcher.get('notify_only', False)

            # 매수 대기 중
            if status == 'waiting_buy':
                target_price = watcher['buy_target_price']
                # 매수 타점의 ±1% 범위 내
                if abs(current_price - target_price) / target_price < 0.01:
                    mode_tag = "🔔 [알림 전용]" if notify_only else "🤖 [자동매매]"
                    logger.info(f"Mode2 | {code} | 매수 타이밍: {current_price:,}원 (notify_only={notify_only})")

                    await self.send_notification(
                        f"{mode_tag} Mode2 매수 시그널\n"
                        f"종목: {watcher.get('name', code)} ({code})\n"
                        f"타점: {target_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"수량: {watcher['quantity']}주"
                    )

                    # notify_only일 때는 알림만 보내고 주문은 하지 않음
                    if not notify_only:
                        return {'action': 'buy', 'price': current_price, 'quantity': watcher['quantity']}
                    else:
                        return None  # 알림만 보내고 주문 X

            # 매도 대기 중 (익절/손절 체크)
            elif status == 'waiting_sell':
                bought_price = watcher.get('bought_price')
                if not bought_price:
                    return None

                # 2차 저항 (익절)
                resistance_2 = watcher.get('resistance_2_price', 0)
                if resistance_2 > 0 and current_price >= resistance_2:
                    profit_pct = ((current_price - bought_price) / bought_price) * 100
                    logger.info(f"Mode2 | {code} | 2차 저항 도달 익절: {current_price:,}원 ({profit_pct:.1f}%)")
                    await self.send_notification(
                        f"💰 Mode2 익절 시그널 (2차 저항)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"수익률: {profit_pct:.1f}%"
                    )
                    return {'action': 'sell', 'price': current_price, 'reason': 'resistance_2'}

                # 1차 저항 (익절)
                resistance_1 = watcher.get('resistance_1_price', 0)
                if resistance_1 > 0 and current_price >= resistance_1:
                    profit_pct = ((current_price - bought_price) / bought_price) * 100
                    logger.info(f"Mode2 | {code} | 1차 저항 도달 익절: {current_price:,}원 ({profit_pct:.1f}%)")
                    await self.send_notification(
                        f"💰 Mode2 익절 시그널 (1차 저항)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"수익률: {profit_pct:.1f}%"
                    )
                    return {'action': 'sell', 'price': current_price, 'reason': 'resistance_1'}

                # 2차 지지 (손절)
                support_2 = watcher.get('support_2_price', 0)
                if support_2 > 0 and current_price <= support_2:
                    loss_pct = ((current_price - bought_price) / bought_price) * 100
                    logger.info(f"Mode2 | {code} | 2차 지지 하락 손절: {current_price:,}원 ({loss_pct:.1f}%)")
                    await self.send_notification(
                        f"⚠️ Mode2 손절 시그널 (2차 지지)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"손실률: {loss_pct:.1f}%"
                    )
                    return {'action': 'sell', 'price': current_price, 'reason': 'support_2'}

                # 1차 지지 (손절)
                support_1 = watcher.get('support_1_price', 0)
                if support_1 > 0 and current_price <= support_1:
                    loss_pct = ((current_price - bought_price) / bought_price) * 100
                    logger.info(f"Mode2 | {code} | 1차 지지 하락 손절: {current_price:,}원 ({loss_pct:.1f}%)")
                    await self.send_notification(
                        f"⚠️ Mode2 손절 시그널 (1차 지지)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"손실률: {loss_pct:.1f}%"
                    )
                    return {'action': 'sell', 'price': current_price, 'reason': 'support_1'}

            return None

        except Exception as e:
            logger.error(f"Mode2 체크 실패 ({code}): {e}")
            return None

    def should_check_interval(self, interval: str, last_check_time: Optional[str] = None) -> bool:
        """
        특정 interval을 체크할 시점인지 판단

        Args:
            interval: "1분", "3분", "5분", "10분"
            last_check_time: 마지막 체크 시각 (ISO format)

        Returns:
            True if should check now
        """
        now = datetime.now(KST)
        current_minute = now.minute
        current_second = now.second

        # 1분봉은 polling_interval로 별도 관리 (여기선 항상 True)
        if interval == "1분":
            return True

        # 3분봉: 0, 3, 6, 9, ... 분의 3초
        elif interval == "3분":
            if current_minute % 3 == 0 and current_second >= 3 and current_second < 6:
                # 이미 이번 cycle에 체크했는지 확인
                if last_check_time:
                    last_check = datetime.fromisoformat(last_check_time)
                    # 3분 이내에 체크했으면 skip
                    if (now - last_check).total_seconds() < 180:
                        return False
                return True

        # 5분봉: 0, 5, 10, 15, ... 분의 3초
        elif interval == "5분":
            if current_minute % 5 == 0 and current_second >= 3 and current_second < 6:
                if last_check_time:
                    last_check = datetime.fromisoformat(last_check_time)
                    if (now - last_check).total_seconds() < 300:
                        return False
                return True

        # 10분봉: 0, 10, 20, 30, ... 분의 3초
        elif interval == "10분":
            if current_minute % 10 == 0 and current_second >= 3 and current_second < 6:
                if last_check_time:
                    last_check = datetime.fromisoformat(last_check_time)
                    if (now - last_check).total_seconds() < 600:
                        return False
                return True

        return False

    async def check_mode1_conditions(self, code: str, watcher: dict):
        """Mode1 조건 체크 (분봉 기반 추세 전환)"""
        try:
            token = get_token()
            if not token:
                logger.error("토큰 발급 실패")
                return None

            status = watcher['status']
            if status != 'waiting_buy':
                return None  # 매수 대기 중일 때만 체크

            monitoring_conditions = watcher.get('monitoring_conditions', [])
            if not monitoring_conditions:
                return None

            # 각 조건마다 체크
            all_satisfied = True
            insights = []

            for idx, condition in enumerate(monitoring_conditions):
                interval = condition['interval']
                trend = condition['trend']
                required_count = condition['count']
                candle_count = condition.get('candle_count', 20)

                # 시간 기반 체크 (1분봉은 매번, 나머지는 정시 기준)
                last_check_key = f"last_check_{idx}"
                last_check_time = watcher.get(last_check_key)

                if not self.should_check_interval(interval, last_check_time):
                    # 아직 체크할 시점이 아님 - 이전 결과 유지
                    prev_status = watcher.get('greenlight_status', {}).get(str(idx), False)
                    if not prev_status:
                        all_satisfied = False
                    continue

                # 분봉 데이터 조회
                candles = get_minute_chart(token, code, interval, candle_count)
                if not candles or len(candles) == 0:
                    logger.warning(f"Mode1 | {code} | {interval} 데이터 없음")
                    all_satisfied = False
                    continue

                # 조건 만족 여부 체크
                satisfied = check_condition_satisfied(candles, trend, required_count)

                # greenlight_status 업데이트
                if self.mode1_mgr:
                    self.mode1_mgr.update_greenlight_status(code, idx, satisfied)

                # 마지막 체크 시각 기록
                watcher[last_check_key] = datetime.now(KST).isoformat()

                # 인사이트 수집
                candle_summary = format_candles_summary(candles, limit=3)
                insights.append(
                    f"[{interval}] {trend} {required_count}개: {'✅' if satisfied else '❌'}\n"
                    f"최근 3개:\n{candle_summary}"
                )

                if not satisfied:
                    all_satisfied = False

                logger.info(f"Mode1 | {code} | {interval}/{trend}/{required_count} -> {'만족' if satisfied else '불만족'}")

            # 인사이트 업데이트
            insight_text = "\n\n".join(insights)
            if self.mode1_mgr:
                self.mode1_mgr.update_insight(code, insight_text)

            # 모든 조건 만족 시 그린라이트!
            if all_satisfied:
                monitoring_price = watcher.get('monitoring_price', 0)
                expected_profit = watcher.get('expected_profit_rate', 0)

                logger.info(f"🎯 Mode1 그린라이트! {code} - 모든 조건 만족")
                await self.send_notification(
                    f"🎯 Mode1 그린라이트!\n\n"
                    f"종목: {watcher.get('name', code)} ({code})\n"
                    f"모니터링가: {monitoring_price:,}원\n"
                    f"기대수익률: {expected_profit}%\n\n"
                    f"📊 조건 상태:\n"
                    f"{insight_text}\n\n"
                    f"💡 수동 매수를 진행하세요!"
                )

                return {'action': 'greenlight', 'code': code}

            return None

        except Exception as e:
            logger.error(f"Mode1 체크 실패 ({code}): {e}")
            import traceback
            traceback.print_exc()
            return None

    async def monitor_loop(self):
        """모니터링 루프"""
        logger.info("모니터링 루프 시작")

        while True:
            try:
                if not self.is_monitoring:
                    await asyncio.sleep(1)
                    continue

                # Tactic1/2 감시
                watchers = self.tactic_mgr.get_all_watchers()

                # Mode1 감시
                mode1_watchers = []
                if self.mode1_mgr:
                    mode1_watchers = self.mode1_mgr.get_all_watchers(active_only=True)

                # Mode2 감시
                mode2_watchers = []
                if self.mode2_mgr:
                    mode2_watchers = self.mode2_mgr.get_all_watchers(active_only=True)

                total_count = len(watchers) + len(mode1_watchers) + len(mode2_watchers)

                if total_count == 0:
                    logger.debug("감시 중인 종목 없음")
                    await asyncio.sleep(self.interval)
                    continue

                logger.info(f"=== 가격 체크 시작 (Tactic: {len(watchers)}개, Mode1: {len(mode1_watchers)}개, Mode2: {len(mode2_watchers)}개) ===")

                # Mode1 체크 (분봉 기반, 별도 polling 주기)
                for watcher in mode1_watchers:
                    code = watcher['code']
                    polling_interval = watcher.get('polling_interval', 20)

                    try:
                        # 마지막 체크 시각 확인 (1분봉용)
                        last_1min_check = watcher.get('last_1min_check')
                        now = datetime.now(KST)

                        # 1분봉 체크 주기 확인
                        should_check_1min = True
                        if last_1min_check:
                            last_check_dt = datetime.fromisoformat(last_1min_check)
                            elapsed = (now - last_check_dt).total_seconds()
                            should_check_1min = elapsed >= polling_interval

                        # 1분봉을 포함하거나, 다른 interval이 체크 시점일 때만 실행
                        has_1min = any(c['interval'] == '1분' for c in watcher.get('monitoring_conditions', []))
                        if has_1min and should_check_1min:
                            watcher['last_1min_check'] = now.isoformat()

                        signal = await self.check_mode1_conditions(code, watcher)

                        if signal and signal['action'] == 'greenlight':
                            logger.info(f"Mode1 그린라이트: {code}")
                            # 수동 매수이므로 자동 주문 없음

                    except Exception as e:
                        logger.error(f"Mode1 종목 체크 실패 ({code}): {e}")
                        continue

                # Tactic1/2 체크
                for watcher in watchers:
                    code = watcher['code']
                    tactic = watcher['tactic']

                    try:
                        if tactic == 'tactic1':
                            signal = await self.check_tactic1_conditions(code, watcher)
                        else:
                            signal = await self.check_tactic2_conditions(code, watcher)

                        if signal:
                            logger.info(f"시그널 발생: {code} - {signal}")
                            # TODO: 실제 매수 처리

                    except Exception as e:
                        logger.error(f"종목 체크 실패 ({code}): {e}")
                        continue

                # Mode2 체크 (polling_interval 기반)
                now = datetime.now()
                for watcher in mode2_watchers:
                    code = watcher['code']
                    polling_interval = watcher.get('polling_interval', 10)  # 기본 10초

                    # 마지막 체크 시간 확인
                    last_check = self.mode2_last_check.get(code)
                    if last_check:
                        elapsed = (now - last_check).total_seconds()
                        if elapsed < polling_interval:
                            # 아직 polling 주기가 안 됨
                            continue

                    # polling 주기가 되었거나 첫 체크
                    self.mode2_last_check[code] = now

                    try:
                        signal = await self.check_mode2_conditions(code, watcher)

                        if signal:
                            logger.info(f"Mode2 시그널 발생: {code} - {signal}")

                            # 매수 시그널
                            if signal['action'] == 'buy':
                                result = self.kiwoom.place_buy_order(
                                    symbol=code,
                                    quantity=signal['quantity'],
                                    price=signal['price'],
                                    order_type="limit"
                                )

                                if result['success'] and self.mode2_mgr:
                                    # 매수 기록
                                    self.mode2_mgr.record_buy(code, signal['price'], signal['quantity'])
                                    await self.send_notification(
                                        f"✅ Mode2 매수 체결\n"
                                        f"종목: {code}\n"
                                        f"가격: {signal['price']:,}원\n"
                                        f"수량: {signal['quantity']}주\n"
                                        f"주문번호: {result['order_no']}"
                                    )

                            # 매도 시그널
                            elif signal['action'] == 'sell':
                                bought_qty = watcher.get('bought_quantity', 0)
                                if bought_qty > 0:
                                    result = self.kiwoom.place_sell_order(
                                        symbol=code,
                                        quantity=bought_qty,
                                        price=signal['price'],
                                        order_type="limit"
                                    )

                                    if result['success'] and self.mode2_mgr:
                                        # 매도 기록
                                        self.mode2_mgr.record_sell(code, is_auto=True)
                                        bought_price = watcher.get('bought_price', 0)
                                        pnl_pct = ((signal['price'] - bought_price) / bought_price * 100) if bought_price > 0 else 0
                                        await self.send_notification(
                                            f"✅ Mode2 매도 체결 ({signal['reason']})\n"
                                            f"종목: {code}\n"
                                            f"매수가: {bought_price:,}원\n"
                                            f"매도가: {signal['price']:,}원\n"
                                            f"수량: {bought_qty}주\n"
                                            f"손익률: {pnl_pct:+.1f}%\n"
                                            f"주문번호: {result['order_no']}"
                                        )

                    except Exception as e:
                        logger.error(f"Mode2 종목 체크 실패 ({code}): {e}")
                        continue

                logger.info(f"=== 가격 체크 완료 ===\n")
                await asyncio.sleep(self.interval)

            except Exception as e:
                logger.error(f"모니터링 루프 에러: {e}")
                await asyncio.sleep(self.interval)

    async def start_monitoring_task(self):
        """모니터링 태스크 시작"""
        if self.monitor_task and not self.monitor_task.done():
            logger.warning("모니터링 태스크가 이미 실행 중입니다")
            return

        self.monitor_task = asyncio.create_task(self.monitor_loop())
        logger.info("모니터링 태스크 생성 완료")
