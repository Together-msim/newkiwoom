# TODO List

## 🔴 High Priority

### 0. 감시리스트 보유종목 자동조회 & 매도
- [x] 감시리스트 페이지 진입 시 자동 보유종목 조회
- [x] 보유종목 테이블에 매도 버튼 추가
- [x] 보유종목에서 직접 매도 주문 실행
- [x] 매도 체결 시 감시리스트 자동 업데이트
- [x] 텔레그램 실시간 알림 전송
- [x] 텔레그램 테스트 엔드포인트 추가
- [x] 다중 시나리오 테스트 스크립트 작성

### 1. Mode1 구현
- [x] `mode1_manager.py` 작성
  - 데이터 구조: code, name, monitoring_price, monitoring_conditions[], greenlight_status, buy_price, expected_profit_rate, status, polling_interval
  - CRUD 메서드
- [x] Mode1 REST API 엔드포인트 (`web_app.py`)
  - GET/POST/PUT/DELETE /api/mode1/watchers
  - PATCH /api/mode1/watchers/:code/active
  - PATCH /api/mode1/watchers/:code/status
- [x] Mode1 페이지 UI 완성
  - 종목 추가 폼
  - 종목명 자동 조회 (blur 이벤트)
  - 모니터링 조건 동적 추가/삭제 UI (분봉/추세/횟수)
  - 기대 수익률 입력
  - Polling 주기 설정 (전역 + 개별)
  - 인사이트 표시 영역
  - 테이블 렌더링 (조건 포함)
- [x] 분봉 데이터 조회 API
  - Kiwoom API 분봉 엔드포인트 연동 (ka10080)
  - 1/3/5/10분봉 데이터 파싱
  - `get_minute_chart()` 함수 구현 완료
- [x] 추세 분석 로직
  - 음봉/양봉 감지 (`is_bullish`, `is_bearish`)
  - 연속 양봉/음봉 카운트 (`count_consecutive_candles`)
  - `trend_analyzer.py` 모듈 작성 완료
- [x] 그린라이트 조건 체크
  - 분봉 종류별 조건 설정 (10분/5분/3분/1분)
  - 시간 기반 polling 스케줄러 구현
  - 조건 만족 시 텔레그램 알림
- [x] Mode1 모니터링 로직 (`price_monitor.py`)
  - check_mode1_conditions() 구현 완료
  - 시간 기반 polling (3분: 00:03, 03:03, ..., 5분: 00:03, 05:03, ..., 10분: 00:03, 10:03, ...)
  - greenlight_status 업데이트 및 인사이트 표시

### 2. 계좌 보유 종목 조회 & 감시리스트 매도 기능
- [x] Kiwoom API `get_positions()` 구현 (ka01690)
- [x] `/api/account/positions` 엔드포인트
- [x] 감시리스트 페이지에 "보유 종목 조회" 버튼
- [x] 계좌 요약 표시 (총 평가금액, 손익, 수익률, 예수금)
- [x] 보유 종목 테이블 (종목코드/명, 수량, 매입가, 현재가, 손익, 수익률)
- [x] 실시간 수익률 컬러 표시
- [x] 감시리스트에 보유수량 컬럼 추가
- [x] 감시리스트 매도 버튼 (waiting_sell 상태일 때)
- [x] 매도 모달 (수량, 시장가/지정가, 가격 입력)
- [x] 보유수량 동기화 기능 (/api/watchlist/sync-holdings)
- [x] 매도 시 manager의 record_sell() 호출하여 상태 자동 변경

### 3. 매매일지 페이지
- [ ] Tradelog API 엔드포인트
  - GET /api/tradelog (date range filter)
  - 확정 손익만 조회 (auto_sold, manual_sold)
- [ ] 통계 계산
  - 총 거래 건수
  - 총 수익 (매도가 - 매수가) * 수량
  - 평균 수익률
- [ ] Tradelog 페이지 UI 연동
  - Date range picker
  - Stats cards 업데이트
  - 테이블 렌더링

### 4. 계좌 polling 및 자동 상태 변경
- [ ] 주기적으로 Kiwoom 계좌 조회 (예: 5분마다)
  - price_monitor.py에 계좌 polling 로직 추가
  - 별도 asyncio task로 실행
- [ ] 보유 종목 확인 후 감시리스트와 비교
  - waiting_sell 상태인데 계좌에 없으면 → manual_sold
  - 수동 매도 감지 및 자동 기록
  - Tradelog에 수동 매도 내역 저장
- [ ] bought_quantity 자동 업데이트
  - 현재는 수동으로 "보유수량 동기화" 버튼 클릭 필요
  - 자동 polling으로 주기적 업데이트

### 3. 종목명 조회 안정화
- [ ] Kiwoom API 응답에서 종목명 추출 개선
  - ka10003 API stk_nm 필드 확인
  - 빈 값 처리
- [ ] corp_master.xlsx 우선 사용
  - symbol_resolver를 항상 먼저 호출
  - API 조회는 fallback
- [ ] Mode2 등록 시 종목명 자동 조회 테스트
  - 여러 종목코드로 테스트
  - 에러 핸들링 강화

## 🟡 Medium Priority

### 4. 실제 주문 API 연동
- [x] `kiwoom_client.py` 주문 API 구현
  - place_buy_order() 실제 구현 (kt10000)
  - place_sell_order() 실제 구현 (kt10001)
  - 보유수량 자동 조회 (_get_holding_qty - kt00018)
  - 시뮬레이션 모드 지원
- [x] Test 페이지 주문 테스트 UI
  - 매수/매도 폼
  - 시장가/지정가 선택
  - 주문 확인 대화상자
  - 결과 표시
- [ ] 주문 체결 확인
  - 주문 후 체결 여부 polling
  - 체결가 기록
  - 실패 시 재시도 로직
- [ ] 주문 취소 기능
  - 대기 중인 주문 취소 API
  - UI에서 수동 취소 버튼

### 5. 감시리스트 필터링
- [ ] Mode 필터 동작 구현
  - Mode1/Mode2 선택 시 해당 종목만 표시
- [ ] Status 필터 동작 구현
  - 매수대기/매도대기/자동매도/수동매도
- [ ] Date 필터 동작 구현
  - 등록일 기준 필터링
- [ ] 정렬 기능
  - 컬럼 클릭으로 정렬 (코드, 등록일, 수익률 등)

### 6. Mode2 페이지 개선
- [x] 종목코드 입력 시 종목명 자동 조회 (blur 이벤트)
- [x] Budget 입력 필드 추가 (종목코드 옆)
- [x] Polling 주기 선택 (5/10/15/20/30초)
- [x] Row 체크박스 추가 → 클릭 시 폼 auto-fill
- [x] 모든 필드 inline editing 완성
  - 종목명, 매수타점, Budget, Polling 주기
  - 저항/지지 가격 및 익절/손절 %
- [x] 편집 후 자동 저장 (blur 이벤트)
- [x] Polling 최적화 (종목별 마지막 체크 시간 기록)
- [x] **알림 전용 모드 추가**
  - 🔔 알림만 체크박스 (자동매매 없이 알림만)
  - 테이블에 모드 태그 표시 (🔔 알림 / 🤖 자동)
  - 모드 태그 클릭으로 토글
  - 매수타점 도달 시 텔레그램 알림
  - notify_only=True일 때 주문 실행 X

### 7. 차트 시각화
- [ ] Mode2 차트에 실제 가격 레벨 표시
  - 현재 이미지만 표시
  - Canvas 또는 Chart.js로 동적 차트
  - 매수타점, 저항/지지 레벨 라인 표시
- [ ] Mode1 분봉 차트 표시
  - 캔들스틱 차트
  - 추세선 표시
  - 그린라이트 조건 만족 시점 마커

## 🟢 Low Priority

### 8. 알림 개선
- [ ] 브라우저 알림 (Web Notification API)
- [ ] 소리 알림
- [ ] 알림 설정 페이지
  - 알림 종류별 on/off
  - 알림 소리 선택

### 9. 성능 최적화
- [ ] 감시리스트 pagination
  - 종목이 많아질 경우 대응
- [ ] 테이블 가상 스크롤
- [ ] API 응답 캐싱

### 10. 백업 및 복구
- [ ] 감시리스트 export/import
  - JSON 파일로 내보내기/가져오기
- [ ] 자동 백업
  - 일일 백업
  - 클라우드 저장

### 11. 다크 모드
- [ ] CSS 다크 테마
- [ ] 테마 전환 버튼
- [ ] 로컬스토리지에 테마 설정 저장

### 12. 모바일 최적화
- [ ] 반응형 레이아웃 개선
- [ ] 터치 제스처 지원
- [ ] 모바일 전용 UI

## 🐛 Known Issues

1. **종목명 조회 실패**
   - Kiwoom API에서 종목명이 빈 값으로 반환되는 경우
   - Workaround: corp_master.xlsx 우선 사용

2. **포트 충돌**
   - 5000번 포트가 이미 사용 중인 경우
   - Workaround: WEB_PORT 환경 변수로 변경

3. **테이블 inline editing 불완전**
   - Budget과 상태만 가능
   - 다른 필드는 폼에서만 수정 가능

## 📝 Notes

- kiwoom-min 프로젝트 참조: `~/Documents/kiwoom-min`
- 분봉 API 구현 시 `monitor_engine.py`, `kiwoom_chart.py` 참고
- 계좌 polling 로직은 `telegram_bot.py`의 positions 명령 참고
- 주문 API는 kiwoom-min의 `test_all_place_orders.py` 참고
- 현재 완료된 주요 기능:
  - Mode1 완전 구현 (분봉 모니터링, 그린라이트 조건, 텔레그램 알림)
  - Mode2 자동매매 (매수/익절/손절)
  - 계좌 보유 종목 조회
  - 실제 주문 API (시뮬레이션 모드 지원)
  - 감시리스트 매도 기능 및 보유수량 동기화
