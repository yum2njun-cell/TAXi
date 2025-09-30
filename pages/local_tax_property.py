"""
TAXi 지방세 관리 시스템 - 재산세 페이지
pages/40_지방세_재산세.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import copy
import io
import base64

# 프로젝트 내부 모듈 임포트
from services.property_tax_service import PropertyTaxService
from components.layout import page_header, sidebar_menu
from utils.settings import settings
from components.theme import apply_custom_theme

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 지방세 관리", 
    page_icon="", 
    layout="wide"
)

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

# 스타일 로드 후에
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

# 서비스 인스턴스 생성
@st.cache_resource
def get_property_tax_service():
    """재산세 서비스 인스턴스 반환 (캐시됨)"""
    return PropertyTaxService()

def initialize_property_tax_data():
    """재산세 데이터 초기화"""
    service = get_property_tax_service()
    service.initialize_default_data()

def create_page_header():
    """페이지 헤더 생성"""
    st.markdown("""
    <div class="page-header">
        <div class="header-content">
            <div class="header-left">
                <span class="page-icon"></span>
                <h1 class="page-title">재산세 관리</h1>
            </div>
            <div class="user-info">
                <span class="user-name"></span>
                <span class="user-role"></span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ===========================================
# 자산 마스터 관리 섹션
# ===========================================

def render_master_management():
    """자산 마스터 관리 섹션"""
    st.markdown("### 자산 마스터 관리")
    
    master_tab1, master_tab2, master_tab3 = st.tabs([
        "자산 등록", "자산 목록", "엑셀 업로드"
    ])
    
    with master_tab1:
        render_asset_registration()
    
    with master_tab2:
        render_asset_list()
    
    with master_tab3:
        render_excel_upload()

def get_taxation_types_for_asset_type(asset_type):
    """자산유형별 과세유형 반환"""
    service = get_property_tax_service()
    return service.get_taxation_types_for_asset_type(asset_type)

def render_asset_registration():
    """자산 등록 폼"""
    st.markdown("#### 새 자산 등록")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**기본정보**")
        asset_id = st.text_input("자산ID", placeholder="ASSET_XXX", key="reg_asset_id")
        asset_name = st.text_input("자산명", placeholder="예: 본사 부지", key="reg_asset_name")
        asset_type = st.selectbox("자산유형", ["토지", "건축물", "주택"], key="reg_asset_type")
        detail_type = st.text_input("상세유형", placeholder="예: 일반토지, 업무시설", key="reg_detail_type")
        group_id = st.selectbox("그룹ID", ["GROUP_A", "GROUP_B", "GROUP_C"], key="reg_group_id")
        
        available_taxation_types = get_taxation_types_for_asset_type(asset_type)
        
        if asset_type == "토지":
            taxation_type = st.selectbox(
                "과세유형", 
                available_taxation_types,
                key="reg_taxation_type",
                help="토지는 과세유형에 따라 다른 세율이 적용됩니다."
            )
        else:
            taxation_type = "기타"
            st.selectbox(
                "과세유형", 
                ["기타"],
                index=0,
                disabled=True,
                key="reg_taxation_type_auto",
                help="건축물과 주택은 기타로 자동 설정됩니다."
            )
        
        urban_area_applicable = st.selectbox(
            "재산세 도시지역분",
            ["Y", "N"],
            index=0,
            key="reg_urban_area",
            help="도시지역에 소재하는 재산에 대해 재산세 도시지역분이 부과됩니다."
        )
    
    with col2:
        st.markdown("**위치정보**")
        sido = st.selectbox("시/도", [
            "서울특별시", "부산광역시", "대구광역시", "인천광역시", "광주광역시", 
            "대전광역시", "울산광역시", "세종특별자치시", "경기도", "강원도", 
            "충청북도", "충청남도", "전라북도", "전라남도", "경상북도", "경상남도", "제주특별자치도"
        ], key="reg_sido")
        sigungu = st.text_input("시/군/구", placeholder="예: 강남구", key="reg_sigungu")
        detail_address = st.text_input("상세주소", placeholder="예: 테헤란로 123번지", key="reg_address")
        area = st.number_input("면적(㎡)", min_value=0.0, format="%.2f", key="reg_area")
    
    st.markdown("**연도별 금액정보**")
    
    col3, col4 = st.columns(2)
    
    with col3:
        service = get_property_tax_service()
        available_years = service.get_all_available_years()
        if available_years:
            apply_year = st.selectbox("적용연도", available_years, key="reg_year")
        else:
            st.warning("등록된 연도가 없습니다.")
            apply_year = datetime.now().year
        official_price = st.number_input("공시지가", min_value=0, format="%d", key="reg_official_price")
        standard_price = st.number_input("시가표준액", min_value=0, format="%d", key="reg_standard_price")
        
        building_price = 0
        if asset_type == "주택":
            building_price = st.number_input("건물시가", min_value=0, format="%d", 
                                           help="주택의 경우 건물시가를 별도로 입력하세요", 
                                           key="reg_building_price")
    
    with col4:
        reduction_rate = st.number_input("감면율(%)", min_value=0.0, max_value=100.0, format="%.2f", key="reg_reduction")
        surcharge_rate = st.number_input("중과세율(%)", min_value=0.0, max_value=100.0, format="%.2f", key="reg_surcharge")
        valid_until = st.date_input("유효기간", value=datetime(apply_year, 12, 31), key="reg_valid")
    
    # 등록 버튼
    if st.button("자산 등록", type="primary", key="reg_submit"):
        if asset_id and asset_name and asset_type:
            service = get_property_tax_service()
            
            year_data = {
                "적용연도": apply_year,
                "공시지가": official_price,
                "시가표준액": standard_price,
                "감면율": reduction_rate,
                "중과세율": surcharge_rate,
                "유효기간": valid_until.strftime("%Y-%m-%d")
            }
            
            if asset_type == "주택":
                year_data["건물시가"] = building_price
            
            new_asset = {
                "자산ID": asset_id,
                "자산명": asset_name,
                "자산유형": asset_type,
                "상세유형": detail_type,
                "과세유형": taxation_type,
                "재산세_도시지역분": urban_area_applicable,
                "그룹ID": group_id,
                "시도": sido,
                "시군구": sigungu,
                "상세주소": detail_address,
                "면적": area,
                "연도별데이터": {str(apply_year): year_data}
            }
            
            success, message = service.create_asset(new_asset)
            
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
        else:
            st.error("필수 필드를 모두 입력해주세요.")

@st.dialog("자산 수정", width="large")
def render_asset_modification_modal(asset_id):
    """자산 수정 모달"""
    service = get_property_tax_service()
    selected_asset = service.get_asset(asset_id)
    
    if not selected_asset:
        st.error("자산을 찾을 수 없습니다.")
        return
    
    st.markdown(f"### {selected_asset['자산명']} ({asset_id})")
    
    available_years = list(selected_asset["연도별데이터"].keys())
    selected_year = st.selectbox("수정할 연도 선택", available_years, key="mod_modal_year_select")
    
    if selected_year:
        year_data = selected_asset["연도별데이터"][selected_year]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**기본정보 수정**")
            new_asset_name = st.text_input("자산명", value=selected_asset["자산명"], key="mod_modal_asset_name")
            new_asset_type = st.selectbox("자산유형", ["토지", "건축물", "주택"], 
                                        index=["토지", "건축물", "주택"].index(selected_asset["자산유형"]),
                                        key="mod_modal_asset_type")
            new_detail_type = st.text_input("상세유형", value=selected_asset["상세유형"], key="mod_modal_detail_type")
            new_group_id = st.selectbox("그룹ID", ["GROUP_A", "GROUP_B", "GROUP_C"],
                                      index=["GROUP_A", "GROUP_B", "GROUP_C"].index(selected_asset["그룹ID"]),
                                      key="mod_modal_group_id")
            
            available_taxation_types = get_taxation_types_for_asset_type(new_asset_type)
            current_taxation_type = selected_asset.get("과세유형", "기타")
            
            if new_asset_type == "토지":
                if current_taxation_type not in available_taxation_types:
                    current_index = 0
                else:
                    current_index = available_taxation_types.index(current_taxation_type)
                
                new_taxation_type = st.selectbox("과세유형", available_taxation_types, index=current_index, key="mod_modal_taxation_type")
            else:
                new_taxation_type = "기타"
                st.selectbox("과세유형", ["기타"], index=0, disabled=True, key="mod_modal_taxation_type_auto")
            
            current_urban_area = selected_asset.get("재산세_도시지역분", "N")
            new_urban_area = st.selectbox("재산세 도시지역분", ["Y", "N"], 
                                        index=0 if current_urban_area == "Y" else 1, key="mod_modal_urban_area")
        
        with col2:
            st.markdown("**연도별 데이터 수정**")
            new_official_price = st.number_input("공시지가", value=year_data["공시지가"], format="%d", key="mod_modal_official_price")
            new_standard_price = st.number_input("시가표준액", value=year_data["시가표준액"], format="%d", key="mod_modal_standard_price")
            
            new_building_price = 0
            if new_asset_type == "주택":
                current_building_price = year_data.get("건물시가", 0)
                new_building_price = st.number_input("건물시가", value=current_building_price, format="%d", key="mod_modal_building_price")
            
            new_reduction_rate = st.number_input("감면율(%)", value=float(year_data["감면율"]), format="%.2f", key="mod_modal_reduction")
            new_surcharge_rate = st.number_input("중과세율(%)", value=float(year_data["중과세율"]), format="%.2f", key="mod_modal_surcharge")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("💾 저장", type="primary", key="mod_modal_submit", use_container_width=True):
                updated_year_data = {
                    "적용연도": int(selected_year),
                    "공시지가": new_official_price,
                    "시가표준액": new_standard_price,
                    "감면율": new_reduction_rate,
                    "중과세율": new_surcharge_rate,
                    "유효기간": year_data["유효기간"]
                }
                
                if new_asset_type == "주택":
                    updated_year_data["건물시가"] = new_building_price
                
                updated_asset = {
                    "자산ID": asset_id,
                    "자산명": new_asset_name,
                    "자산유형": new_asset_type,
                    "상세유형": new_detail_type,
                    "과세유형": new_taxation_type,
                    "재산세_도시지역분": new_urban_area,
                    "그룹ID": new_group_id,
                    "시도": selected_asset["시도"],
                    "시군구": selected_asset["시군구"],
                    "상세주소": selected_asset["상세주소"],
                    "면적": selected_asset["면적"],
                    "연도별데이터": {**selected_asset["연도별데이터"], selected_year: updated_year_data}
                }
                
                success, message = service.update_asset(asset_id, updated_asset)
                
                if success:
                    st.success(message)
                    # ✅ selectbox 초기화를 위해 세션 상태 제거
                    if 'quick_asset_select' in st.session_state:
                        del st.session_state.quick_asset_select
                    st.rerun()
                else:
                    st.error(message)

        with col2:
            if st.button(" 취소", key="mod_modal_cancel", use_container_width=True):
                # ✅ selectbox 초기화
                if 'quick_asset_select' in st.session_state:
                    del st.session_state.quick_asset_select
                st.rerun()

def render_asset_list():
    """자산 목록 표시"""
    st.markdown("#### 등록된 자산 목록")
    
    service = get_property_tax_service()
    all_assets = service.get_all_assets()
    
    if not all_assets:
        st.info("등록된 자산이 없습니다.")
        return
    
    st.markdown("** 개별 자산 빠른 선택**")
    asset_options = ["선택하세요..."] + [f"{asset['자산명']} ({asset_id})" for asset_id, asset in all_assets.items()]

    col_select, col_button = st.columns([3, 1])

    with col_select:
        selected_quick = st.selectbox(
            "자산 선택",
            asset_options,
            key="quick_asset_select",
            label_visibility="collapsed"
        )

    with col_button:
        # 선택된 자산이 있을 때만 버튼 활성화
        if st.button("수정", key="quick_edit_btn", disabled=(selected_quick == "선택하세요..."), use_container_width=True):
            if selected_quick != "선택하세요...":
                asset_id = selected_quick.split("(")[-1].rstrip(")")
                render_asset_modification_modal(asset_id)

    st.markdown("---")

    # 필터 옵션
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # 자산에 실제 등록된 연도만 필터에 표시
        year_options = set()
        for asset in all_assets.values():
            year_options.update(asset.get("연도별데이터", {}).keys())
        year_options = ["전체"] + sorted([str(y) for y in year_options], reverse=True)
        
        year_filter = st.selectbox("연도 필터", year_options, key="list_year_filter")
    
    with col2:
        type_filter = st.selectbox("자산유형 필터", ["전체", "토지", "건축물", "주택"], key="list_type_filter")
    
    with col3:
        taxation_filter = st.selectbox("과세유형 필터", ["전체", "종합합산", "별도합산", "분리과세", "기타"], key="list_taxation_filter")
    
    # 필터 적용
    filters = {}
    if year_filter != "전체":
        filters["year"] = int(year_filter)
    if type_filter != "전체":
        filters["asset_type"] = type_filter
    if taxation_filter != "전체":
        filters["taxation_type"] = taxation_filter
    
    filtered_assets = service.filter_assets(filters)
    
    if filtered_assets:
        asset_list = []
        
        for asset in filtered_assets:
            asset_id = asset.get("asset_id") or asset["자산ID"]
            
            for year, year_data in asset["연도별데이터"].items():
                if year_filter != "전체" and year != year_filter:
                    continue
                
                row = {
                    "선택": False,
                    "자산ID": asset_id,
                    "자산명": asset["자산명"],
                    "자산유형": asset["자산유형"],
                    "과세유형": asset.get("과세유형", "기타"),
                    "도시지역분": asset.get("재산세_도시지역분", "N"),
                    "그룹ID": asset["그룹ID"],
                    "위치": f"{asset['시도']} {asset['시군구']}",
                    "면적(㎡)": f"{asset['면적']:,.2f}",
                    "연도": year,
                    "시가표준액": f"{year_data['시가표준액']:,}원"
                }
                
                if asset["자산유형"] == "주택" and "건물시가" in year_data:
                    row["건물시가"] = f"{year_data['건물시가']:,}원"
                
                asset_list.append(row)
        
        df = pd.DataFrame(asset_list)

        # ✅ 체크박스 추가를 위해 data_editor 사용
        edited_df = st.data_editor(
            df,
            column_config={
                "선택": st.column_config.CheckboxColumn(
                    "선택",
                    help="수정/삭제할 자산을 선택하세요",
                    default=False,
                )
            },
            disabled=[col for col in df.columns if col != "선택"],
            hide_index=True,
            use_container_width=True,
            key="asset_list_editor"
        )

        # 선택된 자산 처리
        selected_assets = edited_df[edited_df["선택"] == True]

        if not selected_assets.empty:
            selected_asset_ids = selected_assets["자산ID"].unique().tolist()
            st.info(f"선택된 자산: {len(selected_asset_ids)}개")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(" 선택 자산 수정", key="bulk_edit_btn", type="secondary"):
                    if len(selected_asset_ids) == 1:
                        render_asset_modification_modal(selected_asset_ids[0])
                    else:
                        st.warning("수정은 한 번에 하나의 자산만 가능합니다.")
            
            with col2:
                if st.button(" 선택 자산 삭제", key="bulk_delete_btn", type="secondary"):
                    st.session_state.assets_to_delete = selected_asset_ids
                    st.session_state.delete_confirm_step = 1
                    st.rerun()
        
        # 통계 정보
        statistics = service.get_asset_statistics()
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("총 자산 수", f"{statistics['총_자산수']}개")
        with col2:
            st.metric("총 시가표준액", f"{statistics['총_시가표준액']:,}원")
        with col3:
            st.metric("평균 자산가액", f"{statistics['평균_자산가액']:,}원")
    else:
        st.info("필터 조건에 맞는 자산이 없습니다.")

def render_excel_upload():
    """엑셀 업로드 기능"""
    st.markdown("#### 엑셀 파일로 대량 등록")
    
    st.info("""
    **엑셀 파일 형식 안내:**
    - 시트명: 'assets'
    - 필수 컬럼: 자산ID, 자산명, 자산유형, 과세유형, 재산세_도시지역분, 그룹ID, 시도, 시군구, 상세주소, 면적, 연도, 시가표준액
    - 선택 컬럼: 공시지가, 건물시가(주택만), 감면율, 중과세율
    - 과세유형: 토지(종합합산/별도합산/분리과세), 건축물/주택(기타)
    - 재산세_도시지역분: Y(적용) 또는 N(미적용)
    """)
    
    uploaded_file = st.file_uploader("엑셀 파일 선택", type=['xlsx', 'xls'], key="excel_upload")
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file, sheet_name='assets')
            
            st.markdown("**업로드된 데이터 미리보기:**")
            st.dataframe(df.head(), use_container_width=True)
            
            service = get_property_tax_service()
            
            # 데이터 유효성 검증
            is_valid, errors, corrected_df = service.validate_excel_data(df)
            
            if errors:
                st.markdown("**데이터 검증 결과:**")
                if any("보정" in error for error in errors):
                    st.warning("일부 데이터가 자동 보정되었습니다:")
                    for error in errors:
                        if "보정" in error:
                            st.write(f"• {error}")
                
                error_messages = [error for error in errors if "보정" not in error]
                if error_messages:
                    st.error("오류가 발견되었습니다:")
                    for error in error_messages[:10]:  # 최대 10개만 표시
                        st.write(f"• {error}")
                    if len(error_messages) > 10:
                        st.write(f"... 외 {len(error_messages)-10}건 더")
            
            if is_valid or st.checkbox("오류가 있어도 강제로 진행", key="force_upload"):
                if st.button("일괄 등록 실행", type="primary", key="excel_submit"):
                    with st.spinner("엑셀 데이터 처리 중..."):
                        success, message, counts = service.import_assets_from_excel(corrected_df)
                        
                        if success:
                            st.success(message)
                            
                            # 결과 통계 표시
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("신규 등록", f"{counts['success']}건")
                            with col2:
                                st.metric("업데이트", f"{counts['update']}건")
                            with col3:
                                st.metric("실패", f"{counts['error']}건")
                            
                            if counts['success'] > 0 or counts['update'] > 0:
                                st.rerun()
                        else:
                            st.error(message)
            else:
                st.error("오류를 수정한 후 다시 업로드해주세요.")
                        
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")
            st.info("엑셀 파일의 시트명이 'assets'인지 확인해주세요.")

# ===========================================
# 세율 관리 섹션
# ===========================================

def render_tax_rate_management():
    """세율 관리 섹션"""
    # 연도 관리 버튼 추가
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 세율 관리")
    
    with col2:
        year_count = len(available_years)
        button_text = f" 연도관리 ({year_count})"
        
        if st.button(button_text, key="open_year_management_modal"):
            render_year_management_modal()
    
    rate_tab1, rate_tab2, rate_tab3, rate_tab4, rate_tab5 = st.tabs([
        "재산세율", "도시지역분", "지방교육세율", "지역자원시설세율", "공정시장가액비율"
    ])
    
    with rate_tab1:
        render_property_tax_rates()
    
    with rate_tab2:
        render_urban_area_tax_rates()
    
    with rate_tab3:
        render_local_education_tax_rates()
    
    with rate_tab4:
        render_regional_resource_tax_rates()
    
    with rate_tab5:
        render_fair_market_ratios()

def render_property_tax_rates():
    """재산세 누진구간 관리 (편집 가능)"""
    st.markdown("#### 재산세 누진구간 관리")
    
    col1, col2 = st.columns(2)
    
    service = get_property_tax_service()
    available_years = service.get_all_available_years()

    if not available_years:
        st.warning("등록된 연도가 없습니다. 연도 관리에서 연도를 추가해주세요.")
        return

    with col1:
        rate_year = st.selectbox("연도 선택", available_years, key="rate_year_select")
    
    with col2:
        asset_type = st.selectbox("자산유형", ["토지", "건축물", "주택"], key="rate_asset_type_select")
    
    service = get_property_tax_service()
    
    # 편집 모드 토글
    edit_mode = st.toggle(f"편집 모드", key=f"edit_mode_{rate_year}_{asset_type}")
    
    if asset_type == "토지":
        st.markdown("#### 토지 과세유형별 세율 관리")
        
        taxation_types = ["종합합산", "별도합산", "분리과세"]
        selected_taxation_type = st.selectbox("과세유형 선택", taxation_types, key="rate_taxation_type_select")
        
        current_rates = service.get_property_tax_rates(rate_year, asset_type, selected_taxation_type)
        
        if current_rates:
            st.markdown(f"**{rate_year}년 토지 {selected_taxation_type} 재산세 누진구간**")
            
            if not edit_mode:
                # 조회 모드
                rate_data = []
                for i, rate_info in enumerate(current_rates):
                    # ✅ service의 메서드 사용
                    upper_text = service.convert_infinity_for_display(rate_info["상한"])
                    
                    rate_data.append({
                        "구간": f"구간 {i+1}",
                        "과세표준 하한": f"{rate_info['하한']:,}원",
                        "과세표준 상한": f"{upper_text}원",
                        "기본세액": f"{rate_info['기본세액']:,}원",
                        "세율": f"{rate_info['세율']}%"
                    })
                
                df = pd.DataFrame(rate_data)
                st.dataframe(df, use_container_width=True)
            
            else:
                # 편집 모드: 입력 필드들
                st.markdown("**세율 편집**")
                updated_rates = []
                
                for i, rate_info in enumerate(current_rates):
                    st.markdown(f"**구간 {i+1}**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        lower = st.number_input("과세표준 하한", value=rate_info["하한"], 
                                              format="%d", key=f"edit_lower_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
                    
                    with col2:
                        if rate_info["상한"] == float('inf'):
                            st.text_input("과세표준 상한", value="무제한", disabled=True, 
                                        key=f"edit_upper_display_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
                            upper = float('inf')
                        else:
                            upper = st.number_input("과세표준 상한", value=rate_info["상한"], 
                                                  format="%d", key=f"edit_upper_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
                    
                    with col3:
                        base_tax = st.number_input("기본세액", value=rate_info["기본세액"], 
                                                 format="%d", key=f"edit_base_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
                    
                    with col4:
                        tax_rate = st.number_input("세율(%)", value=rate_info["세율"], 
                                                 format="%.3f", key=f"edit_rate_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
                    
                    updated_rates.append({
                        "하한": lower,
                        "상한": upper,
                        "기본세액": base_tax,
                        "세율": tax_rate
                    })
                
                # 저장 버튼
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("구간 추가", key=f"add_bracket_{rate_year}_{asset_type}_{selected_taxation_type}"):
                        new_rate = {
                            "하한": 0,
                            "상한": 100000000,
                            "기본세액": 0,
                            "세율": 0.1
                        }
                        current_rates.append(new_rate)
                        st.rerun()
                
                with col2:
                    if st.button("마지막 구간 삭제", key=f"del_bracket_{rate_year}_{asset_type}_{selected_taxation_type}") and len(current_rates) > 1:
                        current_rates.pop()
                        st.rerun()
                
                with col3:
                    if st.button("세율 저장", type="primary", key=f"save_rates_{rate_year}_{asset_type}_{selected_taxation_type}"):
                        success, message = service.update_property_tax_rates(rate_year, asset_type, selected_taxation_type, updated_rates)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.warning(f"{rate_year}년 {asset_type} {selected_taxation_type} 세율 정보가 없습니다.")
    
    else:
        st.markdown(f"#### {asset_type} 세율 관리")
        
        current_rates = service.get_property_tax_rates(rate_year, asset_type, "기타")
        
        if current_rates:
            st.markdown(f"**{rate_year}년 {asset_type} 재산세 누진구간**")
            
            if not edit_mode:
                # 조회 모드
                rate_data = []
                for i, rate_info in enumerate(current_rates):
                    upper_text = service.convert_infinity_for_display(rate_info["상한"])
                    rate_data.append({
                        "구간": f"구간 {i+1}",
                        "과세표준 하한": f"{rate_info['하한']:,}원",
                        "과세표준 상한": f"{upper_text}원",
                        "기본세액": f"{rate_info['기본세액']:,}원",
                        "세율": f"{rate_info['세율']}%"
                    })
                
                df = pd.DataFrame(rate_data)
                st.dataframe(df, use_container_width=True)
            
            else:
                # 편집 모드
                st.markdown("**세율 편집**")
                updated_rates = []
                
                for i, rate_info in enumerate(current_rates):
                    st.markdown(f"**구간 {i+1}**")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        lower = st.number_input("과세표준 하한", value=rate_info["하한"], 
                                              format="%d", key=f"edit_lower_{rate_year}_{asset_type}_기타_{i}")
                    
                    with col2:
                        if rate_info["상한"] == float('inf'):
                            st.text_input("과세표준 상한", value="무제한", disabled=True, 
                                        key=f"edit_upper_display_{rate_year}_{asset_type}_기타_{i}")
                            upper = float('inf')
                        else:
                            upper = st.number_input("과세표준 상한", value=rate_info["상한"], 
                                                  format="%d", key=f"edit_upper_{rate_year}_{asset_type}_기타_{i}")
                    
                    with col3:
                        base_tax = st.number_input("기본세액", value=rate_info["기본세액"], 
                                                 format="%d", key=f"edit_base_{rate_year}_{asset_type}_기타_{i}")
                    
                    with col4:
                        tax_rate = st.number_input("세율(%)", value=rate_info["세율"], 
                                                 format="%.3f", key=f"edit_rate_{rate_year}_{asset_type}_기타_{i}")
                    
                    updated_rates.append({
                        "하한": lower,
                        "상한": upper,
                        "기본세액": base_tax,
                        "세율": tax_rate
                    })
                
                # 저장 버튼
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    if st.button("구간 추가", key=f"add_bracket_{rate_year}_{asset_type}_기타"):
                        new_rate = {
                            "하한": 0,
                            "상한": 100000000,
                            "기본세액": 0,
                            "세율": 0.1
                        }
                        current_rates.append(new_rate)
                        st.rerun()
                
                with col2:
                    if st.button("마지막 구간 삭제", key=f"del_bracket_{rate_year}_{asset_type}_기타") and len(current_rates) > 1:
                        current_rates.pop()
                        st.rerun()
                
                with col3:
                    if st.button("세율 저장", type="primary", key=f"save_rates_{rate_year}_{asset_type}_기타"):
                        success, message = service.update_property_tax_rates(rate_year, asset_type, "기타", updated_rates)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        else:
            st.warning(f"{rate_year}년 {asset_type} 세율 정보가 없습니다.")

def render_urban_area_tax_rates():
    """재산세 도시지역분 세율 관리"""
    st.markdown("#### 재산세 도시지역분 세율 관리")
    
    service = get_property_tax_service()
    
    available_years = service.get_all_available_years()

    if not available_years:
        st.warning("등록된 연도가 없습니다.")
        return

    urban_year = st.selectbox("연도 선택", available_years, key="urban_year_select")
    
    current_ratio = service.get_urban_area_tax_rate(urban_year)
    
    st.info("재산세 도시지역분은 재산세 산출세액의 0.14% (단일세율)로 계산됩니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**현재 세율 정보:**")
        st.markdown(f"- 재산세 도시지역분 세율: {current_ratio}%")
        st.markdown("- 적용 기준: 재산세 산출세액")
        st.markdown("- 적용 조건: 도시지역 소재 재산만")
    
    with col2:
        st.markdown("**계산 예시:**")
        example_property_tax = 1000000
        example_urban_tax = example_property_tax * current_ratio / 100
        
        st.markdown(f"- 재산세 산출세액: {example_property_tax:,}원")
        st.markdown(f"- 도시지역분 세율: {current_ratio}%")
        st.markdown(f"- 재산세 도시지역분: {example_urban_tax:,.0f}원")

def render_local_education_tax_rates():
    """지방교육세율 관리"""
    st.markdown("#### 지방교육세율 관리")
    
    service = get_property_tax_service()
    
    available_years = service.get_all_available_years()

    if not available_years:
        st.warning("등록된 연도가 없습니다.")
        return

    edu_year = st.selectbox("연도 선택", available_years, key="edu_year_select")
    
    current_ratio = st.session_state.property_tax_rates["지방교육세"][str(edu_year)]["비율"]
    
    st.info("지방교육세는 재산세의 일정 비율로 계산됩니다.")
    
    st.markdown(f"**{edu_year}년 지방교육세 비율: {current_ratio*100:.1f}%**")
    st.markdown("(재산세 대비)")

def render_regional_resource_tax_rates():
    """지역자원시설세율 관리 (편집 가능)"""
    st.markdown("#### 지역자원시설세율 관리")
    
    service = get_property_tax_service()
    available_years = service.get_all_available_years()

    if not available_years:
        st.warning("등록된 연도가 없습니다.")
        return

    resource_year = st.selectbox("연도 선택", available_years, key="resource_year_select")
    
    # 편집 모드 토글
    edit_mode = st.toggle(f"편집 모드", key=f"resource_edit_mode_{resource_year}")
    
    service = get_property_tax_service()
    current_rates = st.session_state.property_tax_rates["지역자원시설세"][str(resource_year)]
    
    st.markdown(f"**{resource_year}년 지역자원시설세 누진구간**")
    
    if not edit_mode:
        # 조회 모드: 기존과 동일
        rate_data = []
        for i, rate_info in enumerate(current_rates):
            upper_text = service.convert_infinity_for_display(rate_info["상한"])
            rate_data.append({
                "구간": f"구간 {i+1}",
                "과세표준 하한": f"{rate_info['하한']:,}원",
                "과세표준 상한": f"{upper_text}원",
                "기본세액": f"{rate_info['기본세액']:,}원",
                "세율": f"{rate_info['세율']}%"
            })
        
        df = pd.DataFrame(rate_data)
        st.dataframe(df, use_container_width=True)
    
    else:
        # 편집 모드: 입력 필드들
        st.markdown("**세율 편집**")
        updated_rates = []
        
        for i, rate_info in enumerate(current_rates):
            st.markdown(f"**구간 {i+1}**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                lower = st.number_input("과세표준 하한", value=rate_info["하한"], 
                                      format="%d", key=f"resource_edit_lower_{resource_year}_{i}")
            
            with col2:
                if rate_info["상한"] == float('inf'):
                    st.text_input("과세표준 상한", value="무제한", disabled=True, 
                                key=f"resource_edit_upper_display_{resource_year}_{i}")
                    upper = float('inf')
                else:
                    upper = st.number_input("과세표준 상한", value=rate_info["상한"], 
                                          format="%d", key=f"resource_edit_upper_{resource_year}_{i}")
            
            with col3:
                base_tax = st.number_input("기본세액", value=rate_info["기본세액"], 
                                         format="%d", key=f"resource_edit_base_{resource_year}_{i}")
            
            with col4:
                tax_rate = st.number_input("세율(%)", value=rate_info["세율"], 
                                         format="%.4f", key=f"resource_edit_rate_{resource_year}_{i}")
            
            updated_rates.append({
                "하한": lower,
                "상한": upper,
                "기본세액": base_tax,
                "세율": tax_rate
            })
        
        # 저장 버튼
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("구간 추가", key=f"resource_add_bracket_{resource_year}"):
                new_rate = {
                    "하한": 0,
                    "상한": 100000000,
                    "기본세액": 0,
                    "세율": 0.01
                }
                st.session_state.property_tax_rates["지역자원시설세"][str(resource_year)].append(new_rate)
                st.rerun()
        
        with col2:
            if st.button("마지막 구간 삭제", key=f"resource_del_bracket_{resource_year}") and len(current_rates) > 1:
                st.session_state.property_tax_rates["지역자원시설세"][str(resource_year)].pop()
                st.rerun()
        
        with col3:
            if st.button("세율 저장", type="primary", key=f"resource_save_rates_{resource_year}"):
                st.session_state.property_tax_rates["지역자원시설세"][str(resource_year)] = updated_rates
                st.success(f"{resource_year}년 지역자원시설세율이 성공적으로 업데이트되었습니다!")
                st.rerun()

def render_fair_market_ratios():
    """공정시장가액비율 관리 (편집 가능)"""
    st.markdown("#### 공정시장가액비율 관리")
    
    service = get_property_tax_service()
    
    st.info("공정시장가액비율은 연도별 × 자산유형별로 설정됩니다.")
    
    # 편집 모드 토글
    edit_mode = st.toggle("편집 모드", key="ratio_edit_mode")
    
    years = ["2024", "2023", "2022", "2021"]
    asset_types = ["토지", "건축물", "주택"]
    
    st.markdown("**현재 공정시장가액비율 매트릭스**")
    
    if not edit_mode:
        # 조회 모드: 기존과 동일
        ratio_data = []
        for year in years:
            row = {"연도": year}
            for asset_type in asset_types:
                ratio = service.get_fair_market_ratio(int(year), asset_type)
                row[asset_type] = f"{ratio}%"
            ratio_data.append(row)
        
        df = pd.DataFrame(ratio_data)
        st.dataframe(df, use_container_width=True)
    
    else:
        # 편집 모드: 입력 필드들로 매트릭스 구성
        st.markdown("**비율 편집**")
        
        updated_ratios = copy.deepcopy(st.session_state.fair_market_ratios)
        
        # 헤더
        col_header = st.columns([1] + [1]*len(asset_types))
        col_header[0].markdown("**연도**")
        for i, asset_type in enumerate(asset_types):
            col_header[i+1].markdown(f"**{asset_type}**")
        
        # 각 연도별 입력 필드
        for year in years:
            cols = st.columns([1] + [1]*len(asset_types))
            cols[0].markdown(f"**{year}**")
            
            for i, asset_type in enumerate(asset_types):
                current_ratio = service.get_fair_market_ratio(int(year), asset_type)
                new_ratio = cols[i+1].number_input(
                    f"{year}_{asset_type}",
                    value=current_ratio,
                    min_value=0.0,
                    max_value=100.0,
                    format="%.1f",
                    label_visibility="collapsed",
                    key=f"edit_ratio_{year}_{asset_type}"
                )
                updated_ratios[year][asset_type] = new_ratio
        
        st.markdown("---")
        
        # 저장 버튼 및 연도 추가
        col1, col2, col3 = st.columns(3)
        
        with col1:
            new_year = st.number_input("새 연도 추가", min_value=2020, max_value=2030, value=2025, key="new_year_input")
        
        with col2:
            if st.button("연도 추가", key="add_year_btn"):
                if str(new_year) not in st.session_state.fair_market_ratios:
                    st.session_state.fair_market_ratios[str(new_year)] = {
                        "토지": 70.0,
                        "건축물": 70.0,
                        "주택": 60.0
                    }
                    st.success(f"{new_year}년이 추가되었습니다!")
                    st.rerun()
                else:
                    st.warning(f"{new_year}년은 이미 존재합니다.")
        
        with col3:
            if st.button("비율 저장", type="primary", key="save_ratios_btn"):
                success, message = service.update_fair_market_ratios(updated_ratios)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

# ===========================================
# 통합 세액 계산 및 업무흐름 관리
# ===========================================

def render_integrated_calculation_workflow():
    """세액 계산 및 업무흐름 통합 관리"""
    st.markdown("### 세액 계산 및 업무흐름")
    
    calc_tab1, calc_tab2, calc_tab3, calc_tab4, calc_tab5 = st.tabs([
        "Transaction", "Compare", "Finalize", "Summary", "Report"
    ])
    
    with calc_tab1:
        render_transaction()
    
    with calc_tab2:
        render_compare()
    
    with calc_tab3:
        render_finalize()
    
    with calc_tab4:
        render_summary()
    
    with calc_tab5:
        render_report()

def render_transaction():
    """Transaction - 그룹별 일괄 계산"""
    st.markdown("#### 그룹별 일괄 계산")
    
    service = get_property_tax_service()
    all_assets = service.get_all_assets()
    
    if not all_assets:
        st.info("등록된 자산이 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        available_groups = ["전체"] + service.get_available_groups()
        selected_group = st.selectbox("계산할 그룹 선택", available_groups, key="trans_group_select")
    
    with col2:
        available_years = service.get_available_years()
        calc_year = st.selectbox("계산 연도", available_years, key="trans_year_select")
    
    if st.button("그룹 일괄 계산", type="primary", key="trans_calc_btn"):
        with st.spinner(f"{selected_group} 그룹 {calc_year}년 계산 중..."):
            calc_result = service.calculate_property_tax_for_group(selected_group, calc_year)
            
            if "오류" in calc_result:
                st.error(calc_result["오류"])
                return
            
            calc_key = f"{selected_group}_{calc_year}"
            service.save_calculation_result(calc_key, calc_result)
            
            st.success(f"{selected_group} 그룹 {calc_year}년 세액 계산이 완료되었습니다!")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("계산된 자산 수", f"{len(calc_result['자산별계산'])}개")
            with col2:
                st.metric("그룹 총세액", f"{calc_result['그룹총세액']:,.0f}원")
            with col3:
                st.metric("계산 완료 시간", calc_result["계산일시"])
    
    # 기존 계산 결과 조회
    st.markdown("---")
    st.markdown("#### 계산 결과 조회")
    
    all_calculations = service.get_all_calculation_results()
    
    if all_calculations:
        calc_options = list(all_calculations.keys())
        selected_calc = st.selectbox("조회할 계산 결과", calc_options, key="trans_result_select")
        
        if selected_calc:
            calc_data = all_calculations[selected_calc]
            
            st.markdown(f"**{calc_data['그룹ID']} 그룹 {calc_data['연도']}년 계산 결과**")
            
            if calc_data['자산별계산']:
                result_data = []
                for asset_id, asset_calc in calc_data['자산별계산'].items():
                    result_data.append({
                        "자산ID": asset_id,
                        "자산명": asset_calc["자산명"],
                        "자산유형": asset_calc["자산유형"],
                        "과세유형": asset_calc["과세유형"],
                        "기준금액": f"{asset_calc['기준금액']:,}원",
                        "과세표준": f"{asset_calc['과세표준']:,.0f}원",
                        "재산세": f"{asset_calc['재산세']:,.0f}원",
                        "재산세_도시지역분": f"{asset_calc['재산세_도시지역분']:,.0f}원",
                        "지방교육세": f"{asset_calc['지방교육세']:,.0f}원",
                        "지역자원시설세": f"{asset_calc['지역자원시설세']:,.0f}원",
                        "총세액": f"{asset_calc['총세액']:,.0f}원"
                    })
                
                df = pd.DataFrame(result_data)
                st.dataframe(df, use_container_width=True)
                
                # 엑셀 다운로드
                st.download_button(
                    label="계산 결과 엑셀 다운로드",
                    data=df.to_csv(index=False).encode('utf-8-sig'),
                    file_name=f"재산세_계산결과_{selected_calc}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv"
                )
    else:
        st.info("계산 결과가 없습니다.")

def render_compare():
    """Compare - 계산값 vs 고지서값 비교"""
    st.markdown("#### 계산값 vs 고지서값 비교")
    
    service = get_property_tax_service()
    all_calculations = service.get_all_calculation_results()
    
    if not all_calculations:
        st.info("먼저 Transaction에서 세액을 계산해주세요.")
        return
    
    calc_options = list(all_calculations.keys())
    selected_calc = st.selectbox("비교할 계산 결과 선택", calc_options, key="comp_calc_select")
    
    if selected_calc:
        calc_data = all_calculations[selected_calc]
        
        st.markdown(f"**{calc_data['그룹ID']} 그룹 {calc_data['연도']}년 비교 분석**")
        
        comparison_data = {}
        
        # 고지서 값 입력
        st.markdown("#### 고지서 세액 입력")
        
        for asset_id, asset_calc in calc_data["자산별계산"].items():
            st.markdown(f"**{asset_calc['자산명']} ({asset_id})**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                notice_property_tax = st.number_input(
                    "고지서 재산세", 
                    min_value=0, 
                    format="%d",
                    key=f"notice_prop_{asset_id}"
                )
            
            with col2:
                notice_urban_tax = st.number_input(
                    "고지서 재산세 도시지역분", 
                    min_value=0, 
                    format="%d",
                    key=f"notice_urban_{asset_id}"
                )
            
            with col3:
                notice_edu_tax = st.number_input(
                    "고지서 지방교육세", 
                    min_value=0, 
                    format="%d",
                    key=f"notice_edu_{asset_id}"
                )
            
            with col4:
                notice_resource_tax = st.number_input(
                    "고지서 지역자원시설세", 
                    min_value=0, 
                    format="%d",
                    key=f"notice_resource_{asset_id}"
                )
            
            comparison_data[asset_id] = {
                "자산명": asset_calc["자산명"],
                "과세유형": asset_calc["과세유형"],
                "계산_재산세": asset_calc["재산세"],
                "고지_재산세": notice_property_tax,
                "계산_재산세_도시지역분": asset_calc["재산세_도시지역분"],
                "고지_재산세_도시지역분": notice_urban_tax,
                "계산_지방교육세": asset_calc["지방교육세"],
                "고지_지방교육세": notice_edu_tax,
                "계산_지역자원시설세": asset_calc["지역자원시설세"],
                "고지_지역자원시설세": notice_resource_tax,
                "계산_총세액": asset_calc["총세액"],
                "고지_총세액": notice_property_tax + notice_urban_tax + notice_edu_tax + notice_resource_tax
            }
        
        if st.button("비교 분석 실행", type="primary", key="comp_analyze_btn"):
            comparison_list = []
            
            for asset_id, comp_data in comparison_data.items():
                prop_diff = comp_data["고지_재산세"] - comp_data["계산_재산세"]
                urban_diff = comp_data["고지_재산세_도시지역분"] - comp_data["계산_재산세_도시지역분"]
                edu_diff = comp_data["고지_지방교육세"] - comp_data["계산_지방교육세"]
                resource_diff = comp_data["고지_지역자원시설세"] - comp_data["계산_지역자원시설세"]
                total_diff = comp_data["고지_총세액"] - comp_data["계산_총세액"]
                
                comparison_list.append({
                    "자산ID": asset_id,
                    "자산명": comp_data["자산명"],
                    "과세유형": comp_data["과세유형"],
                    "계산_재산세": f"{comp_data['계산_재산세']:,.0f}원",
                    "고지_재산세": f"{comp_data['고지_재산세']:,}원",
                    "재산세_차이": f"{prop_diff:+,}원",
                    "계산_총세액": f"{comp_data['계산_총세액']:,.0f}원",
                    "고지_총세액": f"{comp_data['고지_총세액']:,}원",
                    "총세액_차이": f"{total_diff:+,}원"
                })
            
            service.save_comparison_result(selected_calc, comparison_data)
            
            st.markdown("#### 비교 결과")
            df = pd.DataFrame(comparison_list)
            st.dataframe(df, use_container_width=True)
            
            total_calc = sum(comp_data["계산_총세액"] for comp_data in comparison_data.values())
            total_notice = sum(comp_data["고지_총세액"] for comp_data in comparison_data.values())
            total_difference = total_notice - total_calc
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("계산 총세액", f"{total_calc:,.0f}원")
            with col2:
                st.metric("고지 총세액", f"{total_notice:,}원")
            with col3:
                st.metric("전체 차이", f"{total_difference:+,}원")

def render_finalize():
    """Finalize - 최종 세액 선택"""
    st.markdown("#### 자산별 최종값 선택")
    
    service = get_property_tax_service()
    all_comparisons = st.session_state.property_comparisons
    
    if not all_comparisons:
        st.info("먼저 Compare에서 비교 분석을 수행해주세요.")
        return
    
    comp_options = list(all_comparisons.keys())
    selected_comp = st.selectbox("최종 확정할 비교 결과 선택", comp_options, key="final_comp_select")
    
    if selected_comp:
        comp_data = all_comparisons[selected_comp]
        
        st.markdown("#### 자산별 최종 세액 선택")
        
        final_selections = {}
        
        for asset_id, asset_data in comp_data.items():
            st.markdown(f"**{asset_data['자산명']} ({asset_id}) - {asset_data['과세유형']}**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("**계산값**")
                st.write(f"재산세: {asset_data['계산_재산세']:,.0f}원")
                st.write(f"재산세 도시지역분: {asset_data['계산_재산세_도시지역분']:,.0f}원")
                st.write(f"지방교육세: {asset_data['계산_지방교육세']:,.0f}원")
                st.write(f"지역자원시설세: {asset_data['계산_지역자원시설세']:,.0f}원")
                st.write(f"**총세액: {asset_data['계산_총세액']:,.0f}원**")
            
            with col2:
                st.markdown("**고지서값**")
                st.write(f"재산세: {asset_data['고지_재산세']:,}원")
                st.write(f"재산세 도시지역분: {asset_data['고지_재산세_도시지역분']:,}원")
                st.write(f"지방교육세: {asset_data['고지_지방교육세']:,}원")
                st.write(f"지역자원시설세: {asset_data['고지_지역자원시설세']:,}원")
                st.write(f"**총세액: {asset_data['고지_총세액']:,}원**")
            
            with col3:
                selection = st.radio(
                    "최종 선택",
                    ["계산값 채택", "고지서값 채택"],
                    key=f"final_{asset_id}"
                )
                
                if selection == "계산값 채택":
                    final_selections[asset_id] = {
                        "선택": "계산값",
                        "과세유형": asset_data["과세유형"],
                        "재산세": asset_data['계산_재산세'],
                        "재산세_도시지역분": asset_data['계산_재산세_도시지역분'],
                        "지방교육세": asset_data['계산_지방교육세'],
                        "지역자원시설세": asset_data['계산_지역자원시설세'],
                        "총세액": asset_data['계산_총세액']
                    }
                else:
                    final_selections[asset_id] = {
                        "선택": "고지서값",
                        "과세유형": asset_data["과세유형"],
                        "재산세": asset_data['고지_재산세'],
                        "재산세_도시지역분": asset_data['고지_재산세_도시지역분'],
                        "지방교육세": asset_data['고지_지방교육세'],
                        "지역자원시설세": asset_data['고지_지역자원시설세'],
                        "총세액": asset_data['고지_총세액']
                    }
            
            st.markdown("---")
        
        if st.button("최종 확정", type="primary", key="final_confirm_btn"):
            service.save_finalization_result(selected_comp, final_selections)
            st.success("최종 세액이 확정되었습니다!")

def render_summary():
    """Summary - 통계 및 현황"""
    st.markdown("#### 통계 분석 및 현황")
    
    service = get_property_tax_service()
    statistics = service.get_asset_statistics()
    
    if statistics['총_자산수'] == 0:
        st.info("등록된 자산이 없습니다.")
        return
    
    # 기본 통계
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 자산 수", f"{statistics['총_자산수']}개")
    
    with col2:
        st.metric("총 시가표준액", f"{statistics['총_시가표준액']:,}원")
    
    with col3:
        st.metric("평균 자산가액", f"{statistics['평균_자산가액']:,}원")
    
    with col4:
        urban_count = statistics['도시지역분별_분포'].get('Y', 0)
        st.metric("도시지역분 적용", f"{urban_count}개")
    
    # 분포 차트
    col1, col2 = st.columns(2)
    
    with col1:
        if statistics['자산유형별_분포']:
            st.markdown("#### 자산유형별 분포")
            type_df = pd.DataFrame(list(statistics['자산유형별_분포'].items()), columns=['자산유형', '개수'])
            st.bar_chart(type_df.set_index('자산유형'))
    
    with col2:
        if statistics['과세유형별_분포']:
            st.markdown("#### 과세유형별 분포")
            taxation_df = pd.DataFrame(list(statistics['과세유형별_분포'].items()), columns=['과세유형', '개수'])
            st.bar_chart(taxation_df.set_index('과세유형'))
    
    # 계산 결과 요약
    all_calculations = service.get_all_calculation_results()
    
    if all_calculations:
        st.markdown("#### 계산 결과 요약")
        
        calc_summary = []
        for calc_key, calc_data in all_calculations.items():
            calc_summary.append({
                "그룹": calc_data['그룹ID'],
                "연도": calc_data['연도'],
                "자산수": len(calc_data['자산별계산']),
                "총세액": f"{calc_data['그룹총세액']:,.0f}원",
                "계산일시": calc_data['계산일시']
            })
        
        if calc_summary:
            df = pd.DataFrame(calc_summary)
            st.dataframe(df, use_container_width=True)

def render_report():
    """Report - 보고서 생성"""
    st.markdown("#### 보고서 생성")
    
    service = get_property_tax_service()
    all_finalizations = st.session_state.property_finalizations
    
    if not all_finalizations:
        st.info("먼저 Finalize에서 최종 세액을 확정해주세요.")
        return
    
    final_options = list(all_finalizations.keys())
    selected_final = st.selectbox("보고서 생성할 확정 결과 선택", final_options, key="report_final_select")
    
    if selected_final:
        report_type = st.selectbox("보고서 유형", [
            "세액 확정 보고서",
            "자산별 상세 보고서",
            "그룹별 요약 보고서"
        ], key="report_type_select")
        
        if st.button("보고서 생성", type="primary", key="report_generate_btn"):
            final_data = all_finalizations[selected_final]
            
            if report_type == "세액 확정 보고서":
                render_tax_confirmation_report(selected_final, final_data)
            elif report_type == "자산별 상세 보고서":
                render_asset_detail_report(selected_final, final_data)
            else:
                st.info(f"{report_type} 기능은 추후 개발 예정입니다.")

def render_tax_confirmation_report(calc_key, final_data):
    """세액 확정 보고서"""
    st.markdown("### 세액 확정 보고서")
    
    parts = calc_key.rsplit("_", 1)
    if len(parts) == 2:
        group_id, year = parts
    else:
        group_id, year = "Unknown", "Unknown"
    
    st.markdown(f"**대상 그룹:** {group_id}")
    st.markdown(f"**기준 연도:** {year}년")
    st.markdown(f"**작성 일시:** {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}")
    
    st.markdown("### 확정 세액 상세")
    
    report_list = []
    total_property_tax = 0
    total_urban_tax = 0
    total_edu_tax = 0
    total_resource_tax = 0
    total_tax = 0
    
    for asset_id, asset_final in final_data.items():
        service = get_property_tax_service()
        asset_info = service.get_asset(asset_id) or {}
        asset_name = asset_info.get("자산명", "Unknown")
        
        report_list.append({
            "자산ID": asset_id,
            "자산명": asset_name,
            "과세유형": asset_final["과세유형"],
            "선택기준": asset_final["선택"],
            "재산세": f"{asset_final['재산세']:,.0f}원",
            "재산세_도시지역분": f"{asset_final['재산세_도시지역분']:,.0f}원",
            "지방교육세": f"{asset_final['지방교육세']:,.0f}원",
            "지역자원시설세": f"{asset_final['지역자원시설세']:,.0f}원",
            "총세액": f"{asset_final['총세액']:,.0f}원"
        })
        
        total_property_tax += asset_final['재산세']
        total_urban_tax += asset_final['재산세_도시지역분']
        total_edu_tax += asset_final['지방교육세']
        total_resource_tax += asset_final['지역자원시설세']
        total_tax += asset_final['총세액']
    
    df = pd.DataFrame(report_list)
    st.dataframe(df, use_container_width=True)
    
    st.markdown("### 세액 총계")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("재산세 합계", f"{total_property_tax:,.0f}원")
    with col2:
        st.metric("재산세 도시지역분", f"{total_urban_tax:,.0f}원")
    with col3:
        st.metric("지방교육세 합계", f"{total_edu_tax:,.0f}원")
    with col4:
        st.metric("지역자원시설세 합계", f"{total_resource_tax:,.0f}원")
    with col5:
        st.metric("총 세액", f"{total_tax:,.0f}원")

def render_asset_detail_report(calc_key, final_data):
    """자산별 상세 보고서"""
    st.markdown("### 자산별 상세 보고서")
    
    service = get_property_tax_service()
    
    for asset_id, asset_final in final_data.items():
        asset_info = service.get_asset(asset_id) or {}
        
        with st.expander(f"{asset_info.get('자산명', 'Unknown')} ({asset_id}) 상세 정보"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**자산 기본정보**")
                st.write(f"자산유형: {asset_info.get('자산유형', 'Unknown')}")
                st.write(f"과세유형: {asset_final.get('과세유형', 'Unknown')}")
                st.write(f"소재지: {asset_info.get('시도', '')} {asset_info.get('시군구', '')}")
                st.write(f"면적: {asset_info.get('면적', 0):,.2f}㎡")
                st.write(f"그룹ID: {asset_info.get('그룹ID', 'Unknown')}")
            
            with col2:
                st.markdown("**확정 세액**")
                st.write(f"재산세: {asset_final['재산세']:,.0f}원")
                st.write(f"재산세 도시지역분: {asset_final['재산세_도시지역분']:,.0f}원")
                st.write(f"지방교육세: {asset_final['지방교육세']:,.0f}원")
                st.write(f"지역자원시설세: {asset_final['지역자원시설세']:,.0f}원")
                st.write(f"**총세액: {asset_final['총세액']:,.0f}원**")
                st.write(f"선택기준: {asset_final['선택']}")

@st.dialog("연도 관리")
def render_year_management_modal():
    """연도 관리 모달"""
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    st.markdown("####  연도 관리")
    
    if available_years:
        year_range = f"{min(available_years)} ~ {max(available_years)}"
        st.info(f"**관리 중인 연도:** {year_range} ({len(available_years)}개)")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("** 연도 추가**")
        new_year = st.number_input(
            "추가할 연도", 
            min_value=2020, 
            max_value=datetime.now().year + 10, 
            value=datetime.now().year + 1,
            key="modal_new_year_input"
        )
        
        if available_years:
            base_years = ["기본값"] + [str(year) for year in available_years]
            base_year_option = st.selectbox("복사할 기준 연도", base_years, key="modal_base_year_select")
            base_year = int(base_year_option) if base_year_option != "기본값" else None
        else:
            base_year = None
        
        if st.button("➕ 추가", key="modal_add_year_btn", type="primary", use_container_width=True):
            success, message = service.add_tax_year(new_year, base_year)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.markdown("** 연도 삭제**")
        if available_years:
            delete_year = st.selectbox("삭제할 연도", available_years, key="modal_delete_year_select")
            
            dependencies = service.check_year_dependencies(delete_year)
            if dependencies:
                st.warning(f"⚠️ {len(dependencies)}개 항목에서 사용 중")
            else:
                st.success(" 삭제 가능")
            
            if st.button(" 삭제", key="modal_delete_year_btn", use_container_width=True):
                if dependencies:
                    st.error("사용 중인 연도는 삭제할 수 없습니다.")
                else:
                    success, message = service.dele

def main():
    """메인 함수"""
    # 페이지 헤더
    page_header("재산세 관리", "")
    
    # 지방세 탭 헤더 추가
    from components.local_tax_tabs import render_local_tax_tabs
    render_local_tax_tabs("재산세")
    
    # 사이드바 메뉴
    with st.sidebar:
        sidebar_menu()
    
    # 데이터 초기화
    initialize_property_tax_data()
    
    # 상단: 자산 마스터 관리(좌) + 세율 관리(우)
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_master_management()
    
    with col2:
        render_tax_rate_management()
    
    # 하단: 세액 계산 및 업무흐름 (통합)
    render_integrated_calculation_workflow()
    
    # 페이지 하단 정보
    st.markdown("---")
    
    service = get_property_tax_service()
    statistics = service.get_asset_statistics()
    
    st.markdown(f"""
    <div style="text-align: center; color: #6b7280; font-size: 0.8rem; padding: 1rem 0;">
        <em>TAXi 지방세 관리 시스템 - 재산세 | 
        {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
        총 자산: {statistics['총_자산수']}개 | 
        도시지역분 적용: {statistics['도시지역분별_분포'].get('Y', 0)}개</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()