"""
Taxtory - 세금 관리 통합 페이지
원천세 신고서 업로드, 분석, 시각화
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import logging

from utils.settings import settings
from components.auth_widget import check_auth
from utils.state import ensure_app_state
from services.tax_record_service import TaxRecordService
from components.file_viewer_modal import show_file_viewer_modal, show_compact_file_viewer
from utils.auth_helper import verify_current_user_password
from utils.auth import is_guest, check_permission
from components.theme import apply_custom_theme
from components.layout import page_header, sidebar_menu

# 로거 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 앱 초기화
ensure_app_state()
st.set_page_config(page_title=f"{settings.APP_NAME} | Taxtory", page_icon="📊", layout="wide")

# 인증 체크
if not check_auth():
    st.warning("로그인이 필요합니다.")
    st.stop()

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

# 사이드바 메뉴
with st.sidebar:
    sidebar_menu()
    
# 서비스 초기화
if 'tax_service' not in st.session_state:
    st.session_state.tax_service = TaxRecordService()

service = st.session_state.tax_service

# 페이지 헤더
st.markdown('<div class="page-header">', unsafe_allow_html=True)
col1, col2 = st.columns([4, 1])
with col1:
    st.title(" Taxtory")
    st.caption("세금 납부 실적 관리 및 분석")
with col2:
    user = st.session_state.get("user", {})
    st.markdown(f'<div class="user-info"><span class="user-name">{user.get("name", "사용자")}</span></div>', 
                unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# 탭 구성 (순서 변경: 납부 실적 → 데이터 관리)
tab1, tab2 = st.tabs([" 납부 실적", " 데이터 관리"])

# ==================== 탭 1: 납부 실적 ====================
with tab1:
    st.markdown("###  납부 실적")
    st.markdown("---")
    
    # 데이터 로드
    all_records = service.get_all_records('withholding_tax')
    
    if not all_records:
        st.info("📌 등록된 납부 실적이 없습니다. '데이터 관리' 탭에서 신고서를 업로드해주세요.")
    else:
        # 필터 옵션
        col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
        
        with col_f1:
            # 연도 필터
            years = sorted(list(set(r['year'] for r in all_records)), reverse=True)
            selected_years = st.multiselect(
                "연도 선택",
                years,
                default=years[:2] if len(years) >= 2 else years,
                key="analysis_years"
            )
        
        with col_f2:
            # 세목 선택 (현재는 원천세만)
            tax_types = st.multiselect(
                "세목 선택",
                ["원천세 전체", "원천세", "지방소득세(특별징수)", "주민세(종업원분)"],
                default=["원천세 전체"],
                key="tax_type_filter"
            )
        
        with col_f3:
            st.markdown("&nbsp;")
            refresh_btn = st.button(" 새로고침", use_container_width=True)
        
        # 필터링된 데이터
        if selected_years:
            filtered_records = [r for r in all_records if r['year'] in selected_years]
            
            # 증감 계산
            records_with_changes = service.calculate_changes(filtered_records)
            
            # 통계 카드
            st.markdown("####  주요 지표")
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            total_amount = sum(r['total_amount'] for r in filtered_records)
            avg_amount = total_amount / len(filtered_records) if filtered_records else 0
            max_record = max(filtered_records, key=lambda x: x['total_amount']) if filtered_records else None
            min_record = min(filtered_records, key=lambda x: x['total_amount']) if filtered_records else None
            
            with col_s1:
                st.metric(
                    "총 납부세액",
                    f"{total_amount:,.0f}원"
                )
            
            with col_s2:
                st.metric(
                    "평균 납부세액",
                    f"{avg_amount:,.0f}원"
                )
            
            with col_s3:
                if max_record:
                    st.metric(
                        "최대 납부",
                        f"{max_record['total_amount']:,.0f}원",
                        delta=f"{max_record['year']}.{max_record['month']:02d}"
                    )
            
            with col_s4:
                if min_record:
                    st.metric(
                        "최소 납부",
                        f"{min_record['total_amount']:,.0f}원",
                        delta=f"{min_record['year']}.{min_record['month']:02d}"
                    )
            
            st.markdown("---")
            
            # 그래프 - 스택 바 차트
            st.markdown("####  월별 납부 추이")
            
            # DataFrame 생성
            df = pd.DataFrame(records_with_changes)
            df['period'] = df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
            df = df.sort_values(['year', 'month'])
            
            # 세목 필터링에 따른 데이터 조정
            if "원천세 전체" in tax_types:
                # 전체 합계만 표시
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['period'],
                    y=df['total_amount'],
                    name='원천세 합계',
                    marker=dict(color='#F6DA7A')
                ))
            else:
                # 세목별 구분 표시 (스택 바)
                fig = go.Figure()
                
                if "원천세" in tax_types:
                    fig.add_trace(go.Bar(
                        x=df['period'],
                        y=df['withholding_tax'],
                        name='원천세',
                        marker=dict(color='#F6DA7A')
                    ))
                
                if "지방소득세(특별징수)" in tax_types:
                    fig.add_trace(go.Bar(
                        x=df['period'],
                        y=df['local_income_tax'],
                        name='지방소득세',
                        marker=dict(color='#FFA07A')
                    ))
                
                if "주민세(종업원분)" in tax_types:
                    fig.add_trace(go.Bar(
                        x=df['period'],
                        y=df['resident_tax'],
                        name='주민세',
                        marker=dict(color='#87CEEB')
                    ))
            
            fig.update_layout(
                barmode='stack',
                height=400,
                xaxis_title="기간",
                yaxis_title="금액 (원)",
                hovermode='x unified',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            
            # 증감 분석
            st.markdown("####  증감 분석")
            
            # 테이블
            display_df = df[['year', 'month', 'withholding_tax', 'local_income_tax', 
                           'resident_tax', 'total_amount']].copy()
            
            # 증감 컬럼 추가
            if 'prev_month_change' in df.columns:
                display_df['prev_month_change'] = df['prev_month_change'].apply(
                    lambda x: f"{x:+,.0f}원" if pd.notna(x) else "-"
                )
                display_df['prev_month_change_rate'] = df['prev_month_change_rate'].apply(
                    lambda x: f"{x:+.1f}%" if pd.notna(x) else "-"
                )
            
            if 'prev_year_change' in df.columns:
                display_df['prev_year_change'] = df['prev_year_change'].apply(
                    lambda x: f"{x:+,.0f}원" if pd.notna(x) else "-"
                )
            
            # 컬럼명 변경 (동적으로 생성)
            column_names = ['연도', '월', '원천세', '지방소득세', '주민세', '합계']
            
            if 'prev_month_change' in display_df.columns:
                column_names.append('전월대비')
            if 'prev_month_change_rate' in display_df.columns:
                column_names.append('전월대비율')
            if 'prev_year_change' in display_df.columns:
                column_names.append('전년동월대비')
            
            display_df.columns = column_names
            
            # 금액 포맷
            for col in ['원천세', '지방소득세', '주민세', '합계']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"{x:,.0f}원")
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # 납부 금액 표 (편집 가능)
            st.markdown("####  납부 금액 상세")
            st.caption("⚠️ 수정하려면 값을 변경한 후 저장 버튼을 클릭하고 비밀번호를 입력하세요.")
            
            # 편집 모드 토글
            if 'edit_mode' not in st.session_state:
                st.session_state.edit_mode = False
            
            col_edit1, col_edit2 = st.columns([1, 5])
            with col_edit1:
                if st.button(" 수정 모드" if not st.session_state.edit_mode else "👁️ 보기 모드"):
                    st.session_state.edit_mode = not st.session_state.edit_mode
                    st.rerun()
            
            if st.session_state.edit_mode:
                # 수정 모드
                edited_data = {}
                
                for idx, record in enumerate(records_with_changes):
                    with st.expander(f"{record['year']}년 {record['month']}월", expanded=False):
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            wt = st.number_input(
                                "원천세",
                                value=float(record['withholding_tax']),
                                step=1000.0,
                                format="%.0f",
                                key=f"edit_wt_{record['id']}"
                            )
                        
                        with col2:
                            lit = st.number_input(
                                "지방소득세",
                                value=float(record['local_income_tax']),
                                step=1000.0,
                                format="%.0f",
                                key=f"edit_lit_{record['id']}"
                            )
                        
                        with col3:
                            rt = st.number_input(
                                "주민세",
                                value=float(record['resident_tax']),
                                step=1000.0,
                                format="%.0f",
                                key=f"edit_rt_{record['id']}"
                            )
                        
                        with col4:
                            total = wt + lit + rt
                            st.metric("합계", f"{total:,.0f}원")
                        
                        # 변경 여부 확인
                        if (wt != record['withholding_tax'] or 
                            lit != record['local_income_tax'] or 
                            rt != record['resident_tax']):
                            
                            edited_data[record['id']] = {
                                'withholding_tax': wt,
                                'local_income_tax': lit,
                                'resident_tax': rt,
                                'total_amount': total
                            }
                
                # 저장 버튼
                if edited_data:
                    st.markdown("---")
                    col_save1, col_save2, col_save3 = st.columns([1, 3, 1])
                    
                    with col_save1:
                        if st.button(" 변경사항 저장", type="primary", use_container_width=True):
                            st.session_state.show_password_confirm = True
                    
                    with col_save3:
                        if st.button("취소", use_container_width=True):
                            st.session_state.edit_mode = False
                            st.rerun()
                    
                    # 비밀번호 확인
                    if st.session_state.get('show_password_confirm', False):
                        with st.form(key="password_form"):
                            st.warning(" 변경사항을 저장하려면 비밀번호를 입력하세요.")
                            password = st.text_input("비밀번호", type="password")
                            
                            col_p1, col_p2 = st.columns(2)
                            with col_p1:
                                submit_pwd = st.form_submit_button("확인", type="primary")
                            with col_p2:
                                cancel_pwd = st.form_submit_button("취소")
                            
                            if submit_pwd:
                                if verify_current_user_password(password):
                                    # 저장 처리
                                    success_count = 0
                                    for record_id, data in edited_data.items():
                                        if service.update_record_data(record_id, data):
                                            success_count += 1
                                    
                                    if success_count > 0:
                                        st.success(f"✅ {success_count}개의 기록이 저장되었습니다!")
                                        st.session_state.edit_mode = False
                                        st.session_state.show_password_confirm = False
                                        st.rerun()
                                    else:
                                        st.error("❌ 저장에 실패했습니다.")
                                else:
                                    st.error("❌ 비밀번호가 일치하지 않습니다.")
                            
                            if cancel_pwd:
                                st.session_state.show_password_confirm = False
                                st.rerun()
            
            else:
                # 보기 모드
                view_df = df[['year', 'month', 'withholding_tax', 'local_income_tax', 
                            'resident_tax', 'total_amount']].copy()
                
                view_df.columns = ['연도', '월', '원천세', '지방소득세', '주민세', '합계']
                
                for col in ['원천세', '지방소득세', '주민세', '합계']:
                    view_df[col] = view_df[col].apply(lambda x: f"{x:,.0f}원")
                
                st.dataframe(view_df, use_container_width=True, hide_index=True)
        
        else:
            st.warning("분석할 연도를 선택해주세요.")

# ==================== 탭 2: 데이터 관리 ====================
with tab2:
    st.markdown("###  원천세 신고서 관리")
    st.markdown("---")
    
    # 게스트 권한 체크
    if is_guest():
        st.warning(" 게스트는 데이터 관리 기능을 사용할 수 없습니다.")
        st.info("실제 기능을 사용하려면 세무팀 계정으로 로그인하세요.")
        st.stop()
    
    # 업로드 섹션
    st.markdown("####  신고서 업로드")
    
    upload_mode = st.radio(
        "업로드 방식",
        ["개별 업로드", "일괄 업로드"],
        horizontal=True,
        key="upload_mode"
    )
    
    if upload_mode == "개별 업로드":
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown("**파일 선택**")
            auto_date = st.checkbox("파일명에서 날짜 자동 추출", value=True, key="auto_date_single")
            
            if not auto_date:
                year = st.selectbox(
                    "연도",
                    range(datetime.now().year, datetime.now().year - 5, -1),
                    key="upload_year_single"
                )
                month = st.selectbox(
                    "월",
                    range(1, 13),
                    key="upload_month_single"
                )
        
        with col2:
            col_excel, col_pdf = st.columns(2)
            
            with col_excel:
                st.markdown("** 엑셀 파일**")
                excel_file = st.file_uploader(
                    "엑셀 업로드",
                    type=['xlsx', 'xls'],
                    key="excel_uploader_single",
                    label_visibility="collapsed"
                )
                if excel_file:
                    st.success(f" {excel_file.name}")
            
            with col_pdf:
                st.markdown("** PDF 파일**")
                pdf_file = st.file_uploader(
                    "PDF 업로드",
                    type=['pdf'],
                    key="pdf_uploader_single",
                    label_visibility="collapsed"
                )
                if pdf_file:
                    st.success(f" {pdf_file.name}")
            
            if excel_file or pdf_file:
                if st.button(" 업로드", type="primary", use_container_width=True):
                    with st.spinner("파일을 처리하는 중..."):
                        result = service.process_uploaded_files(
                            year=year if not auto_date else 0,
                            month=month if not auto_date else 0,
                            excel_file=excel_file,
                            pdf_file=pdf_file,
                            auto_date=auto_date
                        )
                        
                        if result['success']:
                            if result.get('is_update'):
                                st.info(" 기존 데이터를 새로운 데이터로 업데이트했습니다.")
                            else:
                                st.success(" 파일 업로드가 완료되었습니다!")
                            
                            data = result['data']
                            st.json({
                                "원천세": f"{data['withholding_tax']:,.0f}원",
                                "지방소득세": f"{data['local_income_tax']:,.0f}원",
                                "주민세": f"{data['resident_tax']:,.0f}원",
                                "합계": f"{data['total']:,.0f}원"
                            })
                        else:
                            st.error(f" 업로드 실패: {result.get('error')}")
    
    else:
        # 일괄 업로드
        st.markdown("**여러 파일 선택**")
        uploaded_files = st.file_uploader(
            "엑셀/PDF 파일",
            type=['xlsx', 'xls', 'pdf'],
            accept_multiple_files=True,
            key="batch_uploader"
        )
        
        if uploaded_files:
            st.info(f" {len(uploaded_files)}개 파일 선택됨")
            
            if st.button(" 일괄 업로드", type="primary", use_container_width=True):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                success_count = 0
                fail_count = 0
                
                for idx, file in enumerate(uploaded_files):
                    status_text.text(f"처리 중... {idx+1}/{len(uploaded_files)}")
                    
                    file_ext = file.name.split('.')[-1].lower()
                    excel_file = file if file_ext in ['xlsx', 'xls'] else None
                    pdf_file = file if file_ext == 'pdf' else None
                    
                    result = service.process_uploaded_files(
                        year=0,
                        month=0,
                        excel_file=excel_file,
                        pdf_file=pdf_file,
                        auto_date=True
                    )
                    
                    if result['success']:
                        success_count += 1
                    else:
                        fail_count += 1
                    
                    progress_bar.progress((idx + 1) / len(uploaded_files))
                
                status_text.empty()
                progress_bar.empty()
                
                if success_count > 0:
                    st.success(f" {success_count}개 파일 업로드 완료!")
                if fail_count > 0:
                    st.warning(f" {fail_count}개 파일 업로드 실패")
    
    st.markdown("---")
    
    # 업로드된 데이터 목록
    st.markdown("####  업로드된 데이터")
    
    all_records = service.get_all_records('withholding_tax')
    
    if not all_records:
        st.info("업로드된 데이터가 없습니다.")
    else:
        for record in all_records[:10]:  # 최근 10개만 표시
            with st.expander(
                f" {record['year']}년 {record['month']}월 - {record['total_amount']:,.0f}원",
                expanded=False
            ):
                col_r1, col_r2 = st.columns([2, 1])
                
                with col_r1:
                    st.write(f"**원천세**: {record['withholding_tax']:,.0f}원")
                    st.write(f"**지방소득세**: {record['local_income_tax']:,.0f}원")
                    st.write(f"**주민세**: {record['resident_tax']:,.0f}원")
                    st.caption(f"등록: {record.get('created_at', 'N/A')}")
                
                with col_r2:
                    # 파일 다운로드
                    show_compact_file_viewer(record)
                    
                    # 삭제 버튼
                    if st.button(" 삭제", key=f"del_{record['id']}", use_container_width=True):
                        st.session_state[f'confirm_delete_{record["id"]}'] = True
                    
                    # 삭제 확인
                    if st.session_state.get(f'confirm_delete_{record["id"]}', False):
                        st.warning(" 정말 삭제하시겠습니까?")
                        
                        with st.form(key=f"delete_form_{record['id']}"):
                            password = st.text_input("비밀번호", type="password")
                            
                            col_d1, col_d2 = st.columns(2)
                            with col_d1:
                                confirm = st.form_submit_button("삭제", type="primary")
                            with col_d2:
                                cancel = st.form_submit_button("취소")
                            
                            if confirm:
                                if verify_current_user_password(password):
                                    if service.delete_record(record['id']):
                                        st.success("삭제 완료!")
                                        del st.session_state[f'confirm_delete_{record["id"]}']
                                        st.rerun()
                                    else:
                                        st.error("삭제 실패")
                                else:
                                    st.error("비밀번호가 일치하지 않습니다.")
                            
                            if cancel:
                                del st.session_state[f'confirm_delete_{record["id"]}']
                                st.rerun()