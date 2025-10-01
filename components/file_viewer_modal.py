"""
파일 뷰어 모달 컴포넌트
엑셀/PDF 원본 파일을 모달로 표시
"""

import streamlit as st
from pathlib import Path
import pandas as pd
from pdf2image import convert_from_path
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)


def show_file_viewer_modal(excel_path: str = None, pdf_path: str = None):
    """
    파일 뷰어 모달 표시
    
    Args:
        excel_path: 엑셀 파일 경로
        pdf_path: PDF 파일 경로
    """
    
    # 모달 열기 버튼
    if st.button("📄 서식 원본 보기", key="open_file_viewer"):
        st.session_state['show_file_viewer'] = True
    
    # 모달 표시
    if st.session_state.get('show_file_viewer', False):
        with st.container():
            st.markdown("---")
            
            # 헤더
            col1, col2 = st.columns([6, 1])
            with col1:
                st.markdown("### 📄 신고서식 원본")
            with col2:
                if st.button("✕ 닫기", key="close_file_viewer"):
                    st.session_state['show_file_viewer'] = False
                    st.rerun()
            
            # 파일이 둘 다 있으면 탭으로 표시
            if excel_path and pdf_path:
                tab1, tab2 = st.tabs(["📊 엑셀 파일", "📑 PDF 파일"])
                
                with tab1:
                    _show_excel_viewer(excel_path)
                
                with tab2:
                    _show_pdf_viewer(pdf_path)
            
            # 엑셀만 있는 경우
            elif excel_path:
                _show_excel_viewer(excel_path)
            
            # PDF만 있는 경우
            elif pdf_path:
                _show_pdf_viewer(pdf_path)
            
            else:
                st.warning("표시할 파일이 없습니다.")
            
            st.markdown("---")


def _show_excel_viewer(file_path: str):
    """
    엑셀 파일 뷰어
    
    Args:
        file_path: 엑셀 파일 경로
    """
    try:
        if not Path(file_path).exists():
            st.error(f"파일을 찾을 수 없습니다: {file_path}")
            return
        
        # 다운로드 버튼
        with open(file_path, 'rb') as f:
            st.download_button(
                label="⬇️ 엑셀 파일 다운로드",
                data=f,
                file_name=Path(file_path).name,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        
        st.markdown("#### 📊 데이터 미리보기")
        
        # 엑셀 파일 읽기 (모든 시트)
        excel_file = pd.ExcelFile(file_path)
        
        if len(excel_file.sheet_names) > 1:
            # 여러 시트가 있으면 선택
            selected_sheet = st.selectbox(
                "시트 선택",
                excel_file.sheet_names,
                key="excel_sheet_selector"
            )
        else:
            selected_sheet = excel_file.sheet_names[0]
        
        # 데이터 읽기
        df = pd.read_excel(file_path, sheet_name=selected_sheet, header=None)
        
        # 중요 셀 하이라이트 옵션
        highlight = st.checkbox("중요 셀 하이라이트 (E43, K51, K53, K54, F110, F111, F115)", 
                               value=True, key="excel_highlight")
        
        if highlight:
            st.info("💡 노란색 셀: 원천세 데이터 추출 위치")
        
        # DataFrame 표시 (스타일 적용)
        if highlight:
            # 하이라이트할 셀 좌표 (0-based index)
            highlight_cells = [
                (42, 4),   # E43
                (50, 10),  # K51
                (52, 10),  # K53
                (53, 10),  # K54
                (109, 5),  # F110
                (110, 5),  # F111
                (114, 5),  # F115
            ]
            
            def highlight_important_cells(row):
                styles = [''] * len(row)
                row_idx = row.name
                for cell_row, cell_col in highlight_cells:
                    if row_idx == cell_row and cell_col < len(styles):
                        styles[cell_col] = 'background-color: #FFEB3B; font-weight: bold;'
                return styles
            
            styled_df = df.style.apply(highlight_important_cells, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=600)
        else:
            st.dataframe(df, use_container_width=True, height=600)
        
        # 메타 정보
        with st.expander("📋 파일 정보"):
            st.write(f"**파일명**: {Path(file_path).name}")
            st.write(f"**시트 수**: {len(excel_file.sheet_names)}")
            st.write(f"**행 수**: {len(df)}")
            st.write(f"**열 수**: {len(df.columns)}")
        
    except Exception as e:
        logger.error(f"엑셀 뷰어 오류: {str(e)}")
        st.error(f"엑셀 파일을 표시할 수 없습니다: {str(e)}")


def _show_pdf_viewer(file_path: str):
    """
    PDF 파일 뷰어
    
    Args:
        file_path: PDF 파일 경로
    """
    try:
        if not Path(file_path).exists():
            st.error(f"파일을 찾을 수 없습니다: {file_path}")
            return
        
        # 다운로드 버튼
        with open(file_path, 'rb') as f:
            st.download_button(
                label="⬇️ PDF 파일 다운로드",
                data=f,
                file_name=Path(file_path).name,
                mime="application/pdf"
            )
        
        st.markdown("#### 📑 PDF 미리보기")
        
        # PDF를 이미지로 변환
        with st.spinner("PDF를 불러오는 중..."):
            try:
                images = convert_from_path(file_path, dpi=150)
            except Exception as e:
                # pdf2image가 없는 경우 대체 방법
                st.warning("PDF 미리보기를 사용할 수 없습니다. 다운로드 후 확인해주세요.")
                logger.error(f"PDF 변환 실패: {str(e)}")
                return
        
        # 페이지 선택
        if len(images) > 1:
            page_num = st.selectbox(
                "페이지 선택",
                range(1, len(images) + 1),
                format_func=lambda x: f"{x} / {len(images)}",
                key="pdf_page_selector"
            )
            page_idx = page_num - 1
        else:
            page_idx = 0
        
        # 확대/축소 옵션
        zoom = st.slider("확대/축소", min_value=50, max_value=200, value=100, step=10, key="pdf_zoom")
        
        # 이미지 표시
        image = images[page_idx]
        
        # 확대/축소 적용
        if zoom != 100:
            new_width = int(image.width * zoom / 100)
            new_height = int(image.height * zoom / 100)
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        st.image(image, use_container_width=True)
        
        # 메타 정보
        with st.expander("📋 파일 정보"):
            st.write(f"**파일명**: {Path(file_path).name}")
            st.write(f"**페이지 수**: {len(images)}")
            st.write(f"**현재 페이지**: {page_idx + 1}")
        
        # A99 항목 안내
        st.info("💡 원천세 금액은 'A99' 항목의 맨 끝 숫자에서 추출됩니다.")
        
    except Exception as e:
        logger.error(f"PDF 뷰어 오류: {str(e)}")
        st.error(f"PDF 파일을 표시할 수 없습니다: {str(e)}")


def show_compact_file_viewer(record: dict):
    """
    간단한 파일 뷰어 (버튼만)
    
    Args:
        record: 세금 기록 딕셔너리
    """
    excel_path = record.get('excel_file')
    pdf_path = record.get('pdf_file')
    
    if not excel_path and not pdf_path:
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        if excel_path and Path(excel_path).exists():
            with open(excel_path, 'rb') as f:
                st.download_button(
                    label="📊 엑셀 다운로드",
                    data=f,
                    file_name=Path(excel_path).name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_excel_{record.get('id', 'unknown')}"
                )
    
    with col2:
        if pdf_path and Path(pdf_path).exists():
            with open(pdf_path, 'rb') as f:
                st.download_button(
                    label="📑 PDF 다운로드",
                    data=f,
                    file_name=Path(pdf_path).name,
                    mime="application/pdf",
                    key=f"download_pdf_{record.get('id', 'unknown')}"
                )
