import streamlit as st
import html  # ✅ 추가
from utils.schedule_manager import get_upcoming_deadline, get_recent_past_deadline
from utils.user_assignments import get_user_priority_task
from utils.activity_logger import get_recent_activities_for_sidebar

def _ensure_min_css():
    st.markdown("""
    <style>
    /* Streamlit 기본 transform 로직은 유지, 클리핑만 해제 */
    div[data-testid="stAppViewContainer"]{ overflow:visible !important; }
    header[data-testid="stHeader"]{ z-index:200 !important; }
    .block-container{ overflow:visible !important; }

    /* 🔔 토글 버튼(키: right_toggle_btn) 자체를 화면 우상단에 고정 */
    button[data-testid*="right_toggle_btn"]{
      position: fixed !important;
      top: 20px !important;
      right: 20px !important;
      z-index: 2147483000 !important;
      background: var(--gold) !important;
      color: var(--gray-900) !important;
      border: none !important;
      border-radius: 50% !important;
      width: 50px !important;
      height: 50px !important;
      font-size: 1.2rem !important;
      box-shadow: 0 4px 12px rgba(0,0,0,.15) !important;
      text-align: center !important;
    }
    button[data-testid*="right_toggle_btn"]:hover{
      transform: scale(1.05) !important;
      box-shadow: 0 6px 16px rgba(0,0,0,.2) !important;
      background: var(--gold-600) !important;
    }

    /* 담당자 업무 스타일 */
    .notification-item.assignment {
      background: #F0F9FF;
      border-left: 4px solid #0EA5E9;
    }
    
    .notification-item.assignment .notification-icon {
      color: #0EA5E9;
    }
                
    /* 오른쪽 패널 / 오버레이 */
    .right-sidebar{position:fixed !important; top:0; right:-400px; width:380px; height:100vh;
      background:#fff !important; z-index:2147483000 !important; box-shadow:-4px 0 20px rgba(0,0,0,.15);
      transition:right .3s cubic-bezier(.4,0,.2,1); overflow-y:auto; border-left:3px solid var(--gold);}
    .right-sidebar.open{right:0;}
    .right-sidebar-overlay{position:fixed !important; top:0; left:0; width:100vw; height:100vh;
      background:rgba(0,0,0,.35); z-index:2147482999 !important; backdrop-filter:blur(2px); pointer-events:none;}
    </style>
    """, unsafe_allow_html=True)


def _init_state():
    if "right_sidebar_open" not in st.session_state:
        st.session_state["right_sidebar_open"] = False

def _toggle_open():
    st.session_state["right_sidebar_open"] = not st.session_state["right_sidebar_open"]

def _close():
    st.session_state["right_sidebar_open"] = False

def _render_toggle_button():
    label = "✖" if st.session_state["right_sidebar_open"] else "🔔"
    st.button(label, key="right_toggle_btn", on_click=_toggle_open, help="알림 및 최근 활동")

def _render_panel(notifications, activities):
    # 오버레이
    st.markdown('<div class="right-sidebar-overlay"></div>', unsafe_allow_html=True)

    # ✅ HTML escape 함수 추가
    def escape(text):
        """HTML 특수문자 이스케이프"""
        if text is None:
            return ""
        return html.escape(str(text))

    def _notif_html(n):
        return (
            '<div class="notification-item {typ}">'
            '<div class="notification-icon">{icon}</div>'
            '<div class="notification-content">'
            '<div class="notification-title">{title}</div>'
            '<div class="notification-desc">{desc}</div>'
            '<div class="notification-time">{time}</div>'
            '</div></div>'
        ).format(
            typ=escape(n.get("type", "todo")),
            icon=escape(n.get("icon", "🔔")),
            title=escape(n.get("title", "제목")),
            desc=escape(n.get("desc", "설명")),
            time=escape(n.get("time", "방금")),
        )

    def _act_html(a):
        return (
            '<div class="activity-item">'
            '<div class="activity-icon">{icon}</div>'
            '<div class="activity-content">'
            '<div class="activity-title">{title}</div>'
            '<div class="activity-desc">{desc}</div>'
            '<div class="activity-time">{time}</div>'
            '</div></div>'
        ).format(
            icon=escape(a.get("icon", "")),
            title=escape(a.get("title", "처리 내역")),
            desc=escape(a.get("desc", "설명")),
            time=escape(a.get("time", "방금")),
        )

    notif_items = "".join(_notif_html(n) for n in notifications[:3])
    act_items   = "".join(_act_html(a)   for a in activities[:3])

    # 패널 전체
    panel_html = (
        '<aside class="right-sidebar open">'
        '<div class="right-sidebar-header"><h3>알림 & 활동</h3></div>'
        '<section class="notification-section"><div class="section-title">최근 알림</div>'
        f'{notif_items}'
        '</section>'
        '<section class="activity-section"><div class="section-title">최근 처리 내역</div>'
        f'{act_items}'
        '</section>'
        '</aside>'
    )
    st.markdown(panel_html, unsafe_allow_html=True)


def right_sidebar(
    notifications=None,
    activities=None,
):
    _ensure_min_css()
    _init_state()

    # ✅ 예외 처리 추가
    try:
        # 실제 데이터 생성 (없으면)
        if notifications is None:
            notifications = []
            
            # 1. 담당자별 우선순위 업무
            user = st.session_state.get("user", {})
            username = user.get("name") or user.get("username") or "사용자"
            
            # 게스트가 아닐 때만 실행
            if user.get("role") != "게스트":
                user_task = get_user_priority_task(username)
                if user_task:
                    notifications.append({
                        "type": "assignment", 
                        "icon": user_task.get("icon", ""), 
                        "title": f"{user_task.get('tax_type', '업무')} 담당 업무", 
                        "desc": user_task.get("task", ""), 
                        "time": "확인 필요"
                    })
            
            # 2. 가장 임박한 일정
            upcoming = get_upcoming_deadline()
            if upcoming:
                notifications.append({
                    "type": "upcoming", 
                    "icon": upcoming.get("icon", ""), 
                    "title": upcoming.get("title", "일정"), 
                    "desc": f"마감일: {upcoming.get('display_date', '')}", 
                    "time": f"D-{upcoming.get('days_left', 0)}"
                })
            
            # 3. 가장 최근 지난 일정
            past = get_recent_past_deadline()
            if past:
                notifications.append({
                    "type": "completed", 
                    "icon": past.get("icon", ""), 
                    "title": past.get("title", "일정"), 
                    "desc": f"완료일: {past.get('display_date', '')}", 
                    "time": f"D+{past.get('days_passed', 0)}"
                })
            
            # 기본 데이터가 없으면 더미 데이터 제공
            if not notifications:
                notifications = [
                    {"type": "todo", "icon": "", "title": "담당 업무 설정", "desc": "사용자 정보를 설정하세요", "time": "설정 필요"},
                    {"type": "upcoming", "icon": "", "title": "일정 확인", "desc": "세무 일정을 확인하세요", "time": "확인 필요"},
                    {"type": "completed", "icon": "", "title": "시스템 준비", "desc": "TAXi 시스템이 준비되었습니다", "time": "방금"},
                ]

        if activities is None:
            # 실제 활동 로그에서 데이터 가져오기
            activities = get_recent_activities_for_sidebar(limit=3)
            
            # 활동 로그가 없으면 기본 안내 메시지
            if not activities:
                activities = [
                    {"icon": "ℹ", "title": "아직 처리된 내역이 없습니다", "desc": "세무 업무를 처리하면 여기에 표시됩니다", "time": "-"},
                    {"icon": "", "title": "TAXi 시작하기", "desc": "원천세, 법인세, 부가세 업무를 시작해보세요", "time": "지금"},
                    {"icon": "", "title": "도움말 보기", "desc": "시스템 사용법을 확인하세요", "time": "언제든지"},
                ]

    except Exception as e:
        # ✅ 오류 발생 시 기본 데이터로 대체
        st.error(f"알림 데이터 로딩 오류: {e}")
        notifications = [
            {"type": "error", "icon": "", "title": "알림 로딩 오류", "desc": "잠시 후 다시 시도해주세요", "time": "방금"}
        ]
        activities = []

    # 🔔 토글 버튼(항상 표시)
    _render_toggle_button()

    # 패널 열림 상태라면 렌더
    if st.session_state["right_sidebar_open"]:
        _render_panel(notifications, activities)