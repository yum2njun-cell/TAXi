import streamlit as st
import pandas as pd
from datetime import datetime
from utils.settings import settings
from components.layout import page_header, sidebar_menu, show_toast
from components.auth_widget import check_auth
from services.card_service import CardService
from components.vat_tabs import render_vat_tabs_simple
from components.theme import apply_custom_theme
from utils.auth import is_guest, check_permission

# 인증 체크 (다른 페이지와 동일한 방식)
if not check_auth():
    st.switch_page("app.py")

# 페이지 설정
st.set_page_config(
    page_title=f"{settings.APP_NAME} | 부가세",
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

from components.vat_tabs import render_vat_tabs_simple
render_vat_tabs_simple("법인카드 공제 여부 확인")

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()

# 서비스 초기화
card_service = CardService()

# 키워드 관리 섹션
st.markdown("###  키워드 설정 관리")

# 세션에 저장된 키워드가 있는지 확인
if 'custom_keywords_loaded' not in st.session_state:
    st.session_state.custom_keywords_loaded = False

# 현재 키워드 상태 표시
keyword_summary = card_service.get_keywords_summary()
if st.session_state.custom_keywords_loaded:
    st.success(f" 사용자 키워드 설정 적용됨 (불공제: {keyword_summary['no_vat_count']}개, 예외: {keyword_summary['vat_exceptions_count']}개)")
else:
    st.info(f" 기본 키워드 사용 중 (불공제: {keyword_summary['no_vat_count']}개, 예외: {keyword_summary['vat_exceptions_count']}개)")

col_kw1, col_kw2, col_kw3 = st.columns([1, 1, 1])

with col_kw1:
    # 키워드 파일 업로드
    keywords_file = st.file_uploader(
        " 키워드 파일 업로드",
        type=["xlsx", "xls"],
        help="no_vat, vat_exceptions 시트가 포함된 Excel 파일",
        key="keywords_upload",
        disabled=is_guest()
    )
    
    if keywords_file is not None:
        try:
            card_service.load_keywords_from_file(keywords_file)
            st.session_state.custom_keywords_loaded = True
            # 세션에 키워드 저장
            st.session_state.no_vat_keywords = card_service.no_vat_keywords.copy()
            st.session_state.vat_exceptions_keywords = card_service.vat_exceptions_keywords.copy()
            st.success("키워드 파일이 적용되었습니다!")
            st.rerun()
        except Exception as e:
            st.error(f"키워드 파일 로드 실패: {str(e)}")

with col_kw2:
    # 기본 키워드로 초기화
    if st.button(" 기본 키워드로 초기화", help="시스템 기본 키워드로 되돌립니다", disabled=is_guest()):
        if check_permission("키워드 초기화"):
            card_service.reset_to_default_keywords()
            st.session_state.custom_keywords_loaded = False
            if 'no_vat_keywords' in st.session_state:
                del st.session_state.no_vat_keywords
            if 'vat_exceptions_keywords' in st.session_state:
                del st.session_state.vat_exceptions_keywords
            st.success("기본 키워드로 초기화되었습니다!")
            st.rerun()

with col_kw3:
    # 현재 키워드 다운로드
    if st.button(" 현재 키워드 다운로드", help="현재 설정된 키워드를 Excel 파일로 다운로드"):
        keywords_excel = card_service.export_current_keywords()
        st.download_button(
            label="키워드 파일 다운로드",
            data=keywords_excel,
            file_name=f"keywords_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# 키워드 미리보기
with st.expander(f" 현재 키워드 미리보기"):
    col_preview1, col_preview2 = st.columns(2)
    with col_preview1:
        st.markdown("** 불공제 키워드:**")
        if keyword_summary['no_vat_keywords']:
            st.write(", ".join(keyword_summary['no_vat_keywords']))
            if keyword_summary['no_vat_count'] > 10:
                st.caption(f"... 외 {keyword_summary['no_vat_count'] - 10}개 더")
        else:
            st.write("키워드가 없습니다.")
    
    with col_preview2:
        st.markdown("** 업무유관 예외 키워드:**")
        if keyword_summary['vat_exceptions_keywords']:
            st.write(", ".join(keyword_summary['vat_exceptions_keywords']))
            if keyword_summary['vat_exceptions_count'] > 10:
                st.caption(f"... 외 {keyword_summary['vat_exceptions_count'] - 10}개 더")
        else:
            st.write("키워드가 없습니다.")

st.markdown("---")

# 안내 메시지
st.info(" 법인카드 사용 내역을 업로드하여 공제/불공제 여부를 자동으로 판정합니다.")

# 세션에 저장된 키워드가 있으면 로드
if st.session_state.custom_keywords_loaded and 'no_vat_keywords' in st.session_state:
    card_service.no_vat_keywords = st.session_state.no_vat_keywords
    card_service.vat_exceptions_keywords = st.session_state.vat_exceptions_keywords

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("###  법인카드 파일 업로드")
    
    uploaded_file = st.file_uploader(
        "법인카드 사용 내역 파일을 업로드하세요",
        type=["xlsx", "xls"],
        help="Excel 파일에서 가맹점명 컬럼은 반드시 '거래처'여야 합니다.",
        key="card_file_upload",
        disabled=is_guest()
    )

with col2:
    st.markdown("### ℹ️ 처리 안내")
    st.markdown("""
    **처리 과정:**
    1. 불공제 키워드 매칭
    2. 업무 관련 예외 확인  
    3. 공제 여부 최종 판정
    
    **결과 컬럼:**
    - `no_vat`: 불공제 키워드 매칭 결과
    - `vat_exceptions`: 업무 관련 예외 여부
    - `공제여부`: 최종 판정 (공제/불공제)
    """)

if uploaded_file is not None:
    if st.button("파일 처리", type="primary", use_container_width=True, disabled=is_guest()):
        if check_permission("법인카드 파일 처리"):
            with st.spinner("파일을 처리하는 중입니다..."):
                try:
                    # 파일 처리
                    result_df = card_service.process_card_file(uploaded_file)
                    
                    if result_df is not None:
                        st.success("처리가 완료되었습니다! ")
                        
                        # 결과 통계
                        col1, col2, col3 = st.columns(3)
                        
                        total_count = len(result_df)
                        deductible_count = len(result_df[result_df['공제여부'] == '공제'])
                        non_deductible_count = len(result_df[result_df['공제여부'] == '불공제'])
                        
                        with col1:
                            st.markdown(
                                f'<div class="stats-card">'
                                f'<div class="stat-number">{total_count:,}</div>'
                                f'<div class="stat-label">전체 거래</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        
                        with col2:
                            st.markdown(
                                f'<div class="stats-card">'
                                f'<div class="stat-number">{deductible_count:,}</div>'
                                f'<div class="stat-label">공제 가능</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        
                        with col3:
                            st.markdown(
                                f'<div class="stats-card">'
                                f'<div class="stat-number">{non_deductible_count:,}</div>'
                                f'<div class="stat-label">불공제</div>'
                                f'</div>',
                                unsafe_allow_html=True
                            )
                        
                        st.markdown("---")
                        
                        # 결과 테이블
                        st.markdown("###  처리 결과")
                        
                        # 필터링 옵션
                        col1, col2 = st.columns(2)
                        with col1:
                            deduction_filter = st.selectbox(
                                "공제여부 필터",
                                options=["전체", "공제", "불공제"],
                                index=0
                            )
                        
                        with col2:
                            show_all = st.checkbox("모든 컬럼 보기", value=False)
                        
                        # 데이터 필터링
                        filtered_df = result_df.copy()
                        if deduction_filter != "전체":
                            filtered_df = filtered_df[filtered_df['공제여부'] == deduction_filter]
                        
                        # 컬럼 선택
                        if show_all:
                            display_df = filtered_df
                        else:
                            # 핵심 컬럼만 표시
                            core_columns = ['거래처', 'no_vat', 'vat_exceptions', '공제여부']
                            available_columns = [col for col in core_columns if col in filtered_df.columns]
                            if '거래일시' in filtered_df.columns:
                                available_columns.insert(0, '거래일시')
                            if '금액' in filtered_df.columns:
                                available_columns.append('금액')
                            display_df = filtered_df[available_columns]
                        
                        # 데이터 표시
                        st.dataframe(
                            display_df,
                            use_container_width=True,
                            height=400
                        )
                        
                        # 다운로드 버튼
                        excel_data = card_service.convert_to_excel(result_df)
                        
                        st.download_button(
                            label=" 결과 Excel 다운로드",
                            data=excel_data,
                            file_name=f"card_deduction_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                    
                except Exception as e:
                    st.error(f"파일 처리 중 오류가 발생했습니다: {str(e)}")

else:
    # 파일이 업로드되지 않았을 때 안내
    st.info("법인카드 사용 내역 파일을 업로드하여 공제/불공제 여부를 자동으로 판정하세요.")

# 사용법 안내
with st.expander(" 사용법 및 주의사항"):
    st.markdown("""
    ### 사용법
    1. **키워드 설정**: 기본 키워드를 사용하거나 사용자 정의 키워드 파일을 업로드
    2. **Excel 파일 준비**: 법인카드 사용 내역이 포함된 Excel 파일
    3. **컬럼명 확인**: 가맹점명 컬럼이 '거래처'로 되어 있는지 확인
    4. **파일 업로드**: 위의 파일 업로드 영역에 파일을 드래그하거나 선택
    5. **파일 처리**: '파일 처리' 버튼을 클릭하여 자동 판정 실행
    6. **결과 확인**: 자동으로 공제/불공제 여부가 판정됩니다
    7. **다운로드**: 처리된 결과를 Excel 파일로 다운로드
    
    ### 판정 기준
    - **불공제**: 불공제 키워드에 해당하고 업무 관련 예외에 해당하지 않는 경우
    - **공제**: 불공제 키워드에 해당하지 않거나 업무 관련 예외에 해당하는 경우
    
    ### 키워드 관리
    - **기본 키워드**: 일반적인 불공제 항목들이 미리 설정됨
    - **사용자 키워드**: Excel 파일로 업로드하여 맞춤 설정 가능
    - **키워드 다운로드**: 현재 설정을 Excel로 다운로드하여 수정 후 재업로드 가능
    
    ### 주의사항
    - 키워드 매칭은 부분 문자열 검색을 사용합니다
    - 결과는 참고용이며, 최종 판단은 세무 전문가와 상담하세요
    - 파일 크기가 클 경우 처리 시간이 소요될 수 있습니다
    """)