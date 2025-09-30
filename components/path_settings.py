"""
경로 설정 저장/로드 유틸리티
"""
import json
from pathlib import Path
import streamlit as st

def save_path_settings(tax_type, base_root_path, tax_specific_settings):
    """세목별 경로 설정 저장"""
    user_id = st.session_state.get("user", {}).get("user_id", "default")
    settings_dir = Path("data/path_settings")
    settings_dir.mkdir(parents=True, exist_ok=True)
    
    settings_file = settings_dir / f"{user_id}_paths.json"
    
    # 기존 설정 로드
    if settings_file.exists():
        with open(settings_file, 'r', encoding='utf-8') as f:
            all_settings = json.load(f)
    else:
        all_settings = {}
    
    # 세목별 설정 저장
    all_settings[tax_type] = {
        'base_root_path': base_root_path,
        **tax_specific_settings
    }
    
    # 파일에 저장
    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(all_settings, f, ensure_ascii=False, indent=2)

def load_path_settings(tax_type=None):
    """저장된 경로 설정 로드"""
    user_id = st.session_state.get("user", {}).get("user_id", "default")
    settings_file = Path("data/path_settings") / f"{user_id}_paths.json"
    
    if not settings_file.exists():
        return None
    
    with open(settings_file, 'r', encoding='utf-8') as f:
        all_settings = json.load(f)
    
    if tax_type:
        return all_settings.get(tax_type)
    return all_settings

def get_effective_base_path(tax_type, user_id=None):
    """실제 사용할 기본 경로 반환 (저장된 설정 우선)"""
    if not user_id:
        user_id = st.session_state.get("user", {}).get("user_id", "user")
    
    # 저장된 설정 확인
    saved_settings = load_path_settings(tax_type)
    if saved_settings and 'base_root_path' in saved_settings:
        return saved_settings['base_root_path']
    
    # 기본값 반환
    return f"C:\\Users\\{user_id}\\SK주식회사 C&C\\V_세무TF - General"