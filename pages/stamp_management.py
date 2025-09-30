"""
인지세 관리 페이지
폴더 기반 자동 파일 처리
"""
import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from components.stamp_tax_tabs import render_stamp_tax_tabs
from services.stamp_service import get_stamp_tax_service
from components.theme import apply_custom_theme
from utils.auth import is_guest, check_permission

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 인지세 관리",
    page_icon="",
    layout="wide"
)

# 스타일 로드
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

apply_custom_theme()

# 네비게이션 숨기기
st.markdown("""
<style>
[data-testid="stSidebarNav"] ul,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] a {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """세션 상태 초기화"""
    if 'stamp_folder_path' not in st.session_state:
        st.session_state.stamp_folder_path = ""
    if 'stamp_raw_file' not in st.session_state:
        st.session_state.stamp_raw_file = None
    if 'stamp_total_file' not in st.session_state:
        st.session_state.stamp_total_file = None
    if 'stamp_processed_data' not in st.session_state:
        st.session_state.stamp_processed_data = None


def scan_folder_for_files(folder_path: str):
    """폴더에서 raw와 total 파일 자동 탐색"""
    try:
        folder = Path(folder_path)
        
        if not folder.exists():
            st.error(f"폴더가 존재하지 않습니다: {folder_path}")
            return None, None
        
        raw_file = None
        total_file = None
        
        # 폴더 내 파일 검색
        for file in folder.glob("*.xlsx"):
            filename_lower = file.name.lower()
            
            if 'raw' in filename_lower and not raw_file:
                raw_file = file
            elif 'total' in filename_lower and not total_file:
                total_file = file
        
        return raw_file, total_file
        
    except Exception as e:
        st.error(f"파일 탐색 중 오류: {e}")
        return None, None


def process_stamp_files(raw_file_path, total_file_path=None, fill_zero=False):
    """인지세 파일 처리"""
    try:
        with st.spinner("인지세 파일을 처리 중입니다..."):
            stamp_service = get_stamp_tax_service()
            
            df_raw, df_pivot, excel_data = stamp_service.process_files(
                raw_file=raw_file_path,
                total_file=total_file_path,
                fill_zero=fill_zero
            )
            
            # 결과 저장
            st.session_state.stamp_processed_data = {
                'raw': df_raw,
                'pivot': df_pivot,
                'excel': excel_data,
                'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.success("처리 완료!")
            
    except Exception as e:
        st.error(f"처리 중 오류: {e}")
        import traceback
        st.error(traceback.format_exc())


def render_results():
    """처리 결과 표시"""
    if not st.session_state.stamp_processed_data:
        return
    
    data = st.session_state.stamp_processed_data
    
    st.markdown("---")
    st.markdown("### 처리 결과")
    
    # 통계
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Raw 데이터 행 수", len(data['raw']))
    with col2:
        st.metric("Pivot 데이터 행 수", len(data['pivot']))
    
    # 탭으로 결과 표시
    tab1, tab2 = st.tabs(["Pivot 미리보기", "Raw 데이터"])
    
    with tab1:
        st.dataframe(data['pivot'], use_container_width=True)
    
    with tab2:
        st.dataframe(data['raw'], use_container_width=True)
    
    # 엑셀 다운로드
    st.download_button(
        label="결과를 엑셀로 다운로드",
        data=data['excel'],
        file_name=f"인지세_처리결과_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


def main():
    initialize_session_state()
    
    page_header("인지세 관리", "")
    render_stamp_tax_tabs("인지세 관리")
    
    with st.sidebar:
        sidebar_menu()
    
    st.markdown("### 인지세 관리")
    st.markdown("폴더 내 raw/total 파일을 자동으로 찾아 처리합니다")
    st.markdown("---")
    
    # 폴더 경로 설정
    st.markdown("#### 파일 폴더 경로")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        folder_path = st.text_input(
            "폴더 경로",
            value=st.session_state.stamp_folder_path,
            placeholder="예: C:\\Users\\username\\Documents\\인지세",
            help="raw와 total 파일이 있는 폴더 경로를 입력하세요"
        )
        st.session_state.stamp_folder_path = folder_path
    
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("파일 찾기", use_container_width=True, disabled=is_guest()):
            if not check_permission("파일 탐색"):
                return
            if folder_path:
                raw_file, total_file = scan_folder_for_files(folder_path)
                
                if raw_file or total_file:
                    st.session_state.stamp_raw_file = raw_file
                    st.session_state.stamp_total_file = total_file
                    
                    st.success("파일 탐색 완료!")
                    
                    if raw_file:
                        st.info(f"Raw 파일: {raw_file.name}")
                    if total_file:
                        st.info(f"Total 파일: {total_file.name}")
                    if not raw_file:
                        st.warning("Raw 파일을 찾을 수 없습니다")
                else:
                    st.error("raw 또는 total 파일을 찾을 수 없습니다")
            else:
                st.warning("폴더 경로를 입력하세요")
    
    st.markdown("---")
    
    # 파일이 탐색되면 처리 옵션 표시
    if st.session_state.stamp_raw_file:
        st.markdown("#### 처리 옵션")
        
        fill_zero = st.checkbox(
            "결측치를 0으로 채우기",
            value=False,
            help="체크하면 빈 값을 0으로, 체크 해제하면 공백으로 표시합니다"
        )
        
        if st.button("처리 시작", type="primary", use_container_width=True, disabled=is_guest()):
            if not check_permission("파일 처리"):
                return
            process_stamp_files(
                raw_file_path=st.session_state.stamp_raw_file,
                total_file_path=st.session_state.stamp_total_file,
                fill_zero=fill_zero
            )
    # ========== 챗봇 처리 결과 표시 ==========
    if 'processing_result' in st.session_state and st.session_state.processing_result.get('from_chatbot'):
        if st.session_state.processing_result.get('task') == '인지세':
            st.markdown("---")
            st.markdown("### 챗봇 자동 처리 완료")
            
            result = st.session_state.processing_result
            st.success(f"{result['period']} 인지세 처리가 완료되었습니다!")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Raw 데이터", f"{result['raw_rows']}개 행")
            with col2:
                st.metric("Pivot 데이터", f"{result['pivot_rows']}개 행")
            
            if st.button("확인", type="secondary", key="clear_chatbot_result"):
                del st.session_state.processing_result
                st.rerun()
            
            st.markdown("---")
    # ==========================================

    # 결과 표시
    render_results()


if __name__ == "__main__":
    main()