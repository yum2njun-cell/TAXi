import streamlit as st
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from components.calendar_widget import render_calendar
from services.enhanced_tax_calendar_service import get_enhanced_calendar_service
from datetime import datetime, timedelta
from components.theme import apply_custom_theme
import calendar
calendar.setfirstweekday(6)
import holidays
from utils.auth import is_guest, check_permission

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

st.set_page_config(
    page_title=f"{settings.APP_NAME} | TAXday", 
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

# 페이지 헤더
page_header("TAXday", "")

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()

# 세무 달력 서비스 초기화
tax_service = get_enhanced_calendar_service()

# 세션 상태 초기화
if "current_year" not in st.session_state:
    st.session_state.current_year = datetime.now().year
if "current_month" not in st.session_state:
    st.session_state.current_month = datetime.now().month
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None
if "search_results" not in st.session_state:
    st.session_state.search_results = []

def search_schedules(keyword, tax_service, start_date=None, end_date=None):
    """키워드로 일정 검색 (공휴일 포함, 기간 설정 가능)"""
    results = []
    
    # 기간 설정이 없으면 현재 연도 전체를 대상으로
    if start_date is None:
        start_date = datetime(st.session_state.current_year, 1, 1).date()
    if end_date is None:
        end_date = datetime(st.session_state.current_year, 12, 31).date()
    
    # 세무 일정 검색
    if hasattr(st.session_state, 'tax_schedules'):
        for date_str, schedules in st.session_state.tax_schedules.items():
            try:
                schedule_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                # 기간 체크
                if start_date <= schedule_date <= end_date:
                    for schedule in schedules:
                        if (keyword.lower() in schedule['title'].lower() or 
                            keyword.lower() in schedule['description'].lower()):
                            results.append({
                                'date': date_str,
                                'title': schedule['title'],
                                'description': schedule['description'],
                                'category': schedule['category'],
                                'type': 'schedule'
                            })
            except ValueError:
                continue
    
    # 공휴일 검색 추가 (설정된 기간의 연도들을 포함)
    if keyword:
        years = list(range(start_date.year, end_date.year + 1))
        for year in years:
            korea_holidays = holidays.SouthKorea(years=year)
            for date, name in korea_holidays.items():
                if (start_date <= date <= end_date and 
                    keyword.lower() in name.lower()):
                    results.append({
                        'date': date.strftime("%Y-%m-%d"),
                        'title': f"🎌 {name}",
                        'description': "공휴일",
                        'category': '공휴일',
                        'type': 'holiday'
                    })
    
    return sorted(results, key=lambda x: x['date'])

# 상단 네비게이션 섹션
nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns([1, 1, 2, 1, 1])

# 간단한 달력 네비게이션 (TAXday 제목 바로 밑)
nav_col1, nav_col2, nav_col3 = st.columns([1, 2, 1])

with nav_col1:
    if st.button("◀ 이전달"):
        if st.session_state.current_month == 1:
            st.session_state.current_month = 12
            st.session_state.current_year -= 1
        else:
            st.session_state.current_month -= 1

with nav_col2:
    st.markdown(f"<h3 style='text-align: center; margin: 0;'>{st.session_state.current_year}년 {st.session_state.current_month}월</h3>", unsafe_allow_html=True)

with nav_col3:
    if st.button("다음달 ▶"):
        if st.session_state.current_month == 12:
            st.session_state.current_month = 1
            st.session_state.current_year += 1
        else:
            st.session_state.current_month += 1

st.markdown("---")

# 메인 컨텐츠 영역
cal_col, manage_col = st.columns([2, 1])

with cal_col:
    # 필터 체크박스 - 사용자 설정 로드 및 저장
    from services.user_preferences_service import get_user_tax_categories, save_user_tax_categories

    st.markdown("#### 세목")

    # 사용자의 이전 선택 상태 로드
    user_selected_categories = get_user_tax_categories()

    filter_cols = st.columns(7)
    filter_categories = ['부', '법', '원', '지', '인', '국', '기']
    selected_categories = []

    # 체크박스 상태 변화 감지를 위한 키 생성
    if "prev_selected_categories" not in st.session_state:
        st.session_state.prev_selected_categories = user_selected_categories.copy()

    for i, category in enumerate(filter_categories):
        with filter_cols[i]:
            # 사용자 설정에서 로드한 값으로 초기 체크 상태 설정
            default_checked = category in user_selected_categories
            if st.checkbox(category, key=f"filter_{category}", value=default_checked):
                selected_categories.append(category)

    # 선택 상태가 변경되었으면 저장
    if selected_categories != st.session_state.prev_selected_categories:
        save_user_tax_categories(selected_categories)
        st.session_state.prev_selected_categories = selected_categories.copy()
    
    # 달력 렌더링
    render_calendar(
        year=st.session_state.current_year,
        month=st.session_state.current_month,
        selected_categories=selected_categories
    )

with manage_col:
    # 1. 일정 관리 (맨 위로 이동)
    if st.session_state.selected_date:
        selected_date_obj = datetime.strptime(st.session_state.selected_date, "%Y-%m-%d")
        st.markdown(f"#### {selected_date_obj.strftime('%m월 %d일')} 일정")
        
        schedules = tax_service.get_schedules_for_date(st.session_state.selected_date)
        
        if schedules:
            for i, schedule in enumerate(schedules):
                with st.expander(f"[{schedule['category']}] {schedule['title']}", expanded=False):
                    st.write(f"**설명:** {schedule['description']}")
                    schedule_type_label = "공통일정" if schedule.get('schedule_type') == 'common' else "개인일정"
                    if schedule.get('is_default', False):
                        schedule_type_label = "기본일정"
                    st.write(f"**구분:** {schedule_type_label}")
                    
                    # 수정/삭제/숨기기 버튼
                    is_default = schedule.get('is_default', False)
                    
                    if is_default:
                        # 기본 일정: 숨기기만 가능
                        col1, col2 = st.columns(2)
                        with col1:
                            st.caption("기본 일정 (수정 불가)")
                        with col2:
                            if st.button("숨기기", key=f"hide_{i}", disabled=is_guest()):
                                if check_permission("일정 관리"):
                                    success, message = tax_service.hide_default_schedule(st.session_state.selected_date, i)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                                    st.rerun()
                    else:
                        # 개인 일정: 수정/삭제 가능
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("수정", key=f"edit_{i}", disabled=is_guest()):
                                if check_permission("일정 수정"):
                                    st.session_state.edit_schedule_index = i
                                    st.rerun()
                        with col2:
                            if st.button("삭제", key=f"delete_{i}", disabled=is_guest()):
                                if check_permission("일정 삭제"):
                                    success, message = tax_service.delete_schedule(st.session_state.selected_date, i)
                                    if success:
                                        st.success(message)
                                    else:
                                        st.error(message)
                                    st.rerun()
        else:
            st.info("선택된 날짜에 일정이 없습니다.")
    else:
        st.markdown("#### 일정 관리")
        st.info("달력에서 날짜를 클릭하여 일정을 관리하세요.")
    
    st.markdown("---")
    
    # 숨긴 기본 일정 관리
    with st.expander("숨긴 기본 일정 관리", expanded=False):
        from services.user_preferences_service import get_hidden_default_schedules, remove_hidden_default_schedule, clear_all_hidden_schedules
        
        hidden_schedules = get_hidden_default_schedules()
        
        if hidden_schedules:
            st.write(f"총 **{len(hidden_schedules)}개**의 기본 일정이 숨겨져 있습니다.")
            
            # 전체 보이기 버튼
            if st.button("전체 다시 보이기", disabled=is_guest()):
                if check_permission("일정 관리"):
                    clear_all_hidden_schedules()
                    st.success("모든 숨긴 일정이 다시 표시됩니다!")
                    st.rerun()
            
            st.markdown("---")
            
            # 개별 일정 목록
            for hidden_key in hidden_schedules:
                try:
                    date_str, title = hidden_key.split("|", 1)
                    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{date_obj.strftime('%m/%d')}** {title}")
                    with col2:
                        if st.button("보이기", key=f"show_{hidden_key}", disabled=is_guest()):
                            if check_permission("일정 관리"):
                                remove_hidden_default_schedule(date_str, title)
                                st.success("일정이 다시 표시됩니다!")
                                st.rerun()
                except ValueError:
                    continue
        else:
            st.info("숨긴 기본 일정이 없습니다.")

    # 2. 날짜 이동
    # 오늘로 버튼
    today_col1, today_col2 = st.columns([1, 1])
    with today_col1:
        if st.button("TODAY"):
            st.session_state.current_year = datetime.now().year
            st.session_state.current_month = datetime.now().month
    
    st.markdown("#### 날짜 이동")
    year_col, month_col = st.columns(2)
    with year_col:
        selected_year = st.selectbox("년도", range(2021, 2028), 
                                   index=st.session_state.current_year-2021)
    with month_col:
        selected_month = st.selectbox("월", range(1, 13), 
                                    index=st.session_state.current_month-1)
    
    if st.button("이동", use_container_width=True):
        st.session_state.current_year = selected_year
        st.session_state.current_month = selected_month
    
    st.markdown("---")

    # 3. 키워드 검색 
    st.markdown("#### 키워드 검색")

    # 기간 설정
    with st.expander("검색 기간 설정", expanded=False):
        period_col1, period_col2 = st.columns(2)
        with period_col1:
            start_date = st.date_input(
                "시작일", 
                value=datetime(st.session_state.current_year, 1, 1),
                key="search_start_date"
            )
        with period_col2:
            end_date = st.date_input(
                "종료일", 
                value=datetime(st.session_state.current_year, 12, 31),
                key="search_end_date"
            )

    # 키워드 입력
    search_keyword = st.text_input("검색어", placeholder="키워드를 입력하세요...")

    if st.button("검색", use_container_width=True):
        if search_keyword:
            if start_date <= end_date:
                results = search_schedules(search_keyword, tax_service, start_date, end_date)
                st.session_state.search_results = results
                st.session_state.search_keyword = search_keyword
                st.session_state.search_period = f"{start_date.strftime('%Y.%m.%d')} ~ {end_date.strftime('%Y.%m.%d')}"
            else:
                st.error("시작일이 종료일보다 늦을 수 없습니다.")
                st.session_state.search_results = []
        else:
            st.session_state.search_results = []

    # 검색 결과 표시 (페이지네이션 버전)
    if st.session_state.search_results:
        # 검색 정보 표시
        search_info = f"**'{st.session_state.get('search_keyword', '')}'** 검색 결과 ({len(st.session_state.search_results)}건)"
        if hasattr(st.session_state, 'search_period'):
            search_info += f"\n {st.session_state.search_period}"
        st.markdown(search_info)
        
        # 페이지네이션 설정
        if 'search_page' not in st.session_state:
            st.session_state.search_page = 0
        
        results_per_page = 5
        total_results = len(st.session_state.search_results)
        total_pages = (total_results + results_per_page - 1) // results_per_page
        
        start_idx = st.session_state.search_page * results_per_page
        end_idx = min(start_idx + results_per_page, total_results)
        displayed_results = st.session_state.search_results[start_idx:end_idx]
        
        # 검색 결과를 expander로 감싸서 공간 절약
        with st.expander("🔍 검색 결과 목록", expanded=True):
            for i, result in enumerate(displayed_results):
                date_str = result['date']
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                
                # 결과 타입에 따른 아이콘
                if result['type'] == 'holiday':
                    icon = ""
                else:
                    icon = ""
                
                # 컬럼으로 나누어서 표시
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"{icon} **{date_obj.strftime('%m/%d')}** [{result['category']}] {result['title']}")
                    st.caption(result['description'][:40] + ('...' if len(result['description']) > 40 else ''))
                
                with col2:
                    if st.button("이동", key=f"goto_{start_idx + i}", help=f"{date_obj.strftime('%Y년 %m월 %d일')}로 이동"):
                        st.session_state.current_year = date_obj.year
                        st.session_state.current_month = date_obj.month
                        st.session_state.selected_date = date_str
                        st.rerun()
                
                if i < len(displayed_results) - 1:
                    st.divider()
        
        # 페이지네이션 컨트롤
        if total_pages > 1:
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col1:
                if st.session_state.search_page > 0:
                    if st.button("◀ 이전", key="prev_search_page"):
                        st.session_state.search_page -= 1
                        st.rerun()
            
            with col2:
                # 현재 페이지 정보 및 더 있음 알림
                current_page = st.session_state.search_page + 1
                remaining_results = total_results - end_idx
                
                if remaining_results > 0:
                    page_info = f" {current_page}/{total_pages} 페이지 (+ {remaining_results}개 항목 더 있음)"
                else:
                    page_info = f" {current_page}/{total_pages} 페이지"
                    
                st.markdown(f"<div style='text-align: center; font-size: 0.9em; color: #666;'>{page_info}</div>", 
                        unsafe_allow_html=True)
            
            with col3:
                if st.session_state.search_page < total_pages - 1:
                    if st.button("다음 ▶", key="next_search_page"):
                        st.session_state.search_page += 1
                        st.rerun()
            
            # 빠른 페이지 이동 (많은 결과가 있을 때)
            if total_pages > 3:
                st.markdown("---")
                quick_col1, quick_col2 = st.columns([1, 1])
                
                with quick_col1:
                    if st.button("🔝 첫 페이지", key="first_page"):
                        st.session_state.search_page = 0
                        st.rerun()
                
                with quick_col2:
                    if st.button("🔚 마지막 페이지", key="last_page"):
                        st.session_state.search_page = total_pages - 1
                        st.rerun()
        
        # 검색 결과 지우기 버튼
        if st.button(" 검색 결과 지우기", use_container_width=True):
            st.session_state.search_results = []
            st.session_state.search_page = 0  # 페이지도 초기화
            if 'search_keyword' in st.session_state:
                del st.session_state.search_keyword
            if 'search_period' in st.session_state:
                del st.session_state.search_period
            st.rerun()

    elif hasattr(st.session_state, 'search_keyword') and st.session_state.search_keyword:
        st.info("검색 결과가 없습니다.")
    
    st.markdown("---")

    # 이번 달 공휴일 표시
    st.markdown("####  이번 달 공휴일")
    korea_holidays = holidays.SouthKorea(years=st.session_state.current_year)
    month_holidays = []
    for date, name in korea_holidays.items():
        if date.year == st.session_state.current_year and date.month == st.session_state.current_month:
            month_holidays.append((date.day, name))
    
    if month_holidays:
        for day, name in sorted(month_holidays):
            st.write(f"• {st.session_state.current_month}월 {day}일: {name}")
    else:
        st.write("이번 달에는 공휴일이 없습니다.")
    
    st.markdown("---")
    
    # 일정 추가 섹션
    st.markdown("#### ➕ 일정 추가")
    
    # 5. 일정 추가 섹션 (expander로 감싸기)
    with st.expander("➕ 일정 추가", expanded=False):
        with st.form("add_schedule_form"):
            add_date = st.date_input("날짜", 
                                value=datetime(st.session_state.current_year, 
                                                st.session_state.current_month, 1))
            add_title = st.text_input("일정 제목")
            category_options = {
                '부가세': '부', '법인세': '법', '원천세': '원',
                '지방세': '지', '인지세': '인', '국세': '국', '기타': '기'
            }
            add_category_display = st.selectbox("세목", list(category_options.keys()))
            add_category = category_options[add_category_display]
            add_description = st.text_area("상세 설명")
            
            # 일정 유형 선택
            schedule_type = st.radio(
                "일정 유형", 
                options=['personal', 'common'],
                format_func=lambda x: "개인 일정" if x == 'personal' else "공통 일정 (모든 사용자가 볼 수 있음)",
                index=0
            )
            
            if st.form_submit_button("일정 추가", disabled=is_guest()):
                if check_permission("일정 추가"):
                    if add_title and add_description:
                        date_str = add_date.strftime("%Y-%m-%d")
                        success = tax_service.add_schedule(
                            date_str, add_title, add_category, add_description, schedule_type
                        )
                        if success:
                            st.success(f"{'공통' if schedule_type == 'common' else '개인'} 일정이 추가되었습니다!")
                            st.rerun()
                        else:
                            st.error("일정 추가에 실패했습니다.")
                    else:
                        st.error("제목과 설명을 모두 입력해주세요.")
    
    st.markdown("---")


# 일정 수정 모달 (세션 상태로 관리)
if "edit_schedule_index" in st.session_state and st.session_state.selected_date:
    schedules = tax_service.get_schedules_for_date(st.session_state.selected_date)
    if st.session_state.edit_schedule_index < len(schedules):
        schedule = schedules[st.session_state.edit_schedule_index]
        
        st.markdown("---")
        st.markdown("#### 일정 수정")
        
        # 기존 edit form을 다음으로 교체:
        with st.form("edit_schedule_form"):
            edit_title = st.text_input("일정 제목", value=schedule['title'])
            category_options = {
                '부가세': '부', '법인세': '법', '원천세': '원',
                '지방세': '지', '인지세': '인', '국제조세': '국', '기타': '기'
            }
            current_display = [k for k, v in category_options.items() if v == schedule['category']][0]
            edit_category_display = st.selectbox("세목", list(category_options.keys()), 
                                            index=list(category_options.keys()).index(current_display))
            edit_category = category_options[edit_category_display]
            edit_description = st.text_area("상세 설명", value=schedule['description'])
            
            col1, col2 = st.columns(2)
            with col1:
                with col1:
                    if st.form_submit_button("수정 완료", disabled=is_guest()):
                        if check_permission("일정 수정"):
                            success = tax_service.update_schedule(
                                st.session_state.selected_date, 
                                st.session_state.edit_schedule_index,
                                edit_title, edit_category, edit_description
                            )
                            if success:
                                del st.session_state.edit_schedule_index
                                st.success("일정이 수정되었습니다!")
                                st.rerun()
                            else:
                                st.error("일정 수정에 실패했습니다. (권한이 없거나 기본 일정입니다)")
            
            with col2:
                if st.form_submit_button("취소"):
                    del st.session_state.edit_schedule_index
                    st.rerun()
