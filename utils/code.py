#!/usr/bin/env python3
"""
종목코드 정규화 유틸리티
6자리 알파벳+숫자 혼용 지원
기존 kiwoom-min 프로젝트에서 검증된 방식 사용
"""
import re


def fullwidth_to_halfwidth(s: str) -> str:
    """전각 숫자·영문(０１２Ｎ 등)을 반각(ASCII)으로 변환. 메시지/종목코드 파싱용."""
    if not s:
        return s
    result = []
    for c in s:
        if "\uff10" <= c <= "\uff19":  # ０-９
            result.append(chr(ord(c) - 0xFF10 + 0x30))
        elif "\uff21" <= c <= "\uff3a":  # Ａ-Ｚ
            result.append(chr(ord(c) - 0xFF21 + 0x41))
        elif "\uff41" <= c <= "\uff5a":  # ａ-ｚ
            result.append(chr(ord(c) - 0xFF41 + 0x61))
        else:
            result.append(c)
    return "".join(result)


def normalize_stock_code(code: str) -> str:
    """
    종목코드를 6자리로 정규화 (알파벳+숫자 혼용 지원)

    - 숫자만 있으면 앞에 0 패딩하여 6자리
    - 알파벳+숫자 혼용이면 그대로 유지 (공백/특수문자 제거, 대문자 변환)

    예:
        "81180" -> "081180"
        "080220" -> "080220"
        "A81180" -> "A81180"
        "KQ178920" -> "KQ178920"
    """
    if not code:
        return code

    code = str(code).strip()
    code = fullwidth_to_halfwidth(code).upper()
    code = re.sub(r"[^A-Za-z0-9]", "", code)

    if not code:
        return code

    if code.isdigit():
        return code.zfill(6)

    return code
