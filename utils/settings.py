from pathlib import Path
import os
import json
from typing import Dict, Optional
import streamlit as st
from typing import Dict, Any, ClassVar
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]
TAX_TYPES = ["법인세", "부가가치세", "원천세", "지방세", "인지세", "국제조세"]

class Settings(BaseSettings):
    APP_NAME: str = "TAXⓘ"
    DEMO_USER: str = "admin"
    DEMO_PASS: str = "taxi1234"
    SECRET_KEY: str = "change-me-please"
    
    # 추가 설정들
    VERSION: str = "2.0.0"
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024
    BATCH_SIZE: int = 100
    MAX_CONCURRENT_JOBS: int = 5
    
    # 세무 기본 설정
    TAX_BASE_COMPANY: str = "SK주식회사 C&C"
    TAX_BASE_FOLDER: str = "V_세무TF - General"

    # 메서드들 추가
    @property
    def colors(self):
        return {
            "primary": "#F6DA7A",
            "primary_dark": "#E6C200", 
            "background": "#FFF9E6",
            "secondary_bg": "#FFF0F5",
            "text": "#111827",
            "text_secondary": "#6B7280",
            "success": "#86C0AD",
            "warning": "#E6D3B3",
            "error": "#DFACAC",
            "info": "#A4BCE2"
        }
    
    @property
    def data_dir(self):
        return ROOT / "data"
    
    @property 
    def upload_dir(self):
        return self.data_dir / "uploads"
    
    @property
    def output_dir(self):
        return self.data_dir / "outputs"
            
    @property
    def cache_dir(self):
        return self.data_dir / "cache"
    
    @property
    def assets_dir(self):
        return ROOT / "assets"
    
    @property
    def config_dir(self):
        """사용자 설정 파일들 저장 디렉토리"""
        return self.data_dir / "config"
    
    @property
    def user_settings_file(self):
        """사용자별 경로 설정 파일"""
        return self.config_dir / "user_paths.json"
    
    def ensure_dirs(self):
        """필요한 디렉토리들 생성"""
        for dir_path in [self.data_dir, self.upload_dir, self.output_dir, 
                        self.cache_dir, self.config_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_color(self, color_name: str) -> str:
        """색상 가져오기"""
        return self.colors.get(color_name, "#000000")
    
    def is_allowed_file(self, filename: str, file_type: str = "excel") -> bool:
        """허용된 파일인지 확인"""
        if not filename:
            return False
            
        ext = Path(filename).suffix.lower()
            
        if file_type == "excel":
            return ext in ['.xlsx', '.xls', '.csv']
        elif file_type == "pdf":
            return ext in ['.pdf']
            
        return False
    
    # 세무 경로 관련 메서드들
    def get_user_tax_base_path(self, user_id: str = None) -> Path:
        """
        사용자별 세무 기본 경로 가져오기
        
        Args:
            user_id: 로그인된 사용자 ID (사번)
            
        Returns:
            세무 기본 경로
        """
        # 1. 직접 전달된 user_id 사용
        if user_id:
            return Path(f"C:\\Users\\{user_id}\\{self.TAX_BASE_COMPANY}\\{self.TAX_BASE_FOLDER}")
        
        # 2. Streamlit 세션에서 user_id 가져오기
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and st.session_state.get("user"):
                session_user_id = st.session_state["user"]["user_id"]
                return Path(f"C:\\Users\\{session_user_id}\\{self.TAX_BASE_COMPANY}\\{self.TAX_BASE_FOLDER}")
        except:
            pass
        
        # 3. 사용자 설정 파일에서 가져오기
        custom_paths = self.load_user_path_settings()
        if custom_paths.get("tax_base_path"):
            return Path(custom_paths["tax_base_path"])
        
        # 4. 기본값 (현재 사용자)
        current_user = os.getenv('USERNAME', 'user')
        return Path(f"C:\\Users\\{current_user}\\{self.TAX_BASE_COMPANY}\\{self.TAX_BASE_FOLDER}")
    
    def load_user_path_settings(self, user_id: str = None) -> Dict:
        """사용자별 경로 설정 로드"""
        if not self.user_settings_file.exists():
            return {}
        
        try:
            with open(self.user_settings_file, 'r', encoding='utf-8') as f:
                all_settings = json.load(f)
            
            # 사용자별 설정 가져오기
            if user_id:
                return all_settings.get(user_id, {})
            
            # 현재 로그인된 사용자 설정
            try:
                import streamlit as st
                if hasattr(st, 'session_state') and st.session_state.get("user"):
                    session_user_id = st.session_state["user"]["user_id"]
                    return all_settings.get(session_user_id, {})
            except:
                pass
            
            return all_settings.get("default", {})
            
        except Exception as e:
            print(f"사용자 설정 로드 중 오류: {e}")
            return {}
    
    def save_user_path_settings(self, user_id: str, settings_dict: Dict):
        """사용자별 경로 설정 저장"""
        try:
            # 기존 설정 로드
            all_settings = {}
            if self.user_settings_file.exists():
                with open(self.user_settings_file, 'r', encoding='utf-8') as f:
                    all_settings = json.load(f)
            
            # 사용자 설정 업데이트
            all_settings[user_id] = settings_dict
            
            # 파일 저장
            with open(self.user_settings_file, 'w', encoding='utf-8') as f:
                json.dump(all_settings, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"사용자 설정 저장 중 오류: {e}")
            return False
    
    def get_work_type_settings(self, user_id: str = None) -> Dict:
        """업무 타입별 사용자 설정 가져오기"""
        user_settings = self.load_user_path_settings(user_id)
        return user_settings.get("work_types", {})
    
    def update_work_type_settings(self, user_id: str, work_type: str, settings_dict: Dict):
        """특정 업무 타입 설정 업데이트"""
        user_settings = self.load_user_path_settings(user_id)
        
        if "work_types" not in user_settings:
            user_settings["work_types"] = {}
        
        user_settings["work_types"][work_type] = settings_dict
        
        return self.save_user_path_settings(user_id, user_settings)
    
    def get_default_path_patterns(self) -> Dict:
        """기본 경로 패턴들 반환"""
        return {
            "원천세": {
                "base_path": "01_ 원천세 자료",
                "folder_pattern": "{full_year}년/01. 신고업무/{year}년 {month}월 귀속*",
                "sub_folders": {
                    "AKT": "AKT",
                    "INC": "HC 및 MR 자료",
                    "MR": "HC 및 MR 자료", 
                    "AX": "HR자료"
                }
            },
            "외화획득명세서": {
                "base_path": "외화획득명세서 작업",
                "folder_pattern": "{year}년{quarter}분기",
                "sub_folders": {
                    "unipass": "unipass실적조회",
                    "환율": "환율조회"
                }
            },
            "법인세": {
                "base_path": "법인세 업무",
                "folder_pattern": "{year}년{quarter}분기"
            },
            "부가세": {
                "base_path": "부가세 업무",
                "folder_pattern": "{year}년{quarter}분기"
            }
        }
    
    def get_current_path_settings():
        """현재 경로 설정 반환"""
        import streamlit as st
        
        default_settings = {
            'withholding_base_path': "01_ 원천세 자료",
            'withholding_report_path': "01. 신고업무", 
            'subfolders': {
                'AKT': 'AKT',
                'INC': 'HC 및 MR 자료',
                'MR': 'HC 및 MR 자료', 
                'AX': 'HR자료'
            }
        }
        
        # 세션에서 사용자 설정 가져오기
        user_settings = st.session_state.get('path_settings', {})
        
        # 기본값과 사용자 설정 병합
        return {**default_settings, **user_settings}

    # 기존 메일 관련 속성들
    @property
    def MAIL_ATTACHMENT_DIR(self):
        return os.path.join(self.data_dir, "mail_attachments")
    
    @property      
    def MAIL_BODY_TEMP_DIR(self):
        return os.path.join(self.data_dir, "body_temp")
    
    @property
    def MAIL_TEMPLATES_FILE(self):
        return os.path.join(self.data_dir, "mail_templates.json")

settings = Settings()

# 앱 시작시 디렉토리 생성
settings.ensure_dirs()