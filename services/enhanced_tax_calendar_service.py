"""
확장된 세무 달력 서비스 - 개인/공통 일정 영구 저장
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import streamlit as st
import calendar
import holidays
from utils.settings import settings
from services.tax_calendar_service import TaxCalendarService

class EnhancedTaxCalendarService(TaxCalendarService):
    """개인/공통 일정을 지원하는 확장된 세무 달력 서비스"""
    
    def __init__(self):
        # 부모 클래스 초기화 (기본 세무 일정)
        super().__init__()
        
        # 저장 디렉토리 설정
        self.schedules_dir = settings.data_dir / "schedules"
        self.schedules_dir.mkdir(parents=True, exist_ok=True)
        
        # 파일 경로
        self.common_schedules_file = self.schedules_dir / "common_schedules.json"
        self.personal_schedules_dir = self.schedules_dir / "personal"
        self.personal_schedules_dir.mkdir(parents=True, exist_ok=True)
        
        # 저장된 일정들 로드
        self._load_saved_schedules()
    
    def get_personal_schedules_file(self, user_id: str) -> Path:
        """사용자별 개인 일정 파일 경로"""
        return self.personal_schedules_dir / f"{user_id}_schedules.json"
    
    def _load_saved_schedules(self):
        """저장된 일정들을 세션에 로드"""
        # 공통 일정 로드
        common_schedules = self._load_common_schedules_from_file()
        
        # 현재 사용자의 개인 일정 로드
        current_user = self._get_current_user()
        if current_user:
            personal_schedules = self._load_personal_schedules_from_file(current_user["user_id"])
            
            # 세션의 tax_schedules에 병합
            for date_str, schedules in common_schedules.items():
                if date_str not in st.session_state.tax_schedules:
                    st.session_state.tax_schedules[date_str] = []
                # 공통 일정 추가 (중복 제거)
                for schedule in schedules:
                    if not any(s.get('id') == schedule.get('id') for s in st.session_state.tax_schedules[date_str]):
                        st.session_state.tax_schedules[date_str].append(schedule)
            
            # 개인 일정 추가
            for date_str, schedules in personal_schedules.items():
                if date_str not in st.session_state.tax_schedules:
                    st.session_state.tax_schedules[date_str] = []
                for schedule in schedules:
                    if not any(s.get('id') == schedule.get('id') for s in st.session_state.tax_schedules[date_str]):
                        st.session_state.tax_schedules[date_str].append(schedule)
    
    def _get_current_user(self):
        """현재 로그인한 사용자 정보 가져오기"""
        try:
            from services.auth_service import get_current_user_info
            return get_current_user_info()
        except ImportError:
            return None
    
    def _load_common_schedules_from_file(self) -> Dict[str, List[Dict]]:
        """파일에서 공통 일정 로드"""
        if not self.common_schedules_file.exists():
            return {}
        
        try:
            with open(self.common_schedules_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"공통 일정 로드 실패: {e}")
            return {}
    
    def _save_common_schedules_to_file(self, schedules: Dict[str, List[Dict]]) -> bool:
        """공통 일정을 파일에 저장"""
        try:
            with open(self.common_schedules_file, 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"공통 일정 저장 실패: {e}")
            return False
    
    def _load_personal_schedules_from_file(self, user_id: str) -> Dict[str, List[Dict]]:
        """파일에서 개인 일정 로드"""
        personal_file = self.get_personal_schedules_file(user_id)
        
        if not personal_file.exists():
            return {}
        
        try:
            with open(personal_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            print(f"개인 일정 로드 실패 ({user_id}): {e}")
            return {}
    
    def _save_personal_schedules_to_file(self, user_id: str, schedules: Dict[str, List[Dict]]) -> bool:
        """개인 일정을 파일에 저장"""
        personal_file = self.get_personal_schedules_file(user_id)
        
        try:
            with open(personal_file, 'w', encoding='utf-8') as f:
                json.dump(schedules, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"개인 일정 저장 실패 ({user_id}): {e}")
            return False
    
    def add_schedule(self, date_str, title, category, description, schedule_type='personal'):
        """일정 추가 (개인/공통 구분)"""
        current_user = self._get_current_user()
        if not current_user and schedule_type == 'personal':
            return False
        
        # 고유 ID 생성
        schedule_id = f"{schedule_type}_{int(datetime.now().timestamp() * 1000)}"
        
        new_schedule = {
            'id': schedule_id,
            'date': date_str,
            'title': title,
            'category': category,
            'description': description,
            'schedule_type': schedule_type,
            'is_default': False,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'created_by': current_user["user_id"] if current_user else 'system'
        }
        
        # 세션에 추가
        if date_str not in st.session_state.tax_schedules:
            st.session_state.tax_schedules[date_str] = []
        st.session_state.tax_schedules[date_str].append(new_schedule)
        
        # 파일에 저장
        if schedule_type == 'common':
            self._save_common_schedule_to_file(date_str, new_schedule)
        else:
            if current_user:
                self._save_personal_schedule_to_file(current_user["user_id"], date_str, new_schedule)
        
        return True
    
    def _save_common_schedule_to_file(self, date_str: str, schedule: Dict):
        """공통 일정 파일에 저장"""
        common_schedules = self._load_common_schedules_from_file()
        if date_str not in common_schedules:
            common_schedules[date_str] = []
        common_schedules[date_str].append(schedule)
        self._save_common_schedules_to_file(common_schedules)
    
    def _save_personal_schedule_to_file(self, user_id: str, date_str: str, schedule: Dict):
        """개인 일정 파일에 저장"""
        personal_schedules = self._load_personal_schedules_from_file(user_id)
        if date_str not in personal_schedules:
            personal_schedules[date_str] = []
        personal_schedules[date_str].append(schedule)
        self._save_personal_schedules_to_file(user_id, personal_schedules)
    
    def update_schedule(self, date_str, schedule_index, updated_title, updated_category, updated_description):
        """일정 수정"""
        if date_str not in st.session_state.tax_schedules:
            return False
        
        schedules = st.session_state.tax_schedules[date_str]
        if 0 <= schedule_index < len(schedules):
            schedule = schedules[schedule_index]
            
            # 기본 일정은 수정 불가
            if schedule.get('is_default', False):
                return False
            
            # 수정 권한 체크
            current_user = self._get_current_user()
            if not current_user:
                return False
            
            schedule_type = schedule.get('schedule_type', 'personal')
            if schedule_type == 'personal' and schedule.get('created_by') != current_user["user_id"]:
                return False
            
            # 일정 업데이트
            schedule.update({
                'title': updated_title,
                'category': updated_category,
                'description': updated_description,
                'updated_at': datetime.now().isoformat()
            })
            
            # 파일에 저장
            self._update_schedule_in_file(schedule)
            return True
        
        return False
    
    def _update_schedule_in_file(self, schedule: Dict):
        """파일의 일정 업데이트"""
        schedule_type = schedule.get('schedule_type', 'personal')
        schedule_id = schedule.get('id')
        
        if schedule_type == 'common':
            common_schedules = self._load_common_schedules_from_file()
            for date_str, schedules in common_schedules.items():
                for i, s in enumerate(schedules):
                    if s.get('id') == schedule_id:
                        schedules[i] = schedule
                        self._save_common_schedules_to_file(common_schedules)
                        return
        else:
            current_user = self._get_current_user()
            if current_user:
                personal_schedules = self._load_personal_schedules_from_file(current_user["user_id"])
                for date_str, schedules in personal_schedules.items():
                    for i, s in enumerate(schedules):
                        if s.get('id') == schedule_id:
                            schedules[i] = schedule
                            self._save_personal_schedules_to_file(current_user["user_id"], personal_schedules)
                            return
    
    def delete_schedule(self, date_str, schedule_index):
        """일정 삭제"""
        if date_str not in st.session_state.tax_schedules:
            return False
        
        schedules = st.session_state.tax_schedules[date_str]
        if 0 <= schedule_index < len(schedules):
            schedule = schedules[schedule_index]
            
            # 기본 일정은 삭제 불가
            if schedule.get('is_default', False):
                return False
            
            # 삭제 권한 체크
            current_user = self._get_current_user()
            if not current_user:
                return False
            
            schedule_type = schedule.get('schedule_type', 'personal')
            if schedule_type == 'personal' and schedule.get('created_by') != current_user["user_id"]:
                return False
            
            # 세션에서 삭제
            schedule_to_delete = schedules.pop(schedule_index)
            
            # 해당 날짜에 일정이 없으면 날짜 키도 삭제
            if not schedules:
                del st.session_state.tax_schedules[date_str]
            
            # 파일에서도 삭제
            self._delete_schedule_from_file(schedule_to_delete)
            return True
        
        return False
    
    def _delete_schedule_from_file(self, schedule: Dict):
        """파일에서 일정 삭제"""
        schedule_type = schedule.get('schedule_type', 'personal')
        schedule_id = schedule.get('id')
        
        if schedule_type == 'common':
            common_schedules = self._load_common_schedules_from_file()
            # 삭제할 날짜들을 먼저 수집
            dates_to_remove = []
            for date_str, schedules in common_schedules.items():
                schedules[:] = [s for s in schedules if s.get('id') != schedule_id]
                if not schedules:
                    dates_to_remove.append(date_str)
            
            # 빈 날짜들 삭제
            for date_str in dates_to_remove:
                del common_schedules[date_str]
                
            self._save_common_schedules_to_file(common_schedules)
        else:
            current_user = self._get_current_user()
            if current_user:
                personal_schedules = self._load_personal_schedules_from_file(current_user["user_id"])
                # 삭제할 날짜들을 먼저 수집
                dates_to_remove = []
                for date_str, schedules in personal_schedules.items():
                    schedules[:] = [s for s in schedules if s.get('id') != schedule_id]
                    if not schedules:
                        dates_to_remove.append(date_str)
                
                # 빈 날짜들 삭제
                for date_str in dates_to_remove:
                    del personal_schedules[date_str]
                    
                self._save_personal_schedules_to_file(current_user["user_id"], personal_schedules)
    
    def get_schedules_for_date(self, date_str):
        """특정 날짜의 일정 조회 (오버라이드)"""
        # 저장된 일정 다시 로드 (다른 사용자가 추가한 공통 일정 반영)
        self._load_saved_schedules()
        
        # 부모 클래스 메서드 호출
        return super().get_schedules_for_date(date_str)
    
    def reload_schedules(self):
        """일정 다시 로드 (다른 사용자 변경사항 반영)"""
        self._load_saved_schedules()

# 싱글톤 인스턴스
_enhanced_calendar_service = None

def get_enhanced_calendar_service():
    """확장된 달력 서비스 싱글톤 반환"""
    global _enhanced_calendar_service
    if _enhanced_calendar_service is None:
        _enhanced_calendar_service = EnhancedTaxCalendarService()
    return _enhanced_calendar_service