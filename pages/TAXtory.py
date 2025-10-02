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
from pathlib import Path

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
    withholding_records = service.get_all_records('withholding_tax')
    vat_records = service.get_vat_records()
    all_records = withholding_records + vat_records
    
    if not all_records:
        st.info("등록된 납부 실적이 없습니다.")
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
            # 세목 선택
            tax_types = st.multiselect(
                "세목 선택",
                ["원천세", "부가세"],
                default=["원천세"],
                key="tax_type_filter"
            )
        
        with col_f3:
            st.markdown("&nbsp;")
            refresh_btn = st.button("🔄 새로고침", use_container_width=True)
        
        # 월 선택 (버튼 형태)
        st.markdown("**월 선택**")
        
        # 세션 state에 선택된 월 저장
        if 'selected_months' not in st.session_state:
            st.session_state.selected_months = list(range(1, 13))
        
        # 전체 선택/해제 버튼
        col_all1, col_all2, col_all3 = st.columns([1, 1, 10])
        with col_all1:
            if st.button("전체 선택", key="select_all_months", use_container_width=True):
                st.session_state.selected_months = list(range(1, 13))
                st.rerun()
        with col_all2:
            if st.button("전체 해제", key="deselect_all_months", use_container_width=True):
                st.session_state.selected_months = []
                st.rerun()
        
        # 월 버튼 (전체 + 1~12월)
        cols = st.columns(13)
        
        # 전체 버튼
        with cols[0]:
            all_selected = len(st.session_state.selected_months) == 12
            if st.button(
                "전체",
                key="month_btn_all",
                type="primary" if all_selected else "secondary",
                use_container_width=True
            ):
                if all_selected:
                    st.session_state.selected_months = []
                else:
                    st.session_state.selected_months = list(range(1, 13))
                st.rerun()
        
        # 1~12월 버튼
        for i in range(12):
            month = i + 1
            with cols[i + 1]:
                is_selected = month in st.session_state.selected_months
                
                if st.button(
                    f"{month}월",
                    key=f"month_btn_{month}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True
                ):
                    # 토글 동작
                    if is_selected:
                        st.session_state.selected_months.remove(month)
                    else:
                        st.session_state.selected_months.append(month)
                    st.rerun()

        selected_months = st.session_state.selected_months
        
        st.markdown("---")            
    
        # 필터링된 데이터
        if selected_years and selected_months:
            # 선택된 세목에 따라 레코드 필터링
            filtered_records = []

            if "원천세" in tax_types:
                filtered_records.extend([
                    r for r in withholding_records 
                    if r['year'] in selected_years and r.get('month') in selected_months
                ])

            if "부가세" in tax_types:
                # 부가세는 분기말월로 변환
                for vat_rec in vat_records:
                    if vat_rec['year'] in selected_years:
                        # 분기를 월로 변환 (1Q→3월, 2Q→6월, 3Q→9월, 4Q→12월)
                        quarter_to_month = {1: 3, 2: 6, 3: 9, 4: 12}
                        month = quarter_to_month[vat_rec['quarter']]
                        
                        if month in selected_months:
                            # 부가세 데이터에 month 필드 추가 (표시용)
                            vat_display = vat_rec.copy()
                            vat_display['month'] = month
                            vat_display['tax_type'] = 'vat'
                            vat_display['display_period'] = f"{vat_rec['year']}-{vat_rec['quarter']}Q"
                            filtered_records.append(vat_display)
            
            # 증감 계산
            records_with_changes = service.calculate_changes(filtered_records)
            
            # 통계 카드
            st.markdown("####  주요 지표")
            
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            
            # 원천세와 부가세의 총합 계산
            total_amount = 0
            for r in filtered_records:
                if r.get('tax_type') == 'vat':
                    total_amount += r.get('payment_amount', 0)
                else:
                    total_amount += r.get('total_amount', 0)
            avg_amount = total_amount / len(filtered_records) if filtered_records else 0
            
            # max/min 계산 시에도 동일하게 수정
            def get_amount(r):
                # tax_type이 vat이거나 quarter 필드가 있으면 부가세
                if r.get('tax_type') == 'vat' or 'quarter' in r:
                    return r.get('payment_amount', 0)
                else:
                    return r.get('total_amount', 0)

            max_record = max(filtered_records, key=get_amount) if filtered_records else None
            min_record = min(filtered_records, key=get_amount) if filtered_records else None
            
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
                    amount = get_amount(max_record)
                    st.metric(
                        "최대 납부",
                        f"{amount:,.0f}원",
                        delta=f"{max_record['year']}.{max_record['month']:02d}"
                    )
            
            with col_s4:
                if min_record:
                    amount = get_amount(min_record)
                    st.metric(
                        "최소 납부",
                        f"{amount:,.0f}원",
                        delta=f"{min_record['year']}.{min_record['month']:02d}"
                    )
            
            st.markdown("---")
            
            # 그래프 - 그룹 바 차트
            st.markdown("#### 월별/분기별 납부 추이")

            # 세목별로 데이터 분리
            withholding_data = [r for r in filtered_records if r.get('tax_type') != 'vat']
            vat_data = [r for r in filtered_records if r.get('tax_type') == 'vat']

            # 부가세만 선택한 경우
            if tax_types == ["부가세"] and vat_data:
                df = pd.DataFrame(vat_data)
                df = df.sort_values(['year', 'quarter'])
                
                fig = go.Figure()
                
                # 4개 값 모두 표시 (그룹 바)
                fig.add_trace(go.Bar(
                    x=df['display_period'],
                    y=df['sales_vat'],
                    name='매출부가세',
                    marker=dict(color='#90EE90')
                ))
                fig.add_trace(go.Bar(
                    x=df['display_period'],
                    y=df['purchase_vat'],
                    name='매입부가세',
                    marker=dict(color='#FFB6C1')
                ))
                fig.add_trace(go.Bar(
                    x=df['display_period'],
                    y=df['penalty'],
                    name='가산세/감경',
                    marker=dict(color='#DDA0DD')
                ))
                
                fig.update_layout(
                    barmode='group',  # stack → group
                    height=400,
                    xaxis_title="기간",
                    yaxis_title="금액 (원)",
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

            # 원천세만 선택한 경우
            elif tax_types == ["원천세"] and withholding_data:
                df = pd.DataFrame(withholding_data)
                df['period'] = df.apply(lambda x: f"{x['year']}-{x['month']:02d}", axis=1)
                df = df.sort_values(['year', 'month'])
                
                # 원천세 상세 보기 옵션
                show_detail = st.checkbox("원천세 상세 보기 (원천세/지방소득세/주민세 구분)", value=False, key="wt_detail")
                
                fig = go.Figure()
                
                if show_detail:
                    # 세목별 구분 표시 (그룹 바)
                    fig.add_trace(go.Bar(
                        x=df['period'],
                        y=df['withholding_tax'],
                        name='원천세',
                        marker=dict(color='#F6DA7A')
                    ))
                    fig.add_trace(go.Bar(
                        x=df['period'],
                        y=df['local_income_tax'],
                        name='지방소득세',
                        marker=dict(color='#FFA07A')
                    ))
                    fig.add_trace(go.Bar(
                        x=df['period'],
                        y=df['resident_tax'],
                        name='주민세',
                        marker=dict(color='#87CEEB')
                    ))
                    
                    fig.update_layout(barmode='group')  # 구분할 때는 group
                else:
                    # 전체 합계만 표시
                    fig.add_trace(go.Bar(
                        x=df['period'],
                        y=df['total_amount'],
                        name='원천세 합계',
                        marker=dict(color='#F6DA7A')
                    ))
                    
                    fig.update_layout(barmode='stack')  # 합계만 볼 때는 stack 유지
                
                fig.update_layout(
                    height=400,
                    xaxis_title="기간",
                    yaxis_title="금액 (원)",
                    hovermode='x unified',
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )

            # 원천세 + 부가세 함께 선택한 경우
            elif "원천세" in tax_types and "부가세" in tax_types:
                # 모든 데이터 합치기
                combined_data = []
                
                # 원천세 데이터 (합계만)
                for r in withholding_data:
                    combined_data.append({
                        'period': f"{r['year']}-{r['month']:02d}",
                        'year': r['year'],
                        'month': r['month'],
                        'amount': r['total_amount'],
                        'tax_name': '원천세'
                    })
                
                # 부가세 데이터 (납부세액만)
                for r in vat_data:
                    combined_data.append({
                        'period': f"{r['year']}-{r['month']:02d}",
                        'year': r['year'],
                        'month': r['month'],
                        'amount': r['payment_amount'],
                        'tax_name': '부가세'
                    })
                
                if combined_data:
                    df = pd.DataFrame(combined_data)
                    df = df.sort_values(['year', 'month'])
                    
                    fig = go.Figure()
                    
                    # 세목별로 그룹 바
                    for tax_name, color in [('원천세', '#F6DA7A'), ('부가세', '#98D8C8')]:
                        tax_df = df[df['tax_name'] == tax_name]
                        fig.add_trace(go.Bar(
                            x=tax_df['period'],
                            y=tax_df['amount'],
                            name=tax_name,
                            marker=dict(color=color)
                        ))
                    
                    fig.update_layout(
                        barmode='group',  # stack → group
                        height=400,
                        xaxis_title="기간",
                        yaxis_title="금액 (원)",
                        hovermode='x unified',
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                    )
                else:
                    fig = go.Figure()

            else:
                st.info("세목을 선택해주세요.")
                fig = None

            if fig:
                st.plotly_chart(fig, use_container_width=True)

            st.markdown("---")
            
            # 증감 분석
            st.markdown("####  증감 분석")
            
            # 원천세 증감 분석
            if withholding_data and "원천세" in tax_types:
                st.markdown("**원천세 (월별)**")
                
                wt_records_with_changes = service.calculate_changes(withholding_data)
                display_df = pd.DataFrame(wt_records_with_changes)
                
                # 테이블 생성
                table_df = display_df[['year', 'month', 'withholding_tax', 'local_income_tax', 
                               'resident_tax', 'total_amount']].copy()
                
                # 증감 컬럼 추가
                if 'prev_month_change' in display_df.columns:
                    table_df['prev_month_change'] = display_df['prev_month_change'].apply(
                        lambda x: f"{x:+,.0f}원" if pd.notna(x) else "-"
                    )
                    table_df['prev_month_change_rate'] = display_df['prev_month_change_rate'].apply(
                        lambda x: f"{x:+.1f}%" if pd.notna(x) else "-"
                    )
                
                if 'prev_year_change' in display_df.columns:
                    table_df['prev_year_change'] = display_df['prev_year_change'].apply(
                        lambda x: f"{x:+,.0f}원" if pd.notna(x) else "-"
                    )
                
                # 컬럼명 변경 (동적으로 생성)
                column_names = ['연도', '월', '원천세', '지방소득세', '주민세', '합계']
                
                if 'prev_month_change' in table_df.columns:
                    column_names.append('전월대비')
                if 'prev_month_change_rate' in table_df.columns:
                    column_names.append('전월대비율')
                if 'prev_year_change' in table_df.columns:
                    column_names.append('전년동월대비')
                
                table_df.columns = column_names
                
                # 금액 포맷
                for col in ['원천세', '지방소득세', '주민세', '합계']:
                    if col in table_df.columns:
                        table_df[col] = table_df[col].apply(lambda x: f"{x:,.0f}원")
                
                st.dataframe(table_df, use_container_width=True, hide_index=True)
            
            # 부가세 증감 분석
            if vat_data and "부가세" in tax_types:
                st.markdown("**부가세 (분기별)**")
                
                vat_records_with_changes = service.calculate_vat_changes(vat_data)
                vat_display_df = pd.DataFrame(vat_records_with_changes)
                
                vat_table = vat_display_df[['year', 'quarter', 'sales_vat', 'purchase_vat', 
                                           'penalty', 'payment_amount']].copy()
                
                # 증감 컬럼 추가
                if 'prev_quarter_change' in vat_display_df.columns:
                    vat_table['prev_quarter_change'] = vat_display_df['prev_quarter_change'].apply(
                        lambda x: f"{x:+,.0f}원" if pd.notna(x) else "-"
                    )
                    vat_table['prev_quarter_change_rate'] = vat_display_df['prev_quarter_change_rate'].apply(
                        lambda x: f"{x:+.1f}%" if pd.notna(x) else "-"
                    )
                
                if 'prev_year_change' in vat_display_df.columns:
                    vat_table['prev_year_change'] = vat_display_df['prev_year_change'].apply(
                        lambda x: f"{x:+,.0f}원" if pd.notna(x) else "-"
                    )
                
                # 컬럼명
                column_names = ['연도', '분기', '매출부가세', '매입부가세', '가산세/감경', '납부세액']
                
                if 'prev_quarter_change' in vat_table.columns:
                    column_names.append('전분기대비')
                if 'prev_quarter_change_rate' in vat_table.columns:
                    column_names.append('전분기대비율')
                if 'prev_year_change' in vat_table.columns:
                    column_names.append('전년동분기대비')
                
                vat_table.columns = column_names
                
                # 금액 포맷
                for col in ['매출부가세', '매입부가세', '가산세/감경', '납부세액']:
                    if col in vat_table.columns:
                        vat_table[col] = vat_table[col].apply(lambda x: f"{x:,.0f}원")
                
                # 분기 표시
                vat_table['분기'] = vat_table['분기'].apply(lambda x: f"{x}Q")
                
                st.dataframe(vat_table, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            
            # 납부 금액 표 (편집 가능)
            st.markdown("#### 납부 금액 상세")
            st.caption("⚠️ 수정하려면 값을 변경한 후 저장 버튼을 클릭하고 비밀번호를 입력하세요.")
            
            # 편집 모드 토글
            if 'edit_mode' not in st.session_state:
                st.session_state.edit_mode = False
            
            col_edit1, col_edit2 = st.columns([1, 5])
            with col_edit1:
                if st.button("수정 모드" if not st.session_state.edit_mode else "보기 모드", key="edit_toggle_main"):
                    st.session_state.edit_mode = not st.session_state.edit_mode
                    st.rerun()
            
            if st.session_state.edit_mode:
                # 수정 모드
                edited_data = {}
                
                # 원천세 편집
                if withholding_data and "원천세" in tax_types:
                    st.markdown("**원천세 수정**")
                    for idx, record in enumerate(withholding_data):
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
                                    'total_amount': total,
                                    'tax_type': 'withholding_tax'
                                }
                
                # 부가세 편집
                if vat_data and "부가세" in tax_types:
                    st.markdown("**부가세 수정**")
                    for idx, record in enumerate(vat_data):
                        with st.expander(f"{record['year']}년 {record['quarter']}분기", expanded=False):
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                sv = st.number_input(
                                    "매출부가세",
                                    value=float(record['sales_vat']),
                                    step=1000.0,
                                    format="%.0f",
                                    key=f"edit_sv_{record['id']}"
                                )
                            
                            with col2:
                                pv = st.number_input(
                                    "매입부가세",
                                    value=float(record['purchase_vat']),
                                    step=1000.0,
                                    format="%.0f",
                                    key=f"edit_pv_{record['id']}"
                                )
                            
                            with col3:
                                pen = st.number_input(
                                    "가산세/감경",
                                    value=float(record['penalty']),
                                    step=1000.0,
                                    format="%.0f",
                                    key=f"edit_pen_{record['id']}"
                                )
                            
                            with col4:
                                pay = st.number_input(
                                    "납부세액",
                                    value=float(record['payment_amount']),
                                    step=1000.0,
                                    format="%.0f",
                                    key=f"edit_pay_{record['id']}"
                                )
                            
                            # 변경 여부 확인
                            if (sv != record['sales_vat'] or 
                                pv != record['purchase_vat'] or 
                                pen != record['penalty'] or
                                pay != record['payment_amount']):
                                
                                edited_data[record['id']] = {
                                    'sales_vat': sv,
                                    'purchase_vat': pv,
                                    'penalty': pen,
                                    'payment_amount': pay,
                                    'tax_type': 'vat'
                                }
                
                # 저장 버튼
                if edited_data:
                    st.markdown("---")
                    col_save1, col_save2, col_save3 = st.columns([1, 3, 1])
                    
                    with col_save1:
                        if st.button("변경사항 저장", type="primary", use_container_width=True, key="save_changes_main"):
                            st.session_state.show_password_confirm = True
                    
                    with col_save3:
                        if st.button("취소", use_container_width=True, key="cancel_changes_main"):
                            st.session_state.edit_mode = False
                            st.rerun()
                    
                    # 비밀번호 확인
                    if st.session_state.get('show_password_confirm', False):
                        with st.form(key="password_form_main"):
                            st.warning("변경사항을 저장하려면 비밀번호를 입력하세요.")
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
                                        tax_type = data.pop('tax_type')
                                        if service.update_record_data(record_id, data):
                                            success_count += 1
                                    
                                    if success_count > 0:
                                        st.success(f" {success_count}개의 기록이 저장되었습니다!")
                                        st.session_state.edit_mode = False
                                        st.session_state.show_password_confirm = False
                                        st.rerun()
                                    else:
                                        st.error(" 저장에 실패했습니다.")
                                else:
                                    st.error(" 비밀번호가 일치하지 않습니다.")
                            
                            if cancel_pwd:
                                st.session_state.show_password_confirm = False
                                st.rerun()
            
            else:
                # 보기 모드
                if withholding_data and "원천세" in tax_types:
                    st.markdown("**원천세**")
                    view_df = pd.DataFrame(withholding_data)
                    view_df = view_df[['year', 'month', 'withholding_tax', 'local_income_tax', 
                                'resident_tax', 'total_amount']].copy()
                    
                    view_df.columns = ['연도', '월', '원천세', '지방소득세', '주민세', '합계']
                    
                    for col in ['원천세', '지방소득세', '주민세', '합계']:
                        view_df[col] = view_df[col].apply(lambda x: f"{x:,.0f}원")
                    
                    st.dataframe(view_df, use_container_width=True, hide_index=True)
                
                if vat_data and "부가세" in tax_types:
                    st.markdown("**부가세**")
                    vat_view_df = pd.DataFrame(vat_data)
                    vat_view_df = vat_view_df[['year', 'quarter', 'sales_vat', 'purchase_vat', 
                                               'penalty', 'payment_amount']].copy()
                    
                    vat_view_df.columns = ['연도', '분기', '매출부가세', '매입부가세', '가산세/감경', '납부세액']
                    
                    for col in ['매출부가세', '매입부가세', '가산세/감경', '납부세액']:
                        vat_view_df[col] = vat_view_df[col].apply(lambda x: f"{x:,.0f}원")
                    
                    vat_view_df['분기'] = vat_view_df['분기'].apply(lambda x: f"{x}Q")
                    
                    st.dataframe(vat_view_df, use_container_width=True, hide_index=True)
        
        else:
            st.warning("분석할 연도를 선택해주세요.")

# ==================== 탭 2: 데이터 관리 ====================
with tab2:
    st.markdown("###  신고서 관리")
    st.markdown("---")
    
    # 게스트 권한 체크
    if is_guest():
        st.warning(" 게스트는 데이터 관리 기능을 사용할 수 없습니다.")
        st.info("실제 기능을 사용하려면 세무팀 계정으로 로그인하세요.")
        st.stop()
    
    # 업로드 섹션
    st.markdown("####  신고서 업로드")
    
    # 세목 선택 추가
    selected_tax_type = st.radio(
        "세목 선택",
        ["원천세", "부가세"],
        horizontal=True,
        key="upload_tax_type"
    )

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
                        if selected_tax_type == "원천세":
                            result = service.process_uploaded_files(
                                year=year if not auto_date else 0,
                                month=month if not auto_date else 0,
                                excel_file=excel_file,
                                pdf_file=pdf_file,
                                auto_date=auto_date
                            )
                        else:  # 부가세
                            result = service.process_vat_file(
                                excel_file=excel_file,
                                auto_date=True
                            )
                        
                        if result['success']:
                            if result.get('is_update'):
                                st.info(" 기존 데이터를 새로운 데이터로 업데이트했습니다.")
                            else:
                                st.success(" 파일 업로드가 완료되었습니다!")
                            
                            data = result['data']
                            
                            # 원천세와 부가세 구분해서 표시
                            if selected_tax_type == "원천세":
                                st.json({
                                    "원천세": f"{data.get('withholding_tax', 0):,.0f}원",
                                    "지방소득세": f"{data.get('local_income_tax', 0):,.0f}원",
                                    "주민세": f"{data.get('resident_tax', 0):,.0f}원",
                                    "합계": f"{data.get('total', 0):,.0f}원"
                                })
                            else:  # 부가세
                                st.json({
                                    "매출부가세": f"{data.get('sales_vat', 0):,.0f}원",
                                    "매입부가세": f"{data.get('purchase_vat', 0):,.0f}원",
                                    "가산세/감경": f"{data.get('penalty', 0):,.0f}원",
                                    "납부세액": f"{data.get('payment_amount', 0):,.0f}원"
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
                    
                    # 파일명으로 세목 판단 또는 선택된 세목 사용
                    if selected_tax_type == "부가세" or "분기" in file.name or "Q" in file.name:
                        result = service.process_vat_file(
                            excel_file=excel_file,
                            auto_date=True
                        )
                    else:
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
    
    # 세목별 탭으로 분리
    data_tab1, data_tab2 = st.tabs(["원천세", "부가세"])
    
    # 원천세 데이터
    with data_tab1:
        withholding_records = service.get_all_records('withholding_tax')
        
        if not withholding_records:
            st.info("업로드된 원천세 데이터가 없습니다.")
        else:
            for record in withholding_records[:10]:  # 최근 10개만 표시
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
                        if st.button(" 삭제", key=f"del_wt_{record['id']}", use_container_width=True):
                            st.session_state[f'confirm_delete_{record["id"]}'] = True
                        
                        # 삭제 확인
                        if st.session_state.get(f'confirm_delete_{record["id"]}', False):
                            st.warning(" 정말 삭제하시겠습니까?")
                            
                            with st.form(key=f"delete_form_wt_{record['id']}"):
                                password = st.text_input("비밀번호", type="password")
                                
                                col_d1, col_d2 = st.columns(2)
                                with col_d1:
                                    confirm = st.form_submit_button("삭제", type="primary")
                                with col_d2:
                                    cancel = st.form_submit_button("취소")
                                
                                if confirm:
                                    if verify_current_user_password(password):
                                        if service.delete_record(record['id'], 'withholding_tax'):
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
    
    # 부가세 데이터
    with data_tab2:
        vat_records = service.get_vat_records()
        
        if not vat_records:
            st.info("업로드된 부가세 데이터가 없습니다.")
        else:
            for record in vat_records[:10]:  # 최근 10개만 표시
                with st.expander(
                    f" {record['year']}년 {record['quarter']}분기 - {record['payment_amount']:,.0f}원",
                    expanded=False
                ):
                    col_r1, col_r2 = st.columns([2, 1])
                    
                    with col_r1:
                        st.write(f"**매출부가세**: {record['sales_vat']:,.0f}원")
                        st.write(f"**매입부가세**: {record['purchase_vat']:,.0f}원")
                        st.write(f"**가산세/감경**: {record['penalty']:,.0f}원")
                        st.write(f"**납부세액**: {record['payment_amount']:,.0f}원")
                        st.caption(f"등록: {record.get('created_at', 'N/A')}")
                    
                    with col_r2:
                        # 파일 다운로드
                        if record.get('excel_file'):
                            with open(record['excel_file'], 'rb') as f:
                                st.download_button(
                                    label=" 엑셀 다운로드",
                                    data=f,
                                    file_name=Path(record['excel_file']).name,
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                    key=f"download_vat_{record['id']}"
                                )
                        
                        # 삭제 버튼
                        if st.button(" 삭제", key=f"del_vat_{record['id']}", use_container_width=True):
                            st.session_state[f'confirm_delete_vat_{record["id"]}'] = True
                        
                        # 삭제 확인
                        if st.session_state.get(f'confirm_delete_vat_{record["id"]}', False):
                            st.warning(" 정말 삭제하시겠습니까?")
                            
                            with st.form(key=f"delete_form_vat_{record['id']}"):
                                password = st.text_input("비밀번호", type="password")
                                
                                col_d1, col_d2 = st.columns(2)
                                with col_d1:
                                    confirm = st.form_submit_button("삭제", type="primary")
                                with col_d2:
                                    cancel = st.form_submit_button("취소")
                                
                                if confirm:
                                    if verify_current_user_password(password):
                                        if service.delete_record(record['id'], 'vat'):
                                            st.success("삭제 완료!")
                                            del st.session_state[f'confirm_delete_vat_{record["id"]}']
                                            st.rerun()
                                        else:
                                            st.error("삭제 실패")
                                    else:
                                        st.error("비밀번호가 일치하지 않습니다.")
                                
                                if cancel:
                                    del st.session_state[f'confirm_delete_vat_{record["id"]}']
                                    st.rerun()