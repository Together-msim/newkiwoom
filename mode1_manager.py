"""
Mode1 전략 관리자
전일대비 급등 종목 첫 조정 노리기 (분봉 기반 모니터링)
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

DATA_DIR = ".data"
MODE1_FILE = os.path.join(DATA_DIR, "mode1_watchers.json")


class Mode1Manager:
    """Mode1 감시 리스트 관리"""

    def __init__(self):
        """초기화"""
        os.makedirs(DATA_DIR, exist_ok=True)
        self.watchers = self._load_watchers()

    def _load_watchers(self) -> Dict:
        """감시 리스트 로드"""
        if not os.path.exists(MODE1_FILE):
            return {}

        try:
            with open(MODE1_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Mode1 감시 리스트 로드 실패: {e}")
            return {}

    def _save_watchers(self):
        """감시 리스트 저장"""
        try:
            tmp_file = MODE1_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.watchers, f, ensure_ascii=False, indent=2)
            os.replace(tmp_file, MODE1_FILE)
            logger.info(f"Mode1 감시 리스트 저장 완료: {len(self.watchers)}개 종목")
        except Exception as e:
            logger.error(f"Mode1 감시 리스트 저장 실패: {e}")

    def add_watcher(self, data: Dict) -> Dict:
        """
        Mode1 전략 추가 (3단계 시스템)

        Args:
            data: {
                "code": str,  # 종목코드
                "name": str,  # 종목명
                "monitoring_price": float,  # 모니터링 기준 가격
                "step1": {  # 상승 추세 전환
                    "interval": str,  # 분봉 (1분, 3분, 5분, 10분)
                    "trend": str,     # 추세 (상승, 하락)
                    "count": int,     # 연속 봉 개수
                    "candle_count": int  # 조회할 총 봉 개수
                },
                "step2": {  # 첫 조정
                    "interval": str,
                    "trend": str,
                    "count": int,
                    "candle_count": int
                },
                "step3": {  # 재반등
                    "interval": str,
                    "trend": str,
                    "count": int,
                    "candle_count": int
                },
                "auto_buy": bool,  # True=자동매수, False=알림만
                "expected_profit_rate": float,  # 기대 수익률 (%)
                "polling_interval": int,  # polling 주기 (초)
            }

        Returns:
            생성된 watcher 객체
        """
        code = data["code"]

        watcher = {
            "code": code,
            "name": data.get("name", ""),
            "mode": "mode1",
            "monitoring_price": data.get("monitoring_price", 0),
            "step1": data.get("step1", {
                "interval": "1분",
                "trend": "상승",
                "count": 4
            }),
            "step2": data.get("step2", {
                "interval": "3분",
                "trend": "하락",
                "count": 1
            }),
            "step3": data.get("step3", {
                "interval": "1분",
                "trend": "상승",
                "count": 2
            }),
            "auto_buy": data.get("auto_buy", False),
            "current_step": 0,  # 0=대기, 1~3=진행중, 4=완료
            "recommended_buy_price": None,  # Step 3 완료 시 계산
            "expected_profit_rate": data.get("expected_profit_rate", 0),
            "polling_interval": data.get("polling_interval", 20),  # 기본 20초
            "greenlight_status": {},  # 각 조건별 만족 여부
            "insight": "",  # 모니터링 인사이트
            "buy_price": None,  # 매수 실행 가격
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
        logger.info(f"Mode1 추가: {code}")
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
        watcher.update(data)
        watcher["updated_at"] = datetime.now().isoformat()

        self._save_watchers()
        logger.info(f"Mode1 업데이트: {code}")
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
            logger.info(f"Mode1 삭제: {code}")
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
        logger.info(f"Mode1 {'활성화' if active else '비활성화'}: {code}")
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
        logger.info(f"Mode1 상태 변경: {code} -> {status}")
        return True

    def update_insight(self, code: str, insight: str) -> bool:
        """
        모니터링 인사이트 업데이트

        Args:
            code: 종목코드
            insight: 인사이트 메시지

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        self.watchers[code]["insight"] = insight
        self.watchers[code]["updated_at"] = datetime.now().isoformat()
        self._save_watchers()
        return True

    def update_greenlight_status(self, code: str, condition_index: int, satisfied: bool) -> bool:
        """
        그린라이트 조건 만족 여부 업데이트

        Args:
            code: 종목코드
            condition_index: 조건 인덱스
            satisfied: 만족 여부

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        if "greenlight_status" not in self.watchers[code]:
            self.watchers[code]["greenlight_status"] = {}

        self.watchers[code]["greenlight_status"][str(condition_index)] = satisfied
        self.watchers[code]["updated_at"] = datetime.now().isoformat()
        self._save_watchers()
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
        logger.info(f"Mode1 매수 기록: {code} @ {price:,}원 x {quantity}주")
        return True

    def record_sell(self, code: str, is_auto: bool = True) -> bool:
        """
        매도 체결 기록

        Args:
            code: 종목코드
            is_auto: 자동 매도 여부

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        status = "auto_sold" if is_auto else "manual_sold"
        self.watchers[code].update({
            "status": status,
            "updated_at": datetime.now().isoformat(),
        })
        self._save_watchers()
        logger.info(f"Mode1 매도 기록: {code} - {status}")
        return True
