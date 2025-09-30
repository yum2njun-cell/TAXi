import streamlit as st
import time
from utils.settings import settings
from services.auth_service import authenticate_user
from utils.auth_cookie import set_cookie_with_js, get_auth_from_cookie  
from utils.auth_cookie import ensure_auth_session

def login_card():
    # 고유한 key를 위해 timestamp 또는 session state 기반으로 생성
    if "login_form_id" not in st.session_state:
        st.session_state.login_form_id = int(time.time() * 1000)
    
    form_key = f"login_form_{st.session_state.login_form_id}"
    
    # 전체를 하나의 컨테이너로 감싸기
    with st.container():
        # 로고
        st.markdown('<div class="logo">TAXⓘ</div>', unsafe_allow_html=True)
        
        # 슬로건
        st.markdown('<div class="slogan">세금의 길 위에서, 가장 스마트한 드라이버</div>', unsafe_allow_html=True)
        
        # 로그인 폼
        with st.form(key=form_key):
            user = st.text_input("아이디", placeholder="아이디를 입력하세요", key=f"user_input_{st.session_state.login_form_id}")
            pwd = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요", key=f"pwd_input_{st.session_state.login_form_id}")
            
            st.markdown('<div class="gold-btn">', unsafe_allow_html=True)
            submit = st.form_submit_button("로그인")
            st.markdown('</div>', unsafe_allow_html=True)
        
                
        if submit:
            auth_result = authenticate_user(user, pwd)
            
            if auth_result["success"]:
                user_info = auth_result["user"]
                
                st.session_state["user"] = user_info
                st.session_state["authenticated"] = True

                st.success(auth_result["message"])

                # 사용자 설정 초기화 (로그인 시 개인 설정 로드)
                from services.user_preferences_service import get_user_preferences_service
                user_prefs_service = get_user_preferences_service()
                user_prefs_service.load_user_preferences(user_info["user_id"])
                
                set_cookie_with_js(user_info, days=7)  # JavaScript 방식으로 변경
                
                # 쿠키 설정 확인
                time.sleep(2.0)  # JavaScript 실행 시간 대기
                
                # 브라우저에서 쿠키 확인을 위한 JavaScript 추가
                check_js = """
                <script>
                console.log("All cookies:", document.cookie);
                setTimeout(() => {
                    console.log("Cookie check after 1sec:", document.cookie);
                }, 1000);
                </script>
                """
                st.markdown(check_js, unsafe_allow_html=True)
                
                time.sleep(1.0)
                st.rerun()
            else:
                st.error(auth_result["message"])

def check_auth():
    """인증 상태 확인: 세션 없으면 쿠키로 복원 시도"""
    
    # 1) 세션에 이미 있으면 OK
    if st.session_state.get("user"):
        return True
    
    # 2) 세션에 없으면 쿠키에서 복원 시도
    from utils.auth_cookie import get_auth_from_cookie
    user_from_cookie = get_auth_from_cookie()
    
    if user_from_cookie:
        st.session_state["user"] = user_from_cookie
        st.session_state["authenticated"] = True
        return True
    
    return False