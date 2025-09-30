"""
TAXi - 원천세 이행상황신고서 메인 페이지 (법인세와 동일한 구조)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
from pathlib import Path

from utils.settings import settings
from components.layout import page_header, sidebar_menu
from components.withholding_tax_tabs import render_withholding_tax_tabs
from services.withholding_tax_service import WithholdingTaxService
from components.auth_widget import check_auth
from utils.path_mapper import PathMapper
from services.file_scanner import FileScanner
from components.toast import show_toast
from components.theme import apply_custom_theme
from components.path_settings import get_effective_base_path
from utils.auth import is_guest, check_permission

# 인증 체크
if not check_auth():
    st.switch_page("app.py")

# 페이지 설정
st.set_page_config(
    page_title=f"{settings.APP_NAME} | 원천세 관리",
    page_icon="",
    layout="wide"
)

# 스타일 로드 후에
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

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
    if 'wt_session_id' not in st.session_state:
        st.session_state.wt_session_id = str(uuid.uuid4())[:8]
    if 'wt_processed_files' not in st.session_state:
        st.session_state.wt_processed_files = {}
    if 'wt_all_companies_data' not in st.session_state:
        st.session_state.wt_all_companies_data = {}
    if 'wt_processing_errors' not in st.session_state:
        st.session_state.wt_processing_errors = []
    if 'wt_combined_excel_data' not in st.session_state:
        st.session_state.wt_combined_excel_data = None
    if 'selected_year' not in st.session_state:
        st.session_state.selected_year = 2025
    if 'selected_month' not in st.session_state:
        st.session_state.selected_month = 1
    if 'wt_auto_scan_results' not in st.session_state:
        st.session_state.wt_auto_scan_results = {}
    if 'wt_processing_mode' not in st.session_state:
        st.session_state.wt_processing_mode = 'individual'  # 'individual', 'combined', 'mixed'
    if 'wt_selected_auto_files' not in st.session_state:
        st.session_state.wt_selected_auto_files = {}

def render_sidebar_status():
    """사이드바 처리 현황 표시"""
    with st.sidebar:
        st.markdown("---")
        st.markdown("###  원천세 처리 현황")
        
        processed_count = len(st.session_state.wt_processed_files)
        combined_count = len(st.session_state.wt_all_companies_data)
        
        st.metric("처리된 개별 파일", processed_count)
        st.metric("통합 처리 회사", combined_count)
        
        if st.session_state.wt_processing_errors:
            with st.expander(" 처리 오류"):
                for error in st.session_state.wt_processing_errors[-3:]:
                    st.error(error, icon="")
        
        if st.button(" 원천세 데이터 초기화", use_container_width=True, disabled=is_guest()):
            if not check_permission("데이터 초기화"):
                return
            st.session_state.wt_processed_files = {}
            st.session_state.wt_all_companies_data = {}
            st.session_state.wt_processing_errors = []
            st.session_state.wt_combined_excel_data = None
            st.session_state.wt_auto_scan_results = {}
            st.success("원천세 데이터가 초기화되었습니다.")
            st.rerun()

with st.sidebar:
    sidebar_menu()

def scan_files_automatically(year: int, month: int):
    """자동 파일 탐색 함수"""
    try:
        # PathMapper 생성 시 세목 타입 전달
        mapper = PathMapper(work_type="원천세")
        scanner = FileScanner(mapper)
        
        period_str = f"{year}년 {month:02d}월"
        
        with st.spinner("파일을 자동으로 탐색 중..."):
            # 원천세 작업 폴더 스캔
            work_result = scanner.scan_work_folder("원천세", period_str)
            
            if work_result.found:
                
                # 결과를 세션에 저장
                st.session_state.wt_auto_scan_results = {
                    'period': period_str,
                    'work_folder': work_result.path,
                    'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # 파일들 스캔
                file_results = scanner.scan_files("원천세", period_str)
                
                is_valid, errors = scanner.validate_scan_results(file_results)
                
                if is_valid:
                    final_paths = scanner.get_final_file_paths(file_results)
                    st.success(f"파일을 성공적으로 찾았습니다! (총 {len(final_paths)}개)")
                    st.session_state.wt_auto_scan_results['files'] = final_paths
                elif final_paths := scanner.get_final_file_paths(file_results):
                    # 일부 파일만 찾은 경우도 처리 가능하도록
                    st.session_state.wt_auto_scan_results['files'] = final_paths
                    st.warning(f"일부 파일만 찾았습니다 ({len(final_paths)}개). 나머지는 수동으로 추가할 수 있습니다.")
                    for error in errors:
                        st.error(error)
                
                else:
                    st.warning("⚠️ 일부 파일을 찾을 수 없습니다:")
                    for error in errors:
                        st.error(error)
                        
            else:
                st.error(f"❌ {work_result.error}")
                
                if work_result.candidates:
                    st.info(" 비슷한 폴더들:")
                    for candidate in work_result.candidates:
                        st.write(f"- {candidate}")
                        
    except Exception as e:
        st.error(f"❌ 자동 탐색 중 오류: {e}")
        import traceback
        st.error(traceback.format_exc())

def process_auto_found_file(file_path, file_type, period_str):
    """자동으로 찾은 파일 처리"""
    try:
        # 파일 타입별 회사 타입 매핑
        file_type_to_company = {
            "AKT": 1,  # 애커튼
            "INC": 2,  # SK INC
            "MR": 3,   # SK MRCIC  
            "AX": 4    # SK AX
        }
        
        company_type = file_type_to_company.get(file_type, 1)
        
        # 실제 파일을 읽어서 처리
        if Path(file_path).exists():
            # 파일을 업로드된 파일처럼 처리하기 위해 변환
            with open(file_path, 'rb') as f:
                file_content = f.read()
            
            # 임시 파일 객체 생성 (Streamlit UploadedFile과 유사하게)
            class MockUploadedFile:
                def __init__(self, content, name):
                    self.content = content
                    self.name = name
                
                def getvalue(self):
                    return self.content
                
                def getbuffer(self):
                    return self.content
            
            mock_file = MockUploadedFile(file_content, Path(file_path).name)
            
            # 기존 처리 함수 호출
            service = WithholdingTaxService()
            process_individual_file(mock_file, company_type, None, service)
            
        else:
            st.error(f"파일이 존재하지 않습니다: {file_path}")
            
    except Exception as e:
        st.error(f"자동 처리 중 오류: {e}")

def process_auto_combined_files(auto_files):
    """자동 탐색 파일들을 통합 처리"""
    service = WithholdingTaxService()
    file_type_to_company = {
        "AKT": 1, "INC": 2, "MR": 3, "AX": 4
    }
    
    file_company_mappings = []
    
    for file_type, file_path in auto_files.items():
        try:
            if Path(file_path).exists():
                company_type = file_type_to_company.get(file_type, 1)
                
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                # Mock 파일 객체 생성
                class MockUploadedFile:
                    def __init__(self, content, name):
                        self.content = content
                        self.name = name
                    def getvalue(self):
                        return self.content
                    def getbuffer(self):
                        return self.content
                
                mock_file = MockUploadedFile(file_content, Path(file_path).name)
                file_company_mappings.append((mock_file, company_type, None))
                
        except Exception as e:
            st.error(f"{file_type} 파일 처리 중 오류: {e}")
    
    if file_company_mappings:
        process_combined_files(file_company_mappings, service)
    else:
        st.error("처리할 수 있는 파일이 없습니다.")

def display_auto_scan_results():
    """자동 탐색 결과 표시 (개별 처리용)"""
    if st.session_state.wt_auto_scan_results:
        results = st.session_state.wt_auto_scan_results
        with st.expander(f" 자동 탐색 결과 ({results.get('period', 'Unknown')})", expanded=False):
            st.info(f"**탐색 시간**: {results.get('scan_time', 'Unknown')}")
            st.info(f"**작업 폴더**: {results.get('work_folder', 'Unknown')}")
            
            if 'files' in results:
                st.write("**찾은 파일들**:")
                for file_type, file_path in results['files'].items():
                    st.write(f"- **{file_type}**: {file_path}")

def display_auto_scan_results_for_combined():
    """자동 탐색 결과 표시 (통합 처리용)"""
    if st.session_state.wt_auto_scan_results:
        results = st.session_state.wt_auto_scan_results
        with st.expander(f" 통합 처리용 자동 탐색 결과", expanded=False):
            st.info("자동 탐색된 파일들을 통합 처리에 활용할 수 있습니다.")
            if 'files' in results:
                st.write("**사용 가능한 파일들**:")
                for file_type, file_path in results['files'].items():
                    st.write(f"- **{file_type}**: {file_path}")

def render_unified_processing_flow():
    """통합된 처리 플로우"""
    
    # Step 1: 기간 설정
    st.subheader("기간 설정")
    render_period_selection_simple()
    
    st.markdown("---")
    
    # Step 2: 파일 수집 부분을 다음과 같이 수정
    st.subheader("파일 수집 및 설정")
    
    auto_files = st.session_state.wt_auto_scan_results.get('files', {})
    manual_files = st.session_state.get('wt_manual_files', {})
    
    # 자동 탐색 파일 설정
    if auto_files:
        st.markdown("**자동 탐색 파일 설정**")
        render_auto_file_settings(auto_files)
        st.markdown("---")
    
    # 수동 파일 업로드
    with st.expander("추가 파일 업로드", expanded=not auto_files):
        uploaded_files = st.file_uploader(
            "Excel 파일 추가",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="자동 탐색되지 않은 파일이나 추가 파일을 업로드",
            disabled=is_guest()
        )
        
        if uploaded_files:
            render_manual_file_settings(uploaded_files)
    
    st.markdown("---")
    
    # Step 3: 처리 방식 선택
    total_files = len(auto_files) + len(manual_files)
    if total_files > 0:
        st.subheader("처리 실행")
        
        st.info(f"처리 대상: 자동 {len(auto_files)}개 + 수동 {len(manual_files)}개 = 총 {total_files}개 파일")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("개별 처리", use_container_width=True, type="secondary", disabled=is_guest()):
                if not check_permission("파일 처리"):
                    return
                process_all_files_individually(auto_files, manual_files)
        
        with col2:
            if st.button("통합 처리", use_container_width=True, type="primary", disabled=is_guest()):
                if not check_permission("통합 처리"):
                    return
                process_all_files_combined(auto_files, manual_files)

def render_auto_file_settings(auto_files):
    """자동 탐색 파일 설정"""
    if 'wt_auto_file_settings' not in st.session_state:
        st.session_state.wt_auto_file_settings = {}
    
    service = WithholdingTaxService()
    file_type_to_company = {"AKT": 1, "INC": 2, "MR": 3, "AX": 4}
    
    for file_type, file_path in auto_files.items():
        company_type = file_type_to_company.get(file_type, 1)
        
        with st.container():
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.info(f"**{file_type}**: {Path(file_path).name}")
            
            with col2:
                # AKT, INC, MR만 시트 선택 가능
                if company_type in [1, 2, 3]:
                    try:
                        # 파일에서 시트 목록 가져오기
                        import pandas as pd
                        excel_file = pd.ExcelFile(file_path)
                        sheets = excel_file.sheet_names
                        
                        if len(sheets) > 1:
                            sheet_name = st.selectbox(
                                f"시트 선택",
                                options=sheets,
                                key=f"auto_sheet_{file_type}",
                                help=f"{file_type} 파일의 처리할 시트를 선택하세요"
                            )
                        else:
                            sheet_name = sheets[0] if sheets else None
                            st.info(f"시트: {sheet_name}")
                            
                        # 설정 저장
                        st.session_state.wt_auto_file_settings[file_type] = {
                            'file_path': file_path,
                            'company_type': company_type,
                            'sheet_name': sheet_name
                        }
                        
                    except Exception as e:
                        st.error(f"시트 정보를 읽을 수 없습니다: {e}")
                        st.session_state.wt_auto_file_settings[file_type] = {
                            'file_path': file_path,
                            'company_type': company_type,
                            'sheet_name': None
                        }
                else:
                    st.info("다중 시트 자동 처리")
                    st.session_state.wt_auto_file_settings[file_type] = {
                        'file_path': file_path,
                        'company_type': company_type,
                        'sheet_name': None
                    }

def render_period_selection_simple():
    """간소화된 기간 선택"""
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        year = st.selectbox("연도", list(range(2021, 2030)), index=4)
    with col2:
        month = st.selectbox("월", list(range(1, 13)), 
                           format_func=lambda x: f"{x:02d}월")
    with col3:
        if st.button("파일 찾기", use_container_width=True, disabled=is_guest()):
            if not check_permission("파일 탐색"):
                return
            scan_files_automatically(year, month)

def render_manual_file_settings(uploaded_files):
    """수동 파일 설정"""
    service = WithholdingTaxService()
    manual_settings = {}
    
    for i, uploaded_file in enumerate(uploaded_files):
        with st.container():
            col1, col2 = st.columns(2)
            
            with col1:
                company_type = st.selectbox(
                    f"회사 ({uploaded_file.name})",
                    [1, 2, 3, 4],
                    format_func=lambda x: {1:"애커튼", 2:"SK INC", 3:"SK MRCIC", 4:"SK AX"}[x],
                    key=f"manual_company_{i}"
                )
            
            with col2:
                sheet_name = None
                if company_type in [1, 2, 3]:
                    sheets = service.get_sheet_names(uploaded_file)
                    if sheets:
                        sheet_name = st.selectbox(f"시트", sheets, key=f"manual_sheet_{i}")
                else:
                    st.info("다중 시트 자동 처리")
            
            manual_settings[uploaded_file.name] = (uploaded_file, company_type, sheet_name)
    
    st.session_state.wt_manual_files = manual_settings

def process_all_files_individually(auto_files, manual_files):
    """모든 파일을 개별 처리"""
    # 자동 파일들 개별 처리 (시트 설정 반영)
    if auto_files:
        process_auto_files_with_settings(auto_files)
    
    # 수동 파일들 개별 처리  
    if manual_files:
        service = WithholdingTaxService()
        for filename, (uploaded_file, company_type, sheet_name) in manual_files.items():
            process_individual_file(uploaded_file, company_type, sheet_name, service)

def process_auto_files_with_settings(auto_files):
    """설정이 반영된 자동 파일들 처리"""
    service = WithholdingTaxService()
    auto_settings = st.session_state.get('wt_auto_file_settings', {})
    
    for file_type, file_path in auto_files.items():
        try:
            # 설정에서 회사 타입과 시트명 가져오기
            settings = auto_settings.get(file_type, {})
            company_type = settings.get('company_type', 1)
            sheet_name = settings.get('sheet_name', None)
            
            if Path(file_path).exists():
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                class MockUploadedFile:
                    def __init__(self, content, name):
                        self.content = content
                        self.name = name
                    def getvalue(self):
                        return self.content
                    def getbuffer(self):
                        return self.content
                
                mock_file = MockUploadedFile(file_content, Path(file_path).name)
                process_individual_file(mock_file, company_type, sheet_name, service)
                
        except Exception as e:
            st.error(f"{file_type} 처리 중 오류: {e}")

def process_all_files_combined(auto_files, manual_files):
    """모든 파일을 통합 처리"""
    service = WithholdingTaxService()
    
    # 혼합 처리 함수 호출
    result = service.process_mixed_files(auto_files, list(manual_files.values()))
    
    if result['success']:
        st.session_state.wt_all_companies_data = result['data']
        st.session_state.wt_combined_excel_data = result['excel_data']
        st.success(f"통합 처리 완료!")
    else:
        st.error(f"통합 처리 실패: {result['error']}")

def process_auto_files_individually(auto_files):
    """자동 탐색 파일들을 개별적으로 처리"""
    service = WithholdingTaxService()
    file_type_to_company = {
        "AKT": 1, "INC": 2, "MR": 3, "AX": 4
    }
    
    success_count = 0
    total_files = len(auto_files)
    
    for file_type, file_path in auto_files.items():
        try:
            company_type = file_type_to_company.get(file_type, 1)
            
            if Path(file_path).exists():
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                class MockUploadedFile:
                    def __init__(self, content, name):
                        self.content = content
                        self.name = name
                    def getvalue(self):
                        return self.content
                    def getbuffer(self):
                        return self.content
                
                mock_file = MockUploadedFile(file_content, Path(file_path).name)
                result = service.process_file(mock_file, company_type, None)
                
                if result['success']:
                    file_id = str(len(st.session_state.wt_processed_files) + 1)
                    st.session_state.wt_processed_files[file_id] = {
                        'filename': mock_file.name,
                        'company_type': company_type,
                        'company_name': result['company_name'],
                        'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'result_data': result['data'],
                        'excel_data': result['excel_data'],
                        'errors': result.get('errors', []),
                        'source': 'auto'
                    }
                    success_count += 1
                    
        except Exception as e:
            st.session_state.wt_processing_errors.append(f"{file_type}: {str(e)}")
    
    if success_count > 0:
        st.success(f"{success_count}/{total_files}개 파일이 성공적으로 처리되었습니다!")


def render_results_section():
    """처리 결과 섹션"""
    
    # 개별 처리 결과
    if st.session_state.wt_processed_files:
        st.markdown("---")
        st.markdown("###  개별 처리 결과")
    
        service = WithholdingTaxService()
        
        for file_id, file_info in st.session_state.wt_processed_files.items():
            with st.expander(f" {file_info['filename']} - {file_info['company_name']}", expanded=False):
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**처리 시간:** {file_info['processed_time']}")
                    
                    if 'result_data' in file_info and file_info['result_data']:
                        df = service.create_summary_dataframe(file_info['result_data'], file_info['company_type'])
                        
                        if not df.empty:
                            total_row = df[df['항목'] == '총합계']
                            if not total_row.empty:
                                metric_col1, metric_col2, metric_col3 = st.columns(3)
                                with metric_col1:
                                    st.metric("총 인원", service.format_number(total_row.iloc[0]['인원']))
                                with metric_col2:
                                    st.metric("총 소득세", service.format_number(total_row.iloc[0]['소득세']))
                                with metric_col3:
                                    st.metric("총 주민세", service.format_number(total_row.iloc[0]['주민세']))
                        
                        st.dataframe(df, use_container_width=True)
                
                with col2:
                    if 'excel_data' in file_info and file_info['excel_data']:
                        st.download_button(
                            label=" Excel 다운로드",
                            data=file_info['excel_data'],
                            file_name=f"{file_info['company_name']}_결과_{file_id}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key=f"download_{file_id}"
                        )
                    
                    if st.button(" 삭제", key=f"delete_{file_id}", use_container_width=True, disabled=is_guest()):
                        if not check_permission("결과 삭제"):
                            return
                        del st.session_state.wt_processed_files[file_id]
                        st.rerun()
    
    # 통합 처리 결과
    if st.session_state.wt_all_companies_data:
        st.markdown("---")
        st.markdown("###  통합 처리 결과")
        
        service = WithholdingTaxService()
        
        companies_processed = list(st.session_state.wt_all_companies_data.keys())
        company_names = [service.get_company_name(ct) for ct in companies_processed]
        
        st.write(f"**처리된 회사:** {len(companies_processed)}개")
        st.write(f"**회사 목록:** {', '.join(company_names)}")
        
        # 전체 합계
        total_personnel = 0
        total_income_tax = 0
        total_resident_tax = 0
        
        for company_type, company_data in st.session_state.wt_all_companies_data.items():
            if '총합계' in company_data:
                total_data = company_data['총합계']
                total_personnel += total_data.get('인원', 0)
                total_income_tax += total_data.get('소득세', 0)
                total_resident_tax += total_data.get('주민세', 0)
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("전체 인원", service.format_number(total_personnel))
        with metric_col2:
            st.metric("전체 소득세", service.format_number(total_income_tax))
        with metric_col3:
            st.metric("전체 주민세", service.format_number(total_resident_tax))
        
        # 통합 엑셀 다운로드
        if st.session_state.wt_combined_excel_data:
            st.download_button(
                label=" 통합 보고서 Excel 다운로드",
                data=st.session_state.wt_combined_excel_data,
                file_name=f"원천세_통합보고서_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="combined_download"
            )

def process_individual_file(uploaded_file, company_type, sheet_name, service):
    """개별 파일 처리"""
    with st.spinner("데이터 처리 중..."):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("파일 분석 중...")
            progress_bar.progress(0.2)
            
            result = service.process_file(uploaded_file, company_type, sheet_name)
            
            progress_bar.progress(0.8)
            status_text.text("결과 저장 중...")
            
            if result['success']:
                file_id = str(len(st.session_state.wt_processed_files) + 1)
                st.session_state.wt_processed_files[file_id] = {
                    'filename': uploaded_file.name,
                    'company_type': company_type,
                    'company_name': result['company_name'],
                    'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'result_data': result['data'],
                    'excel_data': result['excel_data'],
                    'errors': result.get('errors', [])
                }
                
                progress_bar.progress(1.0)
                status_text.text("처리 완료!")
                
                st.success(" 데이터 처리 완료!")
                
                if result.get('errors'):
                    st.warning(f"처리 중 {len(result['errors'])}건의 오류가 발생했습니다.")
            else:
                progress_bar.progress(1.0)
                status_text.text("처리 실패")
                st.error(f" 처리 실패: {result['error']}")
                st.session_state.wt_processing_errors.append(f"{uploaded_file.name}: {result['error']}")
            
        # 수정 후
        except Exception as e:
            error_msg = f"처리 중 예외 발생: {e}"
            st.error(error_msg)
            st.session_state.wt_processing_errors.append(f"{uploaded_file.name}: {str(e)}")
            
            # 상세 오류 정보를 expander로 제공
            with st.expander("상세 오류 정보"):
                import traceback
                st.code(traceback.format_exc())

def process_combined_files(file_company_mappings, service):
    """통합 파일 처리"""
    with st.spinner("통합 데이터 처리 중..."):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("통합 처리 시작...")
            progress_bar.progress(0.1)
            
            result = service.process_combined_files(file_company_mappings)
            
            progress_bar.progress(0.9)
            status_text.text("통합 보고서 생성 중...")
            
            if result['success']:
                st.session_state.wt_all_companies_data = result['data']
                st.session_state.wt_combined_excel_data = result['excel_data']
                
                progress_bar.progress(1.0)
                status_text.text("통합 처리 완료!")
                
                st.success(f" {len(result['data'])}개 회사 통합 처리 완료!")
                
                if result.get('errors'):
                    st.warning(f"처리 중 {len(result['errors'])}건의 오류가 발생했습니다.")
            else:
                progress_bar.progress(1.0)
                status_text.text("통합 처리 실패")
                st.error(f" 통합 처리 실패: {result['error']}")
                st.session_state.wt_processing_errors.append(f"통합 처리: {result['error']}")
            
        except Exception as e:
            st.error(f"통합 처리 중 예외 발생: {e}")
            st.session_state.wt_processing_errors.append(f"통합 처리: {str(e)}")

def main():
    # 폴더 설정 체크 (가장 먼저 실행)
    from services.folder_service import FolderService
    
    folder_service = FolderService()
    user_id = st.session_state.get("user", {}).get("user_id", "user")
    structure = folder_service.load_user_folder_structure(user_id, "원천세")
    
    if not structure:
        st.warning("원천세 폴더가 설정되지 않았습니다.")
        st.info("설정 페이지에서 원천세 폴더 구조를 먼저 설정해주세요.")
        if st.button("설정 페이지로 이동", type="primary"):
            st.switch_page("pages/settings.py")
        st.stop()
    
    # 기존 코드 (세션 상태 초기화)
    initialize_session_state()
    
    # 페이지 헤더
    page_header("원천세 관리", "")
    render_withholding_tax_tabs("이행상황신고서")
    
    st.markdown("원천세 데이터를 처리하고 신고서를 자동 생성합니다.")
    
    # 단계별 플로우로 변경
    render_unified_processing_flow()
    
    # 사이드바 현황
    render_sidebar_status()
    
    # 결과 영역
    render_results_section()

    # 챗봇에서 전달된 처리 결과 확인 (하단에 표시)
    if 'processing_result' in st.session_state and st.session_state.processing_result.get('from_chatbot'):
        st.markdown("---")
        st.markdown("### 챗봇 자동 처리 완료")
        
        result = st.session_state.processing_result
        st.success(f"{result['period']} {result['task']} 처리가 완료되었습니다!")
        
        # 실제 처리된 데이터 표시
        if st.session_state.wt_processed_files:
            service = WithholdingTaxService()
            
            # 전체 합계 계산
            total_personnel = 0
            total_income_tax = 0
            total_resident_tax = 0
            
            for file_id, file_info in st.session_state.wt_processed_files.items():
                if file_info.get('source') == 'chatbot_auto' and 'result_data' in file_info:
                    df = service.create_summary_dataframe(file_info['result_data'], file_info['company_type'])
                    
                    if not df.empty:
                        total_row = df[df['항목'] == '총합계']
                        if not total_row.empty:
                            total_personnel += total_row.iloc[0]['인원']
                            total_income_tax += total_row.iloc[0]['소득세']
                            total_resident_tax += total_row.iloc[0]['주민세']
            
            # 메트릭 표시
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("총 인원", service.format_number(total_personnel))
            with col2:
                st.metric("총 소득세", service.format_number(total_income_tax))
            with col3:
                st.metric("총 주민세", service.format_number(total_resident_tax))
            
            st.info("상세 결과는 위의 '개별 처리 결과' 섹션에서 확인하세요.")
            
            # 엑셀 다운로드 버튼들
            st.markdown("#### 다운로드")
            download_col1, download_col2 = st.columns(2)
            
            with download_col1:
                # 개별 파일들 다운로드
                for file_id, file_info in st.session_state.wt_processed_files.items():
                    if file_info.get('source') == 'chatbot_auto' and 'excel_data' in file_info:
                        st.download_button(
                            label=f"{file_info['company_name']} 다운로드",
                            data=file_info['excel_data'],
                            file_name=f"{file_info['company_name']}_원천세_{result['period']}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key=f"chatbot_download_{file_id}"
                        )
            
            with download_col2:
                # 통합 보고서가 있다면 (통합 처리한 경우)
                if st.session_state.wt_combined_excel_data:
                    st.download_button(
                        label="통합 보고서 다운로드",
                        data=st.session_state.wt_combined_excel_data,
                        file_name=f"원천세_통합보고서_{result['period']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                        key="chatbot_combined_download"
                    )
        
        # 확인 버튼
        if st.button("확인", type="secondary", key="clear_chatbot_result"):
            del st.session_state.processing_result
            st.rerun()
        
        st.markdown("---")

if __name__ == "__main__":
    main()