"""
TAXi - 사용자 활동 로그 관리 시스템
"""

import json
import streamlit as st
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class ActivityLogger:
    """활동 로그 관리 클래스"""
    
    def __init__(self, log_file_path: str = "data/logs/activities.json"):
        self.log_file = Path(log_file_path)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.max_logs = 200  # 최대 저장할 로그 수
    
    def log_activity(
        self, 
        activity_type: str, 
        description: str, 
        details: Optional[Dict[str, Any]] = None,
        icon: str = "📋"
    ) -> None:
        """활동 로그 기록"""
        try:
            activity = {
                "id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{activity_type}",
                "timestamp": datetime.now().isoformat(),
                "type": activity_type,
                "description": description,
                "details": details or {},
                "icon": icon,
                "user": st.session_state.get("username", "사용자"),
                "session_id": st.session_state.get("session_id", "unknown")
            }
            
            # 기존 로그 읽기
            activities = self._load_activities()
            
            # 새 활동 추가 (최신이 맨 앞)
            activities.insert(0, activity)
            
            # 최대 개수 제한
            activities = activities[:self.max_logs]
            
            # 저장
            self._save_activities(activities)
            
        except Exception as e:
            # 로그 실패해도 메인 기능에 영향 주지 않도록
            print(f"활동 로그 기록 실패: {e}")
    
    def get_recent_activities(self, limit: int = 3, user: Optional[str] = None) -> List[Dict[str, Any]]:
        """최근 활동 가져오기"""
        try:
            activities = self._load_activities()
            
            # 사용자 필터링
            if user:
                activities = [a for a in activities if a.get("user") == user]
            
            # 제한된 개수만 반환
            return activities[:limit]
            
        except Exception as e:
            print(f"활동 로그 조회 실패: {e}")
            return []
    
    def get_activities_by_type(self, activity_type: str, limit: int = 10) -> List[Dict[str, Any]]:
        """특정 타입의 활동 가져오기"""
        try:
            activities = self._load_activities()
            filtered = [a for a in activities if a.get("type") == activity_type]
            return filtered[:limit]
            
        except Exception as e:
            print(f"타입별 활동 조회 실패: {e}")
            return []
    
    def get_user_statistics(self, user: Optional[str] = None) -> Dict[str, Any]:
        """사용자별 활동 통계"""
        try:
            activities = self._load_activities()
            
            if user:
                activities = [a for a in activities if a.get("user") == user]
            
            # 타입별 카운트
            type_counts = {}
            for activity in activities:
                activity_type = activity.get("type", "unknown")
                type_counts[activity_type] = type_counts.get(activity_type, 0) + 1
            
            return {
                "total_activities": len(activities),
                "type_breakdown": type_counts,
                "most_recent": activities[0] if activities else None,
                "user": user or "전체"
            }
            
        except Exception as e:
            print(f"사용자 통계 조회 실패: {e}")
            return {"total_activities": 0, "type_breakdown": {}, "most_recent": None}
    
    def _load_activities(self) -> List[Dict[str, Any]]:
        """활동 로그 파일 읽기"""
        if not self.log_file.exists():
            return []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_activities(self, activities: List[Dict[str, Any]]) -> None:
        """활동 로그 파일 저장"""
        with open(self.log_file, 'w', encoding='utf-8') as f:
            json.dump(activities, f, ensure_ascii=False, indent=2)
    
    def clear_old_logs(self, days_to_keep: int = 30) -> int:
        """오래된 로그 정리"""
        try:
            activities = self._load_activities()
            cutoff_date = datetime.now().timestamp() - (days_to_keep * 24 * 60 * 60)
            
            filtered_activities = []
            for activity in activities:
                try:
                    activity_time = datetime.fromisoformat(activity["timestamp"]).timestamp()
                    if activity_time >= cutoff_date:
                        filtered_activities.append(activity)
                except (ValueError, KeyError):
                    # 잘못된 형식의 로그는 제거
                    continue
            
            removed_count = len(activities) - len(filtered_activities)
            
            if removed_count > 0:
                self._save_activities(filtered_activities)
            
            return removed_count
            
        except Exception as e:
            print(f"로그 정리 실패: {e}")
            return 0

# 전역 인스턴스
_activity_logger = None

def get_activity_logger() -> ActivityLogger:
    """활동 로거 싱글톤 인스턴스 반환"""
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = ActivityLogger()
    return _activity_logger

# 편의 함수들
# 원천세 세분화 함수들 (기존 log_withholding_tax_activity 다음에 추가)
def log_withholding_return_activity(description: str, details: Optional[Dict] = None):
    """원천세-이행상황신고서 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("원천세-이행상황신고서", description, details, "")

def log_withholding_foreign_tax_activity(description: str, details: Optional[Dict] = None):
    """원천세-외국납부세액공제 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("원천세-외국납부세액공제", description, details, "")

def log_withholding_payment_statement_activity(description: str, details: Optional[Dict] = None):
    """원천세-지급명세서 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("원천세-지급명세서", description, details, "")
def log_corporate_vehicle_activity(description: str, details: Optional[Dict] = None):
    """법인세-업무용승용차 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("법인세-업무용승용차", description, details, "")

def log_corporate_depreciation_activity(description: str, details: Optional[Dict] = None):
    """법인세-감가상각비 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("법인세-감가상각비", description, details, "")

def log_corporate_loss_activity(description: str, details: Optional[Dict] = None):
    """법인세-이월결손금 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("법인세-이월결손금", description, details, "")

def log_vat_activity(description: str, details: Optional[Dict] = None):
    """부가세 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("부가세", description, details, "")

def log_stamp_tax_activity(description: str, details: Optional[Dict] = None):
    """인지세 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("인지세", description, details, "")

def log_file_processing_activity(description: str, file_name: str, details: Optional[Dict] = None):
    """파일 처리 활동 로그"""
    logger = get_activity_logger()
    full_details = {"file_name": file_name}
    if details:
        full_details.update(details)
    logger.log_activity("파일처리", description, full_details, "")

def log_excel_generation_activity(description: str, details: Optional[Dict] = None):
    """Excel 생성 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("Excel생성", description, details, "")

def log_pdf_extraction_activity(description: str, details: Optional[Dict] = None):
    """PDF 추출 활동 로그"""
    logger = get_activity_logger()
    logger.log_activity("PDF추출", description, details, "")

def get_recent_activities_for_sidebar(limit: int = 3) -> List[Dict[str, str]]:
    """사이드바용 최근 활동 포맷으로 반환"""
    logger = get_activity_logger()
    activities = logger.get_recent_activities(limit)
    
    formatted_activities = []
    for activity in activities:
        # 시간 계산
        try:
            activity_time = datetime.fromisoformat(activity["timestamp"])
            time_diff = datetime.now() - activity_time
            
            if time_diff.days > 0:
                time_str = f"{time_diff.days}일 전"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours}시간 전"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes}분 전"
            else:
                time_str = "방금"
        except:
            time_str = "알 수 없음"
        
        formatted_activities.append({
            "icon": activity.get("icon", "📋"),
            "title": activity.get("description", "활동"),
            "desc": f"{activity.get('type', '')} 처리",
            "time": time_str
        })
    
    return formatted_activities
