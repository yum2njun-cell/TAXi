"""
TAXi 지방세 관리 시스템 - 재산세 페이지 v1.4.2
pages/local_tax_property.py

버전 정보:
- v1.4.1 → v1.4.2 (Phase 3 완료 - 메이저 버전업)

주요 변경사항 (Phase 3):
- render_summary() 함수 수정
- statistics['도시지역분별_분포'] → 호환성 처리
- statistics['자산유형별_분포'] → 호환성 처리
- statistics['과세유형별_분포'] → 호환성 처리
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import copy
import io
import base64

from services.property_tax_service import PropertyTaxService
from components.layout import page_header, sidebar_menu
from utils.settings import settings
from components.theme import apply_custom_theme

st.set_page_config(
    page_title=f"{settings.APP_NAME} | 지방세 관리", 
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

# ============================================================================
# 📌 자산 마스터 관리 - 체크박스 기반 액션 (v1.3.3 유지)
# ============================================================================

def render_asset_master_list():
    """자산 마스터 리스트 화면 (메인) - v1.3.3 체크박스 유지"""
    st.markdown("###  자산 마스터 관리")
    
    col_btn1, col_btn2, col_btn3, col_spacer = st.columns([0.8, 0.8, 0.8, 7.6])
    
    with col_btn1:
        if st.button("➕", 
                     key="btn_asset_create", 
                     help="신규 자산 등록",
                     use_container_width=True):
            st.session_state['show_create_modal'] = True
            st.session_state['show_edit_modal'] = False
            st.session_state['show_delete_modal'] = False
            st.session_state['show_excel_modal'] = False
    
    with col_btn2:
        if st.button("UP", 
                     key="btn_excel_upload", 
                     help="엑셀 파일로 일괄 업로드",
                     use_container_width=True):
            st.session_state['show_excel_modal'] = True
            st.session_state['show_create_modal'] = False
            st.session_state['show_edit_modal'] = False
            st.session_state['show_delete_modal'] = False
    
    with col_btn3:
        service = get_property_tax_service()
        all_assets = service.get_all_assets()
        
        if all_assets:
            download_data = []
            
            for asset_id, asset_info in all_assets.items():
                year_data = asset_info.get("연도별데이터", {})
                
                for year_str, year_info in year_data.items():
                    download_data.append({
                        "자산ID": asset_id,
                        "그룹ID": asset_info.get("그룹ID", ""),
                        "자산명": asset_info.get("자산명", ""),
                        "자산유형": asset_info.get("자산유형", ""),
                        "상세유형": asset_info.get("상세유형", ""),
                        "과세유형": asset_info.get("과세유형", ""),
                        "시도": asset_info.get("시도", ""),
                        "시군구": asset_info.get("시군구", ""),
                        "상세주소": asset_info.get("상세주소", ""),
                        "면적": asset_info.get("면적", 0),
                        "재산세_도시지역분": asset_info.get("재산세_도시지역분", "N"),
                        "적용연도": year_info.get("적용연도", ""),
                        "공시지가": year_info.get("공시지가", 0),
                        "시가표준액": year_info.get("시가표준액", 0),
                        "건물시가": year_info.get("건물시가", 0),
                        "감면율": year_info.get("감면율", 0),
                        "중과세율": year_info.get("중과세율", 0)
                    })
            
            df = pd.DataFrame(download_data)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='assets', index=False)
            buffer.seek(0)
            
            download_clicked = st.download_button(
                label="다운로드",
                data=buffer,
                file_name=f"재산세_자산목록_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_excel_btn",
                help="자산 목록 Excel 다운로드",
                use_container_width=True
            )
            
            if download_clicked:
                st.session_state['show_edit_modal'] = False
                st.session_state['show_delete_modal'] = False
                st.session_state['show_create_modal'] = False
                st.session_state['show_excel_modal'] = False
        else:
            st.button("DN", 
                     disabled=True, 
                     key="download_excel_btn_disabled", 
                     help="다운로드할 자산이 없습니다",
                     use_container_width=True)
    
    service = get_property_tax_service()
    
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns([2, 2, 2, 4])
    
    with col_filter1:
        filter_asset_type = st.selectbox(
            "자산유형",
            ["전체", "토지", "건축물", "주택"],
            key="filter_asset_type"
        )
    
    with col_filter2:
        available_years = ["전체"] + [str(y) for y in service.get_all_available_years()]
        filter_year = st.selectbox(
            "연도",
            available_years,
            key="filter_year"
        )
    
    with col_filter3:
        available_groups = ["전체"] + service.get_available_groups()
        filter_group = st.selectbox(
            "그룹ID",
            available_groups,
            key="filter_group"
        )
    
    with col_filter4:
        filter_search = st.text_input(
            "검색 (자산ID/자산명)",
            placeholder="검색어 입력",
            key="filter_search"
        )
    
    all_assets = service.get_all_assets()
    
    if not all_assets:
        st.info("등록된 자산이 없습니다. ➕ 신규 등록 버튼을 눌러 자산을 추가해주세요.")
        return
    
    display_data = []
    
    for asset_id, asset_info in all_assets.items():
        if filter_asset_type != "전체" and asset_info.get("자산유형") != filter_asset_type:
            continue
        
        if filter_group != "전체" and asset_info.get("그룹ID") != filter_group:
            continue
        
        if filter_search:
            if filter_search.lower() not in asset_id.lower() and filter_search.lower() not in asset_info.get("자산명", "").lower():
                continue
        
        year_data = asset_info.get("연도별데이터", {})
        
        for year_str, year_info in year_data.items():
            if filter_year != "전체" and year_str != filter_year:
                continue
            
            display_data.append({
                "선택": False,
                "자산ID": asset_id,
                "자산명": asset_info.get("자산명", ""),
                "자산유형": asset_info.get("자산유형", ""),
                "과세유형": asset_info.get("과세유형", ""),
                "연도": year_str,
                "시가표준액": f"{year_info.get('시가표준액', 0):,}원",
                "그룹ID": asset_info.get("그룹ID", ""),
                "도시지역분": asset_info.get("재산세_도시지역분", "N"),
                "액션_자산ID": asset_id,
                "액션_연도": year_str
            })
    
    if not display_data:
        st.warning("필터 조건에 맞는 자산이 없습니다.")
        return
    
    df = pd.DataFrame(display_data)
    
    st.markdown(f"**총 {len(display_data)}개 자산 (연도별 행)**")
    
    edited_df = st.data_editor(
        df[["선택", "자산ID", "자산명", "자산유형", "과세유형", "연도", "시가표준액", "그룹ID", "도시지역분"]],
        column_config={
            "선택": st.column_config.CheckboxColumn(
                "선택",
                help="수정/삭제할 자산을 선택하세요",
                default=False,
            )
        },
        disabled=["자산ID", "자산명", "자산유형", "과세유형", "연도", "시가표준액", "그룹ID", "도시지역분"],
        hide_index=True,
        use_container_width=True,
        height=400,
        key="asset_data_editor"
    )
    
    st.markdown("---")
    st.markdown("**액션**")
    
    selected_rows = edited_df[edited_df["선택"] == True]
    
    if len(selected_rows) == 0:
        st.info(" 수정 또는 삭제할 자산을 체크박스로 선택해주세요.")
    elif len(selected_rows) > 1:
        st.warning(" 한 번에 하나의 자산만 선택 가능합니다. 첫 번째 선택된 자산으로 작업합니다.")
    
    if len(selected_rows) > 0:
        selected_row = selected_rows.iloc[0]
        selected_asset_id = selected_row["자산ID"]
        selected_year = selected_row["연도"]
        
        st.markdown(f"**선택된 자산**: {selected_asset_id} - {selected_year}년")
        
        col_action1, col_action2 = st.columns(2)
        
        with col_action1:
            if st.button(" 수정", key="btn_asset_update", use_container_width=True):
                st.session_state['edit_asset_id'] = selected_asset_id
                st.session_state['edit_year'] = selected_year
                st.session_state['show_edit_modal'] = True
                st.session_state['show_create_modal'] = False
                st.session_state['show_delete_modal'] = False
                st.session_state['show_excel_modal'] = False
                st.rerun()
        
        with col_action2:
            if st.button(" 삭제", key="btn_asset_delete", use_container_width=True):
                st.session_state['delete_asset_id'] = selected_asset_id
                st.session_state['delete_year'] = selected_year
                st.session_state['show_delete_modal'] = True
                st.session_state['show_create_modal'] = False
                st.session_state['show_edit_modal'] = False
                st.session_state['show_excel_modal'] = False
                st.rerun()
    
    if st.session_state.get('show_create_modal', False):
        asset_create_modal()
    
    if st.session_state.get('show_edit_modal', False):
        asset_update_modal(
            st.session_state.get('edit_asset_id'),
            st.session_state.get('edit_year')
        )
    
    if st.session_state.get('show_delete_modal', False):
        asset_delete_modal(
            st.session_state.get('delete_asset_id'),
            st.session_state.get('delete_year')
        )
    
    if st.session_state.get('show_excel_modal', False):
        excel_upload_modal()

@st.dialog("자산 신규 등록")
def asset_create_modal():
    """자산 신규 등록 모달"""
    st.markdown("#### 새 자산 정보 입력")
    
    service = get_property_tax_service()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("** 기본 정보**")
        asset_id = st.text_input("자산ID*", placeholder="ASSET_XXX", key="create_asset_id")
        asset_name = st.text_input("자산명*", placeholder="예: 본사 부지", key="create_asset_name")
        asset_type = st.selectbox("자산유형*", ["토지", "건축물", "주택"], key="create_asset_type")
        detail_type = st.text_input("상세유형", placeholder="예: 일반토지, 업무시설", key="create_detail_type")
        
        available_taxation_types = service.get_taxation_types_for_asset_type(asset_type)
        
        if asset_type == "토지":
            taxation_type = st.selectbox(
                "과세유형*",
                available_taxation_types,
                key="create_taxation_type"
            )
        else:
            taxation_type = "기타"
            st.selectbox(
                "과세유형*",
                ["기타"],
                disabled=True,
                key="create_taxation_type_auto"
            )
        
        urban_area = st.selectbox("재산세 도시지역분*", ["Y", "N"], key="create_urban_area")
    
    with col2:
        st.markdown("** 위치 정보**")
        sido = st.text_input("시도*", placeholder="예: 서울특별시", key="create_sido")
        sigungu = st.text_input("시군구*", placeholder="예: 강남구", key="create_sigungu")
        address = st.text_area("상세주소", placeholder="예: 테헤란로 123", key="create_address", height=100)
        area = st.number_input("면적(㎡)*", min_value=0.0, format="%.2f", key="create_area")
        group_id = st.selectbox(
            "그룹ID*",
            ["GROUP_A", "GROUP_B", "GROUP_C"],
            key="create_group_id"
        )
    
    st.markdown("** 연도별 데이터**")
    
    col_year1, col_year2, col_year3, col_year4 = st.columns(4)
    
    with col_year1:
        year = st.number_input("적용연도*", min_value=2020, max_value=2030, value=datetime.now().year, key="create_year")
    
    with col_year2:
        gongsijiga = st.number_input("공시지가", min_value=0, value=0, format="%d", key="create_gongsijiga")
    
    with col_year3:
        standard_value = st.number_input("시가표준액*", min_value=0, value=0, format="%d", key="create_standard_value")
    
    with col_year4:
        if asset_type == "주택":
            building_value = st.number_input("건물시가", min_value=0, value=0, format="%d", key="create_building_value")
        else:
            building_value = 0
    
    col_rate1, col_rate2 = st.columns(2)
    
    with col_rate1:
        exemption_rate = st.number_input("감면율(%)", min_value=0.0, max_value=100.0, value=0.0, format="%.2f", key="create_exemption")
    
    with col_rate2:
        surcharge_rate = st.number_input("중과세율(%)", min_value=0.0, value=0.0, format="%.2f", key="create_surcharge")
    
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("취소", key="create_cancel", use_container_width=True):
            st.session_state['show_create_modal'] = False
            st.rerun()
    
    with col_btn2:
        if st.button("저장", key="create_save", type="primary", use_container_width=True):
            if not asset_id or not asset_name or not sido or not sigungu or standard_value == 0:
                st.error("필수 항목(*)을 모두 입력해주세요.")
            else:
                new_asset = {
                    "자산ID": asset_id,
                    "자산명": asset_name,
                    "자산유형": asset_type,
                    "상세유형": detail_type,
                    "과세유형": taxation_type,
                    "재산세_도시지역분": urban_area,
                    "그룹ID": group_id,
                    "시도": sido,
                    "시군구": sigungu,
                    "상세주소": address,
                    "면적": area,
                    "연도별데이터": {
                        str(year): {
                            "적용연도": year,
                            "공시지가": gongsijiga,
                            "시가표준액": standard_value,
                            "건물시가": building_value,
                            "감면율": exemption_rate,
                            "중과세율": surcharge_rate
                        }
                    }
                }
                
                success, message = service.add_asset(new_asset)
                
                if success:
                    st.success(message)
                    st.session_state['show_create_modal'] = False
                    st.rerun()
                else:
                    st.error(message)

@st.dialog("자산 수정")
def asset_update_modal(asset_id, year):
    """자산 수정 모달"""
    st.markdown(f"#### {asset_id} - {year}년 데이터 수정")
    
    service = get_property_tax_service()
    asset_info = service.get_asset(asset_id)
    
    if not asset_info:
        st.error(f"자산 {asset_id}를 찾을 수 없습니다.")
        return
    
    year_data = asset_info.get("연도별데이터", {}).get(str(year), {})
    
    if not year_data:
        st.error(f"{year}년 데이터를 찾을 수 없습니다.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**기본 정보**")
        st.text_input("자산ID", value=asset_id, disabled=True, key="edit_asset_id_display")
        asset_name = st.text_input("자산명*", value=asset_info.get("자산명", ""), key="edit_asset_name")
        asset_type = st.selectbox(
            "자산유형*",
            ["토지", "건축물", "주택"],
            index=["토지", "건축물", "주택"].index(asset_info.get("자산유형", "토지")),
            key="edit_asset_type"
        )
        detail_type = st.text_input("상세유형", value=asset_info.get("상세유형", ""), key="edit_detail_type")
        
        available_taxation_types = service.get_taxation_types_for_asset_type(asset_type)
        current_taxation = asset_info.get("과세유형", "기타")
        
        if asset_type == "토지":
            taxation_type = st.selectbox(
                "과세유형*",
                available_taxation_types,
                index=available_taxation_types.index(current_taxation) if current_taxation in available_taxation_types else 0,
                key="edit_taxation_type"
            )
        else:
            taxation_type = "기타"
            st.selectbox("과세유형*", ["기타"], disabled=True, key="edit_taxation_type_auto")
        
        urban_area = st.selectbox(
            "재산세 도시지역분*",
            ["Y", "N"],
            index=["Y", "N"].index(asset_info.get("재산세_도시지역분", "N")),
            key="edit_urban_area"
        )
    
    with col2:
        st.markdown("**위치 정보**")
        sido = st.text_input("시도*", value=asset_info.get("시도", ""), key="edit_sido")
        sigungu = st.text_input("시군구*", value=asset_info.get("시군구", ""), key="edit_sigungu")
        address = st.text_area("상세주소", value=asset_info.get("상세주소", ""), key="edit_address", height=100)
        area = st.number_input("면적(㎡)*", min_value=0.0, value=float(asset_info.get("면적", 0)), format="%.2f", key="edit_area")
        group_id = st.selectbox(
            "그룹ID*",
            ["GROUP_A", "GROUP_B", "GROUP_C"],
            index=["GROUP_A", "GROUP_B", "GROUP_C"].index(asset_info.get("그룹ID", "GROUP_A")) if asset_info.get("그룹ID") in ["GROUP_A", "GROUP_B", "GROUP_C"] else 0,
            key="edit_group_id"
        )
    
    st.markdown(f"**{year}년 데이터**")
    
    col_year1, col_year2, col_year3, col_year4 = st.columns(4)
    
    with col_year1:
        st.text_input("적용연도", value=str(year), disabled=True, key="edit_year_display")
    
    with col_year2:
        gongsijiga = st.number_input("공시지가", min_value=0, value=int(year_data.get("공시지가", 0)), format="%d", key="edit_gongsijiga")
    
    with col_year3:
        standard_value = st.number_input("시가표준액*", min_value=0, value=int(year_data.get("시가표준액", 0)), format="%d", key="edit_standard_value")
    
    with col_year4:
        if asset_type == "주택":
            building_value = st.number_input("건물시가", min_value=0, value=int(year_data.get("건물시가", 0)), format="%d", key="edit_building_value")
        else:
            building_value = 0
    
    col_rate1, col_rate2 = st.columns(2)
    
    with col_rate1:
        exemption_rate = st.number_input("감면율(%)", min_value=0.0, max_value=100.0, value=float(year_data.get("감면율", 0.0)), format="%.2f", key="edit_exemption")
    
    with col_rate2:
        surcharge_rate = st.number_input("중과세율(%)", min_value=0.0, value=float(year_data.get("중과세율", 0.0)), format="%.2f", key="edit_surcharge")
    
    st.markdown("---")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("취소", key="edit_cancel", use_container_width=True):
            st.session_state['show_edit_modal'] = False
            st.rerun()
    
    with col_btn2:
        if st.button("저장", key="edit_save", type="primary", use_container_width=True):
            if not asset_name or not sido or not sigungu or standard_value == 0:
                st.error("필수 항목(*)을 모두 입력해주세요.")
            else:
                updated_asset = {
                    "자산ID": asset_id,
                    "자산명": asset_name,
                    "자산유형": asset_type,
                    "상세유형": detail_type,
                    "과세유형": taxation_type,
                    "재산세_도시지역분": urban_area,
                    "그룹ID": group_id,
                    "시도": sido,
                    "시군구": sigungu,
                    "상세주소": address,
                    "면적": area,
                    "연도별데이터": {
                        str(year): {
                            "적용연도": int(year),
                            "공시지가": gongsijiga,
                            "시가표준액": standard_value,
                            "건물시가": building_value,
                            "감면율": exemption_rate,
                            "중과세율": surcharge_rate
                        }
                    }
                }
                
                asset_info["자산명"] = asset_name
                asset_info["자산유형"] = asset_type
                asset_info["상세유형"] = detail_type
                asset_info["과세유형"] = taxation_type
                asset_info["재산세_도시지역분"] = urban_area
                asset_info["그룹ID"] = group_id
                asset_info["시도"] = sido
                asset_info["시군구"] = sigungu
                asset_info["상세주소"] = address
                asset_info["면적"] = area
                asset_info["연도별데이터"][str(year)] = updated_asset["연도별데이터"][str(year)]
                
                success, message = service.update_asset(asset_id, asset_info)
                
                if success:
                    st.success(message)
                    st.session_state['show_edit_modal'] = False
                    st.rerun()
                else:
                    st.error(message)

@st.dialog("자산 삭제 확인")
def asset_delete_modal(asset_id, year):
    """자산 삭제 확인 모달"""
    st.markdown("#### 삭제 확인")
    
    service = get_property_tax_service()
    asset_info = service.get_asset(asset_id)
    
    if not asset_info:
        st.error(f"자산 {asset_id}를 찾을 수 없습니다.")
        return
    
    st.warning(f"다음 자산의 **{year}년 데이터**를 삭제하시겠습니까?")
    
    st.info(f"""
**자산ID:** {asset_id}  
**자산명:** {asset_info.get('자산명', 'Unknown')}  
**연도:** {year}년  
**자산유형:** {asset_info.get('자산유형', 'Unknown')}  
**그룹ID:** {asset_info.get('그룹ID', 'Unknown')}
    """)
    
    st.error("이 작업은 되돌릴 수 없습니다!")
    
    col_btn1, col_btn2 = st.columns(2)
    
    with col_btn1:
        if st.button("취소", key="delete_cancel", use_container_width=True):
            st.session_state['show_delete_modal'] = False
            st.rerun()
    
    with col_btn2:
        if st.button("삭제", key="delete_confirm", type="primary", use_container_width=True):
            year_data = asset_info.get("연도별데이터", {})
            
            if str(year) in year_data:
                del year_data[str(year)]
                
                if len(year_data) == 0:
                    success, message = service.delete_asset(asset_id)
                else:
                    asset_info["연도별데이터"] = year_data
                    success, message = service.update_asset(asset_id, asset_info)
                
                if success:
                    st.success(f"{asset_id}의 {year}년 데이터가 삭제되었습니다.")
                    st.session_state['show_delete_modal'] = False
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error(f"{year}년 데이터를 찾을 수 없습니다.")

@st.dialog("엑셀 파일 업로드")
def excel_upload_modal():
    """엑셀 업로드 모달"""
    st.markdown("#### 엑셀 파일로 일괄 등록")
    
    st.info("""
**업로드 형식 안내:**
- 시트명: `assets`
- 필수 컬럼: 자산ID, 자산명, 자산유형, 과세유형, 그룹ID, 시도, 시군구, 면적, 재산세_도시지역분, 적용연도, 시가표준액
- 선택 컬럼: 상세유형, 상세주소, 공시지가, 건물시가, 감면율, 중과세율
    """)
    
    uploaded_file = st.file_uploader(
        "엑셀 파일 선택 (.xlsx)",
        type=['xlsx'],
        key="excel_upload_file"
    )
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file, sheet_name='assets')
            
            st.markdown("**업로드된 데이터 미리보기**")
            st.dataframe(df.head(10), use_container_width=True)
            st.markdown(f"총 {len(df)}개 행")
            
            service = get_property_tax_service()
            validation_errors = service.validate_excel_format(df)
            
            if validation_errors:
                st.error("다음 오류를 수정해주세요:")
                for error in validation_errors:
                    st.markdown(f"- {error}")
            else:
                st.success("형식 검증 완료")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    if st.button("취소", key="excel_cancel", use_container_width=True):
                        st.session_state['show_excel_modal'] = False
                        st.rerun()
                
                with col_btn2:
                    if st.button("업로드", key="excel_confirm", type="primary", use_container_width=True):
                        with st.spinner("엑셀 데이터 처리 중..."):
                            success, message, counts = service.import_assets_from_excel(df)
                            
                            if success:
                                st.success(message)
                                
                                col_metric1, col_metric2, col_metric3 = st.columns(3)
                                with col_metric1:
                                    st.metric("신규 등록", f"{counts['success']}건")
                                with col_metric2:
                                    st.metric("업데이트", f"{counts['update']}건")
                                with col_metric3:
                                    st.metric("실패", f"{counts['error']}건")
                                
                                if counts['success'] > 0 or counts['update'] > 0:
                                    st.session_state['show_excel_modal'] = False
                                    st.rerun()
                            else:
                                st.error(message)
        
        except Exception as e:
            st.error(f"파일 읽기 오류: {str(e)}")
            st.info("엑셀 파일의 시트명이 'assets'인지 확인해주세요.")

# ============================================================================
# 📌 세율 관리 (v1.3.6 유지)
# ============================================================================

@st.dialog("연도 관리")
def render_year_management_modal():
    """연도 관리 모달 팝업"""
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    st.markdown("#### 연도 관리")
    
    if available_years:
        year_range = f"{min(available_years)} ~ {max(available_years)}"
        st.info(f"**관리 중인 연도:** {year_range} ({len(available_years)}개)")
        st.write(f"**연도 목록:** {', '.join(map(str, available_years))}")
    else:
        st.warning("등록된 연도가 없습니다.")
    
    st.markdown("---")
    st.markdown("**새 연도 추가**")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        new_year = st.number_input(
            "추가할 연도",
            min_value=2020,
            max_value=2030,
            value=datetime.now().year,
            step=1,
            key="new_year_input"
        )
    
    with col2:
        if st.button("연도 추가", type="primary", key="add_year_btn"):
            if new_year not in available_years:
                success, message = service.add_year(new_year)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.warning(f"{new_year}년은 이미 존재합니다.")

def render_compact_year_management_button():
    """세율 관리 헤더의 연도 관리 버튼"""
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("### 세율 관리")
    
    with col2:
        year_count = len(available_years)
        button_text = f"연도관리 ({year_count})"
        
        if st.button(button_text, key="open_year_management_modal", help=f"관리 중인 연도: {year_count}개"):
            render_year_management_modal()

def render_tax_rate_management():
    """세율 관리 섹션"""
    render_compact_year_management_button()
    
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
    """재산세 누진구간 관리"""
    st.markdown("#### 재산세 누진구간 관리")
    
    col1, col2 = st.columns(2)
    
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    with col1:
        if available_years:
            rate_year = st.selectbox("연도 선택", available_years, key="rate_year_select")
        else:
            st.warning("등록된 연도가 없습니다. 먼저 연도를 추가해주세요.")
            return
    
    with col2:
        asset_type = st.selectbox("자산유형 선택", ["토지", "건축물", "주택"], key="rate_asset_type_select")
    
    if asset_type == "토지":
        taxation_types = ["종합합산", "별도합산", "분리과세"]
        selected_taxation_type = st.selectbox("과세유형 선택", taxation_types, key="rate_taxation_type_select")
    else:
        selected_taxation_type = "기타"
    
    edit_mode = st.toggle(f"편집 모드", key=f"edit_mode_{rate_year}_{asset_type}_{selected_taxation_type}")
    
    current_rates = service.get_tax_rates(rate_year, asset_type, selected_taxation_type)
    
    if not current_rates:
        st.warning(f"{rate_year}년 {asset_type} - {selected_taxation_type} 세율 정보가 없습니다.")
        return
    
    if not edit_mode:
        rate_data = []
        for i, rate_info in enumerate(current_rates):
            upper_text = service.convert_infinity_for_display(rate_info["상한"])
            rate_display = service.format_tax_rate_for_display(rate_info["세율"], 4)
            rate_data.append({
                "구간": f"구간 {i+1}",
                "과세표준 하한": f"{rate_info['하한']:,}원",
                "과세표준 상한": f"{upper_text}원",
                "기본세액": f"{rate_info['기본세액']:,}원",
                "세율": f"{rate_display}%"
            })
        
        df = pd.DataFrame(rate_data)
        st.dataframe(df, use_container_width=True)
    
    else:
        st.markdown("**세율 편집**")
        
        working_rates = copy.deepcopy(current_rates)
        updated_rates = []
        
        for i, rate_info in enumerate(working_rates):
            st.markdown(f"**구간 {i+1}**")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                lower = st.number_input("과세표준 하한", value=int(rate_info["하한"]), 
                                      format="%d", key=f"edit_lower_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
            
            with col2:
                upper_display = service.convert_infinity_for_display(rate_info["상한"])
                if upper_display == "무제한":
                    st.text_input("과세표준 상한", value="무제한", disabled=True, 
                                key=f"edit_upper_display_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
                    upper = rate_info["상한"]
                else:
                    upper = st.number_input("과세표준 상한", value=int(rate_info["상한"]), 
                                          format="%d", key=f"edit_upper_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
            
            with col3:
                base_tax = st.number_input("기본세액", value=int(rate_info["기본세액"]), 
                                         format="%d", key=f"edit_base_{rate_year}_{asset_type}_{selected_taxation_type}_{i}")
            
            with col4:
                current_rate_value = rate_info["세율"]
                rate = st.number_input(
                    "세율(%)",
                    min_value=0.0,
                    max_value=100.0,
                    value=float(current_rate_value),
                    format="%.4f",
                    step=0.0001,
                    key=f"edit_rate_{rate_year}_{asset_type}_{selected_taxation_type}_{i}"
                )
            
            updated_rates.append({
                "하한": lower,
                "상한": upper,
                "기본세액": base_tax,
                "세율": rate
            })
        
        st.markdown("---")
        
        col_action1, col_action2, col_action3 = st.columns(3)
        
        with col_action1:
            if st.button("구간 추가", key=f"add_bracket_{rate_year}_{asset_type}_{selected_taxation_type}"):
                success = service.add_rate_bracket(rate_year, asset_type, selected_taxation_type)
                if success:
                    st.success("구간이 추가되었습니다.")
                    st.rerun()
        
        with col_action2:
            if len(updated_rates) > 1:
                if st.button("마지막 구간 삭제", key=f"remove_bracket_{rate_year}_{asset_type}_{selected_taxation_type}"):
                    success = service.remove_last_rate_bracket(rate_year, asset_type, selected_taxation_type)
                    if success:
                        st.success("마지막 구간이 삭제되었습니다.")
                        st.rerun()
        
        with col_action3:
            if st.button("저장", type="primary", key=f"save_rates_{rate_year}_{asset_type}_{selected_taxation_type}"):
                success, message = service.update_tax_rates(rate_year, asset_type, selected_taxation_type, updated_rates)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

def render_urban_area_tax_rates():
    """재산세 도시지역분 세율 관리"""
    st.markdown("#### 재산세 도시지역분 세율 관리")
    
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    if not available_years:
        st.warning("등록된 연도가 없습니다. 먼저 연도를 추가해주세요.")
        return
    
    urban_year = st.selectbox("연도 선택", available_years, key="urban_year_select")
    
    current_ratio = service.get_urban_area_tax_rate(urban_year)
    
    st.info("재산세 도시지역분은 재산세 산출세액의 0.14% (단일세율)로 계산됩니다.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**현재 세율 정보:**")
        formatted_ratio = service.format_tax_rate_for_display(current_ratio, 3)
        st.markdown(f"- 재산세 도시지역분 세율: {formatted_ratio}%")
        st.markdown("- 적용 기준: 재산세 산출세액")
        st.markdown("- 적용 조건: 도시지역 소재 재산만")
    
    with col2:
        st.markdown("**계산 예시:**")
        example_property_tax = 1000000
        example_urban_tax = example_property_tax * current_ratio / 100
        
        st.markdown(f"- 재산세 산출세액: {example_property_tax:,}원")
        st.markdown(f"- 도시지역분 세율: {formatted_ratio}%")
        st.markdown(f"- 재산세 도시지역분: {example_urban_tax:,.0f}원")

def render_local_education_tax_rates():
    """지방교육세율 관리"""
    st.markdown("#### 지방교육세율 관리")
    
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    if not available_years:
        st.warning("등록된 연도가 없습니다. 먼저 연도를 추가해주세요.")
        return
    
    edu_year = st.selectbox("연도 선택", available_years, key="edu_year_select")
    
    try:
        current_ratio = st.session_state.property_tax_rates["지방교육세"][str(edu_year)]["비율"]
        
        st.info("지방교육세는 재산세의 일정 비율로 계산됩니다.")
        formatted_ratio = service.format_tax_rate_for_display(current_ratio * 100, 1)
        st.markdown(f"**{edu_year}년 지방교육세 비율: {formatted_ratio}%**")
        st.markdown("(재산세 대비)")
    except KeyError:
        st.warning(f"{edu_year}년 지방교육세율 정보가 없습니다.")

def render_regional_resource_tax_rates():
    """지역자원시설세율 관리"""
    st.markdown("#### 지역자원시설세율 관리")
    
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    if not available_years:
        st.warning("등록된 연도가 없습니다. 먼저 연도를 추가해주세요.")
        return
    
    resource_year = st.selectbox("연도 선택", available_years, key="resource_year_select")
    
    edit_mode = st.toggle(f"편집 모드", key=f"resource_edit_mode_{resource_year}")
    
    try:
        current_rates = st.session_state.property_tax_rates["지역자원시설세"][str(resource_year)]
        
        st.markdown(f"**{resource_year}년 지역자원시설세 누진구간**")
        
        if not edit_mode:
            rate_data = []
            for i, rate_info in enumerate(current_rates):
                upper_text = service.convert_infinity_for_display(rate_info["상한"])
                rate_display = service.format_tax_rate_for_display(rate_info["세율"], 4)
                rate_data.append({
                    "구간": f"구간 {i+1}",
                    "과세표준 하한": f"{rate_info['하한']:,}원",
                    "과세표준 상한": f"{upper_text}원",
                    "기본세액": f"{rate_info['기본세액']:,}원",
                    "세율": f"{rate_display}%"
                })
            
            df = pd.DataFrame(rate_data)
            st.dataframe(df, use_container_width=True)
        
        else:
            st.markdown("**세율 편집**")
            
            working_rates = copy.deepcopy(current_rates)
            updated_rates = []
            
            for i, rate_info in enumerate(working_rates):
                st.markdown(f"**구간 {i+1}**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    lower = st.number_input("과세표준 하한", value=int(rate_info["하한"]), 
                                          format="%d", key=f"res_edit_lower_{resource_year}_{i}")
                
                with col2:
                    upper_display = service.convert_infinity_for_display(rate_info["상한"])
                    if upper_display == "무제한":
                        st.text_input("과세표준 상한", value="무제한", disabled=True, 
                                    key=f"res_edit_upper_display_{resource_year}_{i}")
                        upper = rate_info["상한"]
                    else:
                        upper = st.number_input("과세표준 상한", value=int(rate_info["상한"]), 
                                              format="%d", key=f"res_edit_upper_{resource_year}_{i}")
                
                with col3:
                    base_tax = st.number_input("기본세액", value=int(rate_info["기본세액"]), 
                                             format="%d", key=f"res_edit_base_{resource_year}_{i}")
                
                with col4:
                    rate = st.number_input(
                        "세율(%)",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(rate_info["세율"]),
                        format="%.4f",
                        step=0.0001,
                        key=f"res_edit_rate_{resource_year}_{i}"
                    )
                
                updated_rates.append({
                    "하한": lower,
                    "상한": upper,
                    "기본세액": base_tax,
                    "세율": rate
                })
            
            st.markdown("---")
            
            if st.button("저장", type="primary", key=f"save_resource_rates_{resource_year}"):
                st.session_state.property_tax_rates["지역자원시설세"][str(resource_year)] = updated_rates
                
                save_success, save_msg = service.save_rates_to_json()
                
                if save_success:
                    st.success("지역자원시설세율이 저장되었습니다.")
                    st.rerun()
                else:
                    st.warning(f"세율은 업데이트되었으나 JSON 저장 중 오류: {save_msg}")
                    st.rerun()
    
    except KeyError:
        st.warning(f"{resource_year}년 지역자원시설세율 정보가 없습니다.")

def render_fair_market_ratios():
    """공정시장가액비율 관리"""
    st.markdown("#### 공정시장가액비율 관리")
    
    service = get_property_tax_service()
    available_years = service.get_all_available_years()
    
    if not available_years:
        st.warning("등록된 연도가 없습니다. 먼저 연도를 추가해주세요.")
        return
    
    try:
        fair_market_ratios = st.session_state.fair_market_ratios
        
        st.info("공정시장가액비율은 시가표준액을 과세표준으로 환산할 때 사용됩니다.")
        
        edit_mode = st.toggle("편집 모드", key="ratio_edit_mode")
        
        if not edit_mode:
            ratio_data = []
            for year in available_years:
                year_key = str(year)
                if year_key not in fair_market_ratios:
                    fair_market_ratios[year_key] = {
                        "토지": 70.0,
                        "건축물": 70.0,
                        "주택": 60.0
                    }
                
                ratio_data.append({
                    "연도": f"{year}년",
                    "토지(%)": f"{fair_market_ratios[year_key]['토지']:.1f}",
                    "건축물(%)": f"{fair_market_ratios[year_key]['건축물']:.1f}",
                    "주택(%)": f"{fair_market_ratios[year_key]['주택']:.1f}"
                })
            
            df = pd.DataFrame(ratio_data)
            st.dataframe(df, use_container_width=True, height=400)
        
        else:
            st.markdown("**비율 편집**")
            st.markdown("각 연도별 자산유형별 비율을 입력하세요.")
            
            updated_ratios = {}
            
            col_header1, col_header2, col_header3, col_header4 = st.columns([2, 2, 2, 2])
            with col_header1:
                st.markdown("**연도**")
            with col_header2:
                st.markdown("**토지(%)**")
            with col_header3:
                st.markdown("**건축물(%)**")
            with col_header4:
                st.markdown("**주택(%)**")
            
            for year in available_years:
                year_key = str(year)
                
                if year_key not in fair_market_ratios:
                    fair_market_ratios[year_key] = {
                        "토지": 70.0,
                        "건축물": 70.0,
                        "주택": 60.0
                    }
                
                current = fair_market_ratios[year_key]
                
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                
                with col1:
                    st.markdown(f"**{year}년**")
                
                with col2:
                    land = st.number_input(
                        "토지",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(current["토지"]),
                        step=0.1,
                        key=f"edit_land_{year}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    building = st.number_input(
                        "건축물",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(current["건축물"]),
                        step=0.1,
                        key=f"edit_building_{year}",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    house = st.number_input(
                        "주택",
                        min_value=0.0,
                        max_value=100.0,
                        value=float(current["주택"]),
                        step=0.1,
                        key=f"edit_house_{year}",
                        label_visibility="collapsed"
                    )
                
                updated_ratios[year_key] = {
                    "토지": land,
                    "건축물": building,
                    "주택": house
                }
            
            st.markdown("---")
            
            col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 4])
            
            with col_btn1:
                if st.button("연도 추가", key="add_ratio_year_btn"):
                    current_year = datetime.now().year
                    new_year = current_year
                    
                    while str(new_year) in fair_market_ratios:
                        new_year += 1
                    
                    if new_year <= 2030:
                        success, message = service.add_year(new_year)
                        if success:
                            st.success(f"{new_year}년이 추가되었습니다.")
                            st.rerun()
                        else:
                            st.warning(f"{new_year}년은 이미 존재합니다.")
            
            with col_btn2:
                if st.button("저장", type="primary", key="save_ratios_btn"):
                    success, message = service.update_fair_market_ratios(updated_ratios)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    except KeyError:
        st.error("공정시장가액비율 데이터를 찾을 수 없습니다.")

# ============================================================================
# 📌 계산 워크플로우 (Phase 3 개선)
# ============================================================================

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
    """Transaction - 그룹별 일괄 계산 (v1.4.0 개선: Excel 다운로드에 그룹ID 추가)"""
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
        available_years = service.get_all_available_years()
        if available_years:
            calc_year = st.selectbox("계산 연도", available_years, key="trans_year_select")
        else:
            st.warning("등록된 자산에 연도 데이터가 없습니다.")
            return
    
    if st.button("그룹 일괄 계산", type="primary", key="trans_calc_btn"):
        with st.spinner(f"{selected_group} 그룹 {calc_year}년 계산 중..."):
            calc_result = service.calculate_property_tax_for_group(selected_group, calc_year)
            
            if "오류" in calc_result:
                st.error(calc_result["오류"])
                return
            
            calc_key = f"{selected_group}_{calc_year}"
            service.save_calculation_result(calc_key, calc_result)
            
            st.success(f"{selected_group} 그룹 {calc_year}년 세액 계산이 완료되었습니다!")

            st.markdown("#### 계산 결과 요약")
            
            col_summary1, col_summary2, col_summary3 = st.columns(3)
            
            with col_summary1:
                st.metric("계산 자산 수", f"{len(calc_result['자산별계산'])}개")
            
            with col_summary2:
                st.metric("총세액", f"{calc_result['총세액']:,.0f}원")
            
            with col_summary3:
                st.metric("계산 일시", calc_result['계산일시'][:16])
            
            st.markdown("**자산별 계산 결과**")
            
            calc_list = []
            for asset_id, asset_calc in calc_result['자산별계산'].items():
                calc_list.append({
                    "자산ID": asset_id,
                    "과세표준": f"{asset_calc['과세표준']:,.0f}원",
                    "재산세": f"{asset_calc['재산세']:,.0f}원",
                    "도시지역분": f"{asset_calc['재산세_도시지역분']:,.0f}원",
                    "지방교육세": f"{asset_calc['지방교육세']:,.0f}원",
                    "지역자원시설세": f"{asset_calc['지역자원시설세']:,.0f}원",
                    "총세액": f"{asset_calc['총세액']:,.0f}원"
                })
            
            df = pd.DataFrame(calc_list)
            st.dataframe(df, use_container_width=True)
            
            # v1.4.0 신규: Excel 다운로드에 그룹ID 추가
            download_data = []
            for asset_id, asset_calc in calc_result['자산별계산'].items():
                download_data.append({
                    "자산ID": asset_id,
                    "그룹ID": calc_result['그룹ID'],
                    "자산명": asset_calc['자산명'],
                    "재산세": asset_calc['재산세'],
                    "재산세_도시지역분": asset_calc['재산세_도시지역분'],
                    "지방교육세": asset_calc['지방교육세'],
                    "지역자원시설세": asset_calc['지역자원시설세'],
                    "총세액": asset_calc['총세액']
                })
            
            df_download = pd.DataFrame(download_data)
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_download.to_excel(writer, sheet_name='calculation', index=False)
            buffer.seek(0)
            
            st.download_button(
                label="계산 결과 Excel 다운로드",
                data=buffer,
                file_name=f"재산세계산_{selected_group}_{calc_year}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_calc_result"
            )

def render_compare():
    """Compare - 고지서 데이터 입력 및 비교 (v1.4.0 전면 재작성)"""
    st.markdown("#### 고지서 데이터 입력 및 비교")

    service = get_property_tax_service()
    all_calculations = service.get_all_calculation_results()
    
    if not all_calculations:
        st.info("먼저 Transaction에서 세액을 계산해주세요.")
        return
    
    # STEP 1: 계산 결과 선택
    calc_options = list(all_calculations.keys())
    selected_calc = st.selectbox("비교할 계산 결과 선택", calc_options, key="compare_calc_select")
    
    calc_data = all_calculations[selected_calc]
    asset_list = calc_data['자산별계산']
    
    st.markdown(f"**그룹:** {calc_data['그룹ID']}")
    st.markdown(f"**연도:** {calc_data['계산연도']}")
    st.markdown(f"**자산 수:** {len(asset_list)}개")
    
    # STEP 2: 입력 방식 선택 (라디오 버튼)
    input_method = st.radio(
        "고지서 입력 방식",
        ["직접 입력", "Excel 업로드"],
        horizontal=True,
        key="compare_input_method"
    )
    
    notice_data = {}
    
    if input_method == "Excel 업로드":
        st.info("""
**Excel 형식 안내:**
- 필수 컬럼: 자산ID, 그룹ID, 재산세, 재산세_도시지역분, 지방교육세, 지역자원시설세, 총세액
- Transaction에서 다운로드한 Excel을 수정하여 업로드 가능
        """)
        
        uploaded_file = st.file_uploader("고지서 Excel 업로드 (.xlsx)", type=['xlsx'], key="compare_excel_upload")
        
        if uploaded_file:
            try:
                df = pd.read_excel(uploaded_file)
                
                required_cols = ["자산ID", "그룹ID", "재산세", "재산세_도시지역분", 
                               "지방교육세", "지역자원시설세", "총세액"]
                missing = [c for c in required_cols if c not in df.columns]
                
                if missing:
                    st.error(f"필수 컬럼 누락: {', '.join(missing)}")
                else:
                    for _, row in df.iterrows():
                        asset_id = str(row['자산ID'])
                        if asset_id in asset_list:
                            notice_data[asset_id] = {
                                "재산세": int(row['재산세']),
                                "재산세_도시지역분": int(row['재산세_도시지역분']),
                                "지방교육세": int(row['지방교육세']),
                                "지역자원시설세": int(row['지역자원시설세']),
                                "총세액": int(row['총세액'])
                            }
                    
                    st.success(f"{len(notice_data)}개 자산의 고지서 데이터 로드 완료")
            
            except Exception as e:
                st.error(f"파일 읽기 오류: {str(e)}")
    
    else:  # 직접 입력
        st.markdown("#### 자산별 고지서 금액 입력")
        
        for asset_id, asset_calc in asset_list.items():
            with st.expander(f"{asset_id} - {asset_calc['자산명']}", expanded=False):
                col1, col2, col3, col4, col5 = st.columns(5)
                
                with col1:
                    st.markdown("**계산값**")
                    st.write(f"{asset_calc['재산세']:,.0f}")
                    notice_property = st.number_input(
                        "재산세 (고지서)",
                        value=int(asset_calc['재산세']),
                        format="%d",
                        key=f"notice_prop_{asset_id}",
                        label_visibility="collapsed"
                    )
                
                with col2:
                    st.markdown("**도시지역분**")
                    st.write(f"{asset_calc['재산세_도시지역분']:,.0f}")
                    notice_urban = st.number_input(
                        "도시지역분 (고지서)",
                        value=int(asset_calc['재산세_도시지역분']),
                        format="%d",
                        key=f"notice_urban_{asset_id}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    st.markdown("**지방교육세**")
                    st.write(f"{asset_calc['지방교육세']:,.0f}")
                    notice_edu = st.number_input(
                        "지방교육세 (고지서)",
                        value=int(asset_calc['지방교육세']),
                        format="%d",
                        key=f"notice_edu_{asset_id}",
                        label_visibility="collapsed"
                    )
                
                with col4:
                    st.markdown("**지역자원시설세**")
                    st.write(f"{asset_calc['지역자원시설세']:,.0f}")
                    notice_resource = st.number_input(
                        "지역자원시설세 (고지서)",
                        value=int(asset_calc['지역자원시설세']),
                        format="%d",
                        key=f"notice_resource_{asset_id}",
                        label_visibility="collapsed"
                    )
                
                with col5:
                    st.markdown("**총세액**")
                    notice_total = notice_property + notice_urban + notice_edu + notice_resource
                    st.write(f"{notice_total:,.0f}")
                
                notice_data[asset_id] = {
                    "재산세": notice_property,
                    "재산세_도시지역분": notice_urban,
                    "지방교육세": notice_edu,
                    "지역자원시설세": notice_resource,
                    "총세액": notice_total
                }
    
    # STEP 3: 비교 실행
    if notice_data and st.button("비교 실행", type="primary", key="compare_execute"):
        comparison_table = []
        
        for asset_id, asset_calc in asset_list.items():
            if asset_id in notice_data:
                notice = notice_data[asset_id]
                
                comparison_table.append({
                    "자산ID": asset_id,
                    "자산명": asset_calc['자산명'],
                    "계산_재산세": f"{asset_calc['재산세']:,.0f}",
                    "고지_재산세": f"{notice['재산세']:,.0f}",
                    "차이_재산세": f"{asset_calc['재산세'] - notice['재산세']:+,.0f}",
                    "계산_도시": f"{asset_calc['재산세_도시지역분']:,.0f}",
                    "고지_도시": f"{notice['재산세_도시지역분']:,.0f}",
                    "차이_도시": f"{asset_calc['재산세_도시지역분'] - notice['재산세_도시지역분']:+,.0f}",
                    "계산_교육": f"{asset_calc['지방교육세']:,.0f}",
                    "고지_교육": f"{notice['지방교육세']:,.0f}",
                    "차이_교육": f"{asset_calc['지방교육세'] - notice['지방교육세']:+,.0f}",
                    "계산_자원": f"{asset_calc['지역자원시설세']:,.0f}",
                    "고지_자원": f"{notice['지역자원시설세']:,.0f}",
                    "차이_자원": f"{asset_calc['지역자원시설세'] - notice['지역자원시설세']:+,.0f}",
                    "계산_총액": f"{asset_calc['총세액']:,.0f}",
                    "고지_총액": f"{notice['총세액']:,.0f}",
                    "차이_총액": f"{asset_calc['총세액'] - notice['총세액']:+,.0f}",
                    "일치": "✅" if asset_calc['총세액'] == notice['총세액'] else "❌"
                })
        
        comparison_key = selected_calc
        st.session_state.property_comparisons[comparison_key] = {
            "계산키": selected_calc,
            "그룹ID": calc_data['그룹ID'],
            "계산연도": calc_data['계산연도'],
            "자산별비교": notice_data,
            "비교일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        st.success("비교가 완료되었습니다!")
        
        st.markdown("#### 비교 결과 상세")
        df = pd.DataFrame(comparison_table)
        st.dataframe(df, use_container_width=True, height=400)

def render_finalize():
    """Finalize - 최종값 선택 및 저장 (v1.4.0 전면 재작성: 자산별 개별 선택)"""
    st.markdown("#### 최종값 선택 및 저장")
    
    service = get_property_tax_service()
    all_calculations = service.get_all_calculation_results()
    all_comparisons = st.session_state.property_comparisons
    
    finalize_options = [k for k in all_calculations.keys() if k in all_comparisons]
    
    if not finalize_options:
        st.info("먼저 Compare에서 고지서와 비교해주세요.")
        return
    
    selected_calc = st.selectbox("확정할 계산 결과 선택", finalize_options, key="finalize_select")
    
    calc_data = all_calculations[selected_calc]
    comparison_data = all_comparisons[selected_calc]
    
    st.markdown(f"**그룹:** {calc_data['그룹ID']}")
    st.markdown(f"**연도:** {calc_data['계산연도']}")
    st.markdown(f"**비교 일시:** {comparison_data['비교일시']}")
    
    st.markdown("#### 자산별 최종 세액 선택")
    
    final_selections = {}
    
    for asset_id, asset_calc in calc_data['자산별계산'].items():
        if asset_id in comparison_data['자산별비교']:
            notice = comparison_data['자산별비교'][asset_id]
            
            with st.expander(f"{asset_id} - {asset_calc['자산명']}", expanded=True):
                col1, col2, col3 = st.columns([2, 2, 1])
                
                with col1:
                    st.markdown("**계산값**")
                    st.metric("총세액", f"{asset_calc['총세액']:,.0f}원")
                    st.write(f"- 재산세: {asset_calc['재산세']:,.0f}원")
                    st.write(f"- 도시지역분: {asset_calc['재산세_도시지역분']:,.0f}원")
                    st.write(f"- 지방교육세: {asset_calc['지방교육세']:,.0f}원")
                    st.write(f"- 지역자원시설세: {asset_calc['지역자원시설세']:,.0f}원")
                
                with col2:
                    st.markdown("**고지서값**")
                    st.metric("총세액", f"{notice['총세액']:,.0f}원")
                    st.write(f"- 재산세: {notice['재산세']:,.0f}원")
                    st.write(f"- 도시지역분: {notice['재산세_도시지역분']:,.0f}원")
                    st.write(f"- 지방교육세: {notice['지방교육세']:,.0f}원")
                    st.write(f"- 지역자원시설세: {notice['지역자원시설세']:,.0f}원")
                
                with col3:
                    st.markdown("**선택**")
                    diff = asset_calc['총세액'] - notice['총세액']
                    st.metric("차이", f"{diff:+,.0f}원")
                    
                    choice = st.radio(
                        f"최종값 선택 ({asset_id})",
                        ["계산값", "고지서값"],
                        key=f"final_choice_{asset_id}",
                        label_visibility="collapsed"
                    )
                    
                    final_selections[asset_id] = {
                        "선택": choice,
                        "계산값": asset_calc,
                        "고지서값": notice,
                        "최종값": asset_calc if choice == "계산값" else notice
                    }
    
    st.markdown("---")
    st.markdown("#### 그룹 전체 요약")
    
    total_calc = sum(s['계산값']['총세액'] for s in final_selections.values())
    total_notice = sum(s['고지서값']['총세액'] for s in final_selections.values())
    total_final = sum(s['최종값']['총세액'] for s in final_selections.values())
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("계산값 합계", f"{total_calc:,.0f}원")
    with col2:
        st.metric("고지서값 합계", f"{total_notice:,.0f}원")
    with col3:
        st.metric("최종 확정 합계", f"{total_final:,.0f}원")
    
    st.markdown("---")
    st.markdown("#### 확정 정보")
    
    col1, col2 = st.columns(2)
    
    with col1:
        reason = st.text_area("확정 사유", placeholder="예: 고지서 금액과 일치 확인", key="finalize_reason")
    
    with col2:
        confirmer = st.text_input("확정자", placeholder="담당자명", key="finalize_confirmer")
    
    if st.button("최종 확정 및 저장", type="primary", use_container_width=True, key="finalize_save"):
        if not reason or not confirmer:
            st.error("확정 사유와 확정자를 모두 입력해주세요.")
            return
        
        finalization_data = {
            "고지서금액": total_notice,
            "차이금액": total_calc - total_notice,
            "최종확정값": total_final,
            "확정사유": reason,
            "확정자": confirmer,
            "자산별선택": final_selections
        }
        
        # 1. Phase 3-A 메서드로 통합 저장 (property_tax_calculations)
        success, message = service.calculator.save_calculation_result_with_finalization(
            selected_calc,
            calc_data,
            finalization_data
        )
        
        if success:
            st.success(message)
            
            # 2. JSON 파일 저장
            save_success, save_msg = service.save_calculations_to_json()
            if save_success:
                st.success("계산 결과가 JSON 파일에 저장되었습니다.")
                st.info(f"저장 위치: {service.core.CALCULATIONS_JSON_PATH}")
            else:
                st.warning(f"⚠️ JSON 저장 실패: {save_msg}")
            
            # 3. property_finalizations에도 저장 (Report용) ⭐ 신규 추가
            final_key = selected_calc
            finalize_for_report = {}
            
            for asset_id, selection in final_selections.items():
                chosen_data = selection['최종값']
                finalize_for_report[asset_id] = {
                    "자산ID": asset_id,
                    "자산명": selection['계산값']['자산명'],
                    "자산유형": selection['계산값']['자산유형'],
                    "과세유형": selection['계산값']['과세유형'],
                    "선택": selection['선택'],
                    "재산세": chosen_data['재산세'],
                    "재산세_도시지역분": chosen_data['재산세_도시지역분'],
                    "지방교육세": chosen_data['지방교육세'],
                    "지역자원시설세": chosen_data['지역자원시설세'],
                    "총세액": chosen_data['총세액']
                }
            
            st.session_state.property_finalizations[final_key] = finalize_for_report
            st.success("최종 확정 데이터가 Report에서 사용 가능합니다.")
            
        else:
            st.error(message)

def render_summary():
    """Summary - 통계 및 현황"""
    st.markdown("#### 통계 분석 및 현황")
    
    service = get_property_tax_service()
    statistics = service.get_asset_statistics()
    
    if statistics['총_자산수'] == 0:
        st.info("등록된 자산이 없습니다.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("총 자산 수", f"{statistics['총_자산수']}개")
    
    with col2:
        st.metric("총 시가표준액", f"{statistics['총_시가표준액']:,}원")
    
    with col3:
        st.metric("평균 자산가액", f"{statistics['평균_자산가액']:,}원")
    
    with col4:
        # v1.5.2 호환: '도시지역분별' 또는 '도시지역분별_분포' 모두 지원
        urban_dist = statistics.get('도시지역분별', statistics.get('도시지역분별_분포', {}))
        urban_count = urban_dist.get('Y', 0)
        st.metric("도시지역분 적용", f"{urban_count}개")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # v1.5.2 호환성 처리: 키 이름 변경 대응
        type_dist = statistics.get('자산유형별', statistics.get('자산유형별_분포', {}))
        if type_dist:
            st.markdown("#### 자산유형별 분포")
            type_df = pd.DataFrame(
                list(type_dist.items()),
                columns=['자산유형', '개수']
            )
            st.bar_chart(type_df.set_index('자산유형'))
    
    with col2:
        # v1.5.2 호환성 처리: 키 이름 변경 대응
        taxation_dist = statistics.get('과세유형별', statistics.get('과세유형별_분포', {}))
        if taxation_dist:
            st.markdown("#### 과세유형별 분포")
            taxation_df = pd.DataFrame(
                list(taxation_dist.items()),
                columns=['과세유형', '개수']
            )
            st.bar_chart(taxation_df.set_index('과세유형'))
    
    all_calculations = service.get_all_calculation_results()
    
    if all_calculations:
        st.markdown("#### 계산 결과 요약")
        
        calc_summary = []
        for calc_key, calc_data in all_calculations.items():
            calc_summary.append({
                "그룹": calc_data['그룹ID'],
                "연도": calc_data['계산연도'],
                "자산수": len(calc_data['자산별계산']),
                "총세액": f"{calc_data['총세액']:,.0f}원",
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
    selected_final = st.selectbox(
        "보고서 생성할 확정 결과 선택",
        final_options,
        key="report_final_select"
    )
    
    if selected_final:
        report_type = st.selectbox(
            "보고서 유형",
            ["세액 확정 보고서", "자산별 상세 보고서", "그룹별 요약 보고서"],
            key="report_type_select"
        )
        
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
    
    service = get_property_tax_service()
    
    for asset_id, asset_final in final_data.items():
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
                st.markdown("**확정세액**")
                st.write(f"재산세: {asset_final['재산세']:,.0f}원")
                st.write(f"재산세 도시지역분: {asset_final['재산세_도시지역분']:,.0f}원")
                st.write(f"지방교육세: {asset_final['지방교육세']:,.0f}원")
                st.write(f"지역자원시설세: {asset_final['지역자원시설세']:,.0f}원")
                st.write(f"**총세액: {asset_final['총세액']:,.0f}원**")
                st.write(f"선택기준: {asset_final['선택']}")

# ============================================================================
# 📌 메인 함수
# ============================================================================

def main():
    """메인 함수"""
    page_header("재산세 관리", "")
    
    from components.local_tax_tabs import render_local_tax_tabs
    render_local_tax_tabs("재산세")
    
    with st.sidebar:
        sidebar_menu()
    
    initialize_property_tax_data()
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        render_asset_master_list()
    
    with col2:
        render_tax_rate_management()
    
    render_integrated_calculation_workflow()
    
    st.markdown("---")
    
    service = get_property_tax_service()
    statistics = service.get_asset_statistics()
    
    st.markdown(f"""
    <div style="text-align: center; color: #6b7280; font-size: 0.8rem; padding: 1rem 0;">
        <em>TAXi 지방세 관리 시스템 - 재산세 v1.4.2 | 
        {datetime.now().strftime('%Y-%m-%d %H:%M')} | 
        총 자산: {statistics['총_자산수']}개 | 
        도시지역분 적용: {statistics.get('도시지역분별', statistics.get('도시지역분별_분포', {})).get('Y', 0)}개</em>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
