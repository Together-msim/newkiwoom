# keyword_config.py
"""키워드 파일 경로 설정 모듈"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# newkiwoom 프로젝트 루트 = 이 파일이 있는 디렉토리
ROOT_DIR = Path(__file__).resolve().parent


def resolve_keywords_path() -> Path:
    """
    keywords.json 파일 경로를 결정합니다.

    우선순위:
    1. KEYWORDS_JSON_PATH 환경변수
    2. 기본값: {ROOT_DIR}/.data/keywords.json
    """
    env_path = os.getenv("KEYWORDS_JSON_PATH")
    if env_path:
        resolved = Path(env_path).resolve()
        logger.debug(f"KEYWORDS_JSON_PATH 환경변수 사용: {resolved}")
        return resolved

    default_path = ROOT_DIR / ".data" / "keywords.json"
    logger.debug(f"기본 경로 사용: {default_path.resolve()}")
    return default_path.resolve()
