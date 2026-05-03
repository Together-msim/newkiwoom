"""
Mode2 전략 관리자
스윙 분할 매매 전략 (저항/지지 레벨 기반)
"""
import json
import os
from datetime import datetime
from typing import Optional, List, Dict
from zoneinfo import ZoneInfo
import logging

logger = logging.getLogger(__name__)

DATA_DIR = ".data"
MODE2_FILE = os.path.join(DATA_DIR, "mode2_watchers.json")


class Mode2Manager:
    """Mode2 감시 리스트 관리"""

    def __init__(self):
        """초기화"""
        os.makedirs(DATA_DIR, exist_ok=True)
        self.data = self._load_watchers()
        self.watchers = self.data.get('watchers', {})
        self.sections = self.data.get('sections', [])

        # 자동 마이그레이션
        self._migrate_if_needed()

    def _load_watchers(self) -> Dict:
        """감시 리스트 로드"""
        if not os.path.exists(MODE2_FILE):
            return {'sections': [], 'watchers': {}}

        try:
            with open(MODE2_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)

                # 구버전 데이터 (dict만 있는 경우)
                if not isinstance(data, dict) or 'sections' not in data:
                    return {'sections': [], 'watchers': data if isinstance(data, dict) else {}}

                return data
        except Exception as e:
            logger.error(f"Mode2 감시 리스트 로드 실패: {e}")
            return {'sections': [], 'watchers': {}}

    def _migrate_if_needed(self):
        """자동 마이그레이션: 구버전 데이터를 신버전으로 변환"""
        migrated = False

        # 섹션이 없으면 기본 "미분류" 섹션 생성
        if not self.sections:
            self.sections = [{
                'id': 'uncategorized',
                'name': '미분류',
                'order': 999,
                'collapsed': False
            }]
            migrated = True
            logger.info("기본 '미분류' 섹션 생성")

        # 각 watcher에 새 필드 추가
        for code, watcher in self.watchers.items():
            if self._migrate_watcher(watcher):
                migrated = True

        if migrated:
            # 백업 생성
            if os.path.exists(MODE2_FILE):
                backup_file = MODE2_FILE + ".backup"
                import shutil
                shutil.copy2(MODE2_FILE, backup_file)
                logger.info(f"마이그레이션 전 백업 생성: {backup_file}")

            self._save_watchers()
            logger.info(f"데이터 마이그레이션 완료: {len(self.watchers)}개 종목")

    def _migrate_watcher(self, watcher: Dict) -> bool:
        """단일 watcher 마이그레이션 (필드 추가)"""
        changed = False

        # section 필드
        if 'section' not in watcher:
            watcher['section'] = 'uncategorized'
            changed = True

        # display_order 필드
        if 'display_order' not in watcher:
            watcher['display_order'] = 9999
            changed = True

        # note 필드
        if 'note' not in watcher:
            watcher['note'] = ''
            changed = True

        # record_id 필드
        if 'record_id' not in watcher:
            today = datetime.now().strftime('%y%m%d')
            watcher['record_id'] = f"{today}-{watcher['code']}"
            changed = True

        # monitoring_status 필드
        if 'monitoring_status' not in watcher:
            watcher['monitoring_status'] = ''
            changed = True

        # 구역 필드
        for field, default in [('zone', 0), ('zone_entered_at', None), ('zone_transitions', {})]:
            if field not in watcher:
                watcher[field] = default
                changed = True

        return changed

    def _save_watchers(self):
        """감시 리스트 저장"""
        try:
            tmp_file = MODE2_FILE + ".tmp"
            data = {
                'sections': self.sections,
                'watchers': self.watchers
            }
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_file, MODE2_FILE)
            logger.info(f"Mode2 감시 리스트 저장 완료: {len(self.watchers)}개 종목, {len(self.sections)}개 섹션")
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

        today = datetime.now().strftime('%y%m%d')

        watcher = {
            "code": code,
            "name": data.get("name", ""),  # 종목명은 추후 API로 조회
            "mode": "mode2",
            "record_id": f"{today}-{code}",  # 260426-005930
            "section": data.get("section", "uncategorized"),  # 섹션 ID
            "display_order": data.get("display_order", 9999),  # 섹션 내 순서
            "note": data.get("note", "")[:500],  # 자유노트 (최대 500자)
            "monitoring_status": "",  # 모니터링 상태 (실시간 업데이트)
            "zone": 0,               # 현재 구역 (1~5)
            "zone_entered_at": None, # 현재 구역 진입 시각
            "zone_transitions": {},  # 인접 구역 왕복 카운트 {"3-4": 2, "4-5": 1, ...}
            "buy_target_price": buy_target_price,
            "budget": budget,
            "quantity": quantity,
            "resistance_1_price": data.get("resistance_1_price", 0),
            "resistance_1_profit_pct": data.get("resistance_1_profit_pct", 0),
            "resistance_2_price": data.get("resistance_2_price", 0),
            "resistance_2_profit_pct": data.get("resistance_2_profit_pct", 0),
            "support_1_price": data.get("support_1_price", 0),
            "support_1_mode": data.get("support_1_mode", "손절"),  # "손절" | "물타기"
            "support_1_loss_pct": data.get("support_1_loss_pct", 0),
            "support_1_add_budget": data.get("support_1_add_budget", 0),  # 물타기 추가 예산 (원)
            "support_2_price": data.get("support_2_price", 0),
            # 물타기 모드면 2차 지지 기본값 100%, 명시적으로 입력 시 override 가능
            "support_2_loss_pct": data.get("support_2_loss_pct", 100 if data.get("support_1_mode") == "물타기" else 0),
            "polling_interval": data.get("polling_interval", 30 if not data.get("notify_only") else 180),  # 자동:30초, 알림:3분
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

        # 변경사항 감지를 위한 비교 필드
        tracked_fields = [
            'buy_target_price', 'budget', 'resistance_1_price', 'resistance_1_profit_pct',
            'resistance_2_price', 'resistance_2_profit_pct', 'support_1_price', 'support_1_mode',
            'support_1_loss_pct', 'support_1_add_budget', 'support_2_price', 'support_2_loss_pct',
            'polling_interval', 'notify_only', 'note', 'auto_paused'
        ]

        has_changes = False
        changed_fields = []
        for field in tracked_fields:
            if field in data:
                old_value = watcher.get(field)
                new_value = data[field]
                # note 길이 제한 적용
                if field == 'note':
                    new_value = new_value[:500]
                    data[field] = new_value
                if old_value != new_value:
                    has_changes = True
                    changed_fields.append((field, old_value, new_value))

        # 매수 타점 또는 예산 변경 시 수량 재계산
        if "buy_target_price" in data or "budget" in data:
            buy_price = data.get("buy_target_price", watcher["buy_target_price"])
            budget = data.get("budget", watcher["budget"])
            data["quantity"] = budget // buy_price if buy_price > 0 else 0

        # notify_only 변경 시 polling_interval 기본값 자동 변경
        if "notify_only" in data and "polling_interval" not in data:
            data["polling_interval"] = 180 if data["notify_only"] else 30

        # 물타기 모드로 전환 시 support_2_loss_pct 미입력이면 100% 기본값 적용
        s1_mode = data.get("support_1_mode", watcher.get("support_1_mode", "손절"))
        if s1_mode == "물타기" and "support_2_loss_pct" not in data:
            data["support_2_loss_pct"] = 100

        # 필드 업데이트
        watcher.update(data)
        watcher["updated_at"] = datetime.now().isoformat()

        # record_id 갱신 (실제 변경사항이 있고 날짜가 바뀐 경우에만)
        if has_changes:
            kst_now = datetime.now(ZoneInfo("Asia/Seoul")).strftime('%Y-%m-%d %H:%M:%S KST')
            for field, old_val, new_val in changed_fields:
                logger.info(f"Mode2 필드 변경 [{kst_now}]: {code} ({watcher.get('name', '')}) | {field}: {old_val!r} → {new_val!r}")

            today = datetime.now().strftime('%y%m%d')
            current_record_id = watcher.get("record_id", "")
            current_date = current_record_id.split('-')[0] if '-' in current_record_id else ""

            if current_date != today:
                watcher["record_id"] = f"{today}-{code}"
                logger.info(f"Mode2 업데이트 (record_id 갱신): {code} ({current_date} → {today})")
            else:
                logger.info(f"Mode2 업데이트: {code} (record_id 유지: {watcher['record_id']})")
        else:
            logger.info(f"Mode2 업데이트: {code} (변경사항 없음, record_id 유지)")

        self._save_watchers()
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

    def record_add_buy(self, code: str, price: float, quantity: int) -> bool:
        """물타기(추가매수) 체결 기록 — 평균단가 재계산"""
        if code not in self.watchers:
            return False

        watcher = self.watchers[code]
        prev_qty = watcher.get('bought_quantity', 0)
        prev_price = watcher.get('bought_price', 0)

        new_qty = prev_qty + quantity
        avg_price = round((prev_price * prev_qty + price * quantity) / new_qty) if new_qty > 0 else price

        watcher.update({
            "bought_price": avg_price,
            "bought_quantity": new_qty,
            "updated_at": datetime.now().isoformat(),
        })
        if 'support_1' not in watcher.get('sold_history', []):
            watcher.setdefault('sold_history', []).append('support_1')

        self._save_watchers()
        logger.info(f"Mode2 물타기 기록: {code} @ {price:,}원 x {quantity}주 → 평균단가 {avg_price:,}원, 총 {new_qty}주")
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

    # ========== 섹션 관리 ==========

    def add_section(self, name: str) -> Dict:
        """섹션 추가"""
        section_id = f"section_{len(self.sections) + 1}_{int(datetime.now().timestamp())}"
        max_order = max([s['order'] for s in self.sections], default=0)

        section = {
            'id': section_id,
            'name': name,
            'order': max_order + 1,
            'collapsed': False
        }

        self.sections.append(section)
        self._save_watchers()
        logger.info(f"섹션 추가: {name} (id: {section_id})")
        return section

    def update_section(self, section_id: str, name: str) -> bool:
        """섹션명 변경"""
        for section in self.sections:
            if section['id'] == section_id:
                section['name'] = name
                self._save_watchers()
                logger.info(f"섹션명 변경: {section_id} -> {name}")
                return True
        return False

    def delete_section(self, section_id: str) -> bool:
        """섹션 삭제 (종목은 미분류로 이동)"""
        # 해당 섹션의 종목들을 미분류로 이동
        for code, watcher in self.watchers.items():
            if watcher.get('section') == section_id:
                watcher['section'] = 'uncategorized'

        # 섹션 삭제
        self.sections = [s for s in self.sections if s['id'] != section_id]
        self._save_watchers()
        logger.info(f"섹션 삭제: {section_id}")
        return True

    def reorder_sections(self, section_orders: List[Dict]) -> bool:
        """섹션 순서 변경

        Args:
            section_orders: [{'id': 'section_1', 'order': 1}, ...]
        """
        order_map = {item['id']: item['order'] for item in section_orders}

        for section in self.sections:
            if section['id'] in order_map:
                section['order'] = order_map[section['id']]

        self.sections.sort(key=lambda s: s['order'])
        self._save_watchers()
        logger.info(f"섹션 순서 변경 완료")
        return True

    def toggle_section_collapsed(self, section_id: str) -> bool:
        """섹션 접기/펴기"""
        for section in self.sections:
            if section['id'] == section_id:
                section['collapsed'] = not section.get('collapsed', False)
                self._save_watchers()
                logger.info(f"섹션 토글: {section_id} -> {'접힘' if section['collapsed'] else '펼침'}")
                return True
        return False

    def move_watcher_to_section(self, code: str, section_id: str) -> bool:
        """종목을 다른 섹션으로 이동"""
        if code not in self.watchers:
            return False

        self.watchers[code]['section'] = section_id
        self.watchers[code]['updated_at'] = datetime.now().isoformat()
        self._save_watchers()
        logger.info(f"종목 이동: {code} -> {section_id}")
        return True

    def reorder_watchers_in_section(self, section_id: str, watcher_orders: List[Dict]) -> bool:
        """섹션 내 종목 순서 변경

        Args:
            section_id: 섹션 ID
            watcher_orders: [{'code': '005930', 'display_order': 1}, ...]
        """
        order_map = {item['code']: item['display_order'] for item in watcher_orders}

        for code, watcher in self.watchers.items():
            if watcher.get('section') == section_id and code in order_map:
                watcher['display_order'] = order_map[code]

        self._save_watchers()
        logger.info(f"종목 순서 변경 완료: {section_id}")
        return True

    def update_monitoring_status(self, code: str, status: str) -> bool:
        """모니터링 상태 업데이트 (실시간)"""
        if code not in self.watchers:
            return False

        old_status = self.watchers[code].get('monitoring_status', '')
        self.watchers[code]['monitoring_status'] = status

        if old_status != status and status:
            logger.info(f"모니터링 상태 변경: {code} -> {status}")

        # 메모리에만 저장 (디스크 I/O 최소화)
        return True

    def update_zone(self, code: str, new_zone: int) -> bool:
        """구역 업데이트 — 진입 시각 및 인접 구역 왕복 카운트 관리"""
        if code not in self.watchers:
            return False

        watcher = self.watchers[code]
        old_zone = watcher.get('zone', 0)

        if old_zone == new_zone:
            return False

        now_iso = datetime.now().isoformat()

        # 인접 구역 왕복 카운트 (3↔4, 4↔5, 2↔3, 1↔2)
        if old_zone > 0 and abs(old_zone - new_zone) == 1:
            pair = f"{min(old_zone, new_zone)}-{max(old_zone, new_zone)}"
            transitions = watcher.get('zone_transitions', {})
            transitions[pair] = transitions.get(pair, 0) + 1
            watcher['zone_transitions'] = transitions

        watcher['zone'] = new_zone
        watcher['zone_entered_at'] = now_iso
        logger.info(f"구역 변경: {code} {old_zone}→{new_zone}")
        return True

    def get_or_create_stopped_section(self) -> str:
        """'모니터링 중지' 섹션 ID 조회 또는 생성"""
        for s in self.sections:
            if s.get('name') == '모니터링 중지':
                return s['id']
        # 없으면 맨 마지막 순서로 생성
        section = self.add_section('모니터링 중지')
        return section['id']

    def get_all_sections(self) -> List[Dict]:
        """모든 섹션 조회"""
        return sorted(self.sections, key=lambda s: s['order'])

    def get_watchers_by_section(self, section_id: str) -> List[Dict]:
        """특정 섹션의 종목 리스트 조회"""
        watchers = [
            watcher for code, watcher in self.watchers.items()
            if watcher.get('section') == section_id
        ]
        return sorted(watchers, key=lambda w: w.get('display_order', 9999))
