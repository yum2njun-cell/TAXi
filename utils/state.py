import streamlit as st
from typing import Dict, Any, Optional
from services.user_preferences_service import get_user_preferences_service

def init_session_state():
    """세션 상태 초기화"""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    if "user_data" not in st.session_state:
        st.session_state.user_data = {}
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = "대시보드"
    
    if "upload_history" not in st.session_state:
        st.session_state.upload_history = []
    
    if "processing_results" not in st.session_state:
        st.session_state.processing_results = []

def set_user_session(user_data: Dict[str, Any]):
    """사용자 세션 설정"""
    st.session_state.authenticated = True
    st.session_state.user = user_data

    try:
        from services.user_preferences_service import get_user_preferences_service
        user_prefs_service = get_user_preferences_service()
        user_prefs_service.load_user_preferences(user_data.get("user_id"))
    except Exception as e:
        print(f"사용자 설정 로드 중 오류: {e}")

def get_user_session() -> Dict[str, Any]:
    """사용자 세션 정보 가져오기"""
    return st.session_state.get("user", {})

def clear_user_session():
    """사용자 세션 클리어"""
    st.session_state.authenticated = False
    st.session_state.user = {}

def is_authenticated() -> bool:
    """인증 상태 확인"""
    return st.session_state.get("authenticated", False)

def set_page_state(key: str, value: Any):
    """페이지별 상태 설정"""
    if "page_states" not in st.session_state:
        st.session_state.page_states = {}
    st.session_state.page_states[key] = value

def get_page_state(key: str, default: Any = None) -> Any:
    """페이지별 상태 가져오기"""
    page_states = st.session_state.get("page_states", {})
    return page_states.get(key, default)

def add_upload_history(filename: str, file_type: str, status: str):
    """업로드 히스토리 추가"""
    if "upload_history" not in st.session_state:
        st.session_state.upload_history = []
    
    st.session_state.upload_history.append({
        "filename": filename,
        "file_type": file_type,
        "status": status,
        "timestamp": st.session_state.get("current_time", "")
    })

def get_upload_history() -> list:
    """업로드 히스토리 가져오기"""
    return st.session_state.get("upload_history", [])

def add_processing_result(result: Dict[str, Any]):
    """처리 결과 추가"""
    if "processing_results" not in st.session_state:
        st.session_state.processing_results = []
    
    st.session_state.processing_results.append(result)

def get_processing_results() -> list:
    """처리 결과 목록 가져오기"""
    return st.session_state.get("processing_results", [])

def clear_processing_results():
    """처리 결과 클리어"""
    st.session_state.processing_results = []

import streamlit as st

# (선택) 사번/ID → 표시명 매핑표가 있다면 여기에 적어두세요.
_ID_TO_NAME = {
    "04362": "문상현",
    "11698": "김정민",
    "06488": "김태훈",
    "11375": "박세빈",
    "06337": "윤성은",
    "11470": "전유민",
    "07261": "최민석",
    "04975": "하영수"
}

def get_display_name() -> str:
    """세션 어디에 있든 표시 이름을 최대한 잘 찾아서 반환"""
    sess = st.session_state
    user = sess.get("user", {}) or {}
    auth = sess.get("auth", {}) or {}

    # 1) user_id 기반 매핑(최우선)
    uid = user.get("user_id") or auth.get("user_id") or sess.get("user_id")
    if uid and _ID_TO_NAME.get(uid):
        return _ID_TO_NAME[uid]

    # 2) 명시적 이름 필드
    for cand in [
        user.get("name"), user.get("display_name"),
        auth.get("name"), auth.get("display_name"),
        sess.get("name"), sess.get("display_name"),
    ]:
        if cand: return str(cand)

    # 3) username 계열
    for cand in [
        user.get("username"), auth.get("username"), sess.get("username")
    ]:
        if cand: return str(cand)

    # 4) 그래도 없으면 uid 자체라도
    if uid: return str(uid)

    # 5) 최종 fallback
    return "사용자"

def logout_user(preserve_keys: list[str] | None = None):
    """로그아웃: 세션 초기화 후 필요한 키만 보존."""
    keep = {k: st.session_state[k] for k in (preserve_keys or []) if k in st.session_state}
    st.session_state.clear()
    st.session_state.update(keep)
    
def ensure_app_state():
    """앱 전역에서 사용하는 session_state 키들의 기본값을 보장."""
    defaults = {
        "tax_schedules": {},   # ✅ 문제의 키: 기본적으로 빈 dict
        # 필요하면 여기에 다른 기본 키도 추가 가능
        # "user": {}, 
        # "auth": {},
        # "filters": {},
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def get_user_info():
    """현재 로그인된 사용자 정보 반환"""
    return st.session_state.get("user", None)

def sync_auth_session():
    """auth_cookie와 state.py 간 세션 동기화"""
    # user -> user_data 동기화
    if "user" in st.session_state and not st.session_state.get("user_data"):
        st.session_state["user_data"] = st.session_state["user"]
    
    # user_data -> user 동기화  
    if "user_data" in st.session_state and not st.session_state.get("user"):
        st.session_state["user"] = st.session_state["user_data"]

