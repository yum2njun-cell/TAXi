"""
TAXi - 원천세 비즈니스 로직 서비스
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import os
import tempfile
from typing import Dict, List, Tuple, Any, Optional
from pathlib import Path

from utils.withholding_tax.data_processor import WithholdingTaxProcessor
from utils.withholding_tax.web_helpers import (
    validate_uploaded_file,
    format_number,
    create_summary_dataframe,
    get_sheet_names,
    validate_sheet_exists
)
from utils.activity_logger import (
    log_withholding_return_activity,
    log_withholding_foreign_tax_activity, 
    log_withholding_payment_statement_activity,
    get_activity_logger
)
from config.withholding_tax_config import COMPANY_CONFIGS
import logging
logger = logging.getLogger(__name__)

class WithholdingTaxService:
    """원천세 처리 비즈니스 로직 서비스"""
    
    def __init__(self):
        self.processor = WithholdingTaxProcessor()
        self.logger = logging.getLogger(__name__)
        
    def detect_company_type(self, filename: str) -> Optional[int]:
        """파일명 기반 회사 타입 감지"""
        return self.processor.detect_company_type(filename)
    
    def get_company_name(self, company_type: int) -> str:
        """회사 타입으로 회사명 반환"""
        return COMPANY_CONFIGS.get(company_type, {}).get('name', '알 수 없음')
    
    def get_sheet_names(self, uploaded_file) -> List[str]:
        """업로드된 파일의 시트명 목록 반환"""
        return get_sheet_names(uploaded_file)
    
    def validate_file(self, uploaded_file) -> Tuple[bool, str]:
        """파일 유효성 검증"""
        return validate_uploaded_file(uploaded_file)
    
    def validate_sheet(self, uploaded_file, sheet_name: str) -> Tuple[bool, str]:
        """시트 존재 여부 검증"""
        return validate_sheet_exists(uploaded_file, sheet_name)
    
    def format_number(self, value: Any) -> str:
        """숫자 포맷팅"""
        return format_number(value)
    
    def create_summary_dataframe(self, data_summary: Dict, company_type: int) -> pd.DataFrame:
        """요약 데이터를 데이터프레임으로 변환"""
        return create_summary_dataframe(data_summary, company_type)
    
    def process_file(self, uploaded_file, company_type: int, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """개별 파일 처리"""
        try:
            # 파일 유효성 검증
            is_valid, error_msg = self.validate_file(uploaded_file)
            if not is_valid:
                return {
                    'success': False,
                    'error': error_msg,
                    'data': {},
                    'excel_data': b'',
                    'company_name': ''
                }
            
            # 시트 유효성 검증 (필요한 경우)
            if sheet_name and company_type in [1, 2, 3]:
                is_valid, error_msg = self.validate_sheet(uploaded_file, sheet_name)
                if not is_valid:
                    return {
                        'success': False,
                        'error': error_msg,
                        'data': {},
                        'excel_data': b'',
                        'company_name': ''
                    }
            
            # 데이터 처리
            result = self.processor.process(uploaded_file, company_type, sheet_name)
            
            if result['success']:
                self.logger.info(f"파일 처리 성공: {uploaded_file.name}, 회사: {self.get_company_name(company_type)}")

                # 활동 로그 저장 (회사 타입에 따라 분기)
                stats = self.get_processing_statistics(result['data'])
                
                if company_type in [1, 2]:  # 급여, 사업소득
                    log_withholding_return_activity(
                        f"원천세 파일 처리 완료 - {self.get_company_name(company_type)}",
                        {
                            "company_name": self.get_company_name(company_type),
                            "total_personnel": stats['total_personnel'],
                            "total_income_tax": stats['total_income_tax']
                        }
                    )
                elif company_type == 3:  # 배당소득
                    log_withholding_foreign_tax_activity(
                        f"배당소득 파일 처리 완료",
                        {
                            "company_name": self.get_company_name(company_type),
                            "items_processed": stats['items_processed']
                        }
                    )
                else:  # 기타
                    log_withholding_payment_statement_activity(
                        f"원천세 파일 처리 완료 - {self.get_company_name(company_type)}",
                        {
                            "company_name": self.get_company_name(company_type),
                            "items_processed": stats['items_processed']
                        }
                    )
            else:
                self.logger.error(f"파일 처리 실패: {uploaded_file.name}, 오류: {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"파일 처리 중 예외 발생: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': {},
                'excel_data': b'',
                'company_name': ''
            }
    
    def process_combined_files(self, file_company_mappings: List[Tuple]) -> Dict[str, Any]:
        """통합 파일 처리"""
        try:
            # 각 파일 유효성 검증
            for uploaded_file, company_type, sheet_name in file_company_mappings:
                is_valid, error_msg = self.validate_file(uploaded_file)
                if not is_valid:
                    return {
                        'success': False,
                        'error': f"파일 {uploaded_file.name} 검증 실패: {error_msg}",
                        'data': {},
                        'excel_data': b''
                    }
                
                if sheet_name and company_type in [1, 2, 3]:
                    is_valid, error_msg = self.validate_sheet(uploaded_file, sheet_name)
                    if not is_valid:
                        return {
                            'success': False,
                            'error': f"파일 {uploaded_file.name} 시트 검증 실패: {error_msg}",
                            'data': {},
                            'excel_data': b''
                        }
            
            # 통합 처리
            result = self.processor.process_combined(file_company_mappings)
            
            # 기존: if result['success']: 블록 내부에 추가  
            if result['success']:
                company_names = [self.get_company_name(ct) for _, ct, _ in file_company_mappings]
                self.logger.info(f"통합 처리 성공: {', '.join(company_names)}")
                
                # 추가할 코드:
                # 통합 처리 활동 로그
                log_withholding_return_activity(
                    f"원천세 통합 처리 완료",
                    {
                        "companies": company_names,
                        "file_count": len(file_company_mappings),
                        "combined_processing": True
                    }
                )
            else:
                self.logger.error(f"통합 처리 실패: {result['error']}")
            
            return result
            
        except Exception as e:
            error_msg = f"통합 처리 중 예외 발생: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'data': {},
                'excel_data': b''
            }
    
    def get_processing_statistics(self, data_summary: Dict) -> Dict[str, Any]:
        """처리 결과 통계 계산"""
        try:
            stats = {
                'total_personnel': 0,
                'total_income_tax': 0,
                'total_resident_tax': 0,
                'total_taxable_income': 0,
                'items_processed': len(data_summary)
            }
            
            # 총합계 데이터가 있으면 사용
            if '총합계' in data_summary:
                total_data = data_summary['총합계']
                stats['total_personnel'] = total_data.get('인원', 0)
                stats['total_income_tax'] = total_data.get('소득세', 0)
                stats['total_resident_tax'] = total_data.get('주민세', 0)
                stats['total_taxable_income'] = total_data.get('과세소득', 0)
            else:
                # 총합계가 없으면 직접 계산
                for key, data in data_summary.items():
                    if '합계' not in key:  # 합계 항목은 제외
                        stats['total_personnel'] += data.get('인원', 0)
                        stats['total_income_tax'] += data.get('소득세', 0)
                        stats['total_resident_tax'] += data.get('주민세', 0)
                        stats['total_taxable_income'] += data.get('과세소득', 0)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"통계 계산 중 오류: {str(e)}")
            return {
                'total_personnel': 0,
                'total_income_tax': 0,
                'total_resident_tax': 0,
                'total_taxable_income': 0,
                'items_processed': 0
            }
    
    def get_company_summary(self, all_companies_data: Dict) -> Dict[str, Any]:
        """회사별 데이터 요약"""
        try:
            summary = {}
            
            for company_type, company_data in all_companies_data.items():
                company_name = self.get_company_name(company_type)
                stats = self.get_processing_statistics(company_data)
                
                summary[company_name] = {
                    'company_type': company_type,
                    'statistics': stats,
                    'items_count': len(company_data)
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"회사별 요약 생성 중 오류: {str(e)}")
            return {}
    
    def export_summary_report(self, data_summary: Dict, company_type: int) -> bytes:
        """요약 보고서 Excel 생성"""
        try:
            return self.processor.excel_generator.create_excel_bytes(data_summary, company_type)
        except Exception as e:
            self.logger.error(f"요약 보고서 생성 중 오류: {str(e)}")
            return b''
    
    def export_combined_report(self, all_companies_data: Dict) -> bytes:
        """통합 보고서 Excel 생성"""
        try:
            return self.processor.excel_generator.create_combined_excel_bytes(all_companies_data)
        except Exception as e:
            self.logger.error(f"통합 보고서 생성 중 오류: {str(e)}")
            return b''
    def process_mixed_files(self, auto_files: Dict[str, str], manual_file_mappings: List[Tuple]) -> Dict[str, Any]:
        """자동 탐색 + 수동 업로드 파일 혼합 처리"""
        try:
            file_type_to_company = {"AKT": 1, "INC": 2, "MR": 3, "AX": 4}
            all_file_mappings = []
            
            # 자동 파일들 추가
            for file_type, file_path in auto_files.items():
                if Path(file_path).exists():
                    company_type = file_type_to_company.get(file_type, 1)
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    class MockFile:
                        def __init__(self, content, name):
                            self.content = content
                            self.name = name
                        def getvalue(self):
                            return self.content
                        def getbuffer(self):
                            return self.content
                    
                    mock_file = MockFile(file_content, Path(file_path).name)
                    all_file_mappings.append((mock_file, company_type, None))
            
            # 수동 파일들 추가
            all_file_mappings.extend(manual_file_mappings)
            
            return self.process_combined_files(all_file_mappings)
            
        except Exception as e:
            return {
                'success': False,
                'error': f"혼합 처리 중 오류: {str(e)}",
                'data': {},
                'excel_data': b''
            }
    
@st.cache_resource
def get_withholding_tax_service():
    """원천세 서비스 인스턴스 반환"""
    return WithholdingTaxService()