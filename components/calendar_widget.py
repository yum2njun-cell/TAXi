import streamlit as st
import calendar
import holidays
from datetime import datetime
from services.tax_calendar_service import TaxCalendarService

def get_korean_holidays(year):
    """한국 공휴일 조회"""
    korea_holidays = holidays.SouthKorea(years=year)
    return korea_holidays

def render_calendar(year=None, month=None, selected_categories=None):
    """달력 위젯 렌더링 - 순수 Streamlit 컴포넌트만 사용"""
    
    # 기본값 설정
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    if selected_categories is None:
        selected_categories = []
    
    # 세무 달력 서비스 초기화
    tax_service = TaxCalendarService()
    
    # 해당 월의 일정 조회
    month_schedules = tax_service.get_schedules_for_month(year, month)
    
    # 카테고리 필터 적용
    if selected_categories:
        month_schedules = tax_service.filter_schedules_by_category(month_schedules, selected_categories)
    
    # 한국 공휴일 조회
    korea_holidays = get_korean_holidays(year)
    
    # 달력 컨테이너
    with st.container():
        # 헤더
        st.markdown(f"#### 📅 {year}년 {month}월")
        
        # 요일 헤더 - 일요일부터 시작
        weekdays = ["일", "월", "화", "수", "목", "금", "토"]
        header_cols = st.columns(7)
        for i, day in enumerate(weekdays):
            with header_cols[i]:
                color = "#ff6b6b" if i == 0 else "#339af0" if i == 6 else "#495057"
                st.markdown(f"<div style='text-align: center; font-weight: bold; color: {color};'>{day}</div>", 
                           unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 달력 생성 - calendar.monthcalendar는 월요일부터 시작하므로 일요일부터 시작하도록 수정
        import calendar as cal_module
        cal_module.setfirstweekday(6)  # 일요일부터 시작 (6 = 일요일)
        cal = cal_module.monthcalendar(year, month)
        
        today = datetime.now()
        
        for week_num, week in enumerate(cal):
            week_cols = st.columns(7)
            for i, day in enumerate(week):
                with week_cols[i]:
                    if day == 0:
                        # 빈 날짜
                        st.write("")
                    else:
                        # 해당 날짜의 일정 조회
                        day_schedules = month_schedules.get(day, [])
                        
                        # 날짜 정보
                        current_date = datetime(year, month, day)
                        is_today = (year == today.year and month == today.month and day == today.day)
                        is_holiday = current_date.date() in korea_holidays
                        is_sunday = i == 0  # 일요일
                        is_saturday = i == 6  # 토요일
                        
                        # 날짜 클릭 처리를 위한 버튼
                        date_key = f"date_{year}_{month}_{day}"
                        
                        # 날짜 스타일 결정
                        if is_today:
                            button_style = "background-color: #ffd43b; color: #000; font-weight: bold; border: 2px solid #fab005;"
                        elif is_holiday:
                            button_style = "background-color: #ffdeeb; color: #e91e63; border: 1px solid #f8bbd9;"
                        elif is_sunday:
                            button_style = "background-color: #ffe0e0; color: #d63031; border: 1px solid #fab1a0;"
                        elif is_saturday:
                            button_style = "background-color: #e0f0ff; color: #0984e3; border: 1px solid #74b9ff;"
                        else:
                            button_style = "background-color: transparent; color: #2d3436; border: 1px solid #ddd;"
                        
                        # 버튼 HTML 생성
                        button_html = f"""
                        <button onclick="window.parent.postMessage({{type: 'streamlit:setComponentValue', value: '{date_key}'}}, '*')" 
                                style="width: 100%; height: 35px; margin: 2px 0; border-radius: 4px; cursor: pointer; {button_style}">
                            {day}
                        </button>
                        """
                        
                        # Streamlit 버튼 대신 HTML 버튼 사용 (스타일링을 위해)
                        if st.button(f"{day}", key=date_key, help=f"{year}년 {month}월 {day}일"):
                            # TAXday 페이지에서만 날짜 선택 기능 활성화
                            if hasattr(st.session_state, 'selected_date'):
                                st.session_state.selected_date = f"{year}-{month:02d}-{day:02d}"
                                st.rerun()
                        
                        # 특별 날짜 표시
                        labels = []
                        if is_today:
                            labels.append("**[오늘]**")
                        if is_holiday:
                            holiday_name = korea_holidays.get(current_date.date())
                            labels.append(f"🎌 {holiday_name}")
                        
                        for label in labels:
                            st.markdown(f"<div style='font-size: 0.7em; text-align: center; margin: 1px 0;'>{label}</div>", 
                                       unsafe_allow_html=True)
                        
                        # 일정 표시
                        if day_schedules:
                            category_labels = {
                                '부': '부가세', '법': '법인세', '원': '원천세', 
                                '지': '지방세', '인': '인지세', '국': '국제조세', '기': '기타'
                            }
                            
                            # 최대 2개까지만 표시
                            visible_schedules = day_schedules[:2]
                            for schedule in visible_schedules:
                                category = category_labels.get(schedule['category'], '기타')
                                title_short = schedule['title'][:6] + "..." if len(schedule['title']) > 6 else schedule['title']
                                full_content = f"{schedule['title']}: {schedule['description']}"
                                
                                # 일정 표시 스타일
                                st.markdown(f"""
                                <div style='font-size: 0.65em; background-color: #e3f2fd; 
                                           border-left: 3px solid #2196f3; padding: 2px 4px; margin: 1px 0; 
                                           border-radius: 2px;' title='{full_content}'>
                                    [{schedule['category']}] {title_short}
                                </div>
                                """, unsafe_allow_html=True)
                            
                            # 더 많은 일정이 있으면 표시
                            if len(day_schedules) > 2:
                                remaining_schedules = []
                                for schedule in day_schedules[2:]:
                                    remaining_schedules.append(f"• {schedule['title']}: {schedule['description']}")
                                remaining_text = "\n".join(remaining_schedules)
                                
                                st.markdown(f"""
                                <div style='font-size: 0.6em; color: #666; text-align: center;' title='{remaining_text}'>
                                    +{len(day_schedules)-2}개 더
                                </div>
                                """, unsafe_allow_html=True)
                        
                        # 빈 공간을 위한 최소 높이 확보
                        if not day_schedules and not labels:
                            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            # 주 사이 구분선
            if week_num < len(cal) - 1:
                st.markdown("---")

def render_calendar_with_details(year=None, month=None, selected_categories=None):
    """달력과 상세 일정을 함께 보여주는 버전"""
    
    # 기본값 설정
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    if selected_categories is None:
        selected_categories = []
    
    # 세무 달력 서비스 초기화
    tax_service = TaxCalendarService()
    month_schedules = tax_service.get_schedules_for_month(year, month)
    
    if selected_categories:
        month_schedules = tax_service.filter_schedules_by_category(month_schedules, selected_categories)
    
    # 2개 컬럼으로 나누기
    cal_col, detail_col = st.columns([2, 1])
    
    with cal_col:
        render_calendar(year, month, selected_categories)
    
    with detail_col:
        st.markdown("#### 이번 달 일정")
        
        # 공휴일 정보도 함께 표시
        korea_holidays = get_korean_holidays(year)
        month_holidays = []
        for date, name in korea_holidays.items():
            if date.year == year and date.month == month:
                month_holidays.append((date.day, name))
        
        if month_holidays:
            st.markdown("** 공휴일:**")
            for day, name in sorted(month_holidays):
                st.write(f"• {month}월 {day}일: {name}")
            st.markdown("---")
        
        if month_schedules:
            st.markdown("** 세무 일정:**")
            for day, schedules in sorted(month_schedules.items()):
                with st.expander(f"{month}월 {day}일"):
                    for schedule in schedules:
                        category_labels = {
                            '부': '부가세', '법': '법인세', '원': '원천세', 
                            '지': '지방세', '인': '인지세', '국': '국제조세', '기': '기타'
                        }
                        category = category_labels.get(schedule['category'], '기타')
                        st.write(f"[{schedule['category']}] **{schedule['title']}**")
                        st.caption(schedule['description'])
        else:
            st.info("이번 달에는 세무 일정이 없습니다.")

def render_simple_calendar(year=None, month=None, selected_categories=None):
    """더 간단한 달력 버전"""
    
    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month
    
    # 세무 달력 서비스 초기화
    tax_service = TaxCalendarService()
    month_schedules = tax_service.get_schedules_for_month(year, month)
    
    if selected_categories:
        month_schedules = tax_service.filter_schedules_by_category(month_schedules, selected_categories)
    
    # 공휴일 정보
    korea_holidays = get_korean_holidays(year)
    
    # 달력 제목
    st.subheader(f"{year}년 {month}월")
    
    # 공휴일 표시
    month_holidays = []
    for date, name in korea_holidays.items():
        if date.year == year and date.month == month:
            month_holidays.append((date.day, name))
    
    if month_holidays:
        st.markdown("** 이번 달 공휴일:**")
        for day, name in sorted(month_holidays):
            st.write(f"• {month}월 {day}일: {name}")
        st.markdown("---")
    
    # 일정이 있는 날짜만 표시
    if month_schedules:
        st.write("** 이번 달 세무 일정:**")
        for day, schedules in sorted(month_schedules.items()):
            with st.expander(f"{month}월 {day}일 ({len(schedules)}개 일정)"):
                for schedule in schedules:
                    category_labels = {
                        '부': '부가세', '법': '법인세', '원': '원천세', 
                        '지': '지방세', '인': '인지세', '국': '국제조세', '기': '기타'
                    }
                    category = category_labels.get(schedule['category'], '기타')
                    st.write(f"[{schedule['category']}] **{schedule['title']}**")
                    st.write(f"   {schedule['description']}")
    else:
        st.info("이번 달에는 세무 일정이 없습니다.")

def get_calendar_styles():
    """달력 CSS 스타일 반환"""
    return """
    <style>
    .calendar-day {
        border: 1px solid #ddd;
        border-radius: 4px;
        padding: 4px;
        margin: 2px;
        min-height: 80px;
        background-color: white;
    }
    
    .calendar-day.today {
        background-color: #ffd43b !important;
        border: 2px solid #fab005 !important;
        font-weight: bold;
    }
    
    .calendar-day.holiday {
        background-color: #ffdeeb !important;
        border: 1px solid #f8bbd9 !important;
        color: #e91e63;
    }
    
    .calendar-day.sunday {
        background-color: #ffe0e0 !important;
        color: #d63031;
    }
    
    .calendar-day.saturday {
        background-color: #e0f0ff !important;
        color: #0984e3;
    }
    
    .schedule-item {
        font-size: 0.7em;
        background-color: #e3f2fd;
        border-left: 3px solid #2196f3;
        padding: 2px 4px;
        margin: 1px 0;
        border-radius: 2px;
    }
    </style>
    """