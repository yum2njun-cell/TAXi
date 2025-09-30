from datetime import datetime, timedelta
import streamlit as st
import calendar
import holidays

class TaxCalendarService:
    """세무 달력 서비스"""
    
    def __init__(self):
        self.tax_categories = {
            '부': '부가세',
            '법': '법인세', 
            '원': '원천세',
            '지': '지방세',
            '인': '인지세',
            '국': '국세',
            '기': '기타'
        }
        self.init_default_schedules()
    
    def init_default_schedules(self):
        """기본 세무 일정 초기화"""
        if 'tax_schedules' not in st.session_state:
            st.session_state.tax_schedules = {}
            
        # 2021년부터 2027년까지 기본 일정 생성
        for year in range(2021, 2028):
            self.create_yearly_schedules(year)
    
    def create_yearly_schedules(self, year):
        """연도별 기본 세무 일정 생성"""
        schedules = []
        
        # 법인세 관련
        schedules.append({
            'date': f"{year}-03-31",
            'title': '법인세',
            'category': '법',
            'description': '법인세 신고 및 납부',
            'is_default': True
        })
        
        schedules.append({
            'date': f"{year}-04-30", 
            'title': '법인세 지방소득세분',
            'category': '법',
            'description': '법인세 지방소득세분 신고 및 납부',
            'is_default': True
        })
        
        schedules.append({
            'date': f"{year}-08-31",
            'title': '법인세 중간예납',
            'category': '법', 
            'description': '법인세 중간예납 신고 및 납부',
            'is_default': True
        })
        
        # 부가세 관련
        schedules.append({
            'date': f"{year}-04-25",
            'title': '1기 예정 부가가치세',
            'category': '부',
            'description': '1기 예정 부가가치세 신고 및 납부',
            'is_default': True
        })
        
        schedules.append({
            'date': f"{year}-07-25",
            'title': '1기 확정 부가가치세', 
            'category': '부',
            'description': '1기 확정 부가가치세 신고 및 납부',
            'is_default': True
        })
        
        schedules.append({
            'date': f"{year}-10-25",
            'title': '2기 예정 부가가치세',
            'category': '부', 
            'description': '2기 예정 부가가치세 신고 및 납부',
            'is_default': True
        })
        
        # 다음해 1월 25일
        next_year = year + 1
        schedules.append({
            'date': f"{next_year}-01-25",
            'title': '2기 확정 부가가치세',
            'category': '부',
            'description': '2기 확정 부가가치세 신고 및 납부', 
            'is_default': True
        })
        
        # 매월 반복 일정들
        for month in range(1, 13):
            # 원천징수 이행상황신고 (매월 10일)
            schedules.append({
                'date': f"{year}-{month:02d}-10",
                'title': '원천징수 이행상황신고',
                'category': '원',
                'description': '원천징수 이행상황신고 및 납부',
                'is_default': True
            })
            
            # 지방소득세(특별징수분) (매월 10일)
            schedules.append({
                'date': f"{year}-{month:02d}-10", 
                'title': '지방소득세(특별징수분)',
                'category': '원',
                'description': '지방소득세(특별징수분) 신고 및 납부',
                'is_default': True
            })
            
            # 주민세 종업원분 (매월 10일)
            schedules.append({
                'date': f"{year}-{month:02d}-10",
                'title': '주민세 종업원분',
                'category': '원', 
                'description': '주민세 종업원분 신고 및 납부',
                'is_default': True
            })
        
        # 연간 일정들
        annual_schedules = [
            (f"{year}-07-31", "주민세 사업소분", "지", "주민세 사업소분 신고 및 납부"),
            (f"{year}-07-31", "건축물, 주택1기분 재산세", "지", "건축물, 주택1기분 재산세 납부"),
            (f"{year}-09-30", "토지, 주택2기분 재산세", "지", "토지, 주택2기분 재산세 납부"),
            (f"{year}-12-15", "1차분납 종합부동산세", "지", "1차분납 종합부동산세 납부"),
            (f"{year}-06-15", "2차분납 종합부동산세", "지", "2차분납 종합부동산세 납부"),
            (f"{year}-08-31", "상반기 증권거래세", "지", "상반기 증권거래세 신고 및 납부"),
            (f"{year}-02-28", "하반기 증권거래세", "지", "하반기 증권거래세 신고 및 납부"),
            (f"{year}-12-31", "이전가격보고서", "국", "이전가격보고서 제출"),
            (f"{year}-06-30", "해외계좌신고", "국", "해외계좌신고 제출"),
            (f"{year}-01-31", "근로소득 간이지급명세서(상반기)", "원", "근로소득 간이지급명세서 제출"),
            (f"{year}-07-31", "근로소득 간이지급명세서(하반기)", "원", "근로소득 간이지급명세서 제출"),
            (f"{year}-02-28", "기타소득, 국내원천득, 배당소득 지급명세서", "원", "각종 지급명세서 제출"),
            (f"{year}-02-28", "우리사주 관련 명세서", "원", "우리사주 관련 명세서 제출"),
            (f"{year}-03-10", "사업소득, 근로소득, 퇴직소득 지급명세서", "원", "각종 지급명세서 제출"),
            (f"{year}-06-30", "일감몰아주기 증여세", "지", "일감몰아주기 증여세 신고 및 납부")
        ]
        
        for date_str, title, category, description in annual_schedules:
            schedules.append({
                'date': date_str,
                'title': title,
                'category': category,
                'description': description,
                'is_default': True
            })
        
        # 매월 말일 일정들
        for month in range(1, 13):
            last_day = calendar.monthrange(year, month)[1]
            
            # 사업소득, 기타소득 간이지급명세서
            schedules.append({
                'date': f"{year}-{month:02d}-{last_day}",
                'title': '사업소득, 기타소득 간이지급명세서',
                'category': '원',
                'description': '사업소득, 기타소득 간이지급명세서 제출',
                'is_default': True
            })
            
            # 일용근로소득 지급명세서
            schedules.append({
                'date': f"{year}-{month:02d}-{last_day}",
                'title': '일용근로소득 지급명세서', 
                'category': '원',
                'description': '일용근로소득 지급명세서 제출',
                'is_default': True
            })
        
        # 공휴일/주말 조정하여 저장
        for schedule in schedules:
            adjusted_date = self.adjust_for_holiday(schedule['date'])
            schedule['date'] = adjusted_date
            
            date_key = adjusted_date
            if date_key not in st.session_state.tax_schedules:
                st.session_state.tax_schedules[date_key] = []
            
            # 중복 방지
            if not any(s['title'] == schedule['title'] for s in st.session_state.tax_schedules[date_key]):
                st.session_state.tax_schedules[date_key].append(schedule)
    
    def adjust_for_holiday(self, date_str):
        """공휴일/주말이면 다음 영업일로 조정"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # 한국 공휴일 가져오기
        korea_holidays = holidays.SouthKorea(years=date_obj.year)
        
        # 주말이거나 공휴일이면 다음 영업일로 조정
        while (date_obj.weekday() >= 5 or  # 주말 (5=토요일, 6=일요일)
            date_obj.date() in korea_holidays):  # 공휴일
            date_obj += timedelta(days=1)
        
        return date_obj.strftime("%Y-%m-%d")
    
    def is_weekend_or_holiday(self, date_str):
        """주말이나 공휴일인지 확인"""
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        
        # 주말 체크
        if date_obj.weekday() >= 5:
            return True, "주말"
        
        # 공휴일 체크
        korea_holidays = holidays.SouthKorea(years=date_obj.year)
        if date_obj.date() in korea_holidays:
            holiday_name = korea_holidays.get(date_obj.date())
            return True, f"공휴일 ({holiday_name})"
        
        return False, ""
    
    def get_schedules_for_date(self, date_str):
        """특정 날짜의 일정 조회"""
        return st.session_state.get("tax_schedules", {}).get(date_str, [])
    
    def get_schedules_for_month(self, year, month):
        """특정 월의 모든 일정 조회"""
        schedules = {}
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            day_schedules = self.get_schedules_for_date(date_str)
            if day_schedules:
                schedules[day] = day_schedules
        return schedules
    
    def filter_schedules_by_category(self, schedules, selected_categories):
        """선택된 카테고리로 일정 필터링"""
        if not selected_categories:
            return schedules
        
        filtered = {}
        for day, day_schedules in schedules.items():
            filtered_day_schedules = [
                schedule for schedule in day_schedules 
                if schedule['category'] in selected_categories
            ]
            if filtered_day_schedules:
                filtered[day] = filtered_day_schedules
        return filtered
    
    def add_schedule(self, date_str, title, category, description):
        """일정 추가"""
        if date_str not in st.session_state.tax_schedules:
            st.session_state.tax_schedules[date_str] = []
        
        new_schedule = {
            'date': date_str,
            'title': title,
            'category': category,
            'description': description,
            'is_default': False
        }
        
        st.session_state.tax_schedules[date_str].append(new_schedule)
    
    def delete_schedule(self, date_str, schedule_index):
        """일정 삭제"""
        if date_str in st.session_state.tax_schedules:
            if 0 <= schedule_index < len(st.session_state.tax_schedules[date_str]):
                del st.session_state.tax_schedules[date_str][schedule_index]
                if not st.session_state.tax_schedules[date_str]:
                    del st.session_state.tax_schedules[date_str]

    def search_schedules(self, keyword, start_date=None, end_date=None):
        """키워드로 일정 검색"""
        results = []
        
        # 기간 설정이 없으면 모든 일정을 대상으로
        if start_date is None:
            start_date = datetime(2021, 1, 1).date()
        if end_date is None:
            end_date = datetime(2027, 12, 31).date()
        
        # 세무 일정 검색
        for date_str, schedules in st.session_state.get('tax_schedules', {}).items():
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
        
        # 공휴일 검색 추가
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

    def get_holidays_for_month(self, year, month):
        """특정 월의 공휴일 조회"""
        korea_holidays = holidays.SouthKorea(years=year)
        month_holidays = []
        
        for date, name in korea_holidays.items():
            if date.year == year and date.month == month:
                month_holidays.append((date.day, name))
        
        return sorted(month_holidays)