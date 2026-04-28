# keyword_config.py
"""키워드 파일 경로 설정 모듈"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

ROOT_DIR = Path(__file__).resolve().parent


def resolve_keywords_path() -> Path:
    """기존 단일 keywords.json 경로 (하위호환)."""
    env_path = os.getenv("KEYWORDS_JSON_PATH")
    if env_path:
        return Path(env_path).resolve()
    return (ROOT_DIR / ".data" / "keywords.json").resolve()


def resolve_news_keywords_path() -> Path:
    """뉴스 채널 전용 키워드 파일 경로."""
    env_path = os.getenv("NEWS_KEYWORDS_JSON_PATH")
    if env_path:
        return Path(env_path).resolve()
    return (ROOT_DIR / ".data" / "news_keywords.json").resolve()


def resolve_hotstock_keywords_path() -> Path:
    """급등주 채널 전용 키워드 파일 경로."""
    env_path = os.getenv("HOTSTOCK_KEYWORDS_JSON_PATH")
    if env_path:
        return Path(env_path).resolve()
    return (ROOT_DIR / ".data" / "hotstock_keywords.json").resolve()
