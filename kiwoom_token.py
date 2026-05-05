"""
키움 API OAuth2 토큰 발급
기존 kiwoom-min 프로젝트에서 검증된 방식 사용
"""
import os
import requests
from dotenv import load_dotenv

# 파일 위치 기준으로 .env를 확실히 찾기
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))


def get_token(account: str = 'sub') -> str:
    """
    키움 API에서 OAuth2 토큰을 발급받습니다.

    account='main'이면 KIWOOM_MAIN_APPKEY/KIWOOM_MAIN_SECRETKEY 사용.
    account='sub'(기본)이면 KIWOOM_APPKEY/KIWOOM_SECRETKEY 사용.

    Returns:
        str: 발급받은 토큰

    Raises:
        ValueError: 환경 변수가 설정되지 않은 경우
        RuntimeError: 키움 API에서 에러 응답을 받은 경우
        requests.RequestException: HTTP 요청 실패 시
    """
    if account == 'main':
        appkey_env, secretkey_env = 'KIWOOM_MAIN_APPKEY', 'KIWOOM_MAIN_SECRETKEY'
    else:
        appkey_env, secretkey_env = 'KIWOOM_APPKEY', 'KIWOOM_SECRETKEY'

    # 호출 시마다 .env 재로드 (다른 스레드에서 env가 비어 있는 경우 대비)
    load_dotenv(dotenv_path=os.path.join(BASE_DIR, ".env"))

    host = (os.getenv("KIWOOM_HOST") or "").strip()
    appkey = (os.getenv(appkey_env) or "").strip()
    secretkey = (os.getenv(secretkey_env) or "").strip()

    if not host:
        raise ValueError("KIWOOM_HOST 환경 변수가 설정되지 않았습니다.")
    if not appkey:
        raise ValueError(f"{appkey_env} 환경 변수가 설정되지 않았습니다.")
    if not secretkey:
        raise ValueError(f"{secretkey_env} 환경 변수가 설정되지 않았습니다.")

    # OAuth는 REST용 https 사용 (wss/ws 설정 시 교정)
    oauth_host = host.replace("wss://", "https://").replace("ws://", "http://").rstrip("/")
    if ":10000" in oauth_host:
        oauth_host = oauth_host.split(":10000")[0]
    url = f"{oauth_host}/oauth2/token"

    payload = {
        "grant_type": "client_credentials",
        "appkey": appkey,
        "secretkey": secretkey,
    }

    try:
        r = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json;charset=UTF-8"},
            timeout=10,
        )
        if r.status_code != 200:
            body = r.text[:500] if r.text else "(없음)"
            raise RuntimeError(
                f"키움 API 토큰 요청 실패: HTTP {r.status_code}\n"
                f"URL: {url}\n"
                f"응답: {body}\n\n"
                f"확인 사항:\n"
                f"  - KIWOOM_HOST: https://api.kiwoom.com (실서버) 또는 https://mockapi.kiwoom.com (모의)\n"
                f"  - {appkey_env}, {secretkey_env}가 정확한지\n"
                f"  - 키움 OpenAPI 포털에서 서버 IP 주소가 등록되었는지\n"
                f"  - appkey/secretkey 갱신 또는 지정단말기 인증 필요 여부"
            )
    except requests.RequestException as e:
        raise RuntimeError(f"키움 API 토큰 요청 실패: {e}") from e

    data = r.json()

    # 키움 API 응답 체크: return_code가 0이 아니면 에러
    if "return_code" in data:
        return_code = data.get("return_code")
        return_msg = data.get("return_msg", "알 수 없는 에러")

        if return_code != 0:
            raise RuntimeError(
                f"키움 API 인증 실패 [코드: {return_code}]\n"
                f"메시지: {return_msg}\n\n"
                f"가능한 원인:\n"
                f"  - APPKEY/SECRETKEY가 잘못되었습니다\n"
                f"  - 지정단말기 인증이 필요합니다 (키움 OpenAPI 설정 확인)\n"
                f"  - IP 주소가 등록되지 않았습니다"
            )

    # 토큰이 없으면 에러
    if "token" not in data:
        raise RuntimeError(f"키움 API 응답에 토큰이 없습니다: {data}")

    return data["token"]
