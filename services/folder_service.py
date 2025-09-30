"""
폴더 구조 관리 서비스
"""
import json
from pathlib import Path
from typing import Dict, Optional, Tuple, List

class FolderService:
    """세목별 폴더 구조 관리 (단순 경로만)"""
    
    def __init__(self):
        from utils.settings import settings
        self.config_file = settings.config_dir / "folder_structures.json"
        settings.ensure_dirs()
    
    def get_default_structure(self) -> Dict:
        """기본 구조 - 경로만 저장"""
        return {
            "base_path": ""
        }
    
    def load_user_folder_structure(self, user_id: str, tax_type: str) -> Optional[Dict]:
        """사용자의 세목별 폴더 구조 로드"""
        try:
            if not self.config_file.exists():
                return None
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                all_data = json.load(f)
            
            return all_data.get(user_id, {}).get(tax_type)
        
        except Exception as e:
            print(f"폴더 구조 로드 오류: {e}")
            return None
    
    def save_user_folder_structure(self, user_id: str, tax_type: str, structure: Dict) -> bool:
        """사용자의 세목별 폴더 구조 저장"""
        try:
            all_data = {}
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    all_data = json.load(f)
            
            if user_id not in all_data:
                all_data[user_id] = {}
            
            all_data[user_id][tax_type] = structure
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(all_data, f, ensure_ascii=False, indent=2)
            
            return True
        
        except Exception as e:
            print(f"폴더 구조 저장 오류: {e}")
            return False
    
    def validate_structure(self, structure: Dict) -> Tuple[bool, List[str]]:
        """폴더 구조 유효성 검증"""
        errors = []
        
        if not structure.get('base_path'):
            errors.append("기본 경로를 입력해주세요")
        
        return len(errors) == 0, errors