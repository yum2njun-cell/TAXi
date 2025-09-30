import time, json, hmac, hashlib, base64
import streamlit as st
import extra_streamlit_components as stx
from utils.settings import settings  # settings.SECRET_KEY 사용 가정

_COOKIE_NAME = "taxi_auth"
_SECRET = getattr(settings, "SECRET_KEY", "change-me-please")  # .env/Secrets에 넣어두면 좋아요
_DEFAULT_DAYS = 7

# CookieManager는 컴포넌트라서 함수 안에서 생성해야 함(최초 1회)
def _cookie_mgr():
    # 위젯은 캐시함수 금지: 세션에 1회만 만들어 보관
    if "_cookie_mgr" not in st.session_state:
        st.session_state["_cookie_mgr"] = stx.CookieManager()
    return st.session_state["_cookie_mgr"]

def _b64url(x: bytes) -> str:
    return base64.urlsafe_b64encode(x).rstrip(b"=").decode()

def _b64urld(x: str) -> bytes:
    pad = "=" * (-len(x) % 4)
    return base64.urlsafe_b64decode((x + pad).encode())

def _sign(data: dict, exp_ts: int) -> str:
    payload = {"data": data, "exp": exp_ts}
    raw = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()
    sig = hmac.new(_SECRET.encode(), raw, hashlib.sha256).digest()
    return _b64url(raw) + "." + _b64url(sig)

def _verify(token: str):
    try:
        raw_b64, sig_b64 = token.split(".", 1)
        raw = _b64urld(raw_b64)
        want = hmac.new(_SECRET.encode(), raw, hashlib.sha256).digest()
        got = _b64urld(sig_b64)
        
        
        if not hmac.compare_digest(want, got):
            return None
            
        payload = json.loads(raw.decode())
        
        exp_time = int(payload.get("exp", 0))
        current_time = int(time.time())
        
        if exp_time < current_time:
            return None
            
        return payload.get("data")
    except Exception as e:
        return None

def set_auth_cookie(user: dict, days: int = _DEFAULT_DAYS):
    mgr = _cookie_mgr()
    exp_ts = int(time.time()) + days * 24 * 3600
    token = _sign(
        {"user_id": user.get("user_id"), "name": user.get("name"), "username": user.get("username")},
        exp_ts,
    )
    
    # 여러 방식으로 쿠키 설정 시도
    try:
        # 방법 1: 기본 설정
        mgr.set(_COOKIE_NAME, token, max_age=days * 24 * 3600, path="/", same_site="Lax")
        
        # 방법 2: 추가 옵션으로 재설정
        mgr.set(_COOKIE_NAME, token, max_age=days * 24 * 3600, path="/")
        
        # 즉시 확인 (강제 동기화)
        st.session_state.pop("_cookie_sync_attempted", None)  # 다음에 다시 시도하도록
        
    except Exception as e:
        st.write ("")

def get_auth_from_cookie():
    """앱 시작 시 호출: 쿠키에서 유저 정보 복원"""
    mgr = _cookie_mgr()
    
    # 강제로 쿠키 동기화 시도
    if not st.session_state.get("_cookie_sync_attempted"):
        st.session_state["_cookie_sync_attempted"] = True
        time.sleep(0.5)  # CookieManager 초기화 대기
        st.rerun()
        return None
    
    token = mgr.get(_COOKIE_NAME)
    
    if not token:
        return None
        
    data = _verify(token)
    return data

def clear_auth_cookie():
    mgr = _cookie_mgr()
    mgr.delete(_COOKIE_NAME, path="/")

def prime_cookie_component():
    """스크립트 초기에 CookieManager 위젯을 한 번 마운트해 두기 위한 헬퍼"""
    _cookie_mgr()

def ensure_auth_session():
    """세션에 user가 없으면 CookieManager에서 복원(필요시 1회 리런)"""
    from utils.state import sync_auth_session  # 순환 import 방지
    
    prime_cookie_component()

    if st.session_state.get("user"):
        sync_auth_session()  # 동기화
        return True

    # CookieManager가 첫 프레임에 아직 값이 없을 수 있음
    token = _cookie_mgr().get(_COOKIE_NAME)
    if token is None:
        if not st.session_state.get("_cookie_probe_done"):
            st.session_state["_cookie_probe_done"] = True
            time.sleep(0.1)
            st.rerun()
        return False

    data = _verify(token)
    if data:
        # 두 방식 모두 설정하여 호환성 보장
        st.session_state["user"] = data
        st.session_state["user_data"] = data
        st.session_state["authenticated"] = True
        return True

    return False

def set_cookie_with_js(user: dict, days: int = _DEFAULT_DAYS):
    """JavaScript로 직접 쿠키 설정"""
    exp_ts = int(time.time()) + days * 24 * 3600
    token = _sign(
        {"user_id": user.get("user_id"), "name": user.get("name"), "username": user.get("username")},
        exp_ts,
    )
    
    # JavaScript로 쿠키 설정
    cookie_js = f"""
    <script>
    document.cookie = "{_COOKIE_NAME}={token}; path=/; max-age={days * 24 * 3600}; SameSite=Lax";
    console.log("Cookie set via JS:", document.cookie);
    </script>
    """
    st.markdown(cookie_js, unsafe_allow_html=True)