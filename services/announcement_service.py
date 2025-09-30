"""
공지사항 서비스 - 팀 공지사항 관리
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from utils.settings import settings

class AnnouncementService:
    """공지사항 관리 서비스"""
    
    def __init__(self):
        self.announcements_dir = settings.data_dir / "announcements"
        self.announcements_dir.mkdir(parents=True, exist_ok=True)
        self.announcements_file = self.announcements_dir / "announcements.json"
        
        # 기본 구조 생성
        if not self.announcements_file.exists():
            self._save_announcements([])
    
    def _get_current_user(self):
        """현재 로그인한 사용자 정보 가져오기"""
        try:
            from services.auth_service import get_current_user_info
            return get_current_user_info()
        except ImportError:
            return None
    
    def _load_announcements(self) -> List[Dict]:
        """공지사항 목록 로드"""
        if not self.announcements_file.exists():
            return []
        
        try:
            with open(self.announcements_file, 'r', encoding='utf-8') as f:
                announcements = json.load(f)
                # 최신순으로 정렬 (created_at 기준 내림차순)
                return sorted(announcements, key=lambda x: x.get('created_at', ''), reverse=True)
        except (json.JSONDecodeError, Exception) as e:
            print(f"공지사항 로드 실패: {e}")
            return []
    
    def _save_announcements(self, announcements: List[Dict]) -> bool:
        """공지사항 목록 저장"""
        try:
            with open(self.announcements_file, 'w', encoding='utf-8') as f:
                json.dump(announcements, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"공지사항 저장 실패: {e}")
            return False
    
    def create_announcement(self, title: str, content: str) -> bool:
        """새 공지사항 생성"""
        current_user = self._get_current_user()
        if not current_user:
            return False
        
        # 고유 ID 생성
        announcement_id = f"ann_{int(datetime.now().timestamp() * 1000)}"
        
        new_announcement = {
            'id': announcement_id,
            'title': title,
            'content': content,
            'author_id': current_user["user_id"],
            'author_name': current_user.get("name", "알 수 없음"),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        announcements = self._load_announcements()
        announcements.insert(0, new_announcement)  # 맨 앞에 추가 (최신)
        
        return self._save_announcements(announcements)
    
    def update_announcement(self, announcement_id: str, title: str, content: str) -> bool:
        """공지사항 수정"""
        current_user = self._get_current_user()
        if not current_user:
            return False
        
        announcements = self._load_announcements()
        
        for announcement in announcements:
            if announcement.get('id') == announcement_id:
                # 작성자만 수정 가능
                if announcement.get('author_id') != current_user["user_id"]:
                    return False
                
                announcement.update({
                    'title': title,
                    'content': content,
                    'updated_at': datetime.now().isoformat()
                })
                
                return self._save_announcements(announcements)
        
        return False
    
    def delete_announcement(self, announcement_id: str) -> bool:
        """공지사항 삭제"""
        current_user = self._get_current_user()
        if not current_user:
            return False
        
        announcements = self._load_announcements()
        
        for i, announcement in enumerate(announcements):
            if announcement.get('id') == announcement_id:
                # 작성자만 삭제 가능
                if announcement.get('author_id') != current_user["user_id"]:
                    return False
                
                # 실제 삭제 대신 비활성화
                announcement['is_active'] = False
                announcement['deleted_at'] = datetime.now().isoformat()
                
                return self._save_announcements(announcements)
        
        return False
    
    def get_announcements(self, page: int = 1, per_page: int = 20, include_inactive: bool = False) -> Tuple[List[Dict], int, int]:
        """공지사항 목록 조회 (페이지네이션)"""
        all_announcements = self._load_announcements()
        
        # 활성 공지사항만 필터링
        if not include_inactive:
            all_announcements = [a for a in all_announcements if a.get('is_active', True)]
        
        total_count = len(all_announcements)
        total_pages = (total_count + per_page - 1) // per_page
        
        # 페이지네이션 적용
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_announcements = all_announcements[start_idx:end_idx]
        
        return page_announcements, total_pages, total_count
    
    def get_announcement(self, announcement_id: str) -> Optional[Dict]:
        """특정 공지사항 조회"""
        announcements = self._load_announcements()
        
        for announcement in announcements:
            if announcement.get('id') == announcement_id:
                return announcement
        
        return None
    
    def get_latest_announcement(self) -> Optional[Dict]:
        """최신 공지사항 하나만 조회 (대시보드용)"""
        announcements = self._load_announcements()
        
        # 활성 공지사항 중 가장 최신 것
        active_announcements = [a for a in announcements if a.get('is_active', True)]
        
        return active_announcements[0] if active_announcements else None
    
    def search_announcements(self, keyword: str, page: int = 1, per_page: int = 20) -> Tuple[List[Dict], int, int]:
        """공지사항 검색"""
        all_announcements = self._load_announcements()
        
        # 키워드로 필터링 (제목과 내용에서 검색)
        filtered_announcements = []
        for announcement in all_announcements:
            if not announcement.get('is_active', True):
                continue
                
            title = announcement.get('title', '').lower()
            content = announcement.get('content', '').lower()
            author_name = announcement.get('author_name', '').lower()
            
            if (keyword.lower() in title or 
                keyword.lower() in content or 
                keyword.lower() in author_name):
                filtered_announcements.append(announcement)
        
        total_count = len(filtered_announcements)
        total_pages = (total_count + per_page - 1) // per_page
        
        # 페이지네이션 적용
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_announcements = filtered_announcements[start_idx:end_idx]
        
        return page_announcements, total_pages, total_count
    
    def get_user_announcements(self, user_id: str = None, page: int = 1, per_page: int = 10) -> Tuple[List[Dict], int, int]:
        """사용자별 공지사항 조회"""
        if not user_id:
            current_user = self._get_current_user()
            if not current_user:
                return [], 0, 0
            user_id = current_user["user_id"]
        
        all_announcements = self._load_announcements()
        
        # 해당 사용자가 작성한 공지사항만 필터링
        user_announcements = [a for a in all_announcements if a.get('author_id') == user_id]
        
        total_count = len(user_announcements)
        total_pages = (total_count + per_page - 1) // per_page
        
        # 페이지네이션 적용
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_announcements = user_announcements[start_idx:end_idx]
        
        return page_announcements, total_pages, total_count
    
    def get_stats(self) -> Dict[str, Any]:
        """공지사항 통계"""
        announcements = self._load_announcements()
        
        total_count = len(announcements)
        active_count = len([a for a in announcements if a.get('is_active', True)])
        
        # 작성자별 통계
        author_stats = {}
        for announcement in announcements:
            author_name = announcement.get('author_name', '알 수 없음')
            author_stats[author_name] = author_stats.get(author_name, 0) + 1
        
        # 최근 30일 공지사항 수
        from datetime import timedelta
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        recent_count = len([
            a for a in announcements 
            if a.get('created_at', '') >= thirty_days_ago
        ])
        
        return {
            'total_count': total_count,
            'active_count': active_count,
            'deleted_count': total_count - active_count,
            'recent_30days_count': recent_count,
            'author_stats': dict(sorted(author_stats.items(), key=lambda x: x[1], reverse=True))
        }
    
    def format_date(self, iso_date: str) -> str:
        """ISO 날짜를 읽기 쉬운 형태로 변환"""
        try:
            dt = datetime.fromisoformat(iso_date)
            return dt.strftime("%Y년 %m월 %d일 %H:%M")
        except:
            return iso_date
    
    def get_time_ago(self, iso_date: str) -> str:
        """날짜로부터 경과 시간 계산"""
        try:
            dt = datetime.fromisoformat(iso_date)
            now = datetime.now()
            diff = now - dt
            
            if diff.days > 0:
                return f"{diff.days}일 전"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours}시간 전"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes}분 전"
            else:
                return "방금 전"
        except:
            return "알 수 없음"

# 싱글톤 인스턴스
_announcement_service = None

def get_announcement_service() -> AnnouncementService:
    """공지사항 서비스 싱글톤 반환"""
    global _announcement_service
    if _announcement_service is None:
        _announcement_service = AnnouncementService()
    return _announcement_service