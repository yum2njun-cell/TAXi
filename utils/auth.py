"""
권한 관리 유틸리티
게스트 계정 접근 제한 및 권한 체크
"""

import streamlit as st
from functools import wraps
from typing import Optional, Dict, Any


def get_current_user() -> Optional[Dict[str, Any]]:
    """현재 로그인한 사용자 정보 반환"""
    return st.session_state.get("user")


def is_guest() -> bool:
    """현재 사용자가 게스트인지 확인"""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "게스트"


def is_admin() -> bool:
    """현재 사용자가 관리자인지 확인"""
    user = get_current_user()
    if not user:
        return False
    return user.get("role") == "관리자"


def require_member(message: str = "게스트는 이 기능을 사용할 수 없습니다"):
    """
    게스트 권한 체크 데코레이터
    member 이상만 실행 가능
    
    사용 예:
    @require_member("파일 업로드")
    def upload_file():
        pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if is_guest():
                st.warning(f" {message}")
                st.info(" 실제 기능을 사용하려면 세무팀 계정으로 로그인하세요.")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator


def check_permission(action: str = "이 작업") -> bool:
    """
    인라인 권한 체크 (return bool)
    게스트인 경우 경고 후 실행 중단
    
    사용 예:
    if check_permission("파일 업로드"):
        # 실제 처리 로직
        process_file()
    """
    if is_guest():
        st.warning(f"⚠️ 게스트는 {action}을 수행할 수 없습니다")
        st.info("ℹ️ 실제 기능을 사용하려면 세무팀 계정으로 로그인하세요.")
        st.stop()  # ✅ 여기서 실행 완전 중단
    return True


def show_guest_badge():
    """헤더에 게스트 배지 표시"""
    if is_guest():
        st.markdown("""
        <span style='background: #FEF3C7; color: #92400E; padding: 0.2rem 0.6rem; 
                     border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;
                     border: 1px solid #FCD34D;'>
             게스트 모드
        </span>
        """, unsafe_allow_html=True)


def require_admin(message: str = "관리자만 접근할 수 있습니다"):
    """
    관리자 권한 체크 데코레이터
    
    사용 예:
    @require_admin()
    def admin_function():
        pass
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not is_admin():
                st.error(f" {message}")
                return None
            return func(*args, **kwargs)
        return wrapper
    return decorator