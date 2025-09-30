# pages/31_Treaty_Search.py
"""조세조약 검색 페이지"""

import streamlit as st
from pathlib import Path
import sys

# 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from utils.treaty.constants import TREATY_COUNTRIES, COUNTRY_REGIONS
from utils.treaty.processor import TreatyPDFProcessor, TreatySearchEngine
from utils.treaty.data import TreatyDataManager
from components.auth_widget import check_auth
from components.theme import apply_custom_theme
from utils.auth import is_guest, check_permission

# 기본 페이지 네비게이션만 숨기고, 커스텀 메뉴는 살리기
st.markdown("""
<style>
/* Streamlit 기본 네비게이션만 숨기기 */
[data-testid="stSidebarNav"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# 인증 체크
if not check_auth():
    st.warning("로그인이 필요합니다.")
    st.stop()

# 페이지 설정
st.set_page_config(
    page_title="국제조세 관리",
    page_icon="",
    layout="wide"
)
# 인증 체크
if not check_auth():
    st.warning("로그인이 필요합니다.")
    st.stop()

# 사이드바 메뉴 렌더링 추가
from components.layout import sidebar_menu
with st.sidebar:
    sidebar_menu()

# 스타일 로드 후에
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

# 초기화
if "treaty_processor" not in st.session_state:
    st.session_state.treaty_processor = TreatyPDFProcessor()
if "treaty_search" not in st.session_state:
    st.session_state.treaty_search = TreatySearchEngine()
if "treaty_data" not in st.session_state:
    st.session_state.treaty_data = TreatyDataManager()

# 헤더
st.markdown("""
<div class="page-header">
    <div class="header-content">
        <div class="header-left">
            <span class="page-icon"></span>
            <h1 class="page-title">조세조약 검색</h1>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

from components.international_tax_tabs import render_international_tax_tabs
render_international_tax_tabs("조세조약")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["🔍 검색", " 업로드", " 관리"])

# ===== 탭 1: 검색 =====
with tab1:
    st.markdown("### 조세조약 검색")
    
    # 검색 범위 선택
    col1, col2 = st.columns([1, 3])
    
    with col1:
        search_scope = st.radio(
            "검색 범위",
            ["전체 국가", "특정 국가 선택"],
            help="전체 국가를 검색하거나 특정 국가만 선택할 수 있습니다"
        )
    
    with col2:
        # 특정 국가 선택 시에만 표시
        if search_scope == "특정 국가 선택":
            available_countries = st.session_state.treaty_data.get_available_countries()
            
            # 지역별 빠른 선택
            st.markdown("**빠른 선택:**")
            region_cols = st.columns(len(COUNTRY_REGIONS))
            
            for idx, (region, countries) in enumerate(COUNTRY_REGIONS.items()):
                with region_cols[idx]:
                    if st.button(f"{region}", key=f"region_{region}"):
                        # 해당 지역 중 등록된 국가만 선택
                        region_available = [c for c in countries if c in available_countries]
                        st.session_state.selected_countries = region_available
            
            # 국가 선택
            selected_countries = st.multiselect(
                "국가 선택 (입력하여 검색 가능)",
                options=sorted(available_countries),
                default=st.session_state.get("selected_countries", []),
                help="여러 국가를 선택할 수 있습니다"
            )
            st.session_state.selected_countries = selected_countries
        else:
            selected_countries = st.session_state.treaty_data.get_available_countries()
    
    # 검색어 입력
    keyword = st.text_input(
        "🔍 검색어",
        placeholder="예: 고정사업장, 배당, 이자, 사용료",
        help="조약 내용에서 검색할 키워드를 입력하세요"
    )
    
    # 검색 버튼
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        search_btn = st.button("🔍 검색하기", type="primary", use_container_width=True)
    with col2:
        if st.button(" 초기화", use_container_width=True):
            st.session_state.selected_countries = []
            st.rerun()
    
    # 검색 실행 - 결과를 세션에 저장
    if search_btn and keyword:
        with st.spinner("검색 중..."):
            results = st.session_state.treaty_search.search(
                keyword=keyword,
                countries=selected_countries if search_scope == "특정 국가 선택" else None,
                search_in_articles=True
            )
            # 세션에 저장 (핵심!)
            st.session_state.search_results = results
            st.session_state.search_keyword = keyword

    # 검색 결과 표시 - 세션에서 가져오기
    if "search_results" in st.session_state and st.session_state.search_results:
        results = st.session_state.search_results
        
        # 결과 표시
        st.markdown("---")
        
        if not results:
            st.info("검색 결과가 없습니다.")
        else:
            total_matches = sum(r["match_count"] for r in results)
            
            st.success(f"**검색 결과: {len(results)}개 국가, 총 {total_matches}건**")
            
            # 국가별 결과 표시
            for result in results:
                    country = result["country"]
                    matches = result["matches"]
                    
                    # 국가별 확장 패널
                    with st.expander(f" **{country}** ({result['match_count']}건)", expanded=True):
                        st.caption(f" 파일: {result['filename']} | 총 {result['total_pages']}페이지")
                        
                        # 매칭된 조항 표시
                        for idx, match in enumerate(matches, 1):
                            if match["type"] == "article":
                                # 고유 키 생성
                                article_key = f"{country}_{match['article_num']}_{idx}"
                                
                                # 조항 요약 카드
                                col1, col2 = st.columns([5, 1])
                                
                                with col1:
                                    st.markdown(f"""
                                    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid var(--gold);">
                                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                                            <strong style="color: var(--gray-900); font-size: 1rem;">
                                                제{match['article_num']}조 {match['article_title']}
                                            </strong>
                                            <span style="font-size: 0.85rem; color: var(--gray-500);">
                                                📍 {match['page']}페이지
                                            </span>
                                        </div>
                                        <div style="background: white; padding: 0.75rem; border-radius: 4px; margin-top: 0.5rem;">
                                            {match['highlighted']}
                                        </div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                with col2:
                                    # 전문보기 버튼
                                    if st.button(" 전문보기", key=f"view_{article_key}", use_container_width=True):
                                        # 세션 상태에 저장
                                        st.session_state[f"show_full_{article_key}"] = True
                                
                                # 전문 표시 (토글)
                                if st.session_state.get(f"show_full_{article_key}", False):
                                    keyword = st.session_state.get("search_keyword", "")
                                    
                                    # 키워드 하이라이트 처리 및 앵커 추가
                                    import re
                                    
                                    # 첫 번째 키워드에만 앵커 추가
                                    counter = {'count': 0}  # 딕셔너리로 카운터 사용
                                    
                                    def highlight_keyword(match_obj):
                                        counter['count'] += 1
                                        if counter['count'] == 1:
                                            return f'<span id="keyword_{article_key}" style="background: #FFD700; padding: 2px 4px; border-radius: 3px; font-weight: 600;">{match_obj.group(1)}</span>'
                                        else:
                                            return f'<span style="background: #FFEB3B; padding: 2px 4px; border-radius: 3px;">{match_obj.group(1)}</span>'
                                    
                                    content_with_highlight = re.sub(
                                        f'({re.escape(keyword)})',
                                        highlight_keyword,
                                        match['content'],
                                        flags=re.IGNORECASE
                                    )
                                    
                                    # 포맷팅 적용
                                    formatted_content = st.session_state.treaty_search.format_article_content(content_with_highlight)
                                    
                                    with st.container():
                                        st.markdown(f"""
                                        <div style="background: white; border: 2px solid var(--gold); border-radius: 8px; padding: 1.5rem; margin-bottom: 1rem;">
                                            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; border-bottom: 2px solid var(--gold); padding-bottom: 0.5rem;">
                                                <h4 style="margin: 0; color: var(--gray-900);">
                                                    {country} 조세조약 제{match['article_num']}조 - {match['article_title']}
                                                </h4>
                                            </div>
                                            <div id="content_{article_key}" style="
                                                max-height: 500px; 
                                                overflow-y: auto; 
                                                line-height: 2.0; 
                                                color: var(--gray-900); 
                                                white-space: pre-wrap; 
                                                font-size: 0.95rem;
                                                padding: 1rem;
                                                background: #f9fafb;
                                                border-radius: 4px;
                                            ">
                                                {formatted_content}
                                            </div>
                                        </div>
                                        
                                        <script>
                                        // 키워드 위치로 자동 스크롤
                                        setTimeout(function() {{
                                            var keyword = document.getElementById('keyword_{article_key}');
                                            var container = document.getElementById('content_{article_key}');
                                            if (keyword && container) {{
                                                var keywordTop = keyword.offsetTop;
                                                var containerHeight = container.clientHeight;
                                                container.scrollTop = keywordTop - (containerHeight / 3);
                                            }}
                                        }}, 100);
                                        </script>
                                        """, unsafe_allow_html=True)
                                        
                                        # 닫기 버튼
                                        if st.button("닫기", key=f"close_{article_key}"):
                                            st.session_state[f"show_full_{article_key}"] = False
                                            st.rerun()

with tab2:
    st.markdown("### 조세조약 PDF 업로드")
    
    # 업로드 방식 선택
    upload_mode = st.radio(
        "업로드 방식",
        ["개별 업로드", "일괄 업로드"],
        horizontal=True,
        help="개별: 한 국가씩 선택 / 일괄: 여러 파일 한번에 업로드"
    )
    
    if upload_mode == "개별 업로드":
        # 기존 개별 업로드 로직
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_country = st.selectbox(
                "국가 선택",
                options=[""] + sorted(TREATY_COUNTRIES),
                help="조세조약을 체결한 국가를 선택하세요"
            )
            
            uploaded_file = st.file_uploader(
                "조세조약 PDF 파일 업로드",
                type=["pdf"],
                help="해당 국가와 체결한 조세조약 PDF 파일을 업로드하세요",
                disabled=is_guest()
            )
            
            if st.button(" 업로드 및 처리", type="primary", disabled=not (selected_country and uploaded_file) or is_guest()):
                if check_permission("조약 업로드"):
                    if selected_country and uploaded_file:
                        with st.spinner(f"{selected_country} 조약 처리 중..."):
                            try:
                                pdf_path = st.session_state.treaty_processor.save_pdf(
                                    uploaded_file, 
                                    selected_country
                                )
                                
                                success = st.session_state.treaty_processor.process_and_save(
                                    pdf_path, 
                                    selected_country
                                )
                                
                                if success:
                                    st.success(f" {selected_country} 조약이 성공적으로 등록되었습니다!")
                                    st.balloons()
                                else:
                                    st.error("처리 중 오류가 발생했습니다.")
                            
                            except Exception as e:
                                st.error(f"오류 발생: {e}")
        
        with col2:
            st.info("""
            **업로드 가이드**
            
            1. 국가를 선택합니다
            2. 해당 국가 조세조약 PDF를 업로드합니다
            3. 자동으로 텍스트가 추출되고 조항별로 분류됩니다
            4. 검색 탭에서 바로 검색 가능합니다
            """)
    
    else:  # 일괄 업로드
        st.info("""
        **일괄 업로드 가이드**
        
        - 파일명 형식: `조세조약조문_국가명.pdf` 또는 `국가명_treaty.pdf`
        - 예시: `조세조약조문_미국.pdf`, `조세조약조문_중국.pdf`
        - 여러 파일을 한번에 선택하여 업로드할 수 있습니다
        - 파일명에서 국가명을 자동으로 인식합니다
        """)
        
        # 여러 파일 업로드
        uploaded_files = st.file_uploader(
            "조세조약 PDF 파일들 업로드 (여러 개 선택 가능)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Ctrl/Cmd 키를 누른 채로 여러 파일 선택",
            disabled=is_guest()
        )
                
        if uploaded_files:
            st.write(f"**선택된 파일: {len(uploaded_files)}개**")
            
            # 파일명에서 국가명 추출 미리보기
            import re
            file_info = []
            
            for file in uploaded_files:
                filename = file.name
                
                # 패턴 1: 조세조약조문_국가명.pdf
                match1 = re.search(r'조세조약조문[_\s]*([가-힣]+)', filename)
                # 패턴 2: 국가명_treaty.pdf
                match2 = re.search(r'^([가-힣]+)[_\s]*treaty', filename)
                # 패턴 3: 국가명.pdf (단순)
                match3 = re.search(r'^([가-힣]+)\.pdf$', filename)
                
                if match1:
                    country = match1.group(1)
                elif match2:
                    country = match2.group(1)
                elif match3:
                    country = match3.group(1)
                else:
                    country = None
                
                # 국가명이 리스트에 있는지 확인
                if country and country in TREATY_COUNTRIES:
                    status = " 인식됨"
                    color = "green"
                elif country:
                    status = f" 미등록 국가"
                    color = "orange"
                else:
                    status = " 인식 실패"
                    color = "red"
                
                file_info.append({
                    "filename": filename,
                    "country": country or "알 수 없음",
                    "status": status,
                    "file": file
                })
            
            # 테이블로 표시
            st.markdown("#### 인식 결과")
            for info in file_info:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.text(info["filename"])
                with col2:
                    st.text(info["country"])
                with col3:
                    st.markdown(info["status"])
            
            st.markdown("---")
            
            # 일괄 처리 버튼
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button(" 일괄 업로드 및 처리", type="primary", use_container_width=True, disabled=is_guest()):
                    if check_permission("일괄 업로드"):
                        # 인식 성공한 파일만 처리
                        valid_files = [f for f in file_info if f["country"] in TREATY_COUNTRIES]
                        
                        if not valid_files:
                            st.error("처리 가능한 파일이 없습니다.")
                        else:
                            progress_bar = st.progress(0)
                            status_text = st.empty()
                            
                            success_count = 0
                            fail_count = 0
                            
                            for idx, info in enumerate(valid_files):
                                country = info["country"]
                                file = info["file"]
                                
                                status_text.text(f"처리 중: {country} ({idx+1}/{len(valid_files)})")
                                
                                try:
                                    # PDF 저장
                                    pdf_path = st.session_state.treaty_processor.save_pdf(file, country)
                                    
                                    # 처리 및 저장
                                    success = st.session_state.treaty_processor.process_and_save(
                                        pdf_path, 
                                        country
                                    )
                                    
                                    if success:
                                        success_count += 1
                                    else:
                                        fail_count += 1
                                
                                except Exception as e:
                                    st.error(f"{country} 처리 실패: {e}")
                                    fail_count += 1
                                
                                # 진행률 업데이트
                                progress_bar.progress((idx + 1) / len(valid_files))
                            
                            status_text.empty()
                            progress_bar.empty()
                            
                            # 결과 표시
                            if success_count > 0:
                                st.success(f" {success_count}개 조약 등록 완료!")
                                st.balloons()
                            if fail_count > 0:
                                st.warning(f" {fail_count}개 파일 처리 실패")

# ===== 탭 3: 관리 =====
with tab3:
    st.markdown("### 등록된 조세조약 관리")
    
    # 통계 정보
    stats = st.session_state.treaty_data.get_treaty_stats()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("등록된 국가", f"{stats['total_countries']}개")
    with col2:
        st.metric("전체 조약 국가", f"{len(TREATY_COUNTRIES)}개")
    with col3:
        if stats['last_updated']:
            from datetime import datetime
            last_update = datetime.fromisoformat(stats['last_updated'])
            st.metric("최근 업데이트", last_update.strftime("%Y-%m-%d"))
    
    st.markdown("---")
    
    # 등록된 조약 목록
    available_countries = st.session_state.treaty_data.get_available_countries()
    
    if not available_countries:
        st.info("등록된 조세조약이 없습니다. 업로드 탭에서 PDF를 업로드해주세요.")
    else:
        st.markdown("#### 등록된 조약 목록")
        
        # 국가별 카드 형태로 표시
        cols_per_row = 3
        for i in range(0, len(available_countries), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for idx, country in enumerate(available_countries[i:i+cols_per_row]):
                with cols[idx]:
                    # 조약 데이터 로드
                    treaty_data = st.session_state.treaty_data.load_treaty_data(country)
                    
                    if treaty_data:
                        article_count = len(treaty_data.get("articles", []))
                        page_count = treaty_data.get("total_pages", 0)
                        
                        st.markdown(f"""
                        <div style="background: white; padding: 1rem; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 1rem;">
                            <h4 style="margin: 0 0 0.5rem 0; color: var(--gray-900);"> {country}</h4>
                            <p style="font-size: 0.85rem; color: var(--gray-500); margin: 0.25rem 0;">
                                 {page_count}페이지<br>
                                 {article_count}개 조항
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 삭제 버튼
                        if st.button(f" 삭제", key=f"delete_{country}", use_container_width=True, disabled=is_guest()):
                            if check_permission("조약 삭제"):
                                if st.session_state.treaty_data.delete_treaty(country):
                                    st.success(f"{country} 조약이 삭제되었습니다.")
                                    st.rerun()
                                else:
                                    st.error("삭제 실패")
        
        # 전체 삭제 버튼
        st.markdown("---")
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button(" 전체 삭제", type="secondary", use_container_width=True, disabled=is_guest()):
                if check_permission("전체 삭제"):
                    if st.checkbox("정말 모든 조약을 삭제하시겠습니까?"):
                        for country in available_countries:
                            st.session_state.treaty_data.delete_treaty(country)
                        st.success("모든 조약이 삭제되었습니다.")
                        st.rerun()