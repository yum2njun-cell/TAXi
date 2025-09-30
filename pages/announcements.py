import streamlit as st
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from services.announcement_service import get_announcement_service
from services.auth_service import get_current_user_info
from datetime import datetime
from components.theme import apply_custom_theme
from utils.auth import is_guest, check_permission

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 공지사항", 
    page_icon="", 
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

/* 공지사항 카드 스타일 */
.announcement-card {
    background: white;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
    transition: box-shadow 0.2s;
}

.announcement-card:hover {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.announcement-title {
    font-size: 1.2rem;
    font-weight: 600;
    color: #1F2937;
    margin-bottom: 0.5rem;
}

.announcement-meta {
    font-size: 0.875rem;
    color: #6B7280;
    margin-bottom: 1rem;
}

.announcement-content {
    color: #374151;
    line-height: 1.6;
    margin-bottom: 1rem;
}

.announcement-actions {
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}
</style>
""", unsafe_allow_html=True)

# 페이지 헤더
page_header("공지사항", "")

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()

# 공지사항 서비스 초기화
announcement_service = get_announcement_service()
current_user = get_current_user_info()

# 세션 상태 초기화
if "announcement_page" not in st.session_state:
    st.session_state.announcement_page = 1
if "announcement_mode" not in st.session_state:
    st.session_state.announcement_mode = "list"  # list, create, edit
if "selected_announcement" not in st.session_state:
    st.session_state.selected_announcement = None

# 상단 액션 버튼들
col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

with col1:
    st.markdown("###  팀 공지사항")

with col2:
    if st.button(" 새 공지사항", type="primary", disabled=is_guest()):
        if check_permission("공지사항 작성"):
            st.session_state.announcement_mode = "create"
            st.rerun()

with col3:
    if st.button(" 내 공지사항"):
        st.session_state.announcement_mode = "my_announcements"
        st.rerun()

with col4:
    if st.button(" 목록보기"):
        st.session_state.announcement_mode = "list"
        st.session_state.announcement_page = 1
        st.rerun()

st.markdown("---")

# 모드별 화면 렌더링
if st.session_state.announcement_mode == "create":
    # 새 공지사항 작성
    st.markdown("###  새 공지사항 작성")
    
    with st.form("create_announcement"):
        title = st.text_input("제목", placeholder="공지사항 제목을 입력하세요")
        content = st.text_area("내용", height=200, placeholder="공지사항 내용을 입력하세요")
        
        col1, col2 = st.columns(2)
        with col1:
            submit_btn = st.form_submit_button(" 공지사항 발행", type="primary", use_container_width=True, disabled=is_guest())
            if submit_btn:
                if check_permission("공지사항 발행"):
                    if title.strip() and content.strip():
                        success = announcement_service.create_announcement(title.strip(), content.strip())
                        if success:
                            st.success("공지사항이 발행되었습니다!")
                            st.session_state.announcement_mode = "list"
                            st.session_state.announcement_page = 1
                            st.rerun()
                        else:
                            st.error("공지사항 발행에 실패했습니다.")
                    else:
                        st.error("제목과 내용을 모두 입력해주세요.")
        
        with col2:
            if st.form_submit_button("취소", use_container_width=True):
                st.session_state.announcement_mode = "list"
                st.rerun()

elif st.session_state.announcement_mode == "edit":
    # 공지사항 수정
    announcement = st.session_state.selected_announcement
    if announcement:
        st.markdown("###  공지사항 수정")
        
        with st.form("edit_announcement"):
            title = st.text_input("제목", value=announcement.get('title', ''))
            content = st.text_area("내용", value=announcement.get('content', ''), height=200)
            
            col1, col2 = st.columns(2)
            with col1:
                edit_btn = st.form_submit_button(" 수정 완료", type="primary", use_container_width=True, disabled=is_guest())
                if edit_btn:
                    if check_permission("공지사항 수정"):
                        if title.strip() and content.strip():
                            success = announcement_service.update_announcement(
                                announcement['id'], title.strip(), content.strip()
                            )
                            if success:
                                st.success("공지사항이 수정되었습니다!")
                                st.session_state.announcement_mode = "list"
                                st.session_state.selected_announcement = None
                                st.rerun()
                            else:
                                st.error("공지사항 수정에 실패했습니다.")
                        else:
                            st.error("제목과 내용을 모두 입력해주세요.")
            
            with col2:
                if st.form_submit_button("취소", use_container_width=True):
                    st.session_state.announcement_mode = "list"
                    st.session_state.selected_announcement = None
                    st.rerun()

elif st.session_state.announcement_mode == "my_announcements":
    # 내 공지사항 목록
    st.markdown("###  내가 작성한 공지사항")
    
    my_announcements, total_pages, total_count = announcement_service.get_user_announcements(
        page=st.session_state.announcement_page
    )
    
    if total_count > 0:
        st.info(f"총 {total_count}개의 공지사항을 작성하셨습니다.")
        
        for announcement in my_announcements:
            with st.expander(f" {announcement.get('title', '제목 없음')}", expanded=False):
                st.markdown(f"**작성일:** {announcement_service.format_date(announcement.get('created_at', ''))}")
                if announcement.get('updated_at') != announcement.get('created_at'):
                    st.markdown(f"**수정일:** {announcement_service.format_date(announcement.get('updated_at', ''))}")
                st.markdown(f"**상태:** {'활성' if announcement.get('is_active', True) else '삭제됨'}")
                st.markdown("**내용:**")
                st.write(announcement.get('content', ''))
                
                if announcement.get('is_active', True):
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(" 수정", key=f"edit_my_{announcement['id']}"):
                            st.session_state.selected_announcement = announcement
                            st.session_state.announcement_mode = "edit"
                            st.rerun()
                    with col2:
                        if st.button(" 삭제", key=f"delete_my_{announcement['id']}", disabled=is_guest()):
                            if check_permission("공지사항 삭제"):
                                if announcement_service.delete_announcement(announcement['id']):
                                    st.success("공지사항이 삭제되었습니다!")
                                    st.rerun()
                                else:
                                    st.error("삭제에 실패했습니다.")
    else:
        st.info("작성한 공지사항이 없습니다.")
        if st.button("첫 공지사항 작성하기"):
            st.session_state.announcement_mode = "create"
            st.rerun()

else:
    # 공지사항 목록 (기본 모드)
    # 검색 기능
    col1, col2 = st.columns([3, 1])
    with col1:
        search_keyword = st.text_input(" 검색", placeholder="제목, 내용, 작성자로 검색...")
    with col2:
        if st.button("검색", use_container_width=True):
            st.session_state.announcement_page = 1

    # 공지사항 조회
    if search_keyword:
        announcements, total_pages, total_count = announcement_service.search_announcements(
            search_keyword, page=st.session_state.announcement_page
        )
        st.info(f"'{search_keyword}' 검색 결과: {total_count}개")
    else:
        announcements, total_pages, total_count = announcement_service.get_announcements(
            page=st.session_state.announcement_page
        )

    if total_count > 0:
        # 공지사항 목록 표시
        for announcement in announcements:
            # 공지사항 카드
            st.markdown(f"""
            <div class="announcement-card">
                <div class="announcement-title">{announcement.get('title', '제목 없음')}</div>
                <div class="announcement-meta">
                     {announcement.get('author_name', '알 수 없음')} • 
                     {announcement_service.format_date(announcement.get('created_at', ''))} • 
                     {announcement_service.get_time_ago(announcement.get('created_at', ''))}
                </div>
                <div class="announcement-content">
                    {announcement.get('content', '내용 없음')[:200]}{'...' if len(announcement.get('content', '')) > 200 else ''}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 작성자인 경우 수정/삭제 버튼 표시
            if current_user and announcement.get('author_id') == current_user["user_id"]:
                col1, col2, col3 = st.columns([6, 1, 1])
                with col2:
                    if st.button("", key=f"edit_{announcement['id']}", help="수정", disabled=is_guest()):
                        if check_permission("공지사항 수정"):
                            st.session_state.selected_announcement = announcement
                            st.session_state.announcement_mode = "edit"
                            st.rerun()
                with col3:
                    if st.button("", key=f"delete_{announcement['id']}", help="삭제", disabled=is_guest()):
                        if check_permission("공지사항 삭제"):
                            if announcement_service.delete_announcement(announcement['id']):
                                st.success("공지사항이 삭제되었습니다!")
                                st.rerun()
                            else:
                                st.error("삭제에 실패했습니다.")
            
            st.markdown("---")
        
        # 페이지네이션
        if total_pages > 1:
            col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
            
            with col1:
                if st.session_state.announcement_page > 1:
                    if st.button("◀◀ 첫 페이지", key="first_page"):
                        st.session_state.announcement_page = 1
                        st.rerun()
            
            with col2:
                if st.session_state.announcement_page > 1:
                    if st.button("◀ 이전", key="prev_page"):
                        st.session_state.announcement_page -= 1
                        st.rerun()
            
            with col3:
                st.markdown(
                    f"<div style='text-align: center; padding: 0.5rem;'>"
                    f"<strong>{st.session_state.announcement_page}</strong> / {total_pages} 페이지 "
                    f"(총 {total_count}개)"
                    f"</div>", 
                    unsafe_allow_html=True
                )
            
            with col4:
                if st.session_state.announcement_page < total_pages:
                    if st.button("다음 ▶", key="next_page"):
                        st.session_state.announcement_page += 1
                        st.rerun()
            
            with col5:
                if st.session_state.announcement_page < total_pages:
                    if st.button("마지막 페이지 ▶▶", key="last_page"):
                        st.session_state.announcement_page = total_pages
                        st.rerun()
    else:
        st.info("공지사항이 없습니다.")
        if st.button("첫 공지사항 작성하기"):
            st.session_state.announcement_mode = "create"
            st.rerun()

# 통계 정보 (사이드바나 하단에 표시)
with st.expander(" 공지사항 통계"):
    stats = announcement_service.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("전체 공지사항", stats['total_count'])
    with col2:
        st.metric("활성 공지사항", stats['active_count'])
    with col3:
        st.metric("최근 30일", stats['recent_30days_count'])
    with col4:
        st.metric("삭제된 공지사항", stats['deleted_count'])
    
    if stats['author_stats']:
        st.markdown("**작성자별 통계:**")
        for author, count in list(stats['author_stats'].items())[:5]:
            st.write(f"• {author}: {count}개")