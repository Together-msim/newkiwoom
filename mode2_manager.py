"""
Mode2 전략 관리자
스윙 분할 매매 전략 (저항/지지 레벨 기반)
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

DATA_DIR = ".data"
MODE2_FILE = os.path.join(DATA_DIR, "mode2_watchers.json")


class Mode2Manager:
    """Mode2 감시 리스트 관리"""

    def __init__(self):
        """초기화"""
        os.makedirs(DATA_DIR, exist_ok=True)
        self.watchers = self._load_watchers()

    def _load_watchers(self) -> Dict:
        """감시 리스트 로드"""
        if not os.path.exists(MODE2_FILE):
            return {}

        try:
            with open(MODE2_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Mode2 감시 리스트 로드 실패: {e}")
            return {}

    def _save_watchers(self):
        """감시 리스트 저장"""
        try:
            tmp_file = MODE2_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.watchers, f, ensure_ascii=False, indent=2)
            os.replace(tmp_file, MODE2_FILE)
            logger.info(f"Mode2 감시 리스트 저장 완료: {len(self.watchers)}개 종목")
        except Exception as e:
            logger.error(f"Mode2 감시 리스트 저장 실패: {e}")

    def add_watcher(self, data: Dict) -> Dict:
        """
        Mode2 전략 추가

        Args:
            data: {
                "code": str,  # 종목코드
                "buy_target_price": int,  # 매수 타점
                "budget": int,  # 예산
                "resistance_1_price": int,  # 1차 저항
                "resistance_1_profit_pct": float,  # 1차 익절%
                "resistance_2_price": int,  # 2차 저항
                "resistance_2_profit_pct": float,  # 2차 익절%
                "support_1_price": int,  # 1차 지지
                "support_1_loss_pct": float,  # 1차 손절%
                "support_2_price": int,  # 2차 지지
                "support_2_loss_pct": float,  # 2차 손절%
            }

        Returns:
            생성된 watcher 객체
        """
        code = data["code"]
        buy_target_price = data["buy_target_price"]
        budget = data["budget"]

        # 매수 수량 자동 계산
        quantity = budget // buy_target_price if buy_target_price > 0 else 0

        watcher = {
            "code": code,
            "name": data.get("name", ""),  # 종목명은 추후 API로 조회
            "mode": "mode2",
            "buy_target_price": buy_target_price,
            "budget": budget,
            "quantity": quantity,
            "resistance_1_price": data.get("resistance_1_price", 0),
            "resistance_1_profit_pct": data.get("resistance_1_profit_pct", 0),
            "resistance_2_price": data.get("resistance_2_price", 0),
            "resistance_2_profit_pct": data.get("resistance_2_profit_pct", 0),
            "support_1_price": data.get("support_1_price", 0),
            "support_1_loss_pct": data.get("support_1_loss_pct", 0),
            "support_2_price": data.get("support_2_price", 0),
            "support_2_loss_pct": data.get("support_2_loss_pct", 0),
            "polling_interval": data.get("polling_interval", 10),  # 초 단위 (기본 10초)
            "notify_only": data.get("notify_only", False),  # True: 알림만, False: 자동매매
            "status": "waiting_buy",  # waiting_buy, waiting_sell, auto_sold, manual_sold
            "active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            # 매수 후 정보
            "bought_price": None,
            "bought_quantity": None,
            "bought_at": None,
        }

        self.watchers[code] = watcher
        self._save_watchers()
        logger.info(f"Mode2 추가: {code}")
        return watcher

    def update_watcher(self, code: str, data: Dict) -> Optional[Dict]:
        """
        감시 정보 업데이트

        Args:
            code: 종목코드
            data: 업데이트할 필드들

        Returns:
            업데이트된 watcher 또는 None
        """
        if code not in self.watchers:
            return None

        watcher = self.watchers[code]

        # 매수 타점 또는 예산 변경 시 수량 재계산
        if "buy_target_price" in data or "budget" in data:
            buy_price = data.get("buy_target_price", watcher["buy_target_price"])
            budget = data.get("budget", watcher["budget"])
            data["quantity"] = budget // buy_price if buy_price > 0 else 0

        # 필드 업데이트
        watcher.update(data)
        watcher["updated_at"] = datetime.now().isoformat()

        self._save_watchers()
        logger.info(f"Mode2 업데이트: {code}")
        return watcher

    def delete_watcher(self, code: str) -> bool:
        """
        감시 리스트에서 종목 삭제

        Args:
            code: 종목코드

        Returns:
            성공 여부
        """
        if code in self.watchers:
            del self.watchers[code]
            self._save_watchers()
            logger.info(f"Mode2 삭제: {code}")
            return True
        return False

    def get_watcher(self, code: str) -> Optional[Dict]:
        """
        특정 종목의 감시 정보 조회

        Args:
            code: 종목코드

        Returns:
            감시 정보 또는 None
        """
        return self.watchers.get(code)

    def get_all_watchers(self, active_only: bool = False) -> List[Dict]:
        """
        모든 감시 종목 조회

        Args:
            active_only: True이면 active=True인 종목만 반환

        Returns:
            감시 종목 리스트
        """
        watchers = list(self.watchers.values())
        if active_only:
            watchers = [w for w in watchers if w.get("active", True)]
        return watchers

    def set_active(self, code: str, active: bool) -> bool:
        """
        종목 활성화/비활성화

        Args:
            code: 종목코드
            active: 활성화 여부

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        self.watchers[code]["active"] = active
        self.watchers[code]["updated_at"] = datetime.now().isoformat()
        self._save_watchers()
        logger.info(f"Mode2 {'활성화' if active else '비활성화'}: {code}")
        return True

    def update_status(self, code: str, status: str) -> bool:
        """
        종목 상태 업데이트

        Args:
            code: 종목코드
            status: waiting_buy, waiting_sell, auto_sold, manual_sold

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        self.watchers[code]["status"] = status
        self.watchers[code]["updated_at"] = datetime.now().isoformat()
        self._save_watchers()
        logger.info(f"Mode2 상태 변경: {code} -> {status}")
        return True

    def record_buy(self, code: str, price: float, quantity: int) -> bool:
        """
        매수 체결 기록

        Args:
            code: 종목코드
            price: 매수가
            quantity: 매수 수량

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        self.watchers[code].update({
            "bought_price": price,
            "bought_quantity": quantity,
            "bought_at": datetime.now().isoformat(),
            "status": "waiting_sell",
            "updated_at": datetime.now().isoformat(),
        })
        self._save_watchers()
        logger.info(f"Mode2 매수 기록: {code} @ {price:,}원 x {quantity}주")
        return True

    def record_sell(self, code: str, sold_quantity: int = None, sold_reason: str = None, is_auto: bool = True) -> bool:
        """
        매도 체결 기록 (분할 매도 지원)

        Args:
            code: 종목코드
            sold_quantity: 매도 수량 (None이면 전량 매도)
            sold_reason: 매도 사유 (resistance_1, resistance_2, support_1, support_2)
            is_auto: 자동 매도 여부

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        watcher = self.watchers[code]
        current_qty = watcher.get('bought_quantity', 0)

        # 매도 이력 초기화
        if 'sold_history' not in watcher:
            watcher['sold_history'] = []

        # 매도 수량 결정
        if sold_quantity is None or sold_quantity >= current_qty:
            # 전량 매도
            new_qty = 0
            status = "auto_sold" if is_auto else "manual_sold"
        else:
            # 분할 매도
            new_qty = current_qty - sold_quantity
            status = "waiting_sell"  # 아직 보유 중이므로 매도 대기 상태 유지

        # 매도 이력 기록
        if sold_reason and sold_reason not in watcher['sold_history']:
            watcher['sold_history'].append(sold_reason)

        self.watchers[code].update({
            "bought_quantity": new_qty,
            "status": status,
            "updated_at": datetime.now().isoformat(),
        })

        # 설정된 매도 레벨 목록
        configured_levels = []
        if watcher.get('resistance_2_profit_pct', 0) > 0:
            configured_levels.append('resistance_2')
        if watcher.get('resistance_1_profit_pct', 0) > 0:
            configured_levels.append('resistance_1')
        if watcher.get('support_2_loss_pct', 0) > 0:
            configured_levels.append('support_2')
        if watcher.get('support_1_loss_pct', 0) > 0:
            configured_levels.append('support_1')

        # 설정된 모든 레벨을 소진했는지 체크
        sold_history = watcher.get('sold_history', [])
        all_levels_sold = all(level in sold_history for level in configured_levels) if configured_levels else False

        # 모니터링 종료 조건:
        # 1) bought_quantity = 0 (전량 매도)
        # 2) 설정된 모든 매도 레벨 소진 (홀딩 포지션 진입)
        if new_qty == 0:
            self.watchers[code]["active"] = False
            logger.info(f"Mode2 전량 매도 완료: {code} - 감시 자동 종료 (bought_quantity=0)")
        elif all_levels_sold:
            # 모든 설정된 매도 레벨을 통과했으면 모니터링 종료
            self.watchers[code]["active"] = False
            total_sell_ratio = sum([
                watcher.get('resistance_1_profit_pct', 0),
                watcher.get('resistance_2_profit_pct', 0),
                watcher.get('support_1_loss_pct', 0),
                watcher.get('support_2_loss_pct', 0)
            ])
            holding_pct = 100 - total_sell_ratio
            logger.info(f"Mode2 설정된 매도 완료: {code} - 감시 종료 (홀딩: {holding_pct}%, 잔여: {new_qty}주)")
        else:
            logger.info(f"Mode2 분할 매도: {code} - {sold_quantity}주 매도 ({sold_reason}), 잔여: {new_qty}주")

        self._save_watchers()
        return True
