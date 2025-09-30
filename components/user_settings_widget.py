"""
사용자 설정 위젯 - 개인화 설정 UI 컴포넌트
"""

import streamlit as st
from services.user_preferences_service import get_user_preferences_service, get_user_tax_categories, save_user_tax_categories
from services.auth_service import get_current_user_info
from utils.auth import is_guest, check_permission

def render_user_settings():
    """사용자 설정 페이지 렌더링"""
    
    current_user = get_current_user_info()
    if not current_user:
        st.error("로그인이 필요합니다.")
        return
    
    user_prefs_service = get_user_preferences_service()
    
    st.markdown("### 개인 설정")
    st.markdown("---")
    
    # 현재 사용자 정보 표시
    col1, col2 = st.columns([1, 2])
    with col1:
        st.markdown("**사용자 정보**")
        st.write(f"이름: {current_user['name']}")
        st.write(f"역할: {current_user['role']}")
        st.write(f"부서: {current_user['department']}")
    
    with col2:
        # 세목 선택 설정
        st.markdown("**기본 세목 선택**")
        st.caption("달력에서 기본으로 표시할 세목을 선택하세요.")
        
        # 현재 선택된 세목들
        current_categories = get_user_tax_categories()
        
        # 세목 옵션
        tax_categories = {
            '부': '부가세',
            '법': '법인세', 
            '원': '원천세',
            '지': '지방세',
            '인': '인지세',
            '국': '국제조세',
            '기': '기타'
        }
        
        # 체크박스로 세목 선택
        selected_categories = []
        
        cols = st.columns(3)
        for i, (short_name, full_name) in enumerate(tax_categories.items()):
            with cols[i % 3]:
                checked = st.checkbox(
                    f"{short_name} - {full_name}", 
                    value=(short_name in current_categories),
                    key=f"setting_tax_{short_name}"
                )
                if checked:
                    selected_categories.append(short_name)
        
        # 저장 버튼
        col_save, col_reset = st.columns(2)
        
        with col_save:
            # 설정 저장 버튼
            if st.button("설정 저장", type="primary", disabled=is_guest()):
                if not check_permission("개인 설정 저장"):
                    return
                if save_user_tax_categories(selected_categories):
                    st.success("설정이 저장되었습니다!")
                    st.rerun()
                else:
                    st.error("설정 저장에 실패했습니다.")
        
        with col_reset:
            if st.button("기본값으로 초기화"):
                if save_user_tax_categories([]):
                    st.success("설정이 초기화되었습니다!")
                    st.rerun()
                else:
                    st.error("설정 초기화에 실패했습니다.")
    
    st.markdown("---")
    
    # 추가 설정들
    with st.expander("고급 설정", expanded=False):
        
        # 알림 설정
        st.markdown("**알림 설정**")
        notifications_enabled = user_prefs_service.get_user_preference("notifications", True)
        new_notifications = st.checkbox("알림 받기", value=notifications_enabled)
        
        # 달력 보기 설정
        st.markdown("**달력 보기**")
        calendar_view = user_prefs_service.get_user_preference("calendar_view", "monthly")
        new_calendar_view = st.selectbox(
            "기본 달력 보기", 
            options=["monthly", "weekly", "daily"],
            index=["monthly", "weekly", "daily"].index(calendar_view),
            format_func=lambda x: {"monthly": "월간", "weekly": "주간", "daily": "일간"}[x]
        )
        
        # 테마 설정
        st.markdown("**테마 설정**")
        theme = user_prefs_service.get_user_preference("theme", "default")
        new_theme = st.selectbox(
            "테마", 
            options=["default", "dark", "compact"],
            index=["default", "dark", "compact"].index(theme),
            format_func=lambda x: {"default": "기본", "dark": "다크", "compact": "컴팩트"}[x]
        )
        
        # 고급 설정 저장
        if st.button("고급 설정 저장"):
            success = True
            success &= user_prefs_service.set_user_preference("notifications", new_notifications)
            success &= user_prefs_service.set_user_preference("calendar_view", new_calendar_view)
            success &= user_prefs_service.set_user_preference("theme", new_theme)
            
            if success:
                st.success("고급 설정이 저장되었습니다!")
            else:
                st.error("설정 저장에 실패했습니다.")

def render_quick_category_selector():
    """빠른 세목 선택 위젯 (사이드바용)"""
    
    current_user = get_current_user_info()
    if not current_user:
        return
    
    st.markdown("#### 내 세목 설정")
    
    # 현재 선택된 세목들
    current_categories = get_user_tax_categories()
    
    if current_categories:
        tax_names = {
            '부': '부가세', '법': '법인세', '원': '원천세',
            '지': '지방세', '인': '인지세', '국': '국제조세', '기': '기타'
        }
        
        st.write("**현재 선택된 세목:**")
        for category in current_categories:
            st.write(f"• {category} - {tax_names.get(category, '기타')}")
    else:
        st.info("선택된 세목이 없습니다.")
    
    if st.button("설정 변경", key="quick_settings"):
        st.session_state.show_settings = True

def render_category_quick_buttons():
    """세목별 바로가기 버튼 (역할 기반)"""
    
    current_user = get_current_user_info()
    if not current_user:
        return
    
    user_role = current_user.get("role", "")
    
    # 역할별 추천 세목
    role_categories = {
        "부가세": ["부"],
        "법인세": ["법"],
        "원천세": ["원"],
        "지방세": ["지"],
        "인지세": ["인"],
        "국제조세": ["국"],
        "관리자": ["부", "법", "원", "지", "인", "국"]
    }
    
    recommended = role_categories.get(user_role, [])
    
    if recommended:
        st.markdown("#### 추천 세목")
        st.caption(f"{user_role} 담당자에게 추천하는 세목입니다.")
        
        if st.button(f"{user_role} 세목으로 설정"):
            if save_user_tax_categories(recommended):
                st.success(f"{user_role} 관련 세목이 설정되었습니다!")
                st.rerun()
            else:
                st.error("설정 변경에 실패했습니다.")

def get_user_welcome_message():
    """사용자별 환영 메시지"""
    
    current_user = get_current_user_info()
    if not current_user:
        return "환영합니다!"
    
    name = current_user.get("name", "사용자")
    role = current_user.get("role", "")
    
    # 선택된 세목 개수에 따른 메시지
    selected_categories = get_user_tax_categories()
    category_count = len(selected_categories)
    
    if category_count == 0:
        return f"{name}님, 환영합니다! 세목을 선택해보세요."
    elif category_count == 1:
        tax_names = {
            '부': '부가세', '법': '법인세', '원': '원천세',
            '지': '지방세', '인': '인지세', '국': '국제조세', '기': '기타'
        }
        category_name = tax_names.get(selected_categories[0], '선택한 세목')
        return f"{name}님, {category_name} 일정을 확인해보세요!"
    else:
        return f"{name}님, {category_count}개 세목의 일정을 관리중입니다."