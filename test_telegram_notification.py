"""
텔레그램 알림 테스트
감시리스트 매도 시뮬레이션 및 텔레그램 메시지 전송 테스트
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_telegram_message():
    """텔레그램 메시지 전송 테스트"""

    # 웹 서버 엔드포인트 (로컬 실행 중이어야 함)
    url = "http://localhost:5002/api/test/telegram"

    # 시뮬레이션: 삼성전자 100주 매도 체결
    test_message = """
🔔 매도 체결 알림

종목: 삼성전자 (005930)
수량: 100주
가격: 71,500원
타입: 시장가
주문번호: 20260415001234

✅ 주문이 성공적으로 체결되었습니다.

📊 감시리스트 상태:
- 보유수량: 0주 (전량 매도)
- 매수가: 70,000원
- 매도가: 71,500원
- 수익: +150,000원 (+2.14%)

🎯 체결 시각: 2026-04-15 14:30:25
    """.strip()

    print("=" * 60)
    print("📱 텔레그램 알림 테스트 시작")
    print("=" * 60)
    print("\n[전송할 메시지]")
    print(test_message)
    print("\n" + "=" * 60)

    try:
        response = requests.post(url, json={'message': test_message})
        result = response.json()

        if result['success']:
            print("\n✅ 성공: 텔레그램 메시지가 전송되었습니다!")
            print(f"   메시지: {result['message']}")
            print("\n💡 텔레그램 앱을 확인하세요.")
        else:
            print(f"\n❌ 실패: {result.get('error', '알 수 없는 오류')}")

    except requests.exceptions.ConnectionError:
        print("\n❌ 연결 실패: 웹 서버가 실행 중인지 확인하세요.")
        print("   실행 명령: python web_app.py")
    except Exception as e:
        print(f"\n❌ 오류: {e}")

    print("\n" + "=" * 60)
    print("테스트 완료")
    print("=" * 60)


def test_multiple_scenarios():
    """다양한 시나리오 테스트"""

    scenarios = [
        {
            'title': '시나리오 1: 익절 매도 (시장가)',
            'message': """
🎉 익절 매도 체결 알림

종목: POSCO홀딩스 (005490)
수량: 50주
가격: 385,000원
타입: 시장가
주문번호: 20260415001235

✅ 주문이 성공적으로 체결되었습니다.

📊 수익 정보:
- 매수가: 350,000원
- 매도가: 385,000원
- 수익: +1,750,000원 (+10.00%)

💰 1차 저항 돌파 익절 실행
            """
        },
        {
            'title': '시나리오 2: 손절 매도 (지정가)',
            'message': """
⚠️ 손절 매도 체결 알림

종목: SK하이닉스 (000660)
수량: 전량 (30주)
가격: 142,000원
타입: 지정가
주문번호: 20260415001236

✅ 주문이 성공적으로 체결되었습니다.

📊 손익 정보:
- 매수가: 155,000원
- 매도가: 142,000원
- 손실: -390,000원 (-8.39%)

🛑 2차 지지선 하락 손절 실행
            """
        },
        {
            'title': '시나리오 3: 알림 전용 모드 매수 시그널',
            'message': """
🔔 [알림 전용] Mode2 매수 시그널

종목: 카카오 (035720)
타점: 45,000원
현재가: 44,800원
수량: 22주

💡 알림 전용 모드: 자동 주문 실행 없음
   수동으로 매수를 결정하세요.

📈 매수타점 ±1% 범위 진입
   Budget: 1,000,000원
            """
        }
    ]

    url = "http://localhost:5002/api/test/telegram"

    print("\n" + "=" * 60)
    print("📱 다중 시나리오 텔레그램 알림 테스트")
    print("=" * 60)

    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'=' * 60}")
        print(f"[{i}/{len(scenarios)}] {scenario['title']}")
        print('=' * 60)
        print(scenario['message'].strip())

        try:
            response = requests.post(url, json={'message': scenario['message'].strip()})
            result = response.json()

            if result['success']:
                print(f"\n✅ 시나리오 {i} 전송 성공")
            else:
                print(f"\n❌ 시나리오 {i} 전송 실패: {result.get('error')}")

            # 다음 메시지 전 대기
            import time
            time.sleep(2)

        except Exception as e:
            print(f"\n❌ 시나리오 {i} 오류: {e}")
            break

    print("\n" + "=" * 60)
    print("✅ 모든 시나리오 테스트 완료")
    print("💡 텔레그램 앱에서 메시지를 확인하세요!")
    print("=" * 60)


if __name__ == "__main__":
    print("\n텔레그램 알림 테스트 옵션:")
    print("1. 단일 메시지 테스트")
    print("2. 다중 시나리오 테스트 (3개)")

    choice = input("\n선택 (1 또는 2, 기본값 2): ").strip() or "2"

    if choice == "1":
        test_telegram_message()
    else:
        test_multiple_scenarios()
