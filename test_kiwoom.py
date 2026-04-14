"""
키움 API 연동 테스트
"""
import os
from dotenv import load_dotenv

load_dotenv()


def test_token():
    """토큰 발급 테스트"""
    print("=" * 50)
    print("키움 API 토큰 발급 테스트")
    print("=" * 50)

    try:
        from kiwoom_token import get_token

        token = get_token()
        print(f"✅ 토큰 발급 성공!")
        print(f"   토큰 길이: {len(token)} 문자")
        print(f"   토큰 앞 10자: {token[:10]}...")
        return True
    except Exception as e:
        print(f"❌ 토큰 발급 실패: {e}")
        return False


def test_client():
    """클라이언트 초기화 테스트"""
    print("\n" + "=" * 50)
    print("키움 API 클라이언트 초기화 테스트")
    print("=" * 50)

    try:
        from kiwoom_client import KiwoomClient

        client = KiwoomClient()
        print(f"✅ 클라이언트 초기화 성공!")
        print(f"   호스트: {client.host}")
        return client
    except Exception as e:
        print(f"❌ 클라이언트 초기화 실패: {e}")
        return None


def test_normalize_code():
    """종목코드 정규화 테스트"""
    print("\n" + "=" * 50)
    print("종목코드 정규화 테스트")
    print("=" * 50)

    from utils.code import normalize_stock_code

    test_cases = [
        ("81180", "081180"),
        ("005930", "005930"),
        ("5930", "005930"),
        ("A81180", "A81180"),
        ("kq 178920", "KQ178920"),
        ("５９３０", "005930"),  # 전각
    ]

    for input_code, expected in test_cases:
        result = normalize_stock_code(input_code)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{input_code}' → '{result}' (기대값: '{expected}')")


def test_get_price(client, code="005930"):
    """현재가 조회 테스트"""
    print("\n" + "=" * 50)
    print(f"현재가 조회 테스트: {code}")
    print("=" * 50)

    if not client:
        print("❌ 클라이언트가 초기화되지 않았습니다.")
        return

    # 테스트 모드 체크
    if os.getenv("TEST_LAST_PRICE"):
        print(f"⚠️  테스트 모드 활성화: TEST_LAST_PRICE={os.getenv('TEST_LAST_PRICE')}")

    try:
        price = client.get_last_price(code)
        print(f"✅ 현재가 조회 성공!")
        print(f"   종목코드: {code}")
        print(f"   현재가: {price:,.0f}원")
    except Exception as e:
        print(f"❌ 현재가 조회 실패: {e}")


def test_daily_info(client, code="005930"):
    """일일 가격 정보 조회 테스트"""
    print("\n" + "=" * 50)
    print(f"일일 가격 정보 조회 테스트: {code}")
    print("=" * 50)

    if not client:
        print("❌ 클라이언트가 초기화되지 않았습니다.")
        return

    try:
        info = client.get_daily_price_info(code)
        print(f"✅ 일일 가격 정보 조회 성공!")
        print(f"   종목코드: {code}")
        print(f"   시가: {info['open']:,.0f}원")
        print(f"   고가: {info['high']:,.0f}원")
        print(f"   저가: {info['low']:,.0f}원")
        print(f"   현재가: {info['close']:,.0f}원")
        print(f"   전일종가: {info['prev_close']:,.0f}원")

        # 갭상승률 계산
        if info['prev_close'] > 0:
            gap_ratio = ((info['open'] - info['prev_close']) / info['prev_close']) * 100
            print(f"   갭상승률: {gap_ratio:+.2f}%")

    except Exception as e:
        print(f"❌ 일일 가격 정보 조회 실패: {e}")


def test_gap_up_filter(client):
    """갭상승 필터링 테스트"""
    print("\n" + "=" * 50)
    print("갭상승 필터링 테스트")
    print("=" * 50)

    if not client:
        print("❌ 클라이언트가 초기화되지 않았습니다.")
        return

    test_codes = ["005930", "000660", "035720"]
    print(f"테스트 종목: {', '.join(test_codes)}")

    try:
        gap_up = client.check_gap_up_stocks(test_codes, threshold=7.0)
        print(f"✅ 갭상승 필터링 성공!")
        print(f"   7% 이상 갭상승 종목: {gap_up if gap_up else '없음'}")
    except Exception as e:
        print(f"❌ 갭상승 필터링 실패: {e}")


if __name__ == "__main__":
    print("\n🧪 키움 API 연동 테스트\n")

    # 환경 변수 확인
    print("=" * 50)
    print("환경 변수 확인")
    print("=" * 50)
    print(f"KIWOOM_HOST: {os.getenv('KIWOOM_HOST', '미설정')}")
    print(f"KIWOOM_APPKEY: {'설정됨' if os.getenv('KIWOOM_APPKEY') else '미설정'}")
    print(f"KIWOOM_SECRETKEY: {'설정됨' if os.getenv('KIWOOM_SECRETKEY') else '미설정'}")
    print(f"TEST_LAST_PRICE: {os.getenv('TEST_LAST_PRICE', '미설정')}")

    # 테스트 실행
    test_normalize_code()

    if not os.getenv("KIWOOM_APPKEY"):
        print("\n⚠️  KIWOOM_APPKEY가 설정되지 않아 API 테스트를 건너뜁니다.")
        print("   .env 파일을 설정한 후 다시 시도하세요.")
    else:
        token_ok = test_token()
        if token_ok:
            client = test_client()
            if client:
                test_get_price(client)
                test_daily_info(client)
                test_gap_up_filter(client)

    print("\n✅ 테스트 완료!\n")
