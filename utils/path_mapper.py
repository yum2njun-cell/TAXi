"""
단순 경로 기반 세무 업무 매핑 시스템
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional
from utils.settings import settings

class PathMapper:
    """단순 경로 매퍼 - 저장된 기본 경로만 사용"""
    
    def __init__(self, user_id: str = None, work_type: str = None):
        from services.folder_service import FolderService
        import streamlit as st
        
        self.work_type = work_type
        
        # 사용자 ID 결정
        if not user_id:
            user_id = st.session_state.get("user", {}).get("user_id", "user")
        
        self.user_id = user_id  # ← 추가
        
        # 저장된 경로 로드
        if work_type:
            folder_service = FolderService()
            structure = folder_service.load_user_folder_structure(user_id, work_type)
            
            # 디버그 로그 추가
            print(f"[PathMapper] work_type={work_type}, user_id={user_id}")
            print(f"[PathMapper] loaded structure={structure}")
            
            if structure and structure.get('base_path'):
                self.base_path = Path(structure['base_path'])
                print(f"[PathMapper] ✅ base_path 설정됨: {self.base_path}")
            else:
                # ⚠️ 경로가 없으면 에러 메시지 출력
                st.error(f"⚠️ {work_type} 폴더가 설정되지 않았습니다. 설정 페이지에서 경로를 지정해주세요.")
                self.base_path = None
        else:
            self.base_path = None
    
    def parse_period(self, period_str: str) -> Dict[str, Any]:
        """
        기간 문자열 파싱
        
        Examples:
            "2025년 08월" → {"year": "25", "full_year": "2025", "month": 8}
            "2025년 1분기" → {"year": "25", "full_year": "2025", "quarter": "1"}
        """
        result = {}
        
        # 년도 추출
        year_match = re.search(r'(\d{4})년', period_str)
        if year_match:
            full_year = year_match.group(1)
            result["full_year"] = full_year
            result["year"] = full_year[2:]
        
        # 분기 추출
        quarter_match = re.search(r'(\d)분기', period_str)
        if quarter_match:
            result["quarter"] = quarter_match.group(1)
        
        # 월 추출
        month_match = re.search(r'(\d{1,2})월', period_str)
        if month_match:
            result["month"] = int(month_match.group(1))
        
        return result
    
    def is_path_configured(self) -> bool:
        """경로가 제대로 설정되었는지 확인"""
        return self.base_path is not None and self.base_path.exists()

    def get_base_path_or_error(self) -> Path:
        """
        기본 경로 반환, 없으면 에러
        
        Returns:
            설정된 기본 경로
            
        Raises:
            ValueError: 경로가 설정되지 않았거나 존재하지 않음
        """
        if not self.base_path:
            raise ValueError(
                f"{self.work_type} 폴더 경로가 설정되지 않았습니다.\n"
                "설정 페이지에서 경로를 지정해주세요."
            )
        
        if not self.base_path.exists():
            raise ValueError(
                f"{self.work_type} 폴더가 존재하지 않습니다:\n{self.base_path}\n"
                "설정 페이지에서 올바른 경로를 지정해주세요."
            )
        
        return self.base_path