import streamlit as st
from datetime import datetime
from pathlib import Path
from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.auth_widget import check_auth
from components.corp_tax_tabs import render_corp_tax_tabs_simple
from services.corp_tax_service import get_corp_tax_service
from components.theme import apply_custom_theme
from utils.path_mapper import PathMapper
from services.file_scanner import FileScanner
import io
from utils.auth import is_guest, check_permission

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 법인세 관리", 
    page_icon="", 
    layout="wide"
)

# 스타일 로드
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

# 기본 페이지 네비게이션 숨기기
st.markdown("""
<style>
[data-testid="stSidebarNav"] ul,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] a {
    display: none !important;
}
[data-testid="stSidebarNav"] + div {
    display: block !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """세션 상태 초기화"""
    if 'vehicle_auto_scan_results' not in st.session_state:
        st.session_state.vehicle_auto_scan_results = {}
    if 'vehicle_processed_data' not in st.session_state:
        st.session_state.vehicle_processed_data = None


def scan_vehicle_files_automatically(year: int, quarter: int):
    """업무용승용차 파일 자동 탐색"""
    try:
        mapper = PathMapper(work_type="법인세")
        scanner = FileScanner(mapper)
        
        period_str = f"{year}년 {quarter}분기"
        
        with st.spinner("업무용승용차 파일을 자동으로 탐색 중..."):
            result = scanner.scan_vehicle_folders("법인세", period_str)
            
            if result.found and result.paths:
                st.success(f"파일 탐색 완료! (총 {len(result.paths)}개 파일)")
                
                # 결과 저장
                st.session_state.vehicle_auto_scan_results = {
                    'period': period_str,
                    'files': result.paths,
                    'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 파일 목록 표시
                with st.expander("찾은 파일 목록"):
                    for file_path in result.paths:
                        st.write(f"- {file_path.name}")
            else:
                st.error(f"파일을 찾을 수 없습니다: {result.error}")
                if result.candidates:
                    st.info("비슷한 폴더들:")
                    for candidate in result.candidates:
                        st.write(f"- {candidate}")
                        
    except Exception as e:
        st.error(f"자동 탐색 중 오류: {e}")
        import traceback
        st.error(traceback.format_exc())


def process_auto_found_files():
    """자동 탐색된 파일들 처리"""
    if 'vehicle_auto_scan_results' not in st.session_state or not st.session_state.vehicle_auto_scan_results:
        st.warning("먼저 파일을 탐색해주세요.")
        return
    
    file_paths = st.session_state.vehicle_auto_scan_results['files']
    
    try:
        with st.spinner(f"{len(file_paths)}개 파일을 처리 중..."):
            # 파일 경로를 업로드된 파일처럼 변환
            mock_files = []
            
            for file_path in file_paths:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # io.BytesIO 사용
                file_obj = io.BytesIO(file_content)
                file_obj.name = file_path.name
                
                mock_files.append(file_obj)
            
            # 서비스로 처리
            corp_service = get_corp_tax_service()
            result_df, stats = corp_service.process_vehicle_files(mock_files)
            
            # 결과 저장
            st.session_state.vehicle_processed_data = {
                'dataframe': result_df,
                'stats': stats,
                'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            st.success(f"처리 완료! (성공: {stats['processed_files']}개)")
            
    except Exception as e:
        st.error(f"파일 처리 중 오류: {e}")


def render_results():
    """처리 결과 표시"""
    if 'vehicle_processed_data' not in st.session_state or not st.session_state.vehicle_processed_data:
        return
    
    data = st.session_state.vehicle_processed_data
    result_df = data['dataframe']
    stats = data['stats']
    
    st.markdown("---")
    st.markdown("### 처리 결과")
    
    # 통계 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 파일", stats['total_files'])
    with col2:
        st.metric("처리 성공", stats['processed_files'])
    with col3:
        st.metric("처리 실패", stats['error_files'])
    
    # 결과 테이블
    st.dataframe(result_df, use_container_width=True)
    
    # 엑셀 다운로드
    corp_service = get_corp_tax_service()
    excel_data = corp_service.generate_vehicle_excel(result_df)
    
    st.download_button(
        label="결과를 엑셀로 다운로드",
        data=excel_data,
        file_name=f"업무용승용차_관리_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )


def main():
    initialize_session_state()
    
    # 페이지 헤더
    page_header("법인세 관리", "")
    render_corp_tax_tabs_simple("업무용승용차 관리")
    
    # 사이드바 메뉴
    with st.sidebar:
        sidebar_menu()
    
    st.markdown("### 업무용승용차 관리")
    st.markdown("법인세 관련 업무를 효율적으로 관리하세요")
    st.markdown("---")
    
    # 기간 선택 및 자동 탐색
    st.markdown("#### 자동 파일 탐색")
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        year = st.selectbox("연도", list(range(2021, 2030)), index=4)
    with col2:
        quarter = st.selectbox("분기", list(range(1, 5)), format_func=lambda x: f"{x}분기")
    with col3:
        if st.button("파일 찾기", use_container_width=True, disabled=is_guest()):
            if not check_permission("파일 자동 탐색"):
                return
            scan_vehicle_files_automatically(year, quarter)
    
    if st.session_state.vehicle_auto_scan_results:
        if st.button("자동 탐색 파일 처리", type="primary", use_container_width=True, disabled=is_guest()):
            if not check_permission("파일 처리"):
                return
            process_auto_found_files()
    
    st.markdown("---")
    
    # 수동 업로드
    st.markdown("#### 수동 파일 업로드")
    uploaded_files = st.file_uploader(
        "엑셀 파일을 선택하세요 (여러 개 선택 가능)",
        type=['xlsx', 'xls'],
        accept_multiple_files=True,
        help="업무용승용차 관련 엑셀 파일들을 업로드하세요",
        disabled=is_guest()
    )
    
    if uploaded_files:
        if st.button("수동 파일 처리", type="primary", use_container_width=True, disabled=is_guest()):
            if not check_permission("파일 처리"):
                return
            with st.spinner("파일을 처리 중입니다..."):
                try:
                    corp_service = get_corp_tax_service()
                    result_df, stats = corp_service.process_vehicle_files(uploaded_files)
                    
                    st.session_state.vehicle_processed_data = {
                        'dataframe': result_df,
                        'stats': stats,
                        'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    st.success(f"처리 완료!")
                    
                except Exception as e:
                    st.error(f"파일 처리 중 오류: {e}")
    
    # 결과 표시
    render_results()
    
    # 챗봇에서 전달된 처리 결과 (하단)
    if 'processing_result' in st.session_state and st.session_state.processing_result.get('from_chatbot'):
        st.markdown("---")
        st.markdown("### 챗봇 자동 처리 완료")
        
        result = st.session_state.processing_result
        st.success(f"{result['period']} 업무용승용차 처리가 완료되었습니다!")
        
        if st.button("확인", type="secondary", key="clear_chatbot_result"):
            del st.session_state.processing_result
            st.rerun()


if __name__ == "__main__":
    main()