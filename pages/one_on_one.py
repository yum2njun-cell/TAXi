# pages/one_on_one.py

import streamlit as st
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from utils.state import ensure_app_state, get_user_session
from datetime import datetime
from services.one_on_one_service import OneOnOneService
from utils.auth import is_guest, check_permission

ensure_app_state()

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 1on1 관리", 
    page_icon="", 
    layout="wide"
)

# 스타일 로드
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 기본 페이지 네비게이션 숨기기
st.markdown("""
<style>
[data-testid="stSidebarNav"] ul,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] a {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()

# 페이지 헤더
page_header("1on1 미팅 관리", "💬")

# 현재 로그인한 사용자 정보 가져오기
current_user = get_user_session()
current_user_name = current_user.get("name", "")

if not current_user_name:
    st.error(" 사용자 정보를 불러올 수 없습니다. 다시 로그인해주세요.")
    st.stop()

# 1on1 서비스 초기화 (현재 사용자 이름 전달)
service = OneOnOneService(current_user_name=current_user_name)

# 권한 확인
is_admin = service.is_admin()

# 관리자 표시
if is_admin:
    st.info(" 관리자 권한으로 로그인하셨습니다. 모든 팀원의 1on1 기록을 관리할 수 있습니다.")

# 메인 컨텐츠
st.markdown("---")

# 레이아웃: 왼쪽(팀원 목록), 오른쪽(미팅 기록)
col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("### 팀원 관리")
    
    # 관리자만 팀원 추가 가능
    if is_admin:
        with st.expander(" 새 팀원 추가", expanded=False):
            with st.form("new_member_form", clear_on_submit=True):
                new_name = st.text_input("이름")
                new_email = st.text_input("이메일 (선택)")
                submitted = st.form_submit_button("팀원 추가", use_container_width=True, disabled=is_guest())

                if submitted and new_name:
                    if check_permission("팀원 추가"):
                        success, message = service.add_team_member(new_name, new_email)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        
        st.markdown("---")
    
    # 팀원 목록 (권한에 따라 필터링됨)
    team_members = service.get_team_members()
    
    if not team_members:
        if is_admin:
            st.info("등록된 팀원이 없습니다. 팀원을 추가해주세요.")
        else:
            st.warning(" 귀하의 이름으로 등록된 팀원 정보가 없습니다.\n관리자에게 문의해주세요.")
    else:
        st.markdown("### 팀원 선택")
        
        # 팀원 선택
        member_names = [member['name'] for member in team_members]
        
        # 일반 사용자는 선택 불가 (자기 자신만 표시)
        if len(member_names) == 1:
            selected_name = member_names[0]
            st.markdown(f"""
            <div class="stats-card">
                <div style="font-size: 1.1rem; font-weight: 600; color: var(--gold-600);">
                    {selected_name}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            selected_name = st.selectbox(
                "누구와의 1on1인가요?",
                options=member_names,
                key="selected_member"
            )
        
        # 선택된 팀원 정보
        selected_member = next((m for m in team_members if m['name'] == selected_name), None)
        
        if selected_member:
            # 팀원 정보 카드
            st.markdown(f"""
            <div class="stats-card">
                <div style="font-size: 1.2rem; font-weight: 600; margin-bottom: 0.5rem;">
                    {selected_member['name']}
                </div>
                <div style="font-size: 0.9rem; color: var(--gray-500);">
                    {selected_member['email'] or '이메일 미등록'}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # 미팅 통계
            meetings = service.get_meetings_by_member(selected_member['id'])
            last_meeting = meetings[0]['meeting_date'] if meetings else "없음"
            
            st.markdown(f"""
            <div class="stats-card">
                <div class="stat-number">{len(meetings)}</div>
                <div class="stat-label">총 미팅 횟수</div>
            </div>
            <div class="stats-card">
                <div style="font-size: 1rem; font-weight: 600; color: var(--gray-900);">
                    {last_meeting}
                </div>
                <div class="stat-label">최근 미팅</div>
            </div>
            """, unsafe_allow_html=True)

with col2:
    if not team_members:
        st.info("팀원을 선택해주세요.")
    elif selected_member:
        st.markdown(f"### {selected_name} 님과의 1on1")
        
        # 권한 안내 (일반 사용자인 경우)
        if not is_admin and selected_name == current_user_name:
            st.info(" 본인의 1on1 기록만 조회 가능합니다.")
        
        # 새로운 미팅 기록 추가
        with st.expander(" 새로운 미팅 기록하기", expanded=True):
            with st.form("new_meeting_form", clear_on_submit=True):
                meeting_date = st.date_input(
                    "미팅 날짜",
                    value=datetime.now()
                )
                summary = st.text_area(
                    "미팅 주요 내용",
                    height=250,
                    placeholder="• 논의한 주요 주제\n• 피드백 내용\n• 액션 아이템\n• 다음 미팅 주제 등을 자유롭게 기록하세요."
                )
                
                col_submit, col_cancel = st.columns([3, 1])
                with col_submit:
                    submit_meeting = st.form_submit_button(
                        " 기록 저장",
                        use_container_width=True,
                        type="primary",
                        disabled=is_guest()
                    )

                    if submit_meeting and summary:
                        if check_permission("1on1 기록 저장"):
                            success, message = service.add_meeting(
                                selected_member['id'],
                                meeting_date,
                                summary
                            )
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    elif submit_meeting and not summary:
                        st.warning("미팅 내용을 입력해주세요.")
        
        st.markdown("---")
        
        # 과거 미팅 기록
        st.markdown("###  과거 미팅 기록")
        
        meetings = service.get_meetings_by_member(selected_member['id'])
        
        if not meetings:
            st.info("아직 기록된 1on1이 없습니다.")
        else:
            for idx, meeting in enumerate(meetings):
                with st.expander(
                    f"**{meeting['meeting_date']}** (작성일: {meeting['created_at'][:10]})",
                    expanded=(idx == 0)  # 최신 기록만 펼침
                ):
                    # 미팅 내용
                    st.markdown(f"""
                    <div style="
                        background: white;
                        padding: 1rem;
                        border-radius: 8px;
                        border-left: 4px solid var(--gold);
                        white-space: pre-wrap;
                        line-height: 1.8;
                        margin-bottom: 1rem;
                    ">
                    {meeting['summary']}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # 삭제 버튼
                    if st.button(
                        "기록 삭제",
                        key=f"delete_{meeting['id']}",
                        help="이 미팅 기록을 삭제합니다.",
                        disabled=is_guest()
                    ):
                        if check_permission("1on1 기록 삭제"):
                            success, message = service.delete_meeting(meeting['id'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)