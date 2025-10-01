import streamlit as st
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from utils.state import get_user_session
from services.auth_service import get_current_user_info
from datetime import datetime
from utils.state import ensure_app_state
from components.theme import apply_custom_theme
from components.chatbot_widget import render_chatbot_interface
from utils.auth import is_guest, check_permission

ensure_app_state()
if not check_auth():
    st.switch_page("app.py")

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 대시보드", 
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

# 로고와 슬로건 추가
st.markdown("""
<div style="text-align: center; margin-bottom: 1.5rem; margin-top: -1rem;">
    <div class="logo" style="margin-bottom: 0.5rem;">TAXⓘ</div>
    <div class="slogan">세금의 길 위에서, 가장 스마트한 드라이버</div>
</div>
""", unsafe_allow_html=True)

# 페이지 헤더 (날짜 표시)
from datetime import datetime
today = datetime.now().strftime("%Y년 %m월 %d일")
page_header(today, "")

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()

# 사용자 정보
current_user = get_current_user_info()
if current_user:
    username = current_user.get("name", "{username}")
    user_role = current_user.get("role", "")
else:
    username = "{username}"
    user_role = ""

# 메인 컨텐츠 - 인사말
st.markdown(f"### 안녕하세요, {username}님!")

# 챗봇 인터페이스 (전체 너비)
render_chatbot_interface()

st.markdown("---")

# 오늘의 일정 표시
st.markdown("###  오늘의 일정")

# TAXday와 연동하여 오늘 일정 조회
from services.enhanced_tax_calendar_service import get_enhanced_calendar_service
tax_service = get_enhanced_calendar_service()
today_str = datetime.now().strftime("%Y-%m-%d")
today_schedules = tax_service.get_schedules_for_date(today_str)

if today_schedules:
    for schedule in today_schedules:
        category_labels = {
            '부': '부가세', '법': '법인세', '원': '원천세', 
            '지': '지방세', '인': '인지세', '국': '국제조세', '기': '기타'
        }
        category_name = category_labels.get(schedule['category'], '기타')
        st.write(f"• [{category_name}] **{schedule['title']}**")
        st.caption(f"   {schedule['description']}")
else:
    st.info("오늘 일정 없음")

st.markdown("---")

# 달력과 공지사항을 좌우로 배치
col_calendar, col_notice = st.columns([7, 3])

with col_calendar:
    st.markdown("### TAXday")
    
    # 사용자 설정에서 세목 선택 상태 로드
    from services.user_preferences_service import get_user_tax_categories, save_user_tax_categories

    user_selected_categories = get_user_tax_categories()

    # 대시보드 전용 세션 상태 키로 이전 선택 추적
    if "dashboard_prev_selected" not in st.session_state:
        st.session_state.dashboard_prev_selected = user_selected_categories.copy()

    # 체크박스 필터 (7개) - 사용자 설정과 연동
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5, filter_col6, filter_col7 = st.columns(7)

    selected_categories = []

    with filter_col1:
        if st.checkbox("부가세", key="filter_bu", value="부" in user_selected_categories):
            selected_categories.append("부")
    with filter_col2:
        if st.checkbox("법인세", key="filter_beop", value="법" in user_selected_categories):
            selected_categories.append("법")
    with filter_col3:
        if st.checkbox("원천세", key="filter_won", value="원" in user_selected_categories):
            selected_categories.append("원")
    with filter_col4:
        if st.checkbox("지방세", key="filter_ji", value="지" in user_selected_categories):
            selected_categories.append("지")
    with filter_col5:
        if st.checkbox("인지세", key="filter_in", value="인" in user_selected_categories):
            selected_categories.append("인")
    with filter_col6:
        if st.checkbox("국제조세", key="filter_guk", value="국" in user_selected_categories):
            selected_categories.append("국")
    with filter_col7:
        if st.checkbox("기타", key="filter_gi", value="기" in user_selected_categories):
            selected_categories.append("기")

    # 선택 상태가 변경되었으면 사용자 설정에 저장
    if selected_categories != st.session_state.dashboard_prev_selected:
        save_user_tax_categories(selected_categories)
        st.session_state.dashboard_prev_selected = selected_categories.copy()

    # 달력 렌더링
    from components.calendar_widget import render_calendar
    render_calendar(selected_categories=selected_categories)

with col_notice:
    # 공지사항
    st.markdown("### 공지사항")

    # 최신 공지사항 표시 (팀 + 세법 통합)
    from services.announcement_service import get_announcement_service
    announcement_service = get_announcement_service()
    
    # 최신 공지 3개 가져오기 (팀 + 세법 섞여서)
    latest_announcements = announcement_service.get_latest_announcements_for_dashboard(limit=3)

    if latest_announcements:
        for ann in latest_announcements:
            # 카테고리 태그
            category = ann.get('category', '팀')
            if category == '세법':
                tag = " <세법>"
                tag_color = "#FFF3CD"  # 노란색
            else:
                tag = " <팀>"
                tag_color = "#E3F2FD"  # 파란색
            
            # 공지사항 카드
            st.markdown(f"""
            <div style="
                background: {tag_color}; 
                border-left: 4px solid {'#F59E0B' if category == '세법' else '#2196F3'};
                border-radius: 6px;
                padding: 0.75rem;
                margin-bottom: 0.75rem;
            ">
                <div style="font-size: 0.75rem; color: #6B7280; margin-bottom: 0.25rem;">
                    {tag}
                </div>
                <div style="font-weight: 600; color: #1F2937; margin-bottom: 0.25rem;">
                    {ann.get('title', '제목 없음')}
                </div>
                <div style="font-size: 0.8rem; color: #6B7280;">
                    {announcement_service.get_time_ago(ann.get('created_at', ''))}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("아직 공지사항이 없습니다.")

    # 공지사항 목록 버튼
    if st.button("공지사항 목록", key="announcement_list", use_container_width=True):
        st.switch_page("pages/announcements.py")
    
    st.markdown("---")
    
    # 외부 사이트
    st.markdown("### 외부 사이트")
    
    # 외부 사이트 링크 6개
    external_sites = [
        {"name": "홈택스", "url": "https://www.hometax.go.kr"},
        {"name": "위택스", "url": "https://www.wetax.go.kr"},
        {"name": "국세법령정보시스템", "url": "https://taxlaw.nts.go.kr"},
        {"name": "지방세법령정보시스템", "url": "https://www.elis.go.kr"},
        {"name": "A.Biz", "url": "https://www.adotbiz.ai/gbaa"},
        {"name": "A.Biz Pro 세무", "url": "https://tax.adotbiz.ai/chat"}
    ]
    
    # 외부 사이트 링크를 HTML 버튼으로 직접 생성
    for site in external_sites:
        if site['url'] != "#":
            st.markdown(f"""
            <a href="{site['url']}" target="_blank" style="text-decoration: none;">
                <div class="external-site-btn">
                    {site['name']}
                </div>
            </a>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="external-site-btn disabled">
                {site['name']} (설정 예정)
            </div>
            """, unsafe_allow_html=True)
