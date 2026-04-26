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
from global_config import get_global_config

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

            # 모니터링 상태 업데이트 (실시간)
            await self._update_monitoring_status(code, watcher, current_price)

            # 매수 대기 중
            if status == 'waiting_buy':
                target_price = watcher['buy_target_price']
                # 현재가가 매수 타점 밑으로 떨어지면 매수 (눌림 매매)
                if current_price < target_price:
                    mode_tag = "🔔 [알림 전용]" if notify_only else "🤖 [자동매매]"
                    logger.info(f"Mode2 | {code} | 매수 타이밍: {current_price:,}원 (타점: {target_price:,}원, notify_only={notify_only})")

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
                resistance_2_pct = watcher.get('resistance_2_profit_pct', 0)
                sold_history = watcher.get('sold_history', [])

                # 이미 매도한 레벨은 건너뛰기
                if resistance_2 > 0 and resistance_2_pct > 0 and current_price >= resistance_2 and 'resistance_2' not in sold_history:
                    profit_pct = ((current_price - bought_price) / bought_price) * 100
                    # 현재 보유 수량(모수) 기준 비중 계산
                    current_bought_qty = watcher.get('bought_quantity', 0)
                    sell_qty = int(current_bought_qty * resistance_2_pct / 100)
                    logger.info(f"Mode2 | {code} | 2차 저항 도달 익절: {current_price:,}원 ({profit_pct:.1f}%), 매도: {sell_qty}주 ({resistance_2_pct}%)")
                    await self.send_notification(
                        f"💰 Mode2 익절 시그널 (2차 저항)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"수익률: {profit_pct:.1f}%\n"
                        f"매도 수량: {sell_qty}주 ({resistance_2_pct}%)"
                    )
                    return {'action': 'sell', 'price': current_price, 'quantity': sell_qty, 'reason': 'resistance_2', 'ratio': resistance_2_pct}

                # 1차 저항 (익절)
                resistance_1 = watcher.get('resistance_1_price', 0)
                resistance_1_pct = watcher.get('resistance_1_profit_pct', 0)

                # 이미 매도한 레벨은 건너뛰기
                if resistance_1 > 0 and resistance_1_pct > 0 and current_price >= resistance_1 and 'resistance_1' not in sold_history:
                    profit_pct = ((current_price - bought_price) / bought_price) * 100
                    # 현재 보유 수량(모수) 기준 비중 계산
                    current_bought_qty = watcher.get('bought_quantity', 0)
                    sell_qty = int(current_bought_qty * resistance_1_pct / 100)
                    logger.info(f"Mode2 | {code} | 1차 저항 도달 익절: {current_price:,}원 ({profit_pct:.1f}%), 매도: {sell_qty}주 ({resistance_1_pct}%)")
                    await self.send_notification(
                        f"💰 Mode2 익절 시그널 (1차 저항)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"수익률: {profit_pct:.1f}%\n"
                        f"매도 수량: {sell_qty}주 ({resistance_1_pct}%)"
                    )
                    return {'action': 'sell', 'price': current_price, 'quantity': sell_qty, 'reason': 'resistance_1', 'ratio': resistance_1_pct}

                # 2차 지지 (손절)
                support_2 = watcher.get('support_2_price', 0)
                support_2_pct = watcher.get('support_2_loss_pct', 0)

                # 이미 매도한 레벨은 건너뛰기
                if support_2 > 0 and support_2_pct > 0 and current_price <= support_2 and 'support_2' not in sold_history:
                    loss_pct = ((current_price - bought_price) / bought_price) * 100
                    # 현재 보유 수량(모수) 기준 비중 계산
                    current_bought_qty = watcher.get('bought_quantity', 0)
                    sell_qty = int(current_bought_qty * support_2_pct / 100)
                    logger.info(f"Mode2 | {code} | 2차 지지 하락 손절: {current_price:,}원 ({loss_pct:.1f}%), 매도: {sell_qty}주 ({support_2_pct}%)")
                    await self.send_notification(
                        f"⚠️ Mode2 손절 시그널 (2차 지지)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"손실률: {loss_pct:.1f}%\n"
                        f"매도 수량: {sell_qty}주 ({support_2_pct}%)"
                    )
                    return {'action': 'sell', 'price': current_price, 'quantity': sell_qty, 'reason': 'support_2', 'ratio': support_2_pct}

                # 1차 지지 (손절)
                support_1 = watcher.get('support_1_price', 0)
                support_1_pct = watcher.get('support_1_loss_pct', 0)

                # 이미 매도한 레벨은 건너뛰기
                if support_1 > 0 and support_1_pct > 0 and current_price <= support_1 and 'support_1' not in sold_history:
                    loss_pct = ((current_price - bought_price) / bought_price) * 100
                    # 현재 보유 수량(모수) 기준 비중 계산
                    current_bought_qty = watcher.get('bought_quantity', 0)
                    sell_qty = int(current_bought_qty * support_1_pct / 100)
                    logger.info(f"Mode2 | {code} | 1차 지지 하락 손절: {current_price:,}원 ({loss_pct:.1f}%), 매도: {sell_qty}주 ({support_1_pct}%)")
                    await self.send_notification(
                        f"⚠️ Mode2 손절 시그널 (1차 지지)\n"
                        f"종목: {code}\n"
                        f"매수가: {bought_price:,}원\n"
                        f"현재가: {current_price:,}원\n"
                        f"손실률: {loss_pct:.1f}%\n"
                        f"매도 수량: {sell_qty}주 ({support_1_pct}%)"
                    )
                    return {'action': 'sell', 'price': current_price, 'quantity': sell_qty, 'reason': 'support_1', 'ratio': support_1_pct}

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
        """Mode1 3단계 조건 체크 (상승추세→조정→재반등)"""
        try:
            token = get_token()
            if not token:
                logger.error("토큰 발급 실패")
                return None

            status = watcher['status']
            if status != 'waiting_buy':
                return None  # 매수 대기 중일 때만 체크

            current_step = watcher.get('current_step', 0)
            step1 = watcher.get('step1', {})
            step2 = watcher.get('step2', {})
            step3 = watcher.get('step3', {})

            if not step1 or not step2 or not step3:
                logger.warning(f"Mode1 | {code} | Step 정보 없음")
                return None

            insights = []

            # Step 1: 상승 추세 전환 체크
            if current_step == 0:
                interval = step1['interval']
                last_check_time = watcher.get('last_step1_check')

                if not self.should_check_interval(interval, last_check_time):
                    return None  # 아직 체크 시점 아님

                candles = get_minute_chart(token, code, interval, 20)
                if not candles:
                    return None

                satisfied = check_condition_satisfied(candles, step1['trend'], step1['count'])
                watcher['last_step1_check'] = datetime.now(KST).isoformat()

                candle_summary = format_candles_summary(candles, limit=3)
                insights.append(f"Step 1: {interval} {step1['trend']} {step1['count']}개 → {'✅' if satisfied else '❌'}\n최근:\n{candle_summary}")

                if satisfied:
                    # 현재가 조회
                    try:
                        current_price = self.kiwoom.get_last_price(code)
                    except:
                        current_price = 0

                    logger.info(f"✅ Mode1 | {code} | Step 1 완료 (상승 추세 전환) → Step 2 진행")

                    if self.mode1_mgr:
                        self.mode1_mgr.update_watcher(code, {'current_step': 1})
                        self.mode1_mgr.update_insight(code, "\n\n".join(insights))

                    await self.send_notification(
                        f"✅ Mode1 Step 1 완료 (상승 추세 전환!)\n\n"
                        f"종목: {watcher.get('name', code)} ({code})\n"
                        f"현재가: {current_price:,}원\n\n"
                        f"✅ Step 1: {step1['interval']} {step1['trend']} {step1['count']}개 완료\n"
                        f"⏳ Step 2: {step2['interval']} {step2['trend']} {step2['count']}개 대기중\n"
                        f"⏳ Step 3: {step3['interval']} {step3['trend']} {step3['count']}개 대기중\n\n"
                        f"📊 최근 봉 상태:\n"
                        f"{insights[0]}\n\n"
                        f"💡 다음: 첫 조정({step2['interval']} {step2['trend']}) 대기"
                    )
                else:
                    if self.mode1_mgr:
                        self.mode1_mgr.update_insight(code, "\n\n".join(insights))

                return None

            # Step 2: 첫 조정 체크
            elif current_step == 1:
                interval = step2['interval']
                last_check_time = watcher.get('last_step2_check')

                if not self.should_check_interval(interval, last_check_time):
                    return None

                candles = get_minute_chart(token, code, interval, 20)
                if not candles:
                    return None

                satisfied = check_condition_satisfied(candles, step2['trend'], step2['count'])
                watcher['last_step2_check'] = datetime.now(KST).isoformat()

                candle_summary = format_candles_summary(candles, limit=3)
                insights.append(f"Step 2: {interval} {step2['trend']} {step2['count']}개 → {'✅' if satisfied else '❌'}\n최근:\n{candle_summary}")

                if satisfied:
                    # 현재가 조회
                    try:
                        current_price = self.kiwoom.get_last_price(code)
                    except:
                        current_price = 0

                    # 최근 봉 정보 (매수 타점 참고용)
                    latest_candle = candles[0] if candles else {}
                    candle_time = latest_candle.get('time', '')
                    candle_open = latest_candle.get('open', 0)
                    candle_close = latest_candle.get('close', 0)
                    candle_low = latest_candle.get('low', 0)

                    auto_buy = watcher.get('auto_buy', False)

                    # auto_buy=true면 Step 3로 진행, false면 여기서 종료 (수동 매수)
                    if auto_buy:
                        logger.info(f"✅ Mode1 | {code} | Step 2 완료 → Step 3 자동매수 모드 진행")
                        if self.mode1_mgr:
                            self.mode1_mgr.update_watcher(code, {'current_step': 2})
                            self.mode1_mgr.update_insight(code, "\n\n".join(insights))

                        await self.send_notification(
                            f"✅ Mode1 Step 2 완료 (자동매수 모드)\n\n"
                            f"종목: {watcher.get('name', code)} ({code})\n"
                            f"현재가: {current_price:,}원\n"
                            f"조정 저가: {candle_low:,}원\n\n"
                            f"✅ Step 1 완료\n"
                            f"✅ Step 2 완료\n"
                            f"⏳ Step 3 재반등 대기 중...\n\n"
                            f"🤖 Step 3 완료 시 자동 매수 실행됩니다"
                        )
                    else:
                        # 수동 매수 모드: Step 2가 최종 매수 시그널
                        logger.info(f"🎯 Mode1 | {code} | Step 2 완료 - 매수 시그널! (수동 매수)")

                        if self.mode1_mgr:
                            self.mode1_mgr.update_watcher(code, {
                                'current_step': 4,  # 완료로 표시
                                'recommended_buy_price': candle_low  # 조정 저가 추천
                            })
                            self.mode1_mgr.update_insight(code, "\n\n".join(insights))

                        # 매수 시그널 알림
                        await self.send_notification(
                            f"🎯 Mode1 매수 시그널! (Step 2 완료)\n\n"
                            f"종목: {watcher.get('name', code)} ({code})\n"
                            f"현재가: {current_price:,}원\n"
                            f"추천 매수가: {candle_low:,}원 (조정 저가)\n"
                            f"기대수익률: {watcher.get('expected_profit_rate', 0)}%\n\n"
                            f"📊 조정 봉 정보:\n"
                            f"시간: {candle_time}\n"
                            f"시가: {candle_open:,}원\n"
                            f"종가: {candle_close:,}원\n"
                            f"저가: {candle_low:,}원 ← 추천가\n\n"
                            f"✅ Step 1: {step1['interval']} {step1['trend']} {step1['count']}개 완료\n"
                            f"✅ Step 2: {step2['interval']} {step2['trend']} {step2['count']}개 완료\n\n"
                            f"💡 수동 매수를 진행하세요!\n"
                            f"또는 웹에서 Step 3 조건을 추가하여 자동매수 모드로 전환할 수 있습니다."
                        )
                else:
                    if self.mode1_mgr:
                        self.mode1_mgr.update_insight(code, "\n\n".join(insights))

                return None

            # Step 3: 재반등 체크 (자동매수 모드에서만)
            elif current_step == 2:
                auto_buy = watcher.get('auto_buy', False)
                if not auto_buy:
                    # auto_buy=false면 Step 3 체크 안 함
                    return None
                interval = step3['interval']
                last_check_time = watcher.get('last_step3_check')

                if not self.should_check_interval(interval, last_check_time):
                    return None

                candles = get_minute_chart(token, code, interval, 20)
                if not candles:
                    return None

                satisfied = check_condition_satisfied(candles, step3['trend'], step3['count'])
                watcher['last_step3_check'] = datetime.now(KST).isoformat()

                candle_summary = format_candles_summary(candles, limit=3)
                insights.append(f"Step 3: {interval} {step3['trend']} {step3['count']}개 → {'✅' if satisfied else '❌'}\n최근:\n{candle_summary}")

                if satisfied:
                    # n번째 봉의 시가 = 자동 매수가
                    nth_candle = candles[step3['count'] - 1] if len(candles) >= step3['count'] else candles[0]
                    buy_price = nth_candle['open']

                    logger.info(f"🤖 Mode1 | {code} | Step 3 완료! 자동 매수: {buy_price:,}원")

                    if self.mode1_mgr:
                        self.mode1_mgr.update_watcher(code, {
                            'current_step': 4,
                            'recommended_buy_price': buy_price
                        })
                        self.mode1_mgr.update_insight(code, "\n\n".join(insights))

                    # 자동 매수 실행 알림 (간결하게)
                    await self.send_notification(
                        f"🤖 Mode1 자동 매수 실행!\n\n"
                        f"종목: {watcher.get('name', code)} ({code})\n"
                        f"매수가: {buy_price:,}원\n"
                        f"시간: {nth_candle['time']}\n"
                        f"기대수익률: {watcher.get('expected_profit_rate', 0)}%\n\n"
                        f"✅ 3단계 완료 → 자동 매수 체결"
                    )

                    # 자동 매수 시그널 반환
                    return {'action': 'buy', 'price': buy_price}
                else:
                    if self.mode1_mgr:
                        self.mode1_mgr.update_insight(code, "\n\n".join(insights))

                return None

            return None

        except Exception as e:
            logger.error(f"Mode1 체크 실패 ({code}): {e}")
            import traceback
            traceback.print_exc()
            return None

    def _is_market_open(self) -> bool:
        """장 시간 체크 (평일 08:00~15:30, NXT KRX)"""
        now = datetime.now(KST)

        # 주말 체크
        if now.weekday() >= 5:  # 5=토요일, 6=일요일
            return False

        # 장 시간 체크 (08:00~15:30)
        market_open = now.replace(hour=8, minute=0, second=0, microsecond=0)
        market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)

        return market_open <= now <= market_close

    async def monitor_loop(self):
        """모니터링 루프"""
        logger.info("모니터링 루프 시작")

        while True:
            try:
                if not self.is_monitoring:
                    await asyncio.sleep(1)
                    continue

                # 장 시간 체크
                if not self._is_market_open():
                    now = datetime.now(KST)
                    logger.debug(f"장 시간 외 (현재: {now.strftime('%Y-%m-%d %H:%M:%S')})")
                    await asyncio.sleep(60)  # 1분 대기 후 재확인
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

                # Mode1 체크 (3단계 시스템)
                for watcher in mode1_watchers:
                    code = watcher['code']
                    polling_interval = watcher.get('polling_interval', 20)

                    try:
                        # current_step에 따라 어떤 step을 체크할지 결정
                        current_step = watcher.get('current_step', 0)

                        # 체크할 interval 결정
                        check_interval = None
                        if current_step == 0:
                            check_interval = watcher.get('step1', {}).get('interval')
                        elif current_step == 1:
                            check_interval = watcher.get('step2', {}).get('interval')
                        elif current_step == 2:
                            check_interval = watcher.get('step3', {}).get('interval')

                        if not check_interval:
                            continue

                        # 1분봉은 polling_interval로 체크, 나머지는 정시 체크
                        should_check = False
                        if check_interval == "1분":
                            last_check = watcher.get(f'last_step{current_step}_check')
                            if not last_check:
                                should_check = True
                            else:
                                last_dt = datetime.fromisoformat(last_check)
                                elapsed = (datetime.now(KST) - last_dt).total_seconds()
                                should_check = elapsed >= polling_interval
                        else:
                            # 3분/5분/10분봉은 should_check_interval로 판단
                            should_check = True  # check_mode1_conditions 내부에서 판단

                        if should_check:
                            signal = await self.check_mode1_conditions(code, watcher)

                            if signal:
                                if signal['action'] == 'buy':
                                    logger.info(f"Mode1 자동매수 시그널: {code} @ {signal['price']:,}원")

                                    # 주문 모드 확인
                                    global_config = get_global_config()
                                    simulation_mode = global_config.is_simulation_mode()

                                    # 자동 매수 실행
                                    quantity = signal.get('quantity', 1)
                                    result = self.kiwoom.place_buy_order(
                                        symbol=code,
                                        quantity=quantity,
                                        price=signal['price'],
                                        order_type="limit",
                                        simulation_mode=simulation_mode
                                    )

                                    if result['success'] and self.mode1_mgr:
                                        # 매수 기록
                                        self.mode1_mgr.record_buy(code, signal['price'], quantity)
                                        mode_text = "시뮬레이션" if simulation_mode else "실전"
                                        await self.send_notification(
                                            f"✅ Mode1 자동매수 ({mode_text})\n"
                                            f"종목: {code}\n"
                                            f"가격: {signal['price']:,}원\n"
                                            f"수량: {quantity}주\n"
                                            f"주문번호: {result.get('order_no', 'N/A')}"
                                        )

                                elif signal['action'] == 'signal':
                                    logger.info(f"Mode1 알림 시그널: {code} @ {signal['price']:,}원")

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
                    logger.info(f"Mode2 종목 체크: {code} (status: {watcher['status']})")

                    try:
                        signal = await self.check_mode2_conditions(code, watcher)

                        if signal:
                            logger.info(f"Mode2 시그널 발생: {code} - {signal}")

                            # 주문 모드 확인
                            global_config = get_global_config()
                            simulation_mode = global_config.is_simulation_mode()
                            mode_text = "시뮬레이션" if simulation_mode else "실전"

                            # 매수 시그널
                            if signal['action'] == 'buy':
                                result = self.kiwoom.place_buy_order(
                                    symbol=code,
                                    quantity=signal['quantity'],
                                    price=signal['price'],
                                    order_type="limit",
                                    simulation_mode=simulation_mode
                                )

                                if result['success'] and self.mode2_mgr:
                                    # 매수 기록
                                    self.mode2_mgr.record_buy(code, signal['price'], signal['quantity'])
                                    await self.send_notification(
                                        f"✅ Mode2 매수 체결 ({mode_text})\n"
                                        f"종목: {code}\n"
                                        f"가격: {signal['price']:,}원\n"
                                        f"수량: {signal['quantity']}주\n"
                                        f"주문번호: {result.get('order_no', 'N/A')}"
                                    )

                            # 매도 시그널
                            elif signal['action'] == 'sell':
                                sell_qty = signal.get('quantity', 0)
                                bought_qty = watcher.get('bought_quantity', 0)

                                # 매도 수량이 보유 수량보다 많으면 보유 수량으로 제한
                                actual_sell_qty = min(sell_qty, bought_qty)

                                if actual_sell_qty > 0:
                                    result = self.kiwoom.place_sell_order(
                                        symbol=code,
                                        quantity=actual_sell_qty,
                                        price=signal['price'],
                                        order_type="limit",
                                        simulation_mode=simulation_mode
                                    )

                                    if result['success'] and self.mode2_mgr:
                                        # 매도 기록 (분할 매도 지원)
                                        self.mode2_mgr.record_sell(
                                            code,
                                            sold_quantity=actual_sell_qty,
                                            sold_reason=signal.get('reason'),
                                            is_auto=True
                                        )

                                        bought_price = watcher.get('bought_price', 0)
                                        pnl_pct = ((signal['price'] - bought_price) / bought_price * 100) if bought_price > 0 else 0

                                        # 잔여 수량 계산
                                        remaining_qty = bought_qty - actual_sell_qty

                                        await self.send_notification(
                                            f"✅ Mode2 매도 체결 ({mode_text}, {signal['reason']})\n"
                                            f"종목: {code}\n"
                                            f"매수가: {bought_price:,}원\n"
                                            f"매도가: {signal['price']:,}원\n"
                                            f"매도 수량: {actual_sell_qty}주 ({signal.get('ratio', 0)}%)\n"
                                            f"잔여 수량: {remaining_qty}주\n"
                                            f"손익률: {pnl_pct:+.1f}%\n"
                                            f"주문번호: {result.get('order_no', 'N/A')}"
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

    async def _update_monitoring_status(self, code: str, watcher: dict, current_price: float):
        """모니터링 상태 실시간 업데이트 및 알림"""
        old_status = watcher.get('monitoring_status', '')
        new_status = ''

        buy_target = watcher.get('buy_target_price', 0)
        support_1 = watcher.get('support_1_price', 0)
        support_2 = watcher.get('support_2_price', 0)
        resistance_1 = watcher.get('resistance_1_price', 0)
        resistance_2 = watcher.get('resistance_2_price', 0)

        # 상태 판정
        if watcher['status'] == 'waiting_buy':
            if buy_target > 0 and current_price < buy_target:
                new_status = '매수타점 도달'
        elif watcher['status'] == 'waiting_sell':
            bought_price = watcher.get('bought_price', 0)
            if bought_price > 0:
                # 저항선 돌파 체크 (위에서 아래로)
                if resistance_2 > 0 and current_price >= resistance_2:
                    new_status = '2차저항 통과 (익절 구간)'
                elif resistance_1 > 0 and current_price >= resistance_1:
                    new_status = '1차저항 통과 (익절 구간)'
                # 지지선 이탈 체크
                elif support_2 > 0 and current_price <= support_2:
                    new_status = '2차지지 이탈 (손절 구간)'
                elif support_1 > 0 and current_price <= support_1:
                    new_status = '1차지지 이탈 (손절 구간)'
                else:
                    # 정상 범위
                    if support_1 > 0 and resistance_1 > 0:
                        new_status = f'정상 범위 ({support_1:,}~{resistance_1:,})'

        # 상태 변경 시 업데이트 및 알림
        if old_status != new_status and new_status:
            if self.mode2_manager:
                self.mode2_manager.update_monitoring_status(code, new_status)

            # 중요 상태 변경 시 텔레그램 알림
            if new_status in ['매수타점 도달', '2차지지 이탈 (손절 구간)', '1차지지 이탈 (손절 구간)',
                              '2차저항 통과 (익절 구간)', '1차저항 통과 (익절 구간)']:
                await self.send_notification(
                    f"📊 Mode2 모니터링 상태 변경\n"
                    f"종목: {watcher.get('name', code)} ({code})\n"
                    f"현재가: {current_price:,}원\n"
                    f"상태: {new_status}"
                )
