import streamlit as st

def show_toast(message, toast_type="info", duration=3000):
    """
    토스트 메시지 표시
    
    Args:
        message: 표시할 메시지
        toast_type: 토스트 타입 (info, success, warning, error)
        duration: 표시 시간 (밀리초)
    """
    
    toast_classes = {
        "info": "toast-info",
        "success": "toast-success", 
        "warning": "toast-warning",
        "error": "toast-error"
    }
    
    toast_class = toast_classes.get(toast_type, "toast-info")
    
    st.markdown(
        f'<div class="toast {toast_class}">{message}</div>',
        unsafe_allow_html=True
    )

def show_success(message):
    """성공 토스트"""
    show_toast(message, "success")

def show_error(message):
    """에러 토스트"""
    show_toast(message, "error")

def show_warning(message):
    """경고 토스트"""
    show_toast(message, "warning")

def show_info(message):
    """정보 토스트"""
    show_toast(message, "info")