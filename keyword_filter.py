# keyword_filter.py
"""키워드 필터링 로직"""

import hashlib
import logging
import os
import threading
from typing import Optional, List, Set, Dict, Tuple
from keyword_storage import KeywordStorage

logger = logging.getLogger(__name__)

# 키워드 별칭 매핑 (더 유연한 매칭을 위해)
KEYWORD_ALIASES = {
    "현대차": ["현대", "현대자동차", "hyundai"],
    "삼성전자": ["삼성", "samsung"],
    "머스크": ["엘론", "일론", "elon", "musk", "엘론 머스크", "일론 머스크"],
    "스페이스x": ["spacex", "스페이스 엑스", "스페이스X", "SpaceX"],
}


class KeywordFilter:
    """키워드 필터링 클래스"""
    
    def __init__(self, keyword_storage: KeywordStorage, message_hash_path: str):
        """
        Args:
            keyword_storage: KeywordStorage 인스턴스
            message_hash_path: 메시지 hash 저장 파일 경로
        """
        self.keyword_storage = keyword_storage
        self.message_hash_path = message_hash_path
        # --- Forwarding routing config (env-based) ---
        # SOURCE_CHAT_IDS: comma-separated list of source chat ids
        # SOURCE_DEST_MAPPING: comma-separated pairs source:dest (e.g. -1001:-2001,-1002:-2002)
        # DEST_CHAT_ID: default destination if no per-source mapping exists
        self.source_chat_ids, self.source_dest_mapping, self.default_dest_chat_id = self._load_routing_from_env()
        self._load_message_hashes()
        # 키워드 파일의 마지막 수정 시간 저장 (핫리로드용)
        self._last_keywords_mtime = self._get_keywords_file_mtime()
        # 캐시된 키워드 데이터 (핫리로드 성능 최적화)
        self._cached_include_keywords = None
        self._cached_include_groups = None
        self._cached_exclude_keywords = None
        self._cached_mode = None
        self._cached_all_settings = None
        # Thread-safe를 위한 lock
        self._config_lock = threading.RLock()  # RLock 사용 (같은 스레드에서 재진입 가능)
        # 초기 로드
        self._reload_keywords()
    
    def _parse_int_list(self, raw: str) -> List[int]:
        """Parse comma-separated integers safely."""
        if not raw:
            return []
        out: List[int] = []
        for part in raw.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                out.append(int(part))
            except ValueError:
                logger.warning(f"환경 변수 숫자 파싱 실패(무시): '{part}'")
        return out

    def _load_routing_from_env(self) -> Tuple[List[int], Dict[int, int], Optional[int]]:
        """Load routing settings from environment variables."""
        source_ids_raw = str(os.getenv("SOURCE_CHAT_IDS", "")).strip()
        mapping_raw = str(os.getenv("SOURCE_DEST_MAPPING", "")).strip()
        default_dest_raw = str(os.getenv("DEST_CHAT_ID", "")).strip()

        source_chat_ids = self._parse_int_list(source_ids_raw)

        source_dest_mapping: Dict[int, int] = {}
        if mapping_raw:
            for pair in mapping_raw.split(","):
                pair = pair.strip()
                if not pair:
                    continue
                if ":" not in pair:
                    logger.warning(f"SOURCE_DEST_MAPPING 형식 오류(무시): '{pair}'")
                    continue
                left, right = pair.split(":", 1)
                left = left.strip()
                right = right.strip()
                try:
                    src = int(left)
                    dst = int(right)
                    source_dest_mapping[src] = dst
                except ValueError:
                    logger.warning(f"SOURCE_DEST_MAPPING 숫자 파싱 실패(무시): '{pair}'")

        default_dest_chat_id: Optional[int] = None
        if default_dest_raw:
            try:
                default_dest_chat_id = int(default_dest_raw)
            except ValueError:
                logger.warning(f"DEST_CHAT_ID 숫자 파싱 실패(무시): '{default_dest_raw}'")

        return source_chat_ids, source_dest_mapping, default_dest_chat_id

    def resolve_destination(self, source_chat_id: int) -> Optional[int]:
        """Resolve destination chat id for a given source chat id."""
        if source_chat_id in self.source_dest_mapping:
            return self.source_dest_mapping[source_chat_id]
        return self.default_dest_chat_id

    def _get_keywords_file_mtime(self) -> float:
        """keywords.json 파일의 마지막 수정 시간 반환"""
        try:
            keywords_path = self.keyword_storage.storage_path
            if keywords_path.exists():
                return keywords_path.stat().st_mtime
            return 0.0
        except Exception:
            return 0.0
    
    def _reload_keywords(self):
        """키워드 데이터 리로드 (캐시 업데이트) - 내부용, lock 없이 호출"""
        try:
            all_settings = self.keyword_storage.get_all()
            include_keywords = all_settings.get("include_keywords", [])
            include_groups = all_settings.get("include_groups", [])
            exclude_keywords = all_settings.get("exclude_keywords", [])
            mode = all_settings.get("mode", "loose")
            
            # Atomic swap: 새 데이터를 준비한 후 한 번에 교체
            with self._config_lock:
                self._cached_all_settings = all_settings
                self._cached_include_keywords = include_keywords
                self._cached_include_groups = include_groups
                self._cached_exclude_keywords = exclude_keywords
                self._cached_mode = mode
        except Exception as e:
            logger.error(f"키워드 리로드 실패: {e}", exc_info=True)
    
    def reload_if_changed(self) -> bool:
        """
        keywords.json 파일이 변경되었는지 확인하고, 변경되었으면 리로드
        
        Returns:
            True면 리로드됨, False면 변경 없음
        """
        try:
            current_mtime = self._get_keywords_file_mtime()
            # mtime 체크는 lock 밖에서 (성능 최적화)
            if current_mtime != self._last_keywords_mtime:
                # 리로드 시에만 lock 사용
                logger.info("🔁 keywords.json 변경 감지 → 리로드 완료")
                self._reload_keywords()
                with self._config_lock:
                    self._last_keywords_mtime = current_mtime
                return True
            return False
        except Exception as e:
            logger.error(f"키워드 변경 감지 실패: {e}", exc_info=True)
            return False
    
    def _load_message_hashes(self) -> set:
        """메시지 hash 목록 로드"""
        try:
            with open(self.message_hash_path, "r", encoding="utf-8") as f:
                return set(line.strip() for line in f if line.strip())
        except FileNotFoundError:
            return set()
    
    def _save_message_hash(self, message_hash: str):
        """메시지 hash 저장"""
        hashes = self._load_message_hashes()
        hashes.add(message_hash)
        with open(self.message_hash_path, "w", encoding="utf-8") as f:
            for h in hashes:
                f.write(h + "\n")
    
    def _get_message_hash(self, chat_id: int, message_id: int, text: str) -> str:
        """메시지 hash 생성"""
        content = f"{chat_id}:{message_id}:{text}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()
    
    def _expand_keyword_variants(self, keyword: str) -> Set[str]:
        """
        키워드의 모든 변형을 반환 (원본 + 별칭)
        
        Args:
            keyword: 원본 키워드
        
        Returns:
            키워드 변형 집합 (소문자로 정규화)
        """
        keyword_lower = keyword.lower()
        variants = {keyword_lower}
        
        # 별칭 매핑에서 직접 찾기
        if keyword_lower in KEYWORD_ALIASES:
            for alias in KEYWORD_ALIASES[keyword_lower]:
                variants.add(alias.lower())
        
        # 역방향 검색: 별칭 중 하나가 원본 키워드와 일치하는 경우
        for main_keyword, aliases in KEYWORD_ALIASES.items():
            aliases_lower = [a.lower() for a in aliases]
            if keyword_lower in aliases_lower:
                # 별칭이 매칭되면 메인 키워드와 모든 별칭 추가
                variants.add(main_keyword.lower())
                variants.update(aliases_lower)
        
        return variants
    
    def _match_keyword(self, keyword: str, text_lower: str) -> bool:
        """
        키워드가 텍스트에 포함되는지 확인 (별칭 포함)
        
        Args:
            keyword: 검색할 키워드
            text_lower: 소문자로 변환된 텍스트
        
        Returns:
            매칭 여부
        """
        variants = self._expand_keyword_variants(keyword)
        for variant in variants:
            if variant in text_lower:
                return True
        return False
    
    def should_forward(self, chat_id: int, message_id: int, text: str) -> bool:
        """
        메시지를 전송해야 하는지 판단
        
        Args:
            chat_id: 채널 ID
            message_id: 메시지 ID
            text: 메시지 텍스트
        
        Returns:
            True면 전송, False면 무시
        """
        if not text:
            return False
        
        # 핫리로드: keywords.json 변경 감지 및 리로드
        self.reload_if_changed()
        
        # Thread-safe: config 읽기 시 lock 보호
        with self._config_lock:
            all_settings = self._cached_all_settings
            include_keywords = self._cached_include_keywords
            include_groups = self._cached_include_groups
            exclude_keywords = self._cached_exclude_keywords
            mode = self._cached_mode
        
        # None 체크 및 기본값 설정
        if all_settings is None:
            all_settings = {}
        if exclude_keywords is None:
            exclude_keywords = []
        if include_keywords is None:
            include_keywords = []
        if include_groups is None:
            include_groups = []
        if mode is None:
            mode = "loose"
        
        # enabled 플래그 체크 (캐시된 데이터 사용)
        if not all_settings.get("enabled", True):
            logger.debug("필터링이 비활성화되어 있습니다 (enabled=false)")
            return False
        
        # 중복 체크
        message_hash = self._get_message_hash(chat_id, message_id, text)
        existing_hashes = self._load_message_hashes()
        if message_hash in existing_hashes:
            logger.debug(f"중복 메시지 필터링: {text[:50]}...")
            return False
        
        text_lower = text.lower()
        
        # Exclude 키워드 체크 (하나라도 있으면 제외)
        for keyword in exclude_keywords:
            if self._match_keyword(keyword, text_lower):
                logger.debug(f"Exclude 키워드로 필터링: '{keyword}' in '{text[:50]}...'")
                return False
        
        # Include 키워드와 Include 그룹이 모두 없으면 모든 메시지 통과
        if not include_keywords and not include_groups:
            self._save_message_hash(message_hash)
            logger.debug("Include 키워드와 그룹이 없어 모든 메시지 통과")
            return True
        
        matched_keywords = []
        matched_groups = []
        
        # 1. Include 키워드 체크 (OR 조건)
        include_keywords_matched = False
        if include_keywords:
            if mode == "strict":
                # 모든 키워드가 포함되어야 함
                all_matched = True
                for keyword in include_keywords:
                    if self._match_keyword(keyword, text_lower):
                        matched_keywords.append(keyword)
                    else:
                        all_matched = False
                include_keywords_matched = all_matched
            else:  # loose
                # 하나라도 포함되면 됨
                for keyword in include_keywords:
                    if self._match_keyword(keyword, text_lower):
                        matched_keywords.append(keyword)
                        include_keywords_matched = True
                        break
        
        # 2. Include 그룹 체크 (그룹 내 AND, 그룹 간 OR)
        include_groups_matched = False
        if include_groups:
            for group in include_groups:
                # 그룹 내 모든 키워드가 포함되어야 함 (AND 조건)
                group_matched = True
                matched_group_keywords = []
                for keyword in group:
                    if self._match_keyword(keyword, text_lower):
                        matched_group_keywords.append(keyword)
                    else:
                        group_matched = False
                        break
                
                if group_matched:
                    # 이 그룹이 매칭됨
                    include_groups_matched = True
                    matched_groups.append(group)
                    break  # 그룹 간은 OR이므로 하나만 매칭되면 됨
        
        # 3. 최종 판단: include_keywords 또는 include_groups 중 하나라도 만족하면 통과
        if include_keywords_matched or include_groups_matched:
            self._save_message_hash(message_hash)
            match_info = []
            if matched_keywords:
                match_info.append(f"키워드: {matched_keywords}")
            if matched_groups:
                match_info.append(f"그룹: {matched_groups}")
            logger.info(f"✅ 메시지 통과 ({', '.join(match_info)}): {text[:50]}...")
            return True
        else:
            logger.debug(f"필터링됨: include_keywords={include_keywords_matched}, include_groups={include_groups_matched}: {text[:50]}...")
            return False

    def should_forward_to(self, chat_id: int, message_id: int, text: str) -> Optional[int]:
        """Return destination chat_id if the message should be forwarded; otherwise None."""
        if not self.should_forward(chat_id, message_id, text):
            return None
        return self.resolve_destination(chat_id)
