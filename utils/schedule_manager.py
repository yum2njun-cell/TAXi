"""
TAXi - TAXday 일정 데이터 관리
실제 TAXday 캘린더 서비스와 연동된 일정 알림 시스템
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import calendar

class ScheduleManager:
    """TAXday 일정 관리 클래스 - TaxCalendarService 연동"""
    
    def __init__(self):
        # TaxCalendarService 임포트 (지연 임포트로 순환참조 방지)
        try:
            from services.tax_calendar_service import TaxCalendarService
            self.tax_calendar_service = TaxCalendarService()
            self.service_available = True
        except ImportError:
            self.tax_calendar_service = None
            self.service_available = False
            print("TaxCalendarService를 사용할 수 없습니다. 기본 알림만 제공됩니다.")
        
        # 카테고리 아이콘 매핑
        self.category_icons = {
            '부': "",  # 부가세
            '법': "",  # 법인세  
            '원': "",  # 원천세
            '지': "",  # 지방세
            '인': "",  # 인지세
            '국': "",  # 국제조세
            '기': ""   # 기타
        }
    
    def get_upcoming_deadline(self, days_ahead: int = 30) -> Optional[Dict[str, Any]]:
        """가장 임박한 일정 반환 - TaxCalendarService 연동"""
        if not self.service_available:
            return None
            
        today = datetime.now()
        upcoming_schedules = []
        
        # 다음 N일 동안의 일정 수집
        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            
            # TaxCalendarService에서 해당 날짜의 일정 가져오기
            date_str = check_date.strftime("%Y-%m-%d")
            schedules = self.tax_calendar_service.get_schedules_for_date(date_str)
            
            for schedule in schedules:
                days_left = i
                upcoming_schedules.append({
                    "title": schedule["title"],
                    "description": schedule["description"],
                    "date": date_str,
                    "days_left": days_left,
                    "icon": self.category_icons.get(schedule["category"], "📅"),
                    "priority": "high",  # 기본값
                    "display_date": check_date.strftime("%m/%d"),
                    "category": schedule["category"]
                })
        
        # 가장 가까운 일정 반환
        if upcoming_schedules:
            return min(upcoming_schedules, key=lambda x: x["days_left"])
        return None
    
    def get_recent_past_deadline(self, days_back: int = 30) -> Optional[Dict[str, Any]]:
        """가장 최근 지난 일정 반환 - TaxCalendarService 연동"""
        if not self.service_available:
            return None
            
        today = datetime.now()
        past_schedules = []
        
        # 지난 N일 동안의 일정 수집
        for i in range(1, days_back + 1):
            check_date = today - timedelta(days=i)
            
            # TaxCalendarService에서 해당 날짜의 일정 가져오기
            date_str = check_date.strftime("%Y-%m-%d")
            schedules = self.tax_calendar_service.get_schedules_for_date(date_str)
            
            for schedule in schedules:
                days_passed = i
                past_schedules.append({
                    "title": schedule["title"],
                    "description": schedule["description"],
                    "date": date_str,
                    "days_passed": days_passed,
                    "icon": self.category_icons.get(schedule["category"], "📅"),
                    "priority": "completed",
                    "display_date": check_date.strftime("%m/%d"),
                    "category": schedule["category"]
                })
        
        # 가장 최근 지난 일정 반환
        if past_schedules:
            return min(past_schedules, key=lambda x: x["days_passed"])
        return None
    
    def get_current_month_schedules(self) -> List[Dict[str, Any]]:
        """이번 달 전체 일정 반환 - TaxCalendarService 연동"""
        if not self.service_available:
            return []
            
        today = datetime.now()
        year, month = today.year, today.month
        
        # TaxCalendarService에서 이번 달 일정 가져오기
        month_schedules = self.tax_calendar_service.get_schedules_for_month(year, month)
        
        schedules = []
        for day, daily_schedules in month_schedules.items():
            check_date = datetime(year, month, day)
            
            for schedule in daily_schedules:
                schedules.append({
                    **schedule,
                    "date": check_date.strftime("%Y-%m-%d"),
                    "day": day,
                    "is_today": day == today.day,
                    "is_past": check_date < today,
                    "days_until": (check_date - today).days,
                    "icon": self.category_icons.get(schedule["category"], "📅")
                })
        
        return sorted(schedules, key=lambda x: x["day"])
    
    def _get_schedules_for_date(self, date: datetime) -> List[Dict[str, Any]]:
        """특정 날짜의 일정들 반환 - TaxCalendarService 연동 (내부 메서드)"""
        if not self.service_available:
            return []
            
        date_str = date.strftime("%Y-%m-%d")
        schedules = self.tax_calendar_service.get_schedules_for_date(date_str)
        
        # 아이콘 추가
        for schedule in schedules:
            schedule["icon"] = self.category_icons.get(schedule["category"], "📅")
            
        return schedules
    
    def get_priority_schedules(self, priority: str = "high", days_ahead: int = 7) -> List[Dict[str, Any]]:
        """우선순위별 일정 반환 - 기본 구현"""
        if not self.service_available:
            return []
            
        today = datetime.now()
        priority_schedules = []
        
        for i in range(days_ahead):
            check_date = today + timedelta(days=i)
            schedules = self._get_schedules_for_date(check_date)
            
            # 모든 일정을 high priority로 간주 (향후 개선 가능)
            for schedule in schedules:
                priority_schedules.append({
                    **schedule,
                    "date": check_date.strftime("%Y-%m-%d"),
                    "days_left": i,
                    "display_date": check_date.strftime("%m/%d"),
                    "priority": "high"  # 기본값
                })
        
        return sorted(priority_schedules, key=lambda x: x["days_left"])
    
    def add_custom_schedule(self, name: str, date: str, description: str, icon: str = "📅", priority: str = "medium"):
        """사용자 정의 일정 추가 - TaxCalendarService 연동"""
        if self.service_available:
            # TaxCalendarService를 통해 일정 추가
            self.tax_calendar_service.add_schedule(date, name, "기", description)
    
    def get_schedule_summary(self) -> Dict[str, Any]:
        """일정 요약 정보 반환"""
        upcoming = self.get_upcoming_deadline()
        past = self.get_recent_past_deadline()
        monthly = self.get_current_month_schedules()
        
        return {
            "upcoming_count": 1 if upcoming else 0,
            "past_count": 1 if past else 0,
            "monthly_count": len(monthly),
            "high_priority_count": len(self.get_priority_schedules("high")),
            "upcoming": upcoming,
            "past": past,
            "service_available": self.service_available
        }


# 싱글톤 인스턴스
_schedule_manager = None

def get_schedule_manager() -> ScheduleManager:
    """일정 관리자 싱글톤 인스턴스 반환"""
    global _schedule_manager
    if _schedule_manager is None:
        _schedule_manager = ScheduleManager()
    return _schedule_manager

# 편의 함수들
def get_upcoming_deadline() -> Optional[Dict[str, Any]]:
    """가장 임박한 일정 반환"""
    return get_schedule_manager().get_upcoming_deadline()

def get_recent_past_deadline() -> Optional[Dict[str, Any]]:
    """가장 최근 지난 일정 반환"""
    return get_schedule_manager().get_recent_past_deadline()

def get_current_month_schedules() -> List[Dict[str, Any]]:
    """이번 달 일정 목록 반환"""
    return get_schedule_manager().get_current_month_schedules()

def get_schedule_summary() -> Dict[str, Any]:
    """일정 요약 반환"""
    return get_schedule_manager().get_schedule_summary()