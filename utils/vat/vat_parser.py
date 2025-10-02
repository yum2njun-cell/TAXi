"""
부가세 신고서 파싱 유틸리티
- 엑셀: E23, J23, F23, G23, H23
"""

import pandas as pd
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class VATParser:
    """부가세 신고서 파서"""
    
    def __init__(self):
        self.logger = logger
    
    def _parse_filename_date(self, filename: str) -> Optional[Tuple[int, int]]:
        """
        파일명에서 연도와 분기 추출
        지원 패턴:
        - "25년1분기.xlsx" → (2025, 1)
        - "25년1기.xlsx" → (2025, 1)
        - "25-1Q.xlsx" → (2025, 1)
        - "2025년1분기.xlsx" → (2025, 1)
        
        Args:
            filename: 파일명
            
        Returns:
            (year, quarter) 또는 None
        """
        try:
            # 패턴 1: YY년N분기 또는 YY년N기
            pattern1 = r'(\d{2})년\s*(\d)[분]?기'
            match = re.search(pattern1, filename)
            
            if match:
                year_2digit = int(match.group(1))
                quarter = int(match.group(2))
                year = 2000 + year_2digit if year_2digit < 50 else 1900 + year_2digit
                
                if 1 <= quarter <= 4:
                    logger.info(f"파일명 파싱: {filename} → {year}년 {quarter}분기")
                    return (year, quarter)
            
            # 패턴 2: YY-NQ
            pattern2 = r'(\d{2})-(\d)Q'
            match = re.search(pattern2, filename, re.IGNORECASE)
            
            if match:
                year_2digit = int(match.group(1))
                quarter = int(match.group(2))
                year = 2000 + year_2digit if year_2digit < 50 else 1900 + year_2digit
                
                if 1 <= quarter <= 4:
                    logger.info(f"파일명 파싱: {filename} → {year}년 {quarter}분기")
                    return (year, quarter)
            
            # 패턴 3: YYYY년N분기 또는 YYYY년N기 (4자리 연도)
            pattern3 = r'(\d{4})년\s*(\d)[분]?기'
            match = re.search(pattern3, filename)
            
            if match:
                year = int(match.group(1))
                quarter = int(match.group(2))
                
                if 1 <= quarter <= 4:
                    logger.info(f"파일명 파싱: {filename} → {year}년 {quarter}분기")
                    return (year, quarter)
            
            logger.warning(f"파일명에서 분기 추출 실패: {filename}")
            return None
            
        except Exception as e:
            logger.error(f"파일명 파싱 오류: {filename}, {str(e)}")
            return None
    
    def parse_excel(self, file_path: str) -> Dict[str, Any]:
        """
        엑셀 파일에서 부가세 데이터 추출
        
        Returns:
            {
                'success': bool,
                'data': {
                    'sales_vat': float,
                    'purchase_vat': float,
                    'penalty': float,
                    'payment_amount': float
                }
            }
        """
        try:
            # 파일명에서 기간 추출
            filename = Path(file_path).name
            year, quarter = self._parse_filename_date(filename)
            
            if year is None or quarter is None:
                return {
                    'success': False,
                    'error': f'파일명에서 연도/분기 추출 실패: {filename}'
                }
            
            # 엑셀 파일 읽기
            df = pd.read_excel(file_path, header=None)
            
            # 값 추출 (row=22는 23번째 행, 0-based index)
            e23 = self._safe_get_value(df, 22, 4)   # E23
            j23 = self._safe_get_value(df, 22, 9)   # J23
            f23 = self._safe_get_value(df, 22, 5)   # F23
            g23 = self._safe_get_value(df, 22, 6)   # G23
            h23 = self._safe_get_value(df, 22, 7)   # H23
            
            sales_vat = e23 + j23
            purchase_vat = f23
            penalty = g23
            payment_amount = h23 + j23
            
            result = {
                'success': True,
                'data': {
                    'sales_vat': sales_vat,
                    'purchase_vat': purchase_vat,
                    'penalty': penalty,
                    'payment_amount': payment_amount
                },
                'period': {
                    'year': year,
                    'quarter': quarter
                },
                'source': 'excel',
                'cells': {
                    'sales_vat': 'E23+J23',
                    'purchase_vat': 'F23',
                    'penalty': 'G23',
                    'payment_amount': 'H23+J23'
                }
            }
            
            logger.info(f"부가세 파싱 완료: {year}년 {quarter}분기, 납부세액={payment_amount:,.0f}원")
            return result
            
        except Exception as e:
            logger.error(f"부가세 엑셀 파싱 실패: {str(e)}")
            return {
                'success': False,
                'error': f"엑셀 파일 파싱 중 오류: {str(e)}"
            }
    
    def _safe_get_value(self, df: pd.DataFrame, row: int, col: int) -> float:
        """DataFrame에서 안전하게 값 추출"""
        try:
            if row < len(df) and col < len(df.columns):
                value = df.iloc[row, col]
                
                if pd.isna(value):
                    return 0.0
                
                if isinstance(value, (int, float)):
                    return float(value)
                
                if isinstance(value, str):
                    cleaned = value.replace(',', '').replace('원', '').strip()
                    return float(cleaned) if cleaned else 0.0
                
                return 0.0
            else:
                return 0.0
        except Exception as e:
            logger.warning(f"값 추출 실패 (row={row}, col={col}): {str(e)}")
            return 0.0