import streamlit as st
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from components.user_settings_widget import render_user_settings
from services.auth_service import get_current_user_info
from components.theme import apply_custom_theme
from utils.auth import is_guest, check_permission

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 개인 설정", 
    page_icon="⚙️", 
    layout="wide"
)

# 스타일 로드 후에
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

# 기본 페이지 네비게이션 숨기기
st.markdown("""
<style>
[data-testid="stSidebarNav"] ul,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] a {
    display: none !important;
}

[data-testid="stSidebarNav"] + div {
    display: block !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

# 페이지 헤더
current_user = get_current_user_info()
page_header("개인 설정", "⚙️")

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()

# 사이드바 메뉴 아래에 추가
if is_guest():
    st.warning("⚠️ 게스트 계정은 설정을 저장할 수 없습니다. 임시로만 변경 가능합니다.")

# 메인 컨텐츠
render_user_settings()

# 사용법 안내
with st.expander("📖 사용법 안내"):
    st.markdown("""
    ### 개인 설정 사용법
    
    #### 기본 세목 선택
    - **목적**: TAXday 달력에서 기본으로 표시할 세목을 선택합니다.
    - **방법**: 원하는 세목의 체크박스를 선택/해제한 후 '설정 저장' 버튼을 클릭하세요.
    - **효과**: 다음 번 로그인할 때 선택한 세목들이 자동으로 체크된 상태로 표시됩니다.
    
    #### 역할별 추천 세목
    - 현재 사용자의 역할에 맞는 세목이 자동으로 추천됩니다.
    - 예: 부가세 담당자 → 부가세 세목이 추천됩니다.
    
    #### 설정 초기화
    - '기본값으로 초기화' 버튼을 클릭하면 모든 세목 선택이 해제됩니다.
    - 필요에 따라 다시 원하는 세목을 선택할 수 있습니다.
    
    #### 고급 설정
    - **알림 설정**: 중요한 세무 일정에 대한 알림 수신 여부를 설정합니다.
    - **달력 보기**: 기본 달력 보기 방식(월간/주간/일간)을 설정합니다.
    - **테마**: 화면 테마를 선택합니다.
    """)

# 현재 설정 상태 표시
from services.user_preferences_service import get_user_tax_categories

st.markdown("---")
st.markdown("### 현재 설정 상태")

selected_categories = get_user_tax_categories()
if selected_categories:
    tax_names = {
        '부': '부가세', '법': '법인세', '원': '원천세',
        '지': '지방세', '인': '인지세', '국': '국제조세', '기': '기타'
    }
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"선택된 세목: {len(selected_categories)}개")
        for category in selected_categories:
            st.write(f"✅ {category} - {tax_names.get(category, '기타')}")
    
    with col2:
        st.info("💡 TAXday에서 이 세목들이 기본으로 표시됩니다.")
else:
    st.warning("선택된 세목이 없습니다. 위에서 원하는 세목을 선택해주세요.")

# 개발자 정보 (디버깅용)
if st.checkbox("개발자 정보 보기"):
    from services.user_preferences_service import get_user_preferences_service
    
    st.markdown("### 디버그 정보")
    user_prefs_service = get_user_preferences_service()
    
    with st.expander("전체 사용자 설정"):
        preferences = user_prefs_service.load_user_preferences()
        st.json(preferences)
    
    with st.expander("사용자 통계"):
        stats = user_prefs_service.get_user_stats()
        st.json(stats)