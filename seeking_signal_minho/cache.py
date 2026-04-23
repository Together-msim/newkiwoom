"""
파일 기반 캐싱 레이어 (TTL 5일)
"""
import json
import pickle
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Any
import hashlib

from .config import CACHE_DIR, CACHE_TTL_DAYS


class DataCache:
    """간단한 파일 기반 캐시 (5일 TTL)"""

    def __init__(self, cache_dir: Path = CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_key(self, stock_code: str, data_type: str, **kwargs) -> str:
        """캐시 키 생성 (종목코드 + 데이터타입 + 파라미터)"""
        params_str = json.dumps(kwargs, sort_keys=True)
        key = f"{stock_code}_{data_type}_{params_str}"
        return hashlib.md5(key.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """캐시 파일 경로"""
        return self.cache_dir / f"{cache_key}.pkl"

    def get(self, stock_code: str, data_type: str, **kwargs) -> Optional[Any]:
        """캐시에서 데이터 조회"""
        cache_key = self._get_cache_key(stock_code, data_type, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            return None

        # TTL 체크
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        if datetime.now() - mtime > timedelta(days=CACHE_TTL_DAYS):
            # 만료된 캐시 삭제
            cache_path.unlink()
            return None

        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None

    def set(self, stock_code: str, data_type: str, data: Any, **kwargs):
        """캐시에 데이터 저장"""
        cache_key = self._get_cache_key(stock_code, data_type, **kwargs)
        cache_path = self._get_cache_path(cache_key)

        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"Cache write failed: {e}")

    def clear_expired(self):
        """만료된 캐시 파일 삭제"""
        now = datetime.now()
        for cache_file in self.cache_dir.glob("*.pkl"):
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if now - mtime > timedelta(days=CACHE_TTL_DAYS):
                cache_file.unlink()

    def clear_all(self):
        """모든 캐시 삭제"""
        for cache_file in self.cache_dir.glob("*.pkl"):
            cache_file.unlink()


# 싱글톤 인스턴스
_cache = DataCache()

def get_cache() -> DataCache:
    """캐시 인스턴스 반환"""
    return _cache
