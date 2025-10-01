"""
원천세 신고서 파싱 유틸리티
- 엑셀: E43, K51+K53+K54, F110+F111+F115
- PDF: A99 행의 맨 끝 숫자
"""

import pandas as pd
import PyPDF2
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class WithholdingTaxParser:
    """원천세 신고서 파서"""
    
    def __init__(self):
        self.logger = logger
    
    def parse_excel(self, file_path: str) -> Dict[str, Any]:
        """
        엑셀 파일에서 원천세 데이터 추출
        
        Args:
            file_path: 엑셀 파일 경로
            
        Returns:
            {
                'success': bool,
                'data': {
                    'withholding_tax': float,      # 원천세 (E43)
                    'local_income_tax': float,     # 지방소득세 (K51+K53+K54)
                    'resident_tax': float          # 주민세종업원분 (F110+F111+F115)
                },
                'error': str (optional)
            }
        """
        try:
            # 엑셀 파일 읽기 (헤더 없이)
            df = pd.read_excel(file_path, header=None)
            
            # 값 추출 (인덱스는 0부터 시작하므로 -1)
            withholding_tax = self._safe_get_value(df, 42, 4)  # E43 (row=42, col=4)
            
            # 지방소득세: K51 + K53 + K54
            k51 = self._safe_get_value(df, 50, 10)  # K51
            k53 = self._safe_get_value(df, 52, 10)  # K53
            k54 = self._safe_get_value(df, 53, 10)  # K54
            local_income_tax = k51 + k53 + k54
            
            # 주민세종업원분: F110 + F111 + F115
            f110 = self._safe_get_value(df, 109, 5)  # F110
            f111 = self._safe_get_value(df, 110, 5)  # F111
            f115 = self._safe_get_value(df, 114, 5)  # F115
            resident_tax = f110 + f111 + f115
            
            result = {
                'success': True,
                'data': {
                    'withholding_tax': withholding_tax,
                    'local_income_tax': local_income_tax,
                    'resident_tax': resident_tax,
                    'total': withholding_tax + local_income_tax + resident_tax
                },
                'source': 'excel',
                'cells': {
                    'withholding_tax': 'E43',
                    'local_income_tax': 'K51+K53+K54',
                    'resident_tax': 'F110+F111+F115'
                }
            }
            
            logger.info(f"엑셀 파싱 완료: 원천세={withholding_tax:,.0f}원")
            return result
            
        except Exception as e:
            logger.error(f"엑셀 파싱 실패: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': f"엑셀 파일 파싱 중 오류 발생: {str(e)}"
            }
    
    def parse_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        PDF 파일에서 원천세 데이터 추출 (SK 기준)
        A99 행의 맨 끝 숫자 추출
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            {
                'success': bool,
                'data': {
                    'withholding_tax': float
                },
                'error': str (optional)
            }
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                # 모든 페이지 텍스트 추출
                for page in pdf_reader.pages:
                    text += page.extract_text()
            
            # A99 라인 찾기
            lines = text.split('\n')
            a99_value = None
            
            for line in lines:
                if 'A99' in line or 'a99' in line.lower():
                    # 라인에서 숫자만 추출 (콤마 포함)
                    numbers = re.findall(r'[\d,]+', line)
                    if numbers:
                        # 맨 끝 숫자 (콤마 제거 후 변환)
                        last_number = numbers[-1].replace(',', '')
                        a99_value = float(last_number)
                        logger.info(f"A99 라인 발견: {line}")
                        logger.info(f"추출된 값: {a99_value:,.0f}원")
                        break
            
            if a99_value is None:
                return {
                    'success': False,
                    'data': None,
                    'error': 'PDF에서 A99 항목을 찾을 수 없습니다.'
                }
            
            result = {
                'success': True,
                'data': {
                    'withholding_tax': a99_value,
                    'local_income_tax': 0,  # PDF에서는 원천세만 추출
                    'resident_tax': 0,
                    'total': a99_value
                },
                'source': 'pdf',
                'extraction_key': 'A99'
            }
            
            logger.info(f"PDF 파싱 완료: 원천세={a99_value:,.0f}원")
            return result
            
        except Exception as e:
            logger.error(f"PDF 파싱 실패: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': f"PDF 파일 파싱 중 오류 발생: {str(e)}"
            }
    
    def _safe_get_value(self, df: pd.DataFrame, row: int, col: int) -> float:
        """
        DataFrame에서 안전하게 값 추출
        
        Args:
            df: DataFrame
            row: 행 인덱스 (0부터 시작)
            col: 열 인덱스 (0부터 시작)
            
        Returns:
            추출된 숫자 값 (없으면 0)
        """
        try:
            if row < len(df) and col < len(df.columns):
                value = df.iloc[row, col]
                
                # NaN 체크
                if pd.isna(value):
                    return 0.0
                
                # 숫자로 변환
                if isinstance(value, (int, float)):
                    return float(value)
                
                # 문자열인 경우 (콤마 제거)
                if isinstance(value, str):
                    cleaned = value.replace(',', '').replace('원', '').strip()
                    return float(cleaned) if cleaned else 0.0
                
                return 0.0
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"값 추출 실패 (row={row}, col={col}): {str(e)}")
            return 0.0
    
    def parse_file(self, file_path: str, file_type: str = None) -> Dict[str, Any]:
        """
        파일 형식에 따라 자동 파싱
        
        Args:
            file_path: 파일 경로
            file_type: 'excel' or 'pdf' (None이면 확장자로 판단)
            
        Returns:
            파싱 결과
        """
        if file_type is None:
            file_ext = Path(file_path).suffix.lower()
            if file_ext in ['.xlsx', '.xls']:
                file_type = 'excel'
            elif file_ext == '.pdf':
                file_type = 'pdf'
            else:
                return {
                    'success': False,
                    'data': None,
                    'error': f'지원하지 않는 파일 형식: {file_ext}'
                }
        
        if file_type == 'excel':
            return self.parse_excel(file_path)
        elif file_type == 'pdf':
            return self.parse_pdf(file_path)
        else:
            return {
                'success': False,
                'data': None,
                'error': f'알 수 없는 파일 타입: {file_type}'
            }