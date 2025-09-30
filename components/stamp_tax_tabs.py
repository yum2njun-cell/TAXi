"""
인지세 관리 탭 컴포넌트
"""
import streamlit as st


def render_stamp_tax_tabs(current_page):
    """인지세 관리 탭 헤더 렌더링"""
    
    tab_info = {
        "인지세 관리": {
            "page": "pages/stamp_management.py"
        }
    }
    
    st.subheader("인지세 관리")
    
    cols = st.columns(len(tab_info))
    
    for i, (tab_name, tab_data) in enumerate(tab_info.items()):
        with cols[i]:
            if tab_name == current_page:
                st.markdown(f"""
                <div class="current-tab-highlight">
                    {tab_name}
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(
                    tab_name, 
                    key=f"stamp_tab_{tab_name}",
                    use_container_width=True
                ):
                    st.switch_page(tab_data["page"])
    
    st.divider()