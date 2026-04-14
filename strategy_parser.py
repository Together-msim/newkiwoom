"""
자연어 명령어 파싱
"""
import re
from typing import Optional, Dict


def parse_natural_language(text: str) -> Optional[Dict]:
    """
    자연어 명령어 파싱

    지원 명령어:
    - "종목코드(000660) 삭제"
    - "종목코드(005930) 수정"
    - "감시 중인 종목 알려줘"
    - "리스트 보여줘"

    Args:
        text: 입력 텍스트

    Returns:
        파싱 결과 또는 None
    """
    text = text.strip()

    # 삭제 명령어 패턴
    # "종목코드(000660) 삭제", "000660 삭제", "종목 000660 삭제"
    delete_patterns = [
        r'종목코드\s*\(?\s*(\d{6})\s*\)?\s*삭제',
        r'(\d{6})\s*삭제',
        r'종목\s+(\d{6})\s*삭제',
    ]

    for pattern in delete_patterns:
        match = re.search(pattern, text)
        if match:
            return {
                "action": "delete",
                "code": match.group(1),
            }

    # 수정 명령어 패턴
    # "종목코드(005930) 수정", "005930 수정"
    modify_patterns = [
        r'종목코드\s*\(?\s*(\d{6})\s*\)?\s*수정',
        r'(\d{6})\s*수정',
        r'종목\s+(\d{6})\s*수정',
    ]

    for pattern in modify_patterns:
        match = re.search(pattern, text)
        if match:
            return {
                "action": "modify",
                "code": match.group(1),
            }

    # 리스트 조회 명령어
    list_keywords = [
        "감시 중인 종목",
        "감시중인 종목",
        "감시 리스트",
        "리스트 보여줘",
        "리스트 알려줘",
        "종목 리스트",
        "종목 확인",
    ]

    for keyword in list_keywords:
        if keyword in text:
            return {
                "action": "list",
            }

    # 파싱 실패
    return None


def parse_tactic1_config(args: list) -> Optional[Dict]:
    """
    Tactic1 설정 파싱

    입력 예시:
    - ["005930"]
    - ["005930,000660"]
    - ["005930", "기준봉=1분", "손절=-5%", "익절=7%"]

    Returns:
        {
            "codes": ["005930", "000660"],
            "config": {...}
        }
    """
    if not args:
        return None

    # 첫 번째 인자는 종목코드 (쉼표로 구분 가능)
    codes_str = args[0]
    codes = [c.strip() for c in codes_str.split(',')]

    # 기본 설정
    config = {}

    # 나머지 인자는 설정 (key=value 형식)
    for arg in args[1:]:
        if '=' not in arg:
            continue

        key, value = arg.split('=', 1)
        key = key.strip()
        value = value.strip()

        # 값 파싱
        if key == "기준봉":
            config["기준봉"] = value
        elif key == "손절":
            # "-5%" 또는 "9500" 형식
            if '%' in value:
                config["최대_손실_퍼센트"] = abs(float(value.replace('%', '')))
            else:
                config["손절라인"] = int(value)
        elif key == "익절":
            # "7%" 형식
            if '%' in value:
                config["기대_수익률_퍼센트"] = float(value.replace('%', ''))
        elif key == "익절비중":
            # "50%" 형식
            if '%' in value:
                config["익절_비중_퍼센트"] = float(value.replace('%', ''))

    return {
        "codes": codes,
        "config": config,
    }


def parse_tactic2_config(args: list) -> Optional[Dict]:
    """
    Tactic2 설정 파싱

    입력 예시:
    - ["005930", "70000", "10", "68000", "10"]

    Returns:
        {
            "code": "005930",
            "config": {
                "1차_매수가": 70000,
                "1차_수량": 10,
                "2차_지지선": 68000,
                "2차_수량": 10,
            }
        }
    """
    if len(args) < 5:
        return None

    try:
        code = args[0]
        config = {
            "1차_매수가": int(args[1]),
            "1차_수량": int(args[2]),
            "2차_지지선": int(args[3]),
            "2차_수량": int(args[4]),
        }

        # 추가 옵션 파싱
        for arg in args[5:]:
            if '=' not in arg:
                continue

            key, value = arg.split('=', 1)
            key = key.strip()
            value = value.strip()

            if key == "손절":
                if '%' in value:
                    config["최대_손실_퍼센트"] = abs(float(value.replace('%', '')))
                else:
                    config["손절라인"] = int(value)
            elif key == "익절감시":
                if '%' in value:
                    config["익절_감시_시작_퍼센트"] = float(value.replace('%', ''))

        return {
            "code": code,
            "config": config,
        }

    except (ValueError, IndexError):
        return None
