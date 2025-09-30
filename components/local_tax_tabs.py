import streamlit as st

def render_local_tax_tabs(current_page):
    """지방세 관리 탭 헤더 렌더링 - 순수 Streamlit 컴포넌트"""
    
    # 탭 정보 정의
    tab_info = {
        "재산세": {
            "icon": "",
            "page": "pages/local_tax_property.py"
        },
        "취득세": {
            "icon": "", 
            "page": "pages/41_지방세_취득세.py"
        },
        "증권거래세": {
            "icon": "",
            "page": "pages/42_지방세_증권거래세.py"
        },
        "자동차세": {
            "icon": "",
            "page": "pages/43_지방세_자동차세.py"
        }
    }
    
    # 탭 헤더를 컬럼으로 구현
    st.markdown("#### 지방세 관리")
    
    cols = st.columns(len(tab_info))
    
    for i, (tab_name, tab_data) in enumerate(tab_info.items()):
        with cols[i]:
            # 현재 탭이면 비활성화된 상태로 표시
            if tab_name == current_page:
                st.markdown(f"""
                <div style="
                    background: var(--gold); 
                    color: var(--gray-900); 
                    padding: 0.75rem; 
                    text-align: center; 
                    border-radius: 8px;
                    font-weight: 600;
                    border: 2px solid var(--gold-600);
                    margin-bottom: 0.5rem;
                ">
                    {tab_data['icon']} {tab_name}
                </div>
                """, unsafe_allow_html=True)
            else:
                # 다른 탭은 클릭 가능한 버튼
                if st.button(
                    f"{tab_data['icon']} {tab_name}", 
                    key=f"tab_{tab_name}",
                    use_container_width=True,
                    help=f"{tab_name} 페이지로 이동"
                ):
                    st.switch_page(tab_data["page"])
    
    st.markdown("---")

def render_local_tax_tabs_simple(current_page):
    """더 간단한 버전의 지방세 탭 헤더"""
    
    tab_buttons = [
        ("재산세", "", "pages/40_지방세_재산세.py"),
        ("취득세", "", "pages/41_지방세_취득세.py"),
        ("증권거래세", "", "pages/42_지방세_증권거래세.py"),
        ("자동차세", "", "pages/43_지방세_자동차세.py")
    ]
    
    st.subheader("지방세 관리")
    
    # 탭 버튼들을 한 줄로 배치
    cols = st.columns(len(tab_buttons))
    
    for i, (name, icon, page) in enumerate(tab_buttons):
        with cols[i]:
            if name in current_page or current_page == name:
                st.markdown(f"""
                <div class="current-tab-highlight" style="
                    background: var(--gold); 
                    color: var(--gray-900); 
                    padding: 0.75rem; 
                    text-align: center; 
                    border-radius: 8px;
                    font-weight: 600;
                    border: 2px solid var(--gold-600);
                    margin-bottom: 0.5rem;
                ">
                    {icon} {name}
                </div>
                """, unsafe_allow_html=True)
            else:
                # 다른 페이지는 버튼으로 표시
                if st.button(f"{icon} {name}", key=f"local_tax_nav_{i}", use_container_width=True):
                    st.switch_page(page)
    
    st.divider()

def render_property_tax_status():
    """재산세 현황 요약 (탭 헤더 하단에 표시)"""
    from services.property_tax_service import PropertyTaxService
    
    try:
        service = PropertyTaxService()
        statistics = service.get_asset_statistics()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="총 자산",
                value=f"{statistics['총_자산수']}개",
                help="등록된 총 자산 수"
            )
        
        with col2:
            st.metric(
                label="총 시가표준액",
                value=f"{statistics['총_시가표준액']:,.0f}원",
                help="모든 자산의 시가표준액 합계"
            )
        
        with col3:
            urban_count = statistics['도시지역분별_분포'].get('Y', 0)
            st.metric(
                label="도시지역분 적용",
                value=f"{urban_count}개",
                help="재산세 도시지역분이 적용되는 자산 수"
            )
        
        with col4:
            if statistics['총_자산수'] > 0:
                avg_value = statistics['평균_자산가액']
                st.metric(
                    label="평균 자산가액",
                    value=f"{avg_value:,.0f}원",
                    help="자산별 평균 시가표준액"
                )
            else:
                st.metric(
                    label="평균 자산가액",
                    value="0원",
                    help="등록된 자산이 없습니다"
                )
        
    except Exception as e:
        st.error(f"현황 조회 중 오류: {str(e)}")

def render_local_tax_navigation():
    """지방세 전체 네비게이션 (메인 페이지용)"""
    
    st.markdown("###  지방세 관리")
    
    # 주요 기능 카드
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown("""
            <div class="action-card">
                <div class="action-icon"></div>
                <h4>재산세 관리</h4>
                <p>부동산 재산세 계산 및 관리</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("재산세 바로가기", key="nav_property_tax", use_container_width=True):
                st.switch_page("pages/40_지방세_재산세.py")
    
    with col2:
        with st.container():
            st.markdown("""
            <div class="action-card">
                <div class="action-icon"></div>
                <h4>취득세 관리</h4>
                <p>부동산 취득세 계산 및 관리</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("취득세 바로가기", key="nav_acquisition_tax", use_container_width=True, disabled=True):
                st.info("취득세 기능은 준비 중입니다.")
    
    # 추가 기능들
    st.markdown("#### 기타 지방세")
    
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button(" 증권거래세", key="nav_securities_tax", use_container_width=True, disabled=True):
            st.info("증권거래세 기능은 준비 중입니다.")
    
    with col4:
        if st.button(" 자동차세", key="nav_automobile_tax", use_container_width=True, disabled=True):
            st.info("자동차세 기능은 준비 중입니다.")
