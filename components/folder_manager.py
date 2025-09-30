"""
폴더 추가/삭제 UI 위젯
"""
import streamlit as st
from typing import List
from pathlib import Path

def render_folder_manager(current_folders: List[str], key_prefix: str) -> List[str]:
    """3단계 폴더 관리 위젯 (선택 사항)"""
    st.markdown("**3단계 하위 폴더 관리** _(선택 사항)_")
    st.caption("특정 하위 폴더가 필요한 경우에만 추가하세요")
    
    session_key = f"{key_prefix}_folders"
    if session_key not in st.session_state:
        st.session_state[session_key] = current_folders.copy() if current_folders else []
    
    folders = st.session_state[session_key]
    
    if folders:
        st.markdown("**현재 폴더 목록:**")
        for i, folder in enumerate(folders):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.text_input(
                    f"폴더 {i+1}",
                    value=folder,
                    key=f"{key_prefix}_folder_{i}",
                    disabled=True
                )
            with col2:
                if st.button("삭제", key=f"{key_prefix}_delete_{i}", use_container_width=True):
                    st.session_state[session_key].pop(i)
                    st.rerun()
    
    st.markdown("---")
    col1, col2 = st.columns([4, 1])
    
    with col1:
        new_folder = st.text_input(
            "새 폴더 추가",
            key=f"{key_prefix}_new_folder",
            placeholder="폴더명을 입력하세요"
        )
    
    with col2:
        if st.button("추가", key=f"{key_prefix}_add", use_container_width=True):
            if new_folder and new_folder.strip():
                if new_folder not in st.session_state[session_key]:
                    st.session_state[session_key].append(new_folder.strip())
                    st.rerun()
                else:
                    st.warning("이미 존재하는 폴더명입니다.")
            else:
                st.warning("폴더명을 입력해주세요.")
    
    if folders:
        st.info(f"현재 {len(folders)}개의 하위 폴더가 설정되어 있습니다.")
    
    return st.session_state[session_key]

def render_path_preview(base_path: str, level1: str, level2: str, level3_folders: List[str]):
    """경로 미리보기"""
    st.markdown("**경로 미리보기**")
    
    sample_year = 2025
    sample_month = 1
    
    base = f"{base_path}\\{level1}\\{sample_year}년\\{level2}\\{sample_year}년 {sample_month:02d}월 귀속"
    
    st.code(base, language="text")
    
    if level3_folders:
        st.markdown("**3단계 하위 폴더들:**")
        for folder in level3_folders:
            st.code(f"{base}\\{folder}", language="text")