import streamlit as st
import time 
from utils.settings import settings
from components.auth_widget import login_card, check_auth
from utils.state import ensure_app_state, logout_user
from utils.auth_cookie import get_auth_from_cookie, clear_auth_cookie, prime_cookie_component


ensure_app_state()

st.set_page_config(page_title=f"{settings.APP_NAME} | 로그인", page_icon="🧾", layout="centered")

# 1) 로그아웃 쿼리 최우선 처리
if st.query_params.get("logout") == "1":
    logout_user()
    clear_auth_cookie()
    st.query_params.clear()
    st.rerun()

# 2) CookieManager 컴포넌트 선마운트 (처음 랜더 사이클에서 바로 뜨게)
prime_cookie_component()

# 수정
if not st.session_state.get("user"):
    user_from_cookie = get_auth_from_cookie()
    if user_from_cookie:
        st.session_state["user"] = user_from_cookie
        st.session_state["authenticated"] = True  # 호환성을 위해 추가
    elif not st.session_state.get("_cookie_check_done"):
        # CookieManager가 아직 로딩 중일 수 있으므로 한 번 더 시도
        st.session_state["_cookie_check_done"] = True
        st.rerun()

# 4) 이미 로그인 상태면 대시보드로
if check_auth():
    time.sleep(0.5)
    st.switch_page("pages/dashboard.py")


# 기존 스타일 로드 후
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 로그인 화면용 테마 적용 추가
from components.theme import apply_theme_to_login
apply_theme_to_login()

# 로그인 페이지에서는 사이드바 완전 숨기기
st.markdown("""
<style>
/* 로그인 페이지에서는 사이드바 완전히 숨기기 */
section[data-testid="stSidebar"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 가운데 회색 박스 안에 로그인 위젯 배치
st.markdown('<div class="login-container">', unsafe_allow_html=True)
login_card()
st.markdown('</div>', unsafe_allow_html=True)