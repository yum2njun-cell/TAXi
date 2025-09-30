"""
TAXi - 통합 설정 페이지
"""
import streamlit as st
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from components.theme import apply_custom_theme, save_custom_theme
from components.path_settings import save_path_settings, load_path_settings
from utils.auth import is_guest, check_permission

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

# 페이지 설정
st.set_page_config(
    page_title=f"{settings.APP_NAME} | 설정",
    page_icon="",
    layout="wide"
)

# 스타일 로드 후에
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

# 기본 페이지 네비게이션만 숨기고, 커스텀 메뉴는 살리기
st.markdown("""
<style>
/* 멀티페이지 네비 컨테이너는 유지하되, 그 안의 항목만 숨김 */
[data-testid="stSidebarNav"] ul,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] a {
    display: none !important;
}

/* 혹시 이전에 + div 를 숨기는 규칙을 넣었다면 무력화 */
[data-testid="stSidebarNav"] + div {
    display: block !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    sidebar_menu()

def render_path_settings():
    """경로 설정 섹션"""
    from utils.settings import TAX_TYPES
    from services.folder_service import FolderService
    
    st.subheader("폴더 경로 설정")
    
    selected_tax_type = st.selectbox("설정할 세목 선택", TAX_TYPES)
    
    st.markdown("---")
    
    render_tax_type_path_settings(selected_tax_type)
    
    st.markdown("---")
    
    if st.button("경로 설정 저장", type="primary", disabled=is_guest()):
        if not check_permission("경로 설정"):
            return
        folder_service = FolderService()
        
        structure = st.session_state.get(f'temp_{selected_tax_type}_structure')
        
        if structure:
            is_valid, errors = folder_service.validate_structure(structure)
            
            if is_valid:
                user_id = st.session_state.get("user", {}).get("user_id", "user")
                success = folder_service.save_user_folder_structure(
                    user_id, selected_tax_type, structure
                )
                
                if success:
                    st.success(f"{selected_tax_type} 경로 설정이 저장되었습니다!")
                else:
                    st.error("저장 중 오류가 발생했습니다.")
            else:
                for error in errors:
                    st.error(error)
        else:
            st.error("저장할 폴더 구조가 없습니다.")

def render_tax_type_path_settings(tax_type: str):
    """단순 경로만 설정"""
    from services.folder_service import FolderService
    
    folder_service = FolderService()
    user_id = st.session_state.get("user", {}).get("user_id", "user")
    
    saved_structure = folder_service.load_user_folder_structure(user_id, tax_type)
    
    if not saved_structure:
        st.info(f"{tax_type} 기본 경로가 설정되지 않았습니다.")
        saved_structure = folder_service.get_default_structure()
    
    # 세목별 기본 경로 예시
    default_paths = {
        "원천세": f"C:\\Users\\{user_id}\\SK주식회사 C&C\\V_세무TF - General\\01_ 원천세 자료",
        "부가가치세": f"C:\\Users\\{user_id}\\SK주식회사 C&C\\V_세무TF - General\\02_ 부가세 자료",
        "법인세": f"C:\\Users\\{user_id}\\SK주식회사 C&C\\V_세무TF - General\\03_ 법인세 자료",
        "지방세": f"C:\\Users\\{user_id}\\SK주식회사 C&C\\V_세무TF - General\\04_ 지방세 자료",
        "인지세": f"C:\\Users\\{user_id}\\SK주식회사 C&C\\V_세무TF - General\\05_ 인지세 자료",
        "국제조세": f"C:\\Users\\{user_id}\\SK주식회사 C&C\\V_세무TF - General\\06_ 국제조세 자료"
    }
    
    base_path = st.text_input(
        f"{tax_type} 기본 경로",
        value=saved_structure.get('base_path', default_paths.get(tax_type, '')),
        help=f"{tax_type} 업무의 최상위 폴더 경로"
    )
    
    st.markdown("---")
    
    # 미리보기
    st.markdown("**폴더 구조 미리보기**")
    st.caption("연도/월/하위폴더는 작업 시 자동으로 검색됩니다")
    
    preview_path = f"{base_path}\n└── 2025년\n"
    st.code(preview_path, language="text")
    
    st.session_state[f'temp_{tax_type}_structure'] = {
        'base_path': base_path
    }

def render_user_settings():
    """사용자 개인 설정 섹션"""
    st.subheader("개인 설정")
    
    # 사용자 정보
    if st.session_state.get("user"):
        user_info = st.session_state["user"]
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("사용자 ID", value=user_info.get("user_id", ""), disabled=True)
            st.text_input("이름", value=user_info.get("name", ""))
        
        with col2:
            st.text_input("부서", value=user_info.get("department", ""))
            st.text_input("이메일", value=user_info.get("email", ""))
    
    # 기본 설정
    st.markdown("**기본 작업 설정**")
    
    default_year = st.selectbox(
        "기본 연도",
        options=list(range(2021, 2030)),
        index=4  # 2025
    )
    
    auto_save = st.checkbox("자동 저장", value=True)
    show_debug = st.checkbox("디버그 정보 표시", value=False)
    
    if st.button("개인 설정 저장", type="primary", disabled=is_guest()):
        if not check_permission("개인 설정"):
            return
        st.success("개인 설정이 저장되었습니다.")

def render_system_settings():
    """시스템 설정 섹션"""
    st.subheader("시스템 설정")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**파일 처리 설정**")
        max_file_size = st.number_input("최대 파일 크기 (MB)", value=100, min_value=1, max_value=500)
        batch_size = st.number_input("일괄 처리 크기", value=100, min_value=1, max_value=1000)
    
    with col2:
        st.markdown("**성능 설정**")
        max_workers = st.number_input("최대 동시 작업", value=5, min_value=1, max_value=20)
        cache_enabled = st.checkbox("캐시 사용", value=True)
    
    if st.button("시스템 설정 저장", type="primary", disabled=is_guest()):
        if not check_permission("시스템 설정"):
            return
        st.success("시스템 설정이 저장되었습니다.")

def main():
    page_header("설정", "")
    
    # 탭으로 구분 - 테마 탭 추가
    tab1, tab2, tab3, tab4 = st.tabs(["폴더 경로", "테마 색상", "개인 설정", "시스템 설정"])
    
    with tab1:
        render_path_settings()
    
    with tab2:
        render_theme_settings()  # 이 함수가 누락되어 있었음
        
    with tab3:
        render_user_settings()
        
    with tab4:
        render_system_settings()

def render_theme_settings():
    """테마/색상 설정 섹션"""
    st.subheader("테마 및 색상 설정")
    
    # 현재 색상 값들 (세션에서 가져오거나 기본값)
    current_theme = st.session_state.get('custom_theme', {
        'main_color': '#F6DA7A',
        'main_color_dark': '#E6C200',
        'bg_color1': '#FFF9E6',
        'bg_color2': '#FFF0F5',
        'text_color': '#111827',
        'text_color_light': '#6B7280'
    })
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**메인 색상**")
        main_color = st.color_picker("포인트 색상", current_theme['main_color'])
        main_color_dark = st.color_picker("포인트 색상 (어두운)", current_theme['main_color_dark'])
        
        st.markdown("**텍스트 색상**")
        text_color = st.color_picker("메인 텍스트", current_theme['text_color'])
        text_color_light = st.color_picker("보조 텍스트", current_theme['text_color_light'])
    
    with col2:
        st.markdown("**배경 색상**")
        bg_color1 = st.color_picker("배경색 1", current_theme['bg_color1'])
        bg_color2 = st.color_picker("배경색 2", current_theme['bg_color2'])
        
        # 미리보기
        st.markdown("**미리보기**")
        st.markdown(f"""
        <div style="
            background: linear-gradient(135deg, {bg_color1} 0%, {bg_color2} 100%);
            padding: 20px;
            border-radius: 8px;
            color: {text_color};
            border: 2px solid {main_color};
        ">
            <h4 style="color: {text_color}; margin: 0;">TAXi 미리보기</h4>
            <p style="color: {text_color_light}; margin: 5px 0;">
                선택한 색상으로 적용된 모습입니다.
            </p>
            <button style="
                background: {main_color};
                color: {text_color};
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            ">샘플 버튼</button>
        </div>
        """, unsafe_allow_html=True)
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("색상 테마 적용", type="primary", use_container_width=True):
            # 테마 저장
            new_theme = {
                'main_color': main_color,
                'main_color_dark': main_color_dark,
                'bg_color1': bg_color1,
                'bg_color2': bg_color2,
                'text_color': text_color,
                'text_color_light': text_color_light
            }
            st.session_state.custom_theme = new_theme
            
            # CSS 적용
            st.session_state.custom_theme = new_theme
            from components.theme import save_custom_theme
            save_custom_theme(new_theme)  # 파일로 저장
            apply_custom_theme()  # 인자 없이 호출
            st.success("테마가 저장되었습니다!")
    
    with col4:
        if st.button("기본 테마로 복원", use_container_width=True):
            from components.theme import delete_custom_theme
            
            # 세션에서 삭제
            if 'custom_theme' in st.session_state:
                del st.session_state.custom_theme
            
            # 파일도 삭제
            if delete_custom_theme():
                st.success("기본 테마로 복원되었습니다!")
            else:
                st.warning("테마 파일 삭제 중 오류가 발생했습니다.")
            
            st.rerun()

if __name__ == "__main__":
    main()