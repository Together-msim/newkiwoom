"""
전략 관리자 - Tactic1, Tactic2 감시 리스트 관리
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict
import logging

logger = logging.getLogger(__name__)

DATA_DIR = ".data"
WATCHERS_FILE = os.path.join(DATA_DIR, "watchers.json")


class TacticManager:
    """전략 감시 리스트 관리"""

    def __init__(self):
        """초기화"""
        os.makedirs(DATA_DIR, exist_ok=True)
        self.watchers = self._load_watchers()

    def _load_watchers(self) -> Dict:
        """감시 리스트 로드"""
        if not os.path.exists(WATCHERS_FILE):
            return {}

        try:
            with open(WATCHERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"감시 리스트 로드 실패: {e}")
            return {}

    def _save_watchers(self):
        """감시 리스트 저장"""
        try:
            tmp_file = WATCHERS_FILE + ".tmp"
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(self.watchers, f, ensure_ascii=False, indent=2)
            os.replace(tmp_file, WATCHERS_FILE)
            logger.info(f"감시 리스트 저장 완료: {len(self.watchers)}개 종목")
        except Exception as e:
            logger.error(f"감시 리스트 저장 실패: {e}")

    def add_tactic1(
        self,
        codes: List[str],
        config: Optional[Dict] = None
    ) -> List[str]:
        """
        Tactic1 전략 추가

        Args:
            codes: 종목코드 리스트
            config: 전략 설정 (기준봉, 손절라인, 익절 등)

        Returns:
            추가된 종목코드 리스트
        """
        default_config = {
            "기준봉": "1분",
            "손절라인": None,  # None이면 매수가 -5%
            "보정_퍼센트": 2,
            "최대_손실_퍼센트": 5,
            "기대_수익률_퍼센트": None,  # None이면 첫 상승폭만큼
            "익절_비중_퍼센트": 100,
        }

        if config:
            default_config.update(config)

        added = []
        for code in codes:
            self.watchers[code] = {
                "tactic": "tactic1",
                "code": code,
                "config": default_config.copy(),
                "status": "waiting",  # waiting, bought, sold
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "buy_price": None,
                "buy_quantity": None,
                "buy_time": None,
            }
            added.append(code)
            logger.info(f"Tactic1 추가: {code}")

        self._save_watchers()
        return added

    def add_tactic2(
        self,
        code: str,
        config: Dict
    ) -> bool:
        """
        Tactic2 전략 추가

        Args:
            code: 종목코드
            config: 전략 설정 (1차/2차 매수가, 수량 등)

        Returns:
            성공 여부
        """
        required_fields = ["1차_매수가", "1차_수량", "2차_지지선", "2차_수량"]
        for field in required_fields:
            if field not in config:
                logger.error(f"Tactic2 필수 필드 누락: {field}")
                return False

        default_config = {
            "손절라인": None,  # None이면 1차매수가 -5%
            "보정_퍼센트": 2,
            "익절_감시_시작_퍼센트": 10,
            "익절_트렌드_꺾임_기준": 2,
        }
        default_config.update(config)

        self.watchers[code] = {
            "tactic": "tactic2",
            "code": code,
            "config": default_config,
            "status": "waiting_1st",  # waiting_1st, bought_1st, waiting_2nd, bought_2nd, sold
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "buy_1st_price": None,
            "buy_1st_quantity": None,
            "buy_1st_time": None,
            "buy_2nd_price": None,
            "buy_2nd_quantity": None,
            "buy_2nd_time": None,
            "avg_buy_price": None,
        }

        self._save_watchers()
        logger.info(f"Tactic2 추가: {code}")
        return True

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
            logger.info(f"감시 리스트에서 삭제: {code}")
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

    def update_watcher(self, code: str, updates: Dict) -> bool:
        """
        감시 정보 업데이트

        Args:
            code: 종목코드
            updates: 업데이트할 필드들

        Returns:
            성공 여부
        """
        if code not in self.watchers:
            return False

        self.watchers[code].update(updates)
        self.watchers[code]["updated_at"] = datetime.now().isoformat()
        self._save_watchers()
        logger.info(f"감시 정보 업데이트: {code}")
        return True

    def get_all_watchers(self) -> List[Dict]:
        """
        모든 감시 종목 조회

        Returns:
            감시 종목 리스트
        """
        return list(self.watchers.values())

    def get_tactic1_watchers(self) -> List[Dict]:
        """Tactic1 감시 종목만 조회"""
        return [w for w in self.watchers.values() if w['tactic'] == 'tactic1']

    def get_tactic2_watchers(self) -> List[Dict]:
        """Tactic2 감시 종목만 조회"""
        return [w for w in self.watchers.values() if w['tactic'] == 'tactic2']

    def get_status(self) -> Dict:
        """
        전체 상태 요약

        Returns:
            상태 요약 정보
        """
        tactic1_count = len(self.get_tactic1_watchers())
        tactic2_count = len(self.get_tactic2_watchers())

        return {
            "tactic1": {
                "active": tactic1_count,
            },
            "tactic2": {
                "active": tactic2_count,
            },
            "total": len(self.watchers),
            "last_update": datetime.now().isoformat(),
        }
