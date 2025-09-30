"""
인증 서비스 - 사용자 로그인 및 권한 관리
"""

import streamlit as st
from typing import Dict, Optional, List
from utils.state import set_user_session, get_user_session, clear_user_session
import hashlib
import time

class AuthService:
    """인증 서비스 클래스"""
    
    def __init__(self):
        # 허용된 사용자 ID 목록
        self.allowed_user_ids = [
            "04362", "11698", "06488", "11375",
            "06337", "11470", "07261", "04975",
            "guest"
        ]
        
        # 사용자 정보 매핑 (나중에 DB나 외부 파일로 이동 가능)
        self.user_info = {
            "04362": {"name": "문상현", "role": "관리자", "department": "세무팀"},
            "11698": {"name": "김정민", "role": "국제조세", "department": "세무팀"},
            "06488": {"name": "김태훈", "role": "지방세", "department": "세무팀"},
            "11375": {"name": "박세빈", "role": "부가세", "department": "세무팀"},
            "06337": {"name": "윤성은", "role": "인지세", "department": "세무팀"},
            "11470": {"name": "전유민", "role": "원천세", "department": "세무팀"},
            "07261": {"name": "최민석", "role": "법인세", "department": "세무팀"},
            "04975": {"name": "하영수", "role": "관리자", "department": "세무팀"},
            "guest": {"name": "guest", "role": "guest", "department": "방문자"}
        }
        
        # 기본 비밀번호 패턴: skax + user_id
        self.default_password_prefix = "skax"
    
    def authenticate(self, user_id: str, password: str) -> Dict[str, any]:
        """
        사용자 인증
        
        Args:
            user_id: 사용자 ID
            password: 비밀번호
            
        Returns:
            Dict: 인증 결과 및 사용자 정보
        """
        # 입력값 검증
        if not user_id or not password:
            return {"success": False, "message": "아이디와 비밀번호를 입력하세요."}
        
        # 허용된 사용자인지 확인
        if user_id not in self.allowed_user_ids:
            return {"success": False, "message": "등록되지 않은 사용자입니다."}
        
        # 비밀번호 검증
        if user_id == "guest":
            # 게스트 계정은 고정 비밀번호
            if password != "guest1234":
                return {"success": False, "message": "비밀번호가 틀렸습니다."}
        else:
            # 일반 사용자는 기존 패턴
            expected_password = f"{self.default_password_prefix}{user_id}"
            if password != expected_password:
                return {"success": False, "message": "비밀번호가 틀렸습니다."}
        
        # 사용자 정보 가져오기
        user_data = self.user_info.get(user_id, {})
        
        # 성공적인 인증
        login_data = {
            "user_id": user_id,
            "name": user_data.get("name", f"사용자{user_id}"),
            "role": user_data.get("role", "일반사용자"),
            "department": user_data.get("department", "미지정"),
            "login_time": time.time(),
            "login_datetime": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # 세션에 사용자 정보 저장
        set_user_session(login_data)
        
        return {
            "success": True, 
            "message": f"{login_data['name']}님, 환영합니다!",
            "user": login_data
        }
    
    def logout(self) -> bool:
        """로그아웃"""
        clear_user_session()
        return True
    
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return st.session_state.get("authenticated", False)
    
    def get_current_user(self) -> Optional[Dict[str, any]]:
        """현재 로그인한 사용자 정보 반환"""
        if not self.is_authenticated():
            return None
        return get_user_session()
    
    def has_permission(self, user_id: str, permission: str) -> bool:
        """
        사용자 권한 확인 (향후 확장 가능)
        
        Args:
            user_id: 사용자 ID
            permission: 확인할 권한
            
        Returns:
            bool: 권한 여부
        """
        user_data = self.user_info.get(user_id, {})
        role = user_data.get("role", "")
        
        # 관리자는 모든 권한
        if role == "관리자":
            return True
        
        # 권한별 매핑 (예시)
        role_permissions = {
            "원천세담당": ["excel_process", "pdf_extract", "withholding_tax"],
            "법인세담당": ["excel_process", "pdf_extract", "corporate_tax"],
            "부가세담당": ["excel_process", "pdf_extract", "vat"],
            "종소세담당": ["excel_process", "pdf_extract", "comprehensive_tax"],
            "지방세담당": ["excel_process", "pdf_extract", "local_tax"],
            "감사담당": ["excel_process", "pdf_extract", "audit"],
            "회계담당": ["excel_process", "pdf_extract", "accounting"]
        }
        
        user_permissions = role_permissions.get(role, [])
        return permission in user_permissions
    
    def get_allowed_users(self) -> List[Dict[str, any]]:
        """허용된 사용자 목록 반환"""
        users = []
        for user_id in self.allowed_user_ids:
            user_data = self.user_info.get(user_id, {})
            users.append({
                "user_id": user_id,
                "name": user_data.get("name", f"사용자{user_id}"),
                "role": user_data.get("role", "일반사용자"),
                "department": user_data.get("department", "미지정")
            })
        return users
    
    def add_user(self, user_id: str, name: str, role: str, department: str = "세무팀") -> bool:
        """
        새 사용자 추가 (관리자 전용 - 향후 구현)
        
        Args:
            user_id: 사용자 ID
            name: 사용자 이름
            role: 역할
            department: 부서
            
        Returns:
            bool: 추가 성공 여부
        """
        # 관리자 권한 확인
        current_user = self.get_current_user()
        if not current_user or current_user.get("role") != "관리자":
            return False
        
        # 중복 확인
        if user_id in self.allowed_user_ids:
            return False
        
        # 사용자 추가 (실제로는 DB에 저장)
        self.allowed_user_ids.append(user_id)
        self.user_info[user_id] = {
            "name": name,
            "role": role,
            "department": department
        }
        
        return True
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> Dict[str, any]:
        """
        비밀번호 변경 (향후 구현)
        
        Args:
            user_id: 사용자 ID
            current_password: 현재 비밀번호
            new_password: 새 비밀번호
            
        Returns:
            Dict: 변경 결과
        """
        # 현재는 기본 구현만 제공
        return {
            "success": False,
            "message": "비밀번호 변경 기능은 향후 구현 예정입니다."
        }


# 싱글톤 인스턴스
_auth_service = None

def get_auth_service() -> AuthService:
    """인증 서비스 싱글톤 인스턴스 반환"""
    global _auth_service
    if _auth_service is None:
        _auth_service = AuthService()
    return _auth_service

# 편의 함수들
def authenticate_user(user_id: str, password: str) -> Dict[str, any]:
    """사용자 인증"""
    return get_auth_service().authenticate(user_id, password)

def logout_user() -> bool:
    """사용자 로그아웃"""
    return get_auth_service().logout()

def is_user_authenticated() -> bool:
    """사용자 인증 상태 확인"""
    return get_auth_service().is_authenticated()

def get_current_user_info() -> Optional[Dict[str, any]]:
    """현재 사용자 정보 반환"""
    return get_auth_service().get_current_user()

def check_user_permission(permission: str) -> bool:
    """현재 사용자 권한 확인"""
    current_user = get_current_user_info()
    if not current_user:
        return False
    return get_auth_service().has_permission(current_user["user_id"], permission)
