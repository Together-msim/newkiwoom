# keyword_storage.py
"""키워드 저장소 관리"""

import json
import os
import logging
from pathlib import Path
from typing import List, Set
import portalocker

logger = logging.getLogger(__name__)


class KeywordStorage:
    """키워드 저장소 (JSON 기반)"""
    
    def __init__(self, storage_path: str):
        """
        Args:
            storage_path: 키워드 저장 파일 경로
        """
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_file()
    
    def _init_file(self):
        """파일이 없으면 초기화"""
        if not self.storage_path.exists():
            logger.info(f"📝 keywords.json 파일이 없어 새로 생성합니다: {self.storage_path.resolve()}")
            default_data = {
                "include_keywords": [],
                "include_groups": [],
                "exclude_keywords": [],
                "mode": "loose"  # loose: 하나라도 포함, strict: 모두 포함
            }
            self._write_locked(default_data)
            logger.info(f"✅ keywords.json 파일 생성 완료: {self.storage_path.resolve()}")
        else:
            logger.debug(f"📁 keywords.json 파일 확인됨: {self.storage_path.resolve()}")
    
    def _read_locked(self) -> dict:
        """파일을 잠금하여 읽기"""
        try:
            if not self.storage_path.exists():
                logger.warning(f"⚠️ keywords.json 파일을 찾을 수 없습니다: {self.storage_path.resolve()}")
                return {
                    "include_keywords": [],
                    "include_groups": [],
                    "exclude_keywords": [],
                    "mode": "loose"
                }
            with portalocker.Lock(self.storage_path, "r", timeout=5, encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"❌ keywords.json 파일 파싱 실패: {self.storage_path.resolve()} - {e}")
            return {
                "include_keywords": [],
                "include_groups": [],
                "exclude_keywords": [],
                "mode": "loose"
            }
        except Exception as e:
            logger.error(f"❌ keywords.json 파일 읽기 실패: {self.storage_path.resolve()} - {e}")
            return {
                "include_keywords": [],
                "include_groups": [],
                "exclude_keywords": [],
                "mode": "loose"
            }
    
    def _write_locked(self, data: dict):
        """파일을 잠금하여 atomic write (os.replace 사용)"""
        # 임시 파일 경로 생성
        tmp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
        
        try:
            # 임시 파일에 쓰기 (lock 사용)
            with portalocker.Lock(tmp_path, "w", timeout=5, encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # Atomic replace: 임시 파일을 원본 파일로 교체
            # os.replace는 atomic operation (POSIX에서 rename은 atomic)
            os.replace(tmp_path, self.storage_path)
        except Exception as e:
            # 오류 발생 시 임시 파일 정리
            if tmp_path.exists():
                try:
                    tmp_path.unlink()
                except Exception:
                    pass
            raise
    
    def add_include_keyword(self, keyword: str) -> bool:
        """Include 키워드 추가"""
        data = self._read_locked()
        keywords = list(data.get("include_keywords", []))
        if keyword.lower() not in [k.lower() for k in keywords]:
            keywords.append(keyword)
            data["include_keywords"] = keywords
            self._write_locked(data)
            return True
        return False

    def remove_include_keyword(self, keyword: str) -> bool:
        """Include 키워드 제거"""
        data = self._read_locked()
        keywords = data.get("include_keywords", [])
        new_kws = [k for k in keywords if k.lower() != keyword.lower()]
        if len(new_kws) < len(keywords):
            data["include_keywords"] = new_kws
            self._write_locked(data)
            return True
        return False

    def set_include_keywords(self, keywords: List[str]) -> bool:
        """Include 키워드 전체 교체 (bulk set)"""
        data = self._read_locked()
        data["include_keywords"] = [k.strip() for k in keywords if k.strip()]
        self._write_locked(data)
        return True

    def add_exclude_keyword(self, keyword: str) -> bool:
        """Exclude 키워드 추가"""
        data = self._read_locked()
        keywords = list(data.get("exclude_keywords", []))
        if keyword.lower() not in [k.lower() for k in keywords]:
            keywords.append(keyword)
            data["exclude_keywords"] = keywords
            self._write_locked(data)
            return True
        return False

    def remove_exclude_keyword(self, keyword: str) -> bool:
        """Exclude 키워드 제거"""
        data = self._read_locked()
        keywords = data.get("exclude_keywords", [])
        new_kws = [k for k in keywords if k.lower() != keyword.lower()]
        if len(new_kws) < len(keywords):
            data["exclude_keywords"] = new_kws
            self._write_locked(data)
            return True
        return False

    def set_exclude_keywords(self, keywords: List[str]) -> bool:
        """Exclude 키워드 전체 교체 (bulk set)"""
        data = self._read_locked()
        data["exclude_keywords"] = [k.strip() for k in keywords if k.strip()]
        self._write_locked(data)
        return True
    
    def get_include_keywords(self) -> List[str]:
        """Include 키워드 목록 조회"""
        data = self._read_locked()
        return data.get("include_keywords", [])
    
    def get_exclude_keywords(self) -> List[str]:
        """Exclude 키워드 목록 조회"""
        data = self._read_locked()
        return data.get("exclude_keywords", [])
    
    def set_mode(self, mode: str) -> bool:
        """필터링 모드 설정 (strict 또는 loose)"""
        if mode not in ["strict", "loose"]:
            return False
        data = self._read_locked()
        data["mode"] = mode
        self._write_locked(data)
        return True
    
    def get_mode(self) -> str:
        """필터링 모드 조회"""
        data = self._read_locked()
        return data.get("mode", "loose")
    
    def get_all(self) -> dict:
        """전체 설정 조회"""
        return self._read_locked()
    
    def add_include_group(self, group: List[str]) -> bool:
        """
        Include 그룹 추가 (AND 조건 그룹)
        
        Args:
            group: 키워드 리스트 (예: ["삼성전자", "반도체"])
        
        Returns:
            True면 추가됨, False면 이미 존재함
        """
        data = self._read_locked()
        groups = data.get("include_groups", [])
        
        # 그룹을 정규화 (소문자, 정렬)하여 중복 체크
        normalized_group = sorted([kw.lower() for kw in group if kw.strip()])
        if not normalized_group:
            return False
        
        # 기존 그룹들과 비교 (순서 무관하게 비교)
        for existing_group in groups:
            if sorted([kw.lower() for kw in existing_group]) == normalized_group:
                return False  # 이미 존재
        
        # 새 그룹 추가
        groups.append([kw.strip() for kw in group if kw.strip()])
        data["include_groups"] = groups
        self._write_locked(data)
        return True
    
    def remove_include_group(self, group: List[str]) -> bool:
        """
        Include 그룹 제거
        
        Args:
            group: 키워드 리스트 (예: ["삼성전자", "반도체"])
        
        Returns:
            True면 제거됨, False면 찾을 수 없음
        """
        data = self._read_locked()
        groups = data.get("include_groups", [])
        
        # 정규화된 그룹
        normalized_group = sorted([kw.lower() for kw in group if kw.strip()])
        if not normalized_group:
            return False
        
        # 기존 그룹에서 찾아서 제거
        for i, existing_group in enumerate(groups):
            if sorted([kw.lower() for kw in existing_group]) == normalized_group:
                groups.pop(i)
                data["include_groups"] = groups
                self._write_locked(data)
                return True
        
        return False
    
    def get_include_groups(self) -> List[List[str]]:
        """Include 그룹 목록 조회"""
        data = self._read_locked()
        return data.get("include_groups", [])
    
    def reset(self) -> bool:
        """
        모든 키워드 필터링 설정을 초기값으로 리셋
        
        Returns:
            True (항상 성공)
        """
        default_data = {
            "include_keywords": [],
            "include_groups": [],
            "exclude_keywords": [],
            "mode": "loose",
            "enabled": True
        }
        self._write_locked(default_data)
        return True
