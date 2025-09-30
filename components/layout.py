import streamlit as st
from utils.settings import settings
from utils.state import get_display_name, logout_user, ensure_app_state

ensure_app_state()

# ✅ app.py에서만 처리: 로그아웃 쿼리 감지 → 세션 초기화 → 쿼리 제거 후 새로고침(선택)
if st.query_params.get("logout") == "1":
    logout_user()
    st.query_params.clear()
    st.rerun()  # 선택이지만 권장: 쿼리 제거 상태로 로그인 폼 표시

def page_header(title, icon=""):
    """페이지 상단 헤더"""
    import html  # ✅ 추가
    
    # right_sidebar를 먼저 렌더링하되, 예외 처리 추가
    try:
        from components.right_sidebar import right_sidebar
        if st.session_state.get("user"):
            right_sidebar()
    except Exception as e:
        # 오류는 무시하고 계속 진행
        pass
    
    # 게스트 배지 HTML 생성
    user = st.session_state.get("user", {})
    guest_badge = ""
    if user.get("role") == "게스트":
        guest_badge = """
        <span style='background: #FEF3C7; color: #92400E; padding: 0.2rem 0.6rem; 
                     border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem;
                     border: 1px solid #FCD34D;'>
            게스트 모드
        </span>
        """
    
    # ✅ display_name을 HTML escape 처리
    try:
        display_name = html.escape(str(get_display_name()))
    except Exception as e:
        display_name = "사용자"

    # ✅ HTML을 한 줄로 작성 (들여쓰기/개행 제거)
    st.markdown(f'<div class="page-header"><div class="header-content"><div class="header-left"><span class="page-icon">{icon}</span><h1 class="page-title">{title}</h1></div><div class="header-right"><div class="user-info"><span class="user-name">{display_name}</span>{guest_badge}<a class="logout-btn" href="app.py?logout=1" target="_self" rel="nofollow">로그아웃</a></div></div></div></div>', unsafe_allow_html=True)

def sidebar_menu():
    """사이드바 메뉴"""
    from utils.menu_config import get_menu_config

    # === 로고(버튼) + 슬로건 ===========================
    # 버튼이지만 CSS로 .logo처럼 보이게 만들고, 클릭 시 홈으로 이동
    st.markdown('<div class="sidebar-logo-wrap">', unsafe_allow_html=True)
    clicked_logo = st.button("TAXⓘ", key="logo_home", help="홈으로 이동")
    st.markdown('</div>', unsafe_allow_html=True)
    if clicked_logo:
        st.switch_page("pages/dashboard.py")
    st.markdown("---")
    # ================================================

    # 메뉴 설정 가져오기
    menu_config = get_menu_config()

    # 각 메뉴 섹션 렌더링
    for section_name, section_data in menu_config.items():
        render_menu_section(section_name, section_data)
    
    # TAXk 섹션이 끝난 후 개인 설정 메뉴 추가
    st.markdown("---")
    if st.button("📢 공지사항", key="sidebar_announcements", use_container_width=True):
        st.switch_page("pages/announcements.py")
    if st.button("💬 1on1 관리", key="sidebar_one_on_one", use_container_width=True):
        st.switch_page("pages/one_on_one.py")
    if st.button("⚙️ 설정", key="sidebar_user_settings", use_container_width=True):
        st.switch_page("pages/settings.py")

def render_menu_section(section_name, section_data):
    """메뉴 섹션 렌더링"""
    st.markdown(f'<div class="menu-section-title">{section_name}</div>', unsafe_allow_html=True)
    
    for item_name, item_data in section_data.items():
        # 서브메뉴가 있는 경우 (드롭다운)
        if "submenu" in item_data:
            render_dropdown_menu(item_name, item_data)
        # 일반 메뉴인 경우
        else:
            page = item_data.get("page", "")
            if st.button(item_name, key=f"menu_{item_name}", use_container_width=True):
                if page:
                    st.session_state.current_page = item_name
                    st.switch_page(page)

def render_dropdown_menu(item_name, item_data):
    """드롭다운 메뉴 렌더링 (법인세 등 서브메뉴를 박스로 감싸는 옵션 포함)"""
    submenu = item_data.get("submenu", {})
    # menu_config에 "boxed": True 넣으면 그 값을 사용, 없으면 법인세일 때만 기본 적용
    boxed = item_data.get("boxed", False) or (item_name == "법인세")

    # 드롭다운 상태 관리
    dropdown_key = f"dropdown_{item_name}"
    if dropdown_key not in st.session_state:
        st.session_state[dropdown_key] = False

    # 드롭다운 토글 버튼
    arrow = "▼" if st.session_state[dropdown_key] else "▶"
    if st.button(f"{arrow} {item_name}", key=f"toggle_{item_name}", use_container_width=True):
        st.session_state[dropdown_key] = not st.session_state[dropdown_key]

    # 서브메뉴 표시
    if st.session_state[dropdown_key]:
        # ✅ 서브메뉴 묶음만 박스로 감싸기
        if boxed:
            st.markdown('<div class="submenu-box">', unsafe_allow_html=True)

        for sub_name, sub_data in submenu.items():
            sub_page = sub_data.get("page", "")

            # 들여쓰기용 래퍼 (submenu-box 안에서는 CSS가 겹침 방지 처리됨)
            st.markdown('<div class="submenu-item">', unsafe_allow_html=True)
            if st.button(f"　　{sub_name}", key=f"submenu_{item_name}_{sub_name}", use_container_width=True):
                if sub_page:
                    st.session_state.current_page = f"{item_name} > {sub_name}"
                    st.switch_page(sub_page)
            st.markdown('</div>', unsafe_allow_html=True)



        if boxed:
            st.markdown('</div>', unsafe_allow_html=True)

def show_toast(message, type="info"):
    """토스트 메시지 표시"""
    toast_class = f"toast toast-{type}"
    st.markdown(f'''
    <div class="{toast_class}">
        {message}
    </div>
    ''', unsafe_allow_html=True)

def loading_spinner(text="처리 중..."):
    """로딩 스피너"""
    return st.spinner(text)

def confirm_dialog(title, message, confirm_text="확인", cancel_text="취소"):
    """확인 대화상자"""
    with st.container():
        st.warning(f"**{title}**")
        st.write(message)
        
        col1, col2 = st.columns(2)
        with col1:
            confirm = st.button(confirm_text, type="primary", use_container_width=True)
        with col2:
            cancel = st.button(cancel_text, use_container_width=True)
        
        return confirm, cancel