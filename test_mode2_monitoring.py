"""
Mode2 모니터링 테스트
실제 Kiwoom API를 호출해서 가격 체크 및 조건 모니터링이 동작하는지 확인
"""
import os
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

from mode2_manager import Mode2Manager
from kiwoom_client import KiwoomClient
from price_monitor import PriceMonitor


async def test_mode2_monitoring():
    """Mode2 모니터링 테스트"""
    print("=" * 60)
    print("Mode2 모니터링 테스트")
    print("=" * 60)

    # 초기화
    mode2_mgr = Mode2Manager()
    kiwoom_client = KiwoomClient()
    price_monitor = PriceMonitor(None, kiwoom_client, None, mode2_mgr)

    # 테스트 데이터 추가
    test_code = "003280"  # 흥아해운

    print(f"\n1. 종목 정보 조회: {test_code}")
    try:
        stock_info = kiwoom_client.get_stock_info(test_code)
        print(f"   - 종목코드: {stock_info['code']}")
        print(f"   - 종목명: {stock_info['name']}")
        print(f"   - 현재가: {stock_info['current_price']:,}원")
    except Exception as e:
        print(f"   ❌ 실패: {e}")
        return

    # Mode2 watcher 등록
    print(f"\n2. Mode2 감시 종목 등록")
    current_price = stock_info['current_price']

    # 기존 데이터 삭제
    mode2_mgr.delete_watcher(test_code)

    # 새로 등록
    test_watcher = {
        "code": test_code,
        "name": stock_info['name'],
        "buy_target_price": int(current_price * 0.98),  # 현재가 -2%
        "budget": 1000000,
        "resistance_1_price": int(current_price * 1.05),  # +5%
        "resistance_1_profit_pct": 5.0,
        "resistance_2_price": int(current_price * 1.10),  # +10%
        "resistance_2_profit_pct": 10.0,
        "support_1_price": int(current_price * 0.95),  # -5%
        "support_1_loss_pct": -5.0,
        "support_2_price": int(current_price * 0.90),  # -10%
        "support_2_loss_pct": -10.0,
    }

    watcher = mode2_mgr.add_watcher(test_watcher)
    print(f"   ✅ 등록 완료")
    print(f"   - 매수 타점: {watcher['buy_target_price']:,}원")
    print(f"   - Budget: {watcher['budget']:,}원")
    print(f"   - 수량: {watcher['quantity']}주")

    # 조건 체크 테스트
    print(f"\n3. 조건 체크 테스트 (매수 대기 중)")
    signal = await price_monitor.check_mode2_conditions(test_code, watcher)
    if signal:
        print(f"   ✅ 시그널 발생: {signal}")
    else:
        print(f"   ℹ️  조건 미충족 (현재가: {current_price:,}원, 타점: {watcher['buy_target_price']:,}원)")

    # 매수 후 상태로 변경하여 익절/손절 테스트
    print(f"\n4. 매수 체결 시뮬레이션")
    mode2_mgr.record_buy(test_code, watcher['buy_target_price'], watcher['quantity'])
    watcher = mode2_mgr.get_watcher(test_code)
    print(f"   ✅ 매수 기록 완료")
    print(f"   - 상태: {watcher['status']}")
    print(f"   - 매수가: {watcher['bought_price']:,}원")

    # 익절/손절 조건 체크
    print(f"\n5. 익절/손절 조건 체크 (매도 대기 중)")
    signal = await price_monitor.check_mode2_conditions(test_code, watcher)
    if signal:
        print(f"   ✅ 시그널 발생: {signal}")
    else:
        print(f"   ℹ️  조건 미충족")
        print(f"   - 현재가: {current_price:,}원")
        print(f"   - 1차 저항: {watcher['resistance_1_price']:,}원")
        print(f"   - 2차 저항: {watcher['resistance_2_price']:,}원")
        print(f"   - 1차 지지: {watcher['support_1_price']:,}원")
        print(f"   - 2차 지지: {watcher['support_2_price']:,}원")

    # 연속 모니터링 테스트
    print(f"\n6. 연속 모니터링 테스트 (3회, 5초 간격)")
    for i in range(3):
        print(f"\n   [{i+1}/3] 가격 체크 중...")

        # 현재가 조회
        try:
            current_price = kiwoom_client.get_last_price(test_code)
            print(f"   - 현재가: {current_price:,}원")
        except Exception as e:
            print(f"   ❌ 가격 조회 실패: {e}")
            continue

        # 조건 체크
        watcher = mode2_mgr.get_watcher(test_code)
        signal = await price_monitor.check_mode2_conditions(test_code, watcher)

        if signal:
            print(f"   🔔 시그널 발생: {signal}")
        else:
            print(f"   ✓ 정상 (조건 미충족)")

        if i < 2:
            await asyncio.sleep(5)

    print(f"\n{'=' * 60}")
    print("테스트 완료!")
    print("=" * 60)

    # 테스트 데이터 정리
    mode2_mgr.delete_watcher(test_code)
    print(f"\n✅ 테스트 데이터 정리 완료")


if __name__ == "__main__":
    asyncio.run(test_mode2_monitoring())
