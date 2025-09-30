"""
TAXi - 원천세 탭 구성 컴포넌트 (법인세와 동일한 구조)
"""

import streamlit as st

def render_withholding_tax_tabs(current_page):
    """원천세 관리 탭 헤더 렌더링 - 순수 Streamlit 컴포넌트"""
    
    # 탭 정보 정의
    tab_info = {
        "이행상황신고서": {
            "icon": "",
            "page": "pages/withholding_salary.py"
        },
        "외국납부세액공제": {
            "icon": "", 
            "page": "pages/withholding_foreign_tax.py"
        },
        "지급명세서": {
            "icon": "",
            "page": "pages/withholding_payment_list.py"
        }
    }
    
    # 탭 헤더를 컬럼으로 구현
    st.markdown("#### 원천세 관리")
    
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

def render_withholding_tax_tabs_simple(current_page):
    """더 간단한 버전의 탭 헤더"""
    
    tab_buttons = [
        ("이행상황신고서", "", "pages/withholding_salary.py"),
        ("외국납부세액공제", "", "pages/withholding_foreign_tax.py"),
        ("지급명세서", "", "pages/withholding_payment_list.py")
    ]
    
    st.subheader("원천세 관리")
    
    # 탭 버튼들을 한 줄로 배치
    cols = st.columns(len(tab_buttons))
    
    for i, (name, icon, page) in enumerate(tab_buttons):
        with cols[i]:
            if name == current_page:
                # 현재 페이지는 강조 표시만
                st.success(f"{icon} {name}")
            else:
                # 다른 페이지는 버튼으로 표시
                if st.button(f"{icon} {name}", key=f"nav_{i}", use_container_width=True):
                    st.switch_page(page)
    
    st.divider()