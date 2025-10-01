"""
인증 헬퍼 함수
"""
import streamlit as st
from typing import Optional

def verify_current_user_password(password: str) -> bool:
    """
    현재 로그인한 사용자의 비밀번호 확인
    
    Args:
        password: 입력한 비밀번호
        
    Returns:
        bool: 비밀번호 일치 여부
    """
    user = st.session_state.get("user")
    if not user:
        return False
    
    user_id = user.get("user_id")
    
    if user_id == "guest":
        return password == "guest"
    else:
        return password == f"skax{user_id}"

def require_password_for_action(action_name: str = "이 작업") -> Optional[str]:
    """
    작업 수행 전 비밀번호 확인 팝업
    
    Args:
        action_name: 작업명
        
    Returns:
        str: 입력한 비밀번호 (취소 시 None)
    """
    user = st.session_state.get("user")
    if not user:
        st.error("로그인이 필요합니다.")
        return None
    
    with st.form(key=f"password_confirm_{action_name}"):
        st.warning(f"🔐 {action_name}을(를) 수행하려면 비밀번호를 입력하세요.")
        password = st.text_input(
            "비밀번호",
            type="password",
            placeholder="비밀번호 입력"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button("확인", type="primary", use_container_width=True)
        with col2:
            cancel = st.form_submit_button("취소", use_container_width=True)
        
        if submit:
            if verify_current_user_password(password):
                return password
            else:
                st.error("❌ 비밀번호가 일치하지 않습니다.")
                return None
        
        if cancel:
            return None
    
    return None