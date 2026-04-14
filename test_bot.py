"""
봇 기능 테스트 스크립트
"""
from tactic_manager import TacticManager
from strategy_parser import parse_natural_language, parse_tactic1_config, parse_tactic2_config


def test_tactic_manager():
    """Tactic Manager 기본 기능 테스트"""
    print("=" * 50)
    print("Tactic Manager 테스트")
    print("=" * 50)

    mgr = TacticManager()

    # Tactic1 추가
    print("\n1. Tactic1 종목 추가 테스트")
    added = mgr.add_tactic1(["005930", "000660"], {
        "기준봉": "1분",
        "최대_손실_퍼센트": 5,
        "기대_수익률_퍼센트": 7,
    })
    print(f"추가된 종목: {added}")

    # Tactic2 추가
    print("\n2. Tactic2 종목 추가 테스트")
    result = mgr.add_tactic2("035720", {
        "1차_매수가": 50000,
        "1차_수량": 10,
        "2차_지지선": 48000,
        "2차_수량": 10,
    })
    print(f"추가 성공: {result}")

    # 전체 리스트 확인
    print("\n3. 전체 감시 리스트 확인")
    watchers = mgr.get_all_watchers()
    for w in watchers:
        print(f"  - {w['code']} ({w['tactic']}) | 상태: {w['status']}")

    # 상태 확인
    print("\n4. 전략 상태 확인")
    status = mgr.get_status()
    print(f"  Tactic1: {status['tactic1']['active']}개")
    print(f"  Tactic2: {status['tactic2']['active']}개")
    print(f"  Total: {status['total']}개")

    # 종목 삭제
    print("\n5. 종목 삭제 테스트")
    deleted = mgr.delete_watcher("000660")
    print(f"삭제 성공: {deleted}")

    # 최종 리스트
    print("\n6. 최종 감시 리스트")
    watchers = mgr.get_all_watchers()
    for w in watchers:
        print(f"  - {w['code']} ({w['tactic']})")


def test_natural_language_parser():
    """자연어 파싱 테스트"""
    print("\n" + "=" * 50)
    print("자연어 파싱 테스트")
    print("=" * 50)

    test_cases = [
        "종목코드(005930) 삭제",
        "000660 삭제",
        "종목코드(035720) 수정",
        "감시 중인 종목 알려줘",
        "리스트 보여줘",
    ]

    for text in test_cases:
        result = parse_natural_language(text)
        print(f"\n입력: {text}")
        print(f"결과: {result}")


def test_tactic1_parser():
    """Tactic1 설정 파싱 테스트"""
    print("\n" + "=" * 50)
    print("Tactic1 설정 파싱 테스트")
    print("=" * 50)

    test_cases = [
        ["005930"],
        ["005930,000660"],
        ["005930", "기준봉=1분", "손절=-5%", "익절=7%"],
    ]

    for args in test_cases:
        result = parse_tactic1_config(args)
        print(f"\n입력: {args}")
        print(f"결과: {result}")


def test_tactic2_parser():
    """Tactic2 설정 파싱 테스트"""
    print("\n" + "=" * 50)
    print("Tactic2 설정 파싱 테스트")
    print("=" * 50)

    test_cases = [
        ["005930", "70000", "10", "68000", "10"],
        ["035720", "50000", "20", "48000", "20", "손절=-7%"],
    ]

    for args in test_cases:
        result = parse_tactic2_config(args)
        print(f"\n입력: {args}")
        print(f"결과: {result}")


if __name__ == "__main__":
    print("\n🧪 단타 전략 봇 기능 테스트\n")

    test_tactic_manager()
    test_natural_language_parser()
    test_tactic1_parser()
    test_tactic2_parser()

    print("\n✅ 테스트 완료!\n")
