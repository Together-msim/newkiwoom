#!/usr/bin/env python3
"""관심종목 그룹 마이그레이션: /Users/msim/Downloads/2/ → watchlist_groups + watchlist_items"""

import os
import csv
import sys
import openpyxl
from news_storage import NewsStorage

DATA_DIR = '/Users/msim/Downloads/2'
DB_PATH = '.data/news.db'

# 파일명 → 섹터명 매핑 (사용자가 나중에 변경 가능)
SECTION_NAMES = {
    '1.xlsx':              'ESS/SOFC (블룸에너지 서플라이체인)',
    '2.xlsx':              '방산/조선/에너지/HBM',
    '3.csv':               '포장재/저평가/DRAM',
    '4.csv':               '조선/데이터센터/원전',
    '5.csv':               '2차전지/배터리/스테이블코인',
    '6.csv':               '바이오/광통신',
    '7.csv':               'TSMC/자율주행/방산',
    '8.csv':               'ESS/스토리지/알래스카LNG',
    '9.csv':               '4~5월 관심주 (최신)',
    '10.csv':              '4~5월 관심주 (누적)',
    '11.csv':              '2월 급등/테마 (하락반등)',
    '12.csv':              '2월 급등/테마 (복사본)',
    '13.csv':              '반도체/원전/데이터센터',
    '14.csv':              '에너지/석유/LNG',
    '15.csv':              '이미지센서/토허제',
    '16.csv':              '바이오 (생물보안법)',
    '17.csv':              '현대차/로봇',
    '18.csv':              '배터리/2차전지',
    '19.csv':              '기타 소형',
    '20 오늘정리중.csv':   '2월 설 이후 불장',
    '21.csv':              'DRAM/HBM/소캠',
    '22.csv':              '4월 전체 관심주',
    '23.csv':              '핵심광물/희토류',
    '24.csv':              '드론/관리주/스윙',
    '25.csv':              '바이오 (치료제/진단)',
}


def parse_stock_code(raw) -> str:
    if raw is None:
        return ''
    s = str(raw).lstrip("'").strip()
    try:
        return str(int(float(s))).zfill(6)
    except Exception:
        return ''


def parse_xlsx(filepath: str):
    """Returns list of {item_type, stock_code, stock_name, subgroup_label, memo, display_order}"""
    wb = openpyxl.load_workbook(filepath)
    ws = wb.active
    items = []
    order = 0
    for row in ws.iter_rows(values_only=True):
        if row[0] == '분':
            continue  # header row
        # Subheader: stock_name (col2) is None but col0 has text
        if row[2] is None and row[0] is not None:
            items.append({
                'item_type': 'subheader',
                'stock_code': None,
                'stock_name': None,
                'subgroup_label': str(row[0]).strip(),
                'memo': None,
                'display_order': order,
            })
            order += 1
        else:
            code = parse_stock_code(row[-1])
            name = str(row[2]).strip() if row[2] else ''
            memo = str(row[7]).strip() if row[7] else None
            if not code and not name:
                continue
            items.append({
                'item_type': 'stock',
                'stock_code': code if code else None,
                'stock_name': name if name else None,
                'subgroup_label': None,
                'memo': memo,
                'display_order': order,
            })
            order += 1
    return items


def parse_csv(filepath: str):
    """Returns list of items."""
    items = []
    order = 0
    with open(filepath, encoding='cp949', errors='replace') as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            # Header row
            if row[0] == '분':
                continue
            # Subheader: single-column row starting with BLANK|
            if len(row) == 1:
                label = row[0]
                if label.startswith('BLANK|'):
                    label = label[6:].strip()
                items.append({
                    'item_type': 'subheader',
                    'stock_code': None,
                    'stock_name': None,
                    'subgroup_label': label,
                    'memo': None,
                    'display_order': order,
                })
                order += 1
                continue
            # Need at least 11 columns for a stock row
            if len(row) < 11:
                continue
            code = parse_stock_code(row[10] if len(row) > 10 else '')
            name = row[2].strip() if row[2] else ''
            memo = row[7].strip() if len(row) > 7 and row[7] else None
            if not code and not name:
                continue
            items.append({
                'item_type': 'stock',
                'stock_code': code if code else None,
                'stock_name': name if name else None,
                'subgroup_label': None,
                'memo': memo,
                'display_order': order,
            })
            order += 1
    return items


def main():
    ns = NewsStorage(DB_PATH)

    # Check existing groups
    existing = ns.get_watchlist_groups()
    if existing:
        print(f"⚠️  이미 {len(existing)}개 그룹 존재.")
        if '--force' not in sys.argv:
            print("재실행하려면 --force 옵션 추가")
            return
        # Delete all existing
        for g in existing:
            ns.delete_watchlist_group(g['id'])
        print("기존 그룹 삭제 완료.")

    files = sorted(os.listdir(DATA_DIR), key=lambda x: (
        0 if x.endswith('.xlsx') else 1,
        x
    ))

    total_groups = 0
    total_items = 0

    for i, fname in enumerate(files):
        if not (fname.endswith('.xlsx') or fname.endswith('.csv')):
            continue
        fpath = os.path.join(DATA_DIR, fname)
        section_name = SECTION_NAMES.get(fname, fname.replace('.xlsx', '').replace('.csv', ''))

        try:
            if fname.endswith('.xlsx'):
                items = parse_xlsx(fpath)
            else:
                items = parse_csv(fpath)
        except Exception as e:
            print(f"  ❌ {fname}: {e}")
            continue

        stock_count = sum(1 for it in items if it['item_type'] == 'stock')
        sub_count = sum(1 for it in items if it['item_type'] == 'subheader')

        group_id = ns.add_watchlist_group(
            name=section_name,
            file_origin=fname,
            pinned=True,
            display_order=i,
        )
        inserted = ns.bulk_insert_watchlist_items(group_id, items)

        # Ensure stock_master has these stocks
        for it in items:
            if it['item_type'] == 'stock' and it['stock_code'] and it['stock_name']:
                try:
                    with ns._conn() as conn:
                        conn.execute(
                            """INSERT OR IGNORE INTO stock_master (stock_code, stock_name)
                               VALUES (?, ?)""",
                            (it['stock_code'], it['stock_name'])
                        )
                except Exception:
                    pass

        print(f"  ✅ {fname} → [{section_name}] {stock_count}종목 + {sub_count}서브헤더 (group_id={group_id})")
        total_groups += 1
        total_items += inserted

    print(f"\n완료: {total_groups}개 그룹, {total_items}개 아이템 등록")


if __name__ == '__main__':
    main()
