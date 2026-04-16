# GCP 서버 자동 제어 기능

## 개요

텔레그램 봇을 통해 GCP VM 인스턴스를 자동/수동으로 제어할 수 있습니다.

## 자동 스케줄

- **평일 (월~금)**: 08:00 ON → 15:30 OFF
- **주말 (토~일)**: 종일 OFF
- **효율적 스케줄링**: 08:00, 15:30 시간에만 실행 (불필요한 폴링 없음)

## 명령어

### `/server` - 서버 상태 확인
현재 서버 상태, 모드, 다음 스케줄을 확인합니다.

```
🖥 서버 상태

모드: ⏰ 자동 스케줄
현재: ✅ 운영 중
다음: 오늘 15:30 (종료)

한국시간: 2026-04-17 10:30:00
평일 자동 운영: 08:00~15:30

실제 서버: 🟢 RUNNING
```

### `/on` - 서버 수동 시작
서버를 수동으로 시작하고 **수동 제어 모드**로 전환합니다.
- 수동 모드에서는 자동 스케줄이 무시됩니다
- `/off` 명령으로 끄기 전까지 계속 켜져있습니다

```
✅ 서버를 시작했습니다 (수동 모드)

🖥 서버 상태

모드: 🔧 수동 제어
현재: ✅ 운영 중
다음: 수동 제어 모드 (자동 스케줄 비활성화)
...
```

### `/off` - 서버 수동 중지
서버를 수동으로 중지하고 **자동 스케줄 모드**로 돌아갑니다.

```
✅ 서버를 중지했습니다 (수동 모드 해제)

🖥 서버 상태

모드: ⏰ 자동 스케줄
현재: ❌ 중지
다음: 월요일 08:00 (D-1)
...
```

## 사용 시나리오

### 시나리오 1: 평일 정규 시간 (자동)
- **08:00**: 자동으로 서버 시작
- **15:30**: 자동으로 서버 중지
- 별도 명령 불필요

### 시나리오 2: 주말에 테스트하고 싶을 때
1. `/on` - 서버 수동 시작
2. 작업 수행
3. `/off` - 작업 완료 후 서버 중지 및 자동 모드 복귀

### 시나리오 3: 평일 연장 운영
1. 평일 15:30 이후에도 계속 운영하고 싶은 경우
2. 15:30 이전에 `/on` 실행 (수동 모드 전환)
3. 작업 완료 후 `/off` (자동 모드 복귀)

### 시나리오 4: 특정 날짜 휴무
1. 평일이지만 운영하지 않고 싶은 경우
2. 08:00 이전에 `/off` 실행 (자동 시작 방지)
3. 다음날 자동으로 정상 운영 재개

## 설정 (.env)

```bash
# GCP 서버 제어 설정
GCP_INSTANCE_NAME=kiwoom-trading-bot  # GCP VM 인스턴스 이름
GCP_ZONE=asia-northeast3-a            # GCP Zone (서울)
GCP_PROJECT_ID=                       # GCP 프로젝트 ID (선택)
```

## 사전 요구사항

### 1. gcloud CLI 설치
```bash
# Mac
brew install google-cloud-sdk

# Linux
curl https://sdk.cloud.google.com | bash
```

### 2. gcloud 인증
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### 3. 권한 확인
봇을 실행하는 계정이 다음 권한을 가져야 합니다:
- `compute.instances.get` (상태 조회)
- `compute.instances.start` (시작)
- `compute.instances.stop` (중지)

## 테스트

```bash
# 가상환경 활성화
source .venv/bin/activate

# 스케줄러 테스트
python test_server_scheduler.py
```

출력 예시:
```
============================================================
서버 스케줄러 테스트
============================================================

현재 시간 (KST): 2026-04-17 10:30:00
요일: 목

수동 제어 모드: False
서버 실행 여부: True
다음 스케줄: 오늘 15:30 (종료)

🖥 서버 상태
...

[GCP 서버 상태 확인 중...]
실제 서버 상태: 🟢 RUNNING

============================================================
테스트 완료
============================================================
```

## 주의사항

1. **수동 모드 영구성**: `/on` 명령 후에는 `/off`를 실행하기 전까지 계속 수동 모드로 유지됩니다
2. **자동 복귀**: `/off` 명령은 서버를 끄고 자동 스케줄 모드로 복귀합니다
3. **gcloud 인증**: 봇 실행 환경에서 gcloud 인증이 되어있어야 합니다
4. **네트워크**: 봇이 GCP API에 접근할 수 있어야 합니다

## 상태 파일

수동 제어 상태는 다음 파일에 저장됩니다:
```
.data/manual_server_control.txt
```

내용:
- `on`: 수동 모드 활성화
- `off` 또는 없음: 자동 스케줄 모드

## 트러블슈팅

### "gcloud command not found"
```bash
# gcloud CLI 설치 확인
which gcloud

# PATH 추가
export PATH=$PATH:$HOME/google-cloud-sdk/bin
```

### "Permission denied"
```bash
# 권한 확인
gcloud projects get-iam-policy YOUR_PROJECT_ID \
  --flatten="bindings[].members" \
  --format="table(bindings.role)" \
  --filter="bindings.members:user:YOUR_EMAIL"

# Compute Admin 역할 추가
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="user:YOUR_EMAIL" \
  --role="roles/compute.instanceAdmin.v1"
```

### "Instance not found"
```bash
# 인스턴스 목록 확인
gcloud compute instances list

# .env 파일에서 GCP_INSTANCE_NAME, GCP_ZONE 확인
```

## 로그

서버 제어 관련 로그는 봇 로그에 함께 기록됩니다:
```bash
tail -f bot_v3.log
```

주요 로그:
- `서버 스케줄러 시작`
- `서버를 시작합니다...`
- `서버 시작 완료: kiwoom-trading-bot`
- `서버를 중지합니다...`
- `서버 중지 완료: kiwoom-trading-bot`
