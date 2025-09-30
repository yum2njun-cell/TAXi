"""
사용자 설정 서비스 - 사용자별 개인화 설정 관리
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from utils.settings import settings

class UserPreferencesService:
    """사용자 개인화 설정 관리 서비스"""
    
    def __init__(self):
        self.preferences_dir = settings.data_dir / "user_preferences"
        self.preferences_dir.mkdir(parents=True, exist_ok=True)
        
        # 기본 설정값들
        self.default_preferences = {
            "tax_categories": [],  # 선택된 세목 목록
            "calendar_view": "monthly",  # 달력 보기 방식
            "notifications": True,  # 알림 설정
            "theme": "default",  # 테마 설정
            "dashboard_layout": "default"  # 대시보드 레이아웃
        }
    
    def get_user_preferences_file(self, user_id: str) -> Path:
        """사용자별 설정 파일 경로 반환"""
        return self.preferences_dir / f"{user_id}_preferences.json"
    
    def load_user_preferences(self, user_id: str = None) -> Dict[str, Any]:
        if user_id is None:
        # 순환 import 방지를 위해 함수 내에서 import
            try:
                from services.auth_service import get_current_user_info
                current_user = get_current_user_info()
                if not current_user:
                    return self.default_preferences.copy()
                user_id = current_user["user_id"]
            except ImportError:
                return self.default_preferences.copy()
        
        preferences_file = self.get_user_preferences_file(user_id)
        
        if not preferences_file.exists():
            # 파일이 없으면 기본값으로 생성
            self.save_user_preferences(self.default_preferences.copy(), user_id)
            return self.default_preferences.copy()
        
        try:
            with open(preferences_file, 'r', encoding='utf-8') as f:
                preferences = json.load(f)
                
            # 누락된 기본 설정이 있으면 추가
            updated = False
            for key, default_value in self.default_preferences.items():
                if key not in preferences:
                    preferences[key] = default_value
                    updated = True
            
            # 업데이트된 내용이 있으면 저장
            if updated:
                self.save_user_preferences(preferences, user_id)
                
            return preferences
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"사용자 설정 로드 실패 ({user_id}): {e}")
            # 오류 시 기본값 반환
            return self.default_preferences.copy()
    
    def save_user_preferences(self, preferences: Dict[str, Any], user_id: str = None) -> bool:
        if user_id is None:
            try:
                from services.auth_service import get_current_user_info
                current_user = get_current_user_info()
                if not current_user:
                    return False
                user_id = current_user["user_id"]
            except ImportError:
                return False
        
        preferences_file = self.get_user_preferences_file(user_id)
        
        try:
            with open(preferences_file, 'w', encoding='utf-8') as f:
                json.dump(preferences, f, ensure_ascii=False, indent=2)
            return True
            
        except Exception as e:
            print(f"사용자 설정 저장 실패 ({user_id}): {e}")
            return False
    
    def get_user_tax_categories(self, user_id: str = None) -> List[str]:
        """사용자가 선택한 세목 목록 반환"""
        preferences = self.load_user_preferences(user_id)
        return preferences.get("tax_categories", [])
    
    def save_user_tax_categories(self, categories: List[str], user_id: str = None) -> bool:
        """사용자 세목 선택 상태 저장"""
        preferences = self.load_user_preferences(user_id)
        preferences["tax_categories"] = categories
        return self.save_user_preferences(preferences, user_id)
    
    def get_user_preference(self, key: str, default=None, user_id: str = None) -> Any:
        """특정 사용자 설정값 반환"""
        preferences = self.load_user_preferences(user_id)
        return preferences.get(key, default)
    
    def set_user_preference(self, key: str, value: Any, user_id: str = None) -> bool:
        """특정 사용자 설정값 저장"""
        preferences = self.load_user_preferences(user_id)
        preferences[key] = value
        return self.save_user_preferences(preferences, user_id)
    
    def reset_user_preferences(self, user_id: str = None) -> bool:
        """사용자 설정 초기화"""
        return self.save_user_preferences(self.default_preferences.copy(), user_id)
    
    def get_all_users_preferences(self) -> Dict[str, Dict[str, Any]]:
        """모든 사용자의 설정 반환 (관리자용)"""
        all_preferences = {}
        
        for preferences_file in self.preferences_dir.glob("*_preferences.json"):
            try:
                user_id = preferences_file.stem.replace("_preferences", "")
                with open(preferences_file, 'r', encoding='utf-8') as f:
                    preferences = json.load(f)
                all_preferences[user_id] = preferences
            except Exception as e:
                print(f"설정 파일 읽기 실패 ({preferences_file}): {e}")
                continue
        
        return all_preferences
    
    def migrate_user_preferences(self, old_user_id: str, new_user_id: str) -> bool:
        """사용자 ID 변경시 설정 마이그레이션"""
        old_file = self.get_user_preferences_file(old_user_id)
        new_file = self.get_user_preferences_file(new_user_id)
        
        if not old_file.exists():
            return False
        
        try:
            # 기존 파일을 새 파일로 복사
            preferences = self.load_user_preferences(old_user_id)
            self.save_user_preferences(preferences, new_user_id)
            
            # 기존 파일 삭제
            old_file.unlink()
            return True
            
        except Exception as e:
            print(f"설정 마이그레이션 실패: {e}")
            return False
    
    def cleanup_old_preferences(self, days_old: int = 90) -> int:
        """오래된 설정 파일 정리 (일정 기간 이후 삭제)"""
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_old)
        deleted_count = 0
        
        for preferences_file in self.preferences_dir.glob("*_preferences.json"):
            try:
                file_time = datetime.fromtimestamp(preferences_file.stat().st_mtime)
                if file_time < cutoff_date:
                    preferences_file.unlink()
                    deleted_count += 1
            except Exception as e:
                print(f"파일 정리 실패 ({preferences_file}): {e}")
                continue
        
        return deleted_count
    
    def get_user_stats(self) -> Dict[str, int]:
        """사용자 설정 통계"""
        stats = {
            "total_users": 0,
            "users_with_custom_categories": 0,
            "most_popular_categories": {}
        }
        
        all_prefs = self.get_all_users_preferences()
        stats["total_users"] = len(all_prefs)
        
        category_counts = {}
        
        for user_id, preferences in all_prefs.items():
            tax_categories = preferences.get("tax_categories", [])
            
            if tax_categories:
                stats["users_with_custom_categories"] += 1
                
            for category in tax_categories:
                category_counts[category] = category_counts.get(category, 0) + 1
        
        # 가장 인기있는 세목 순으로 정렬
        stats["most_popular_categories"] = dict(
            sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        )
        
        return stats


# 싱글톤 인스턴스
_user_preferences_service = None

def get_user_preferences_service() -> UserPreferencesService:
    """사용자 설정 서비스 싱글톤 인스턴스 반환"""
    global _user_preferences_service
    if _user_preferences_service is None:
        _user_preferences_service = UserPreferencesService()
    return _user_preferences_service

# 편의 함수들
def get_user_tax_categories(user_id: str = None) -> List[str]:
    """사용자 선택 세목 목록 반환"""
    return get_user_preferences_service().get_user_tax_categories(user_id)

def save_user_tax_categories(categories: List[str], user_id: str = None) -> bool:
    """사용자 세목 선택 저장"""
    return get_user_preferences_service().save_user_tax_categories(categories, user_id)

def get_user_preference(key: str, default=None, user_id: str = None) -> Any:
    """사용자 설정값 반환"""
    return get_user_preferences_service().get_user_preference(key, default, user_id)

def set_user_preference(key: str, value: Any, user_id: str = None) -> bool:
    """사용자 설정값 저장"""
    return get_user_preferences_service().set_user_preference(key, value, user_id)