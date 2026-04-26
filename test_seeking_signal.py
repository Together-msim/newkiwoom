"""
Seeking Signal Minho 테스트 스크립트
"""
from seeking_signal_minho import analyze

# 삼성전자 분석
print("=" * 60)
print("📡 Seeking Signal Minho - 삼성전자 분석")
print("=" * 60)

try:
    report = analyze("005930")

    if 'error' in report:
        print(f"❌ 에러: {report['error']}")
    else:
        # 메타 정보
        meta = report['meta']
        print(f"\n📊 종목: {meta['stock_name']} ({meta['stock_code']})")
        print(f"   현재가: {meta['current_price']:,}원")
        print(f"   시가총액: {meta['market_cap_won']:,.0f}억원")
        print(f"   분석일시: {meta['analyzed_at']}")

        # 판정 결과
        summary = report['summary']
        print(f"\n🎯 판정: {summary['verdict'].upper()}")
        print(f"   신뢰도: {summary['confidence'] * 100:.0f}%")

        # 주요 신호
        print(f"\n✅ 주요 신호:")
        for signal in summary['key_signals']:
            print(f"   • {signal}")

        # 리스크
        if summary['risks']:
            print(f"\n⚠️  리스크:")
            for risk in summary['risks']:
                print(f"   • {risk}")

        # 타입1 분석
        type1 = report['macro']['type1']
        print(f"\n📈 타입1 분석:")
        print(f"   적용 가능: {type1['applicable']}")
        print(f"   횡보 중: {type1['is_sideways']}")
        if type1.get('metrics'):
            print(f"   BBWP: {type1['metrics']['bbwp_today']:.1f}")
            print(f"   60일 상승: +{type1['metrics']['rally_60d_pct']:.1f}%")

        # 타입2 분석
        type2 = report['macro']['type2']
        print(f"\n📉 타입2 분석:")
        print(f"   적용 가능: {type2['applicable']}")
        print(f"   횡보 중: {type2['is_sideways']}")

        # 거래대금
        volume = report['volume_spike']
        print(f"\n💰 거래대금 스파이크:")
        print(f"   신호 품질: {volume['signal_quality']}")
        if volume['days_ago_strong'] is not None:
            print(f"   마지막 강한 거래: {volume['days_ago_strong']}일 전")

        print("\n" + "=" * 60)
        print("✅ 분석 완료!")
        print("=" * 60)

except Exception as e:
    print(f"❌ 분석 실패: {e}")
    import traceback
    traceback.print_exc()
