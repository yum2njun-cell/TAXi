import streamlit as st

def render_vat_tabs(current_page):
    """부가세 관리 탭 헤더 렌더링 - 순수 Streamlit 컴포넌트"""
    
    # 탭 정보 정의
    tab_info = {
        "외화획득명세서": {
            "icon": "",
            "page": "pages/foreign_currency.py"  # 수정된 경로
        },
        "법인카드 공제 여부 확인": {
            "icon": "",
            "page": "pages/card_deduction.py"
        },
        # 추가 부가세 서브메뉴들이 있다면 여기에 추가
        # "세금계산서 관리": {
        #     "icon": "🧾",
        #     "page": "pages/22_Tax_Invoice.py"
        # },
    }
    
    # 탭 헤더를 컬럼으로 구현
    st.markdown("#### 부가세 관리")
    
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
                    key=f"vat_tab_{tab_name}",
                    use_container_width=True,
                    help=f"{tab_name} 페이지로 이동"
                ):
                    st.switch_page(tab_data["page"])
    
    st.markdown("---")

def render_vat_tabs_simple(current_page):
    """더 간단한 버전의 부가세 탭 헤더"""
    
    tab_buttons = [
        ("외화획득명세서", "", "pages/foreign_currency.py"),  # 수정된 경로
        ("법인카드 공제 여부 확인", "", "pages/card_deduction.py"),
        # ("매입매출 관리", "📊", "pages/23_Purchase_Sales.py")
    ]
    
    st.subheader("부가세 관리")
    
    # 탭 버튼들을 한 줄로 배치
    cols = st.columns(len(tab_buttons))
    
    for i, (name, icon, page) in enumerate(tab_buttons):
        with cols[i]:
            if name == current_page:
                st.markdown(f"""
                <div class="current-tab-highlight">
                    {icon} {name}
                </div>
                """, unsafe_allow_html=True)
            else:
                # 다른 페이지는 버튼으로 표시
                if st.button(f"{icon} {name}", key=f"vat_nav_{i}", use_container_width=True):
                    st.switch_page(page)
    
    st.divider()

def render_vat_single_tab(current_page):
    """단일 탭만 있을 때 사용하는 간단한 헤더"""
    st.markdown("#### 부가세 관리")
    
    st.markdown(f"""
    <div style="
        background: var(--gold); 
        color: var(--gray-900); 
        padding: 0.75rem; 
        text-align: center; 
        border-radius: 8px;
        font-weight: 600;
        border: 2px solid var(--gold-600);
        margin-bottom: 1rem;
        max-width: 300px;
    ">
         {current_page}
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")