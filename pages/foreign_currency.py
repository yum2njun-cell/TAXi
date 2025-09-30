import streamlit as st
import pandas as pd
from datetime import datetime
from utils.settings import settings
from components.layout import page_header, sidebar_menu, show_toast
from components.auth_widget import check_auth
from services.foreign_currency_service import ForeignCurrencyService
from components.vat_tabs import render_vat_tabs_simple
from components.theme import apply_custom_theme
from utils.path_mapper import PathMapper
from services.file_scanner import FileScanner
from pathlib import Path
import io
from utils.auth import is_guest, check_permission

# 인증 체크 (다른 페이지와 동일한 방식)
if not check_auth():
    st.switch_page("app.py")

# 페이지 설정
st.set_page_config(
    page_title=f"{settings.APP_NAME} | 부가세 관리",
    page_icon="",
    layout="wide"
)

# 스타일 로드 후에
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

# 기본 페이지 네비게이션만 숨기고, 커스텀 메뉴는 살리기
st.markdown("""
<style>
/* 멀티페이지 네비 컨테이너는 유지하되, 그 안의 항목만 숨김 */
[data-testid="stSidebarNav"] ul,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] a {
    display: none !important;
}

/* 혹시 이전에 + div 를 숨기는 규칙을 넣었다면 무력화 */
[data-testid="stSidebarNav"] + div {
    display: block !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

# 페이지 헤더
page_header("부가세 관리", "")

# 부가세 탭 렌더링
render_vat_tabs_simple("외화획득명세서")

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()

def scan_foreign_currency_files(year: int, quarter: int):
    """외화획득명세서 파일 자동 탐색"""
    try:
        # ===== 기간 설정 추가 =====
        service.set_period(year, quarter)
        st.session_state.fc_year = year
        st.session_state.fc_quarter = quarter
        # ===== 기간 설정 끝 =====

        mapper = PathMapper(work_type="국제조세")
        scanner = FileScanner(mapper)
        
        period_str = f"{year}년 {quarter}분기"
        
        with st.spinner("외화획득명세서 파일을 자동으로 탐색 중..."):
            results = scanner.scan_foreign_currency_folders("국제조세", period_str)
            
            # 오류 체크
            if '_error' in results:
                st.error(f"탐색 실패: {results['_error'].error}")
                return
            
            # 결과 정리
            found_files = {}
            errors = []
            
            for file_type in ['export', 'exchange', 'invoice', 'a2']:
                if file_type in results:
                    result = results[file_type]
                    if result.found:
                        if result.paths:
                            found_files[file_type] = result.paths
                        elif result.path:
                            found_files[file_type] = result.path
                    else:
                        errors.append(f"{file_type}: {result.error}")
            
            # 세션에 저장
            st.session_state.fc_auto_scan_results = {
                'period': period_str,
                'files': found_files,
                'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            if found_files:
                st.success(f"파일 탐색 완료! (총 {len(found_files)}개 항목)")
            
            if errors:
                st.warning("일부 파일을 찾지 못했습니다:")
                for error in errors:
                    st.caption(f"- {error}")
                    
    except Exception as e:
        st.error(f"자동 탐색 중 오류: {e}")
        import traceback
        st.error(traceback.format_exc())


def process_auto_found_files():
    """자동 탐색된 파일들 처리"""
    if 'fc_auto_scan_results' not in st.session_state or not st.session_state.fc_auto_scan_results:
        st.warning("먼저 파일을 탐색해주세요.")
        return
    
    found_files = st.session_state.fc_auto_scan_results.get('files', {})
    
    def create_mock_files(file_paths):
        """파일 경로에서 BytesIO 객체 생성"""
        import io
        
        mock_files = []
        if not isinstance(file_paths, list):
            file_paths = [file_paths]
        
        for file_path in file_paths:
            file_path = Path(file_path)
            
            if not file_path.exists():
                st.error(f"파일을 찾을 수 없습니다: {file_path}")
                continue
            
            try:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                file_obj = io.BytesIO(file_content)
                file_obj.name = file_path.name
                
                mock_files.append(file_obj)
                
            except Exception as e:
                st.error(f"파일 읽기 실패 ({file_path.name}): {e}")
        
        return mock_files
    
    # 진행 상황 표시
    progress_container = st.empty()
    
    try:
        # 1단계: 수출이행내역
        if 'export' in found_files:
            progress_container.info("⏳ 1단계: 수출이행내역 처리 중...")
            try:
                export_files = create_mock_files(found_files['export'])
                if export_files:
                    result = service.process_export_data(export_files)
                    if 'error' in result:
                        st.error(f"❌ 1단계 실패: {result['error']}")
                        progress_container.empty()
                        return
                    else:
                        st.success("✅ 1단계 완료")
                else:
                    st.warning("⚠️ 1단계: 처리할 파일이 없습니다")
            except Exception as e:
                st.error(f"❌ 1단계 오류: {e}")
                with st.expander("상세 오류"):
                    import traceback
                    st.code(traceback.format_exc())
                progress_container.empty()
                return
        
        # 2단계: 환율정보
        if 'exchange' in found_files:
            progress_container.info("⏳ 2단계: 환율정보 처리 중...")
            try:
                exchange_files = create_mock_files(found_files['exchange'])
                if exchange_files:
                    result = service.process_exchange_data(exchange_files)
                    if 'error' in result:
                        st.error(f"❌ 2단계 실패: {result['error']}")
                        with st.expander("상세 오류 정보"):
                            st.write(result)
                        progress_container.empty()
                        return
                    else:
                        st.success("✅ 2단계 완료")
                else:
                    st.warning("⚠️ 2단계: 처리할 파일이 없습니다")
            except Exception as e:
                st.error(f"❌ 2단계 오류: {e}")
                with st.expander("상세 오류"):
                    import traceback
                    st.code(traceback.format_exc())
                progress_container.empty()
                return
        
        # 3단계: 인보이스 발행내역
        if 'invoice' in found_files:
            progress_container.info("⏳ 3단계: 인보이스 발행내역 처리 중...")
            try:
                invoice_files = create_mock_files(found_files['invoice'])
                if invoice_files:
                    export_data = service.get_processed_data('export')
                    result = service.process_invoice_data(invoice_files, export_data)
                    if 'error' in result:
                        st.error(f"❌ 3단계 실패: {result['error']}")
                        progress_container.empty()
                        return
                    else:
                        st.success("✅ 3단계 완료")
                else:
                    st.warning("⚠️ 3단계: 처리할 파일이 없습니다")
            except Exception as e:
                st.error(f"❌ 3단계 오류: {e}")
                with st.expander("상세 오류"):
                    import traceback
                    st.code(traceback.format_exc())
                progress_container.empty()
                return
        
        # 4단계: A2 데이터
        if 'a2' in found_files:
            progress_container.info("⏳ 4단계: A2 데이터 처리 중...")
            try:
                a2_files = create_mock_files(found_files['a2'])
                if a2_files:
                    invoice_data = service.get_processed_data('invoice')
                    result = service.process_a2_data(a2_files, invoice_data)
                    if 'error' in result:
                        st.error(f"❌ 4단계 실패: {result['error']}")
                        progress_container.empty()
                        return
                    else:
                        st.success("✅ 4단계 완료")
                else:
                    st.warning("⚠️ 4단계: 처리할 파일이 없습니다")
            except Exception as e:
                st.error(f"❌ 4단계 오류: {e}")
                with st.expander("상세 오류"):
                    import traceback
                    st.code(traceback.format_exc())
                progress_container.empty()
                return
        
        progress_container.empty()
        st.success("🎉 전체 처리 완료!")
        
        # 처리 완료 후 결과 확인
        st.info("처리 결과는 아래 탭에서 확인하실 수 있습니다.")
        
    except Exception as e:
        progress_container.empty()
        st.error(f"❌ 자동 처리 중 예상치 못한 오류: {e}")
        with st.expander("상세 오류 정보"):
            import traceback
            st.code(traceback.format_exc())

# 폴더 설정 체크 (가장 먼저 실행)
from services.folder_service import FolderService

folder_service = FolderService()
user_id = st.session_state.get("user", {}).get("user_id", "user")
structure = folder_service.load_user_folder_structure(user_id, "국제조세")

if not structure or not structure.get('base_path'):
    st.warning("⚠️ 국제조세 폴더가 설정되지 않았습니다.")
    st.info("""
    설정 페이지에서 '국제조세' 세목을 선택하고 폴더 경로를 먼저 설정해주세요.
            C:\\Users\\[사번]\\SK주식회사 C&C\\V_세무TF - General\\02_ 국제조세 자료
    """)
    
    if st.button("⚙️ 설정 페이지로 이동", type="primary"):
        st.switch_page("pages/settings.py")
    
    st.stop()  # 여기서 페이지 실행 중단
            

# 서비스 초기화
if 'foreign_currency_service' not in st.session_state:
    st.session_state.foreign_currency_service = ForeignCurrencyService()

service = st.session_state.foreign_currency_service

# 연도/분기 설정 섹션
st.markdown("###  처리 기간 설정")

col1, col2, col3 = st.columns([2, 2, 6])

with col1:
    current_year = datetime.now().year
    year = st.selectbox(
        " 처리 연도",
        options=list(range(2020, 2030)),
        index=current_year - 2020,
        key="fc_year_selector"
    )

with col2:
    quarter = st.selectbox(
        " 처리 분기",
        options=[1, 2, 3, 4],
        index=0,
        format_func=lambda x: f"{x}분기",
        key="fc_quarter_selector"
    )

with col3:
    if st.button(" 설정 적용", type="primary", key="apply_fc_period", disabled=is_guest()):
        if check_permission("기간 설정"):
            st.session_state.fc_year = year
            st.session_state.fc_quarter = quarter
            service.set_period(year, quarter)
            st.success(f" {year}년 {quarter}분기로 설정되었습니다")
            st.rerun()

# 현재 설정 표시
if hasattr(st.session_state, 'fc_year') and hasattr(st.session_state, 'fc_quarter'):
    st.info(f" 현재 설정: {st.session_state.fc_year}년 {st.session_state.fc_quarter}분기")

st.markdown("---")

# 처리 현황 표시
st.markdown("###  처리 현황")

stages = {
    1: "수출이행내역 취합",
    2: "환율정보 취합", 
    3: "인보이스 발행내역",
    4: "A2 데이터 정리",
    5: "최종 명세서 생성"
}

current_stage = service.get_processing_stage()

progress_cols = st.columns(5)
for i, (stage_num, stage_name) in enumerate(stages.items()):
    with progress_cols[i]:
        if stage_num <= current_stage:
            st.markdown(f"""
            <div class="stats-card" style="background-color: #d4edda; border-color: #c3e6cb;">
                <div class="stat-number" style="color: #155724;"></div>
                <div class="stat-label" style="color: #155724;">{stage_num}. {stage_name}</div>
            </div>
            """, unsafe_allow_html=True)
        elif stage_num == current_stage + 1:
            st.markdown(f"""
            <div class="stats-card" style="background-color: #d1ecf1; border-color: #bee5eb;">
                <div class="stat-number" style="color: #0c5460;"></div>
                <div class="stat-label" style="color: #0c5460;">{stage_num}. {stage_name}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="stats-card">
                <div class="stat-number"></div>
                <div class="stat-label">{stage_num}. {stage_name}</div>
            </div>
            """, unsafe_allow_html=True)

# 전체 초기화 버튼
col_reset1, col_reset2 = st.columns([8, 2])
with col_reset2:
    if st.button(" 전체 초기화", key="fc_reset", help="모든 처리 단계를 초기화합니다", disabled=is_guest()):
        if check_permission("데이터 초기화"):
            service.reset_all_data()
            st.success("모든 데이터가 초기화되었습니다!")
            st.rerun()

st.markdown("---")

# 자동 파일 탐색 섹션
st.markdown("### 자동 파일 탐색")

col_scan1, col_scan2, col_scan3 = st.columns([2, 2, 1])

with col_scan1:
    scan_year = st.selectbox(
        "탐색 연도",
        options=list(range(2020, 2030)),
        index=current_year - 2020,
        key="fc_scan_year"
    )

with col_scan2:
    scan_quarter = st.selectbox(
        "탐색 분기",
        options=[1, 2, 3, 4],
        index=0,
        format_func=lambda x: f"{x}분기",
        key="fc_scan_quarter"
    )

with col_scan3:
    if st.button("파일 찾기", use_container_width=True, key="fc_auto_scan", disabled=is_guest()):
        if check_permission("파일 자동 탐색"):
            scan_foreign_currency_files(scan_year, scan_quarter)

# 자동 탐색 결과 표시
if 'fc_auto_scan_results' in st.session_state and st.session_state.fc_auto_scan_results:
    results = st.session_state.fc_auto_scan_results
    
    with st.expander("자동 탐색 결과", expanded=True):
        st.info(f"**탐색 기간**: {results.get('period', 'Unknown')}")
        
        file_labels = {
            'export': '1단계: 수출이행내역',
            'exchange': '2단계: 환율정보',
            'invoice': '3단계: 인보이스 발행내역',
            'a2': '4단계: A2리스트'
        }
        
        found_files = results.get('files', {})
        
        for file_type, label in file_labels.items():
            if file_type in found_files:
                files = found_files[file_type]
                if isinstance(files, list):
                    st.success(f"✅ **{label}**: {len(files)}개 파일")
                    for f in files:
                        st.caption(f"  - {Path(f).name}")
                else:
                    st.success(f"✅ **{label}**: {Path(files).name}")
            else:
                st.warning(f"⚠️ **{label}**: 파일 없음")
    
    # 자동 처리 버튼
    if st.button("자동 탐색 파일로 전체 처리", type="primary", use_container_width=True, key="fc_auto_process_all", disabled=is_guest()):
        if check_permission("파일 처리"):
            process_auto_found_files()

# 메인 탭 구성
tab1, tab2, tab3, tab4 = st.tabs([
    " 1-4단계: 데이터 처리", 
    " 5단계: 최종 명세서", 
    " 통합 결과", 
    " 전체 다운로드"
])

with tab1:
    st.header(" 1-4단계: 원시 데이터 처리")
    
    # 1단계: 수출이행내역 처리
    st.subheader("1️ 수출이행내역 취합")
    
    col1_1, col2_1 = st.columns([2, 1])
    
    with col1_1:
        export_files = st.file_uploader(
            "수출이행내역기간조회 파일들을 선택하세요",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="파일명에 '수출이행내역기간조회'가 포함된 Excel 파일들",
            key="fc_export_files",
            disabled=is_guest()
        )
    
    with col2_1:
        if export_files and st.button(" 1단계 처리", key="fc_process_stage1", disabled=is_guest()):
            if check_permission("파일 처리"):
                with st.spinner("수출이행내역 처리 중..."):
                    result = service.process_export_data(export_files)
                    
                    if 'error' in result:
                        st.error(f" 처리 실패: {result['error']}")
                    else:
                        st.success(" 1단계 완료!")
                        
                        # 요약 표시
                        summary = result.get('summary', {})
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("총 행 수", summary.get('total_rows', 0))
                        with col_b:
                            st.metric("처리 파일", summary.get('success_files', 0))
                        with col_c:
                            st.metric("전체 파일", summary.get('total_files', 0))
        
        # 1단계 결과 표시
        export_data = service.get_processed_data('export')
        if export_data is not None and not export_data.empty:
            with st.expander(" 수출이행내역 미리보기"):
                st.dataframe(export_data.head(10), use_container_width=True)
                
                raw_data = service.get_all_data()
                if 'export' in raw_data:
                    st.download_button(
                        " 수출내역 다운로드",
                        data=raw_data['export']['excel_data'],
                        file_name=f"수출내역_통합_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        st.divider()
        
        # 2단계: 환율정보 처리
        st.subheader(" 환율정보 취합")
        
        col1_2, col2_2 = st.columns([2, 1])
    
    with col1_2:
        exchange_files = st.file_uploader(
            "환율정보 파일들을 선택하세요",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="각 통화별 환율 데이터가 포함된 Excel 파일들 (시트명=통화코드)",
            key="fc_exchange_files",
            disabled=is_guest()
        )
    
    with col2_2:
        if export_files and st.button(" 1단계 처리", key="fc_process_stage1", disabled=is_guest()):
            if check_permission("파일 처리"):
                with st.spinner("수출이행내역 처리 중..."):
                    result = service.process_exchange_data(exchange_files)
                    
                    if 'error' in result:
                        st.error(f" 처리 실패: {result['error']}")
                    else:
                        st.success(" 2단계 완료!")
                        
                        # 요약 표시
                        summary = result.get('summary', {})
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.metric("총 일수", summary.get('total_days', 0))
                        with col_b:
                            st.metric("통화 수", summary.get('currency_count', 0))
                        
                        if summary.get('currencies'):
                            currencies = summary['currencies']
                            if isinstance(currencies, list):
                                currencies_str = ', '.join(currencies)
                            else:
                                currencies_str = str(currencies)
                            st.info(f" 처리된 통화: {currencies_str}")
        
        # 2단계 결과 표시
        exchange_data = service.get_processed_data('exchange')
        if exchange_data is not None and not exchange_data.empty:
            with st.expander(" 환율정보 미리보기"):
                st.dataframe(exchange_data.head(10), use_container_width=True)
                
                raw_data = service.get_all_data()
                if 'exchange' in raw_data:
                    st.download_button(
                        " 환율정보 다운로드",
                        data=raw_data['exchange']['excel_data'],
                        file_name=f"환율정보_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        st.divider()
    
    # 3단계: 인보이스 발행내역 처리
    st.subheader(" 인보이스 발행내역 처리")
    
    col1_3, col2_3 = st.columns([2, 1])
    
    with col1_3:
        invoice_files = st.file_uploader(
            "인보이스 파일들을 선택하세요",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="파일명에 '인보이스'가 포함된 Excel 파일들",
            key="fc_invoice_files",
            disabled=is_guest()
        )
        
        use_export_data = st.checkbox(
            "1단계 수출내역 데이터 포함",
            value=True,
            help="1단계에서 처리한 수출내역을 인보이스 형식으로 포함"
        )
    
    with col2_3:
        if invoice_files and st.button(" 3단계 처리", key="fc_process_stage3", disabled=is_guest()):
            if check_permission("파일 처리"):
                with st.spinner("인보이스 발행내역 처리 중..."):
                    # 수출내역 데이터 가져오기
                    export_data = None
                    if use_export_data:
                        export_data = service.get_processed_data('export')
                    
                    result = service.process_invoice_data(invoice_files, export_data)
                    
                    if 'error' in result:
                        st.error(f" 처리 실패: {result['error']}")
                    else:
                        st.success(" 3단계 완료!")
                        
                        # 요약 표시
                        summary = result.get('summary', {})
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("총 행 수", summary.get('total_rows', 0))
                        with col_b:
                            st.metric("용역", summary.get('service_rows', 0))
                        with col_c:
                            st.metric("재화", summary.get('goods_rows', 0))
        
        # 3단계 결과 표시
        invoice_data = service.get_processed_data('invoice')
        if invoice_data is not None and not invoice_data.empty:
            with st.expander(" 인보이스 발행내역 미리보기"):
                st.dataframe(invoice_data.head(10), use_container_width=True)
                
                raw_data = service.get_all_data()
                if 'invoice' in raw_data:
                    st.download_button(
                        " 인보이스 발행내역 다운로드",
                        data=raw_data['invoice']['excel_data'],
                        file_name=f"인보이스_발행내역_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        st.divider()
    
    # 4단계: A2 데이터 정리
    st.subheader(" A2 데이터 정리")
    
    col1_4, col2_4 = st.columns([2, 1])
    
    with col1_4:
        a2_files = st.file_uploader(
            "A2리스트 파일을 선택하세요",
            type=['xlsx', 'xls'],
            accept_multiple_files=True,
            help="파일명에 'A2리스트'가 포함된 Excel 파일",
            key="fc_a2_files",
            disabled=is_guest()
        )
        
        use_invoice_data = st.checkbox(
            "3단계 인보이스 데이터 연동",
            value=True,
            help="3단계에서 처리한 인보이스 발행내역과 연동하여 매칭"
        )
    
    with col2_4:
        if a2_files and st.button(" 4단계 처리", key="fc_process_stage4", disabled=is_guest()):
            if check_permission("파일 처리"):
                with st.spinner("A2 데이터 정리 중..."):
                    # 인보이스 데이터 가져오기
                    invoice_data = None
                    if use_invoice_data:
                        invoice_data = service.get_processed_data('invoice')
                    
                    result = service.process_a2_data(a2_files, invoice_data)
                    
                    if 'error' in result:
                        st.error(f" 처리 실패: {result['error']}")
                    else:
                        st.success(" 4단계 완료!")
                        
                        # 요약 표시
                        summary = result.get('summary', {})
                        col_a, col_b, col_c = st.columns(3)
                        with col_a:
                            st.metric("원본 행", summary.get('original_rows', 0))
                        with col_b:
                            st.metric("필터링 후", summary.get('filtered_rows', 0))
                        with col_c:
                            st.metric("처리 행", summary.get('processed_rows', 0))
    
    # 4단계 결과 표시
    a2_data = service.get_processed_data('a2')
    if a2_data is not None and not a2_data.empty:
        with st.expander(" A2 정리 결과 미리보기"):
            st.dataframe(a2_data.head(10), use_container_width=True)
            
            raw_data = service.get_all_data()
            if 'a2' in raw_data:
                st.download_button(
                    " A2 정리 다운로드",
                    data=raw_data['a2']['excel_data'],
                    file_name=f"A2정리_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

with tab2:
    st.header(" 5단계: 최종 외화획득명세서 생성")
    
    # 전제 조건 확인
    raw_data = service.get_all_data()
    required_data = ['invoice']
    available_data = []
    missing_data = []
    
    for data_type in ['invoice', 'exchange', 'a2']:
        if data_type in raw_data and 'data' in raw_data[data_type]:
            available_data.append(data_type)
        else:
            if data_type == 'invoice':
                missing_data.append(data_type)
    
    # 상태 표시
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader(" 데이터 준비 상태")
        
        data_names = {
            'invoice': '인보이스 발행내역 (필수)',
            'exchange': '환율정보 (선택)',
            'a2': 'A2 정리 데이터 (선택)'
        }
        
        for data_type, name in data_names.items():
            if data_type in available_data:
                st.success(f" {name}")
            else:
                if data_type == 'invoice':
                    st.error(f" {name}")
                else:
                    st.warning(f" {name}")
    
    with col2:
        st.subheader(" 최종 명세서 생성")
        
        if missing_data:
            st.error(" 인보이스 발행내역 데이터가 필요합니다. 3단계를 먼저 완료해주세요.")
        else:
            if st.button(" 최종 명세서 생성", type="primary", key="fc_generate_final", disabled=is_guest()):
                if check_permission("최종 명세서 생성"):
                    with st.spinner("최종 외화획득명세서 생성 중..."):
                        # 데이터 준비
                        invoice_data = raw_data['invoice']['data']
                        exchange_data = raw_data.get('exchange', {}).get('data')
                        a2_data = raw_data.get('a2', {}).get('data')
                        
                        # 최종 보고서 생성
                        result = service.generate_final_report(
                            invoice_data, exchange_data, a2_data
                        )
                        
                        if 'error' in result:
                            st.error(f" 생성 실패: {result['error']}")
                        else:
                            st.success(" 최종 외화획득명세서 생성 완료!")
                            
                            # 다운로드 버튼
                            st.download_button(
                                " 최종 명세서 다운로드",
                                data=result['excel_data'],
                                file_name=f"외화획득명세서_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
    
    # 생성된 최종 보고서 표시
    if 'final_report' in raw_data:
        st.divider()
        st.subheader(" 최종 명세서 정보")
        
        summary = raw_data['final_report'].get('summary', {})
        
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("총 데이터 행 수", summary.get('total_rows', 0))
        with col_b:
            currencies = summary.get('currencies_used', [])
            st.info(f" 사용된 통화: {', '.join(currencies) if currencies else '없음'}")
        
        # 다운로드 버튼 재표시
        st.download_button(
            " 최종 명세서 다시 다운로드",
            data=raw_data['final_report']['excel_data'],
            file_name=f"외화획득명세서_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="fc_final_redownload"
        )

with tab3:
    st.header(" 통합 처리 결과")
    
    raw_data = service.get_all_data()
    
    if not raw_data:
        st.info("아직 처리된 데이터가 없습니다.")
    else:
        # 처리 단계별 결과 표시
        stages = {
            'export': ('1단계', '수출이행내역 취합'),
            'exchange': ('2단계', '환율정보 취합'),
            'invoice': ('3단계', '인보이스 발행내역'),
            'a2': ('4단계', 'A2 데이터 정리'),
            'final_report': ('5단계', '최종 명세서')
        }
        
        for data_type, (stage_num, stage_name) in stages.items():
            if data_type in raw_data:
                with st.expander(f" {stage_num}: {stage_name}", expanded=False):
                    
                    if data_type == 'final_report':
                        # 최종 보고서는 다운로드만 제공
                        summary = raw_data[data_type].get('summary', {})
                        st.write(f"**총 데이터 행 수:** {summary.get('total_rows', 0)}")
                        
                        st.download_button(
                            " 최종 명세서 다운로드",
                            data=raw_data[data_type]['excel_data'],
                            file_name=f"외화획득명세서_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            key=f"fc_download_{data_type}"
                        )
                    else:
                        # 데이터 및 요약 정보 표시
                        data_df = raw_data[data_type].get('data', pd.DataFrame())
                        summary = raw_data[data_type].get('summary', {})
                        
                        # 요약 정보
                        st.write("**처리 요약:**")
                        if summary:
                            summary_cols = st.columns(min(len(summary), 4))
                            for i, (key, value) in enumerate(summary.items()):
                                col_idx = i % len(summary_cols)
                                with summary_cols[col_idx]:
                                    if isinstance(value, list):
                                        display_value = ', '.join(map(str, value))
                                    elif isinstance(value, dict):
                                        display_value = f"{len(value)}개 항목"
                                    else:
                                        display_value = str(value)
                                    
                                    st.metric(key.replace('_', ' ').title(), display_value)
                        
                        # 데이터 미리보기
                        if not data_df.empty:
                            st.write("**데이터 미리보기:**")
                            st.dataframe(data_df.head(5), use_container_width=True)
                        
                        # 다운로드 버튼
                        if 'excel_data' in raw_data[data_type]:
                            filename_map = {
                                'export': f"수출내역_통합_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                                'exchange': f"환율정보_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                                'invoice': f"인보이스_발행내역_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx",
                                'a2': f"A2정리_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx"
                            }
                            
                            st.download_button(
                                f" {stage_name} 다운로드",
                                data=raw_data[data_type]['excel_data'],
                                file_name=filename_map.get(data_type, f"{data_type}.xlsx"),
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                key=f"fc_download_{data_type}"
                            )

with tab4:
    st.header(" 전체 결과 다운로드")
    
    raw_data = service.get_all_data()
    
    if not raw_data:
        st.info("다운로드할 데이터가 없습니다.")
    else:
        st.write("###  개별 파일 다운로드")
        
        # 개별 파일 다운로드 버튼들
        col1, col2 = st.columns(2)
        
        download_files = {
            'export': (' 수출내역 통합', f"수출내역_통합_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx"),
            'exchange': (' 환율정보', f"환율정보_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx"),
            'invoice': (' 인보이스 발행내역', f"인보이스_발행내역_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx"),
            'a2': (' A2 정리', f"A2정리_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx"),
            'final_report': (' 최종 명세서', f"외화획득명세서_{st.session_state.get('fc_year', 2025)}년_{st.session_state.get('fc_quarter', 1)}분기.xlsx")
        }
        
        for i, (data_type, (button_text, filename)) in enumerate(download_files.items()):
            col = col1 if i % 2 == 0 else col2
            
            with col:
                if data_type in raw_data and 'excel_data' in raw_data[data_type]:
                                            st.download_button(
                        button_text,
                        data=raw_data[data_type]['excel_data'],
                        file_name=filename,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"fc_individual_download_{data_type}",
                        use_container_width=True
                    )
                else:
                    st.button(
                        f" {button_text} (미처리)",
                        disabled=True,
                        use_container_width=True
                    )


# 사용법 안내
with st.expander(" 사용법 및 주의사항"):
    st.markdown("""
    ### 사용법
    1. **처리 기간 설정**: 연도와 분기를 선택한 후 '설정 적용' 클릭
    2. **1단계**: 수출이행내역기간조회 Excel 파일들을 업로드하여 취합
    3. **2단계**: 각 통화별 환율 정보 Excel 파일들을 업로드하여 취합
    4. **3단계**: 인보이스 발행내역 Excel 파일들을 업로드하여 처리
    5. **4단계**: A2리스트 Excel 파일을 업로드하여 정리
    6. **5단계**: 최종 외화획득명세서를 생성하여 다운로드
    
    ### 파일 형식 요구사항
    - **수출이행내역**: '수출이행내역기간조회'가 파일명에 포함된 Excel 파일
    - **환율정보**: 시트명이 통화코드(USD, EUR 등)인 Excel 파일
    - **인보이스**: 연도별 시트가 있는 Excel 파일 (예: '25년' 시트)
    - **A2리스트**: 'A2리스트'가 파일명에 포함된 Excel 파일
    
    ### 처리 흐름
    - 각 단계는 순차적으로 진행됩니다
    - 이전 단계의 데이터를 다음 단계에서 활용할 수 있습니다
    - 모든 단계별 결과는 개별적으로 다운로드 가능합니다
    
    ### 주의사항
    - 파일 크기가 클 경우 처리 시간이 소요될 수 있습니다
    - 결과는 참고용이며, 최종 검토는 세무 전문가와 상담하세요
    - 처리 중 오류가 발생하면 파일 형식과 데이터를 확인해주세요
    """)

# ✨ 여기에 추가 ✨
st.markdown("---")

# 챗봇에서 전달된 처리 결과 (하단)
if 'processing_result' in st.session_state and st.session_state.processing_result.get('from_chatbot'):
    st.markdown("### 챗봇 자동 처리 완료")
    
    result = st.session_state.processing_result
    st.success(f"{result['period']} 외화획득명세서 처리가 완료되었습니다!")
    
    if st.button("확인", type="secondary", key="clear_chatbot_result"):
        del st.session_state.processing_result
        st.rerun()