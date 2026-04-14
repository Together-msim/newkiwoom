# 🔒 보안 가이드

## ⚠️ 중요 보안 정보

이 프로젝트는 실제 금융 거래 API를 사용하므로 보안에 특별히 주의해야 합니다.

---

## 🚨 절대로 공개하면 안 되는 정보

### 1. API 키 및 토큰
```
❌ TELEGRAM_BOT_TOKEN
❌ KIWOOM_APPKEY
❌ KIWOOM_SECRETKEY
❌ OPENAI_API_KEY
```

### 2. 계좌 정보
```
❌ KIWOOM_ACCOUNT_NO (계좌번호)
❌ KIWOOM_ACCOUNT_PW (계좌 비밀번호)
❌ TELEGRAM_CHAT_ID
```

### 3. 거래 데이터
```
❌ .data/ 디렉토리의 모든 파일
❌ 로그 파일 (*.log)
❌ 세션 파일 (*.session)
```

---

## ✅ 안전하게 사용하는 방법

### 1. .env 파일 설정

**절대로 .env 파일을 공개 저장소에 올리지 마세요!**

```bash
# .env.example을 복사하여 .env 생성
cp .env.example .env

# 실제 값으로 채우기
nano .env
```

### 2. .gitignore 확인

프로젝트에 포함된 `.gitignore` 파일이 다음을 제외하는지 확인:
- `.env` (환경 변수)
- `.data/` (거래 데이터)
- `.claude/` (Claude Code 설정)
- `*.log` (로그 파일)

### 3. Git 커밋 전 확인

```bash
# 민감한 파일이 포함되지 않았는지 확인
git status

# .env 파일이 목록에 없어야 함
git check-ignore .env  # 출력이 있어야 함

# 추가 전 다시 확인
git diff --cached
```

### 4. GitHub 업로드 전 체크리스트

- [ ] `.env` 파일이 `.gitignore`에 포함되어 있는가?
- [ ] `git status`에 `.env` 파일이 보이지 않는가?
- [ ] `.data/` 디렉토리가 제외되는가?
- [ ] API 키가 코드에 하드코딩되어 있지 않은가?
- [ ] 계좌 정보가 코드에 포함되어 있지 않은가?

---

## 🔐 API 키 관리

### Kiwoom API 키
- **발급처**: [키움증권 OpenAPI 센터](https://apiportal.kiwoom.com)
- **보관**: `.env` 파일에만 저장
- **주의**: 절대 코드에 직접 입력하지 말 것

### 텔레그램 봇 토큰
- **발급**: [@BotFather](https://t.me/botfather)에서 발급
- **보관**: `.env` 파일에만 저장
- **유출 시**: 즉시 BotFather에서 토큰 재발급

---

## 🚨 보안 사고 발생 시 대응

### 1. API 키가 유출된 경우

**즉시 조치**:
1. 해당 API 키 즉시 폐기
2. 새 API 키 발급
3. `.env` 파일 업데이트
4. Git 히스토리에서 제거 (필요시)

```bash
# Git 히스토리에서 민감한 파일 제거
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all
```

### 2. 계좌 정보가 유출된 경우

**즉시 조치**:
1. HTS/MTS에서 계좌 비밀번호 변경
2. API 사용 중지 (키움증권 고객센터 연락)
3. 보안 담당자에게 보고

---

## 📋 보안 체크리스트

### 개발 환경 설정 시
- [ ] `.env` 파일 생성 및 설정
- [ ] `.env`가 `.gitignore`에 포함되어 있는지 확인
- [ ] API 키를 환경 변수로만 관리
- [ ] 계좌 정보를 코드에 하드코딩하지 않음

### Git 커밋 전
- [ ] `git status`로 민감한 파일 제외 확인
- [ ] `git diff`로 민감한 정보 포함 여부 확인
- [ ] 로그 파일, 데이터 파일 제외 확인

### GitHub 업로드 전
- [ ] Public/Private 저장소 선택 신중히 결정
- [ ] `.env.example` 파일만 포함되어 있는지 확인
- [ ] README에 보안 관련 안내 포함

### 운영 중
- [ ] 주기적으로 API 키 갱신 (권장: 3개월)
- [ ] 로그 파일 정기적 삭제
- [ ] `.data/` 디렉토리 백업 후 정리

---

## 🛡️ 추가 보안 권장사항

### 1. 시뮬레이션 모드 사용
```bash
# .env 설정
ORDER_SIMULATION_MODE=1  # 실제 주문 실행 안 됨
```

### 2. Budget 제한
```
종목별 Budget 설정으로 최대 손실 제한
예: Budget 100,000원 → 최대 투입금 10만원
```

### 3. 2단계 인증
- Kiwoom API 사용 시 2FA 활성화 권장
- 텔레그램 계정에 2FA 설정

### 4. 접근 제한
```bash
# 웹 서버를 localhost만 허용
WEB_HOST=127.0.0.1  # 외부 접근 차단
```

---

## 📞 보안 문의

보안 취약점을 발견하셨나요?

- **긴급**: 즉시 Issue를 비공개로 생성
- **일반**: GitHub Issues에 [SECURITY] 태그로 보고
- **이메일**: (프로젝트 관리자 이메일)

---

## 📚 참고 자료

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [키움증권 OpenAPI 가이드](https://apiportal.kiwoom.com)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)

---

**마지막 업데이트**: 2026-04-15

**Remember**: 
- 보안은 한 번의 실수로 큰 손실로 이어질 수 있습니다
- 의심스러우면 공유하지 마세요
- 정기적으로 API 키를 갱신하세요
