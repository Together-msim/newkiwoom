"""
종목명/종목코드 변환 유틸리티
corp_master.xlsx 파일을 사용하여 종목명과 종목코드를 상호 변환합니다.
"""
import os
import re
import unicodedata
import pandas as pd
from utils.code import normalize_stock_code

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def resolve_symbol(symbol: str):
    """
    종목명 / 종목코드 → files/corp_master.xlsx 파일에서 종목코드 찾기

    Args:
        symbol: 종목명 또는 종목코드

    Returns:
        dict { corp_name, stock_code, dart_corp_code } or None
    """
    if symbol is None:
        return None

    # 유니코드 정규화 (NFC)
    symbol = unicodedata.normalize("NFC", str(symbol))

    # 제로폭/특수 공백 제거 (NBSP 포함)
    symbol = re.sub(r"[\u200b\u200c\u200d\uFEFF\u00a0]", "", symbol)

    # 앞뒤 공백 제거 + 내부 연속 공백 단일화
    symbol = symbol.strip()
    symbol = re.sub(r"\s+", " ", symbol)

    if not symbol:
        return None

    # 종목코드 정규화
    normalized = normalize_stock_code(symbol)

    # 6자리 숫자 또는 5~10자리 알파벳+숫자면 종목코드로 간주
    if normalized and len(normalized) >= 5 and len(normalized) <= 10 and normalized.isalnum():
        symbol_code = normalized
    else:
        symbol_code = None

    try:
        # corp_master.xlsx 파일 경로
        excel_path = os.path.join(BASE_DIR, "files", "corp_master1.xlsx")

        if not os.path.exists(excel_path):
            print(f"[WARN] corp_master.xlsx 파일을 찾을 수 없습니다: {excel_path}")
            return None

        # Excel 파일 읽기
        df = pd.read_excel(excel_path)

        # 컬럼명 확인
        stock_code_col = None
        corp_name_col = None
        dart_corp_code_col = None

        for col in df.columns:
            col_str = str(col).lower().strip()
            if "종목코드" in col_str or "stock_code" in col_str or col_str == "stock code":
                stock_code_col = col
            elif "종목명" in col_str or "corp_name" in col_str or "회사명" in col_str:
                corp_name_col = col
            elif "고유번호" in col_str or "dart" in col_str:
                dart_corp_code_col = col

        if stock_code_col is None:
            print("[ERROR] corp_master.xlsx에서 종목코드 컬럼을 찾을 수 없습니다")
            return None

        # 종목코드로 조회
        if symbol_code:
            code_series = df[stock_code_col].astype(str).str.strip()
            matches = df[code_series == symbol_code]

            if len(matches) > 0:
                row = matches.iloc[0]
                return {
                    "stock_code": symbol_code,
                    "corp_name": str(row[corp_name_col]).strip() if corp_name_col else "",
                    "dart_corp_code": str(row[dart_corp_code_col]).strip() if dart_corp_code_col else ""
                }

        # 종목명으로 조회
        if corp_name_col:
            name_series = df[corp_name_col].astype(str).str.strip()

            # 정확 일치
            exact_matches = df[name_series == symbol]
            if len(exact_matches) > 0:
                row = exact_matches.iloc[0]
                code = normalize_stock_code(str(row[stock_code_col]))
                return {
                    "stock_code": code,
                    "corp_name": str(row[corp_name_col]).strip(),
                    "dart_corp_code": str(row[dart_corp_code_col]).strip() if dart_corp_code_col else ""
                }

            # 부분 일치
            partial_matches = df[name_series.str.contains(symbol, case=False, na=False)]
            if len(partial_matches) > 0:
                row = partial_matches.iloc[0]
                code = normalize_stock_code(str(row[stock_code_col]))
                return {
                    "stock_code": code,
                    "corp_name": str(row[corp_name_col]).strip(),
                    "dart_corp_code": str(row[dart_corp_code_col]).strip() if dart_corp_code_col else ""
                }

        return None

    except Exception as e:
        print(f"[ERROR] resolve_symbol 실패: {e}")
        import traceback
        traceback.print_exc()
        return None
