"""
세금 기록 관리 서비스
업로드, 파싱, 저장, 조회 등 비즈니스 로직
"""

import streamlit as st
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

from utils.withholding_tax.withholding_parser import WithholdingTaxParser
from utils.withholding_tax.tax_data_manager import TaxDataManager

logger = logging.getLogger(__name__)


class TaxRecordService:
    """세금 기록 관리 서비스"""
    
    def __init__(self):
        self.parser = WithholdingTaxParser()
        self.data_manager = TaxDataManager()
    
    def process_uploaded_files(self, year: int, month: int, 
                              excel_file=None, pdf_file=None,
                              auto_date: bool = False) -> Dict[str, Any]:
        """
        업로드된 파일 처리
        
        Args:
            year: 연도
            month: 월
            excel_file: 엑셀 파일 (Streamlit UploadedFile)
            pdf_file: PDF 파일 (Streamlit UploadedFile)
            auto_date: 파일명에서 자동으로 날짜 추출 여부
            
        Returns:
            {
                'success': bool,
                'data': {...},
                'files': {...},
                'is_update': bool,  # 기존 데이터 덮어쓰기 여부
                'error': str (optional)
            }
        """
        try:
            # 파일명에서 날짜 자동 추출
            if auto_date and excel_file:
                parsed_date = self.data_manager.parse_filename_date(excel_file.name)
                if parsed_date:
                    year, month = parsed_date
                    logger.info(f"파일명에서 날짜 자동 추출: {year}년 {month}월")
            
            # 중복 체크
            duplicate_id = self.data_manager.check_duplicate_record(year, month, 'withholding_tax')
            is_update = duplicate_id is not None
            
            if is_update:
                logger.info(f"기존 데이터 발견: {year}년 {month}월 (ID: {duplicate_id})")
                # 기존 데이터 삭제
                self.data_manager.delete_record_with_files(duplicate_id, 'withholding_tax')
            
            result_data = {
                'withholding_tax': 0,
                'local_income_tax': 0,
                'resident_tax': 0,
                'total': 0
            }
            file_paths = {}
            errors = []
            
            # 엑셀 파일 처리
            if excel_file is not None:
                # 파일 저장
                excel_path = self.data_manager.save_uploaded_file(
                    excel_file, year, month, 'excel'
                )
                
                if excel_path:
                    file_paths['excel_path'] = excel_path
                    
                    # 데이터 추출
                    parse_result = self.parser.parse_excel(excel_path)
                    
                    if parse_result['success']:
                        # 엑셀 데이터 우선 사용
                        result_data.update(parse_result['data'])
                        logger.info(f"엑셀 파싱 성공: {year}년 {month}월")
                    else:
                        errors.append(f"엑셀 파싱 실패: {parse_result.get('error', '알 수 없는 오류')}")
                else:
                    errors.append("엑셀 파일 저장 실패")
            
            # PDF 파일 처리
            if pdf_file is not None:
                # 파일 저장
                pdf_path = self.data_manager.save_uploaded_file(
                    pdf_file, year, month, 'pdf'
                )
                
                if pdf_path:
                    file_paths['pdf_path'] = pdf_path
                    
                    # 데이터 추출
                    parse_result = self.parser.parse_pdf(pdf_path)
                    
                    if parse_result['success']:
                        # PDF에서는 원천세만 추출
                        # 엑셀이 없는 경우에만 PDF 데이터 사용
                        if excel_file is None:
                            result_data['withholding_tax'] = parse_result['data']['withholding_tax']
                            result_data['total'] = parse_result['data']['total']
                        
                        logger.info(f"PDF 파싱 성공: {year}년 {month}월")
                    else:
                        errors.append(f"PDF 파싱 실패: {parse_result.get('error', '알 수 없는 오류')}")
                else:
                    errors.append("PDF 파일 저장 실패")
            
            # 최소 하나의 파일은 성공해야 함
            if not file_paths:
                return {
                    'success': False,
                    'data': None,
                    'error': '파일 저장에 실패했습니다.'
                }
            
            # 기록 저장
            record = {
                'year': year,
                'month': month,
                'withholding_tax': result_data['withholding_tax'],
                'local_income_tax': result_data['local_income_tax'],
                'resident_tax': result_data['resident_tax'],
                'total_amount': result_data['total'],
                'excel_file': file_paths.get('excel_path'),
                'pdf_file': file_paths.get('pdf_path'),
                'has_excel': 'excel_path' in file_paths,
                'has_pdf': 'pdf_path' in file_paths,
                'processing_errors': errors if errors else None
            }
            
            save_success = self.data_manager.add_record(record, 'withholding_tax')
            
            if not save_success:
                return {
                    'success': False,
                    'data': None,
                    'error': '데이터 저장에 실패했습니다.'
                }
            
            logger.info(f"원천세 기록 저장 완료: {year}년 {month}월")
            
            return {
                'success': True,
                'data': result_data,
                'files': file_paths,
                'record': record,
                'is_update': is_update,  # 덮어쓰기 여부
                'warnings': errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"파일 처리 실패: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': f'파일 처리 중 오류 발생: {str(e)}'
            }
    
    def update_record_data(self, record_id: str, updated_data: Dict[str, Any]) -> bool:
        """
        기록 수동 수정
        
        Args:
            record_id: 수정할 기록 ID
            updated_data: 수정할 데이터
                {
                    'withholding_tax': float,
                    'local_income_tax': float,
                    'resident_tax': float
                }
            
        Returns:
            수정 성공 여부
        """
        # 합계 재계산
        total = (
            updated_data.get('withholding_tax', 0) +
            updated_data.get('local_income_tax', 0) +
            updated_data.get('resident_tax', 0)
        )
        updated_data['total_amount'] = total
        
        success = self.data_manager.update_record(record_id, updated_data, 'withholding_tax')
        
        if success:
            logger.info(f"기록 수정 완료: {record_id}")
        
        return success
    def process_vat_file(self, excel_file, auto_date: bool = True) -> Dict[str, Any]:
        """
        부가세 파일 처리
        
        Args:
            excel_file: 엑셀 파일
            auto_date: 파일명에서 자동 날짜 추출
            
        Returns:
            처리 결과
        """
        try:
            from utils.vat.vat_parser import VATParser
            
            parser = VATParser()
            
            # 파일 저장
            year_quarter = "temp"
            if auto_date:
                parsed = parser._parse_filename_date(excel_file.name)
                if parsed:
                    year, quarter = parsed
                    year_quarter = f"{year}_{quarter}Q"
            
            # 임시 저장
            temp_path = self.data_manager.upload_dir / f"vat_{year_quarter}_{excel_file.name}"
            with open(temp_path, 'wb') as f:
                f.write(excel_file.getbuffer())
            
            # 파싱
            result = parser.parse_excel(str(temp_path))
            
            if not result['success']:
                return result
            
            # 데이터 추출
            data = result['data']
            period = result['period']
            year = period['year']
            quarter = period['quarter']
            
            # 중복 체크
            duplicate_id = self._check_vat_duplicate(year, quarter)
            is_update = duplicate_id is not None
            
            if is_update:
                logger.info(f"기존 부가세 데이터 발견: {year}년 {quarter}분기")
                self.data_manager.delete_record_with_files(duplicate_id, 'vat')
            
            # 레코드 생성
            record = {
                'year': year,
                'quarter': quarter,
                'sales_vat': data['sales_vat'],
                'purchase_vat': data['purchase_vat'],
                'penalty': data['penalty'],
                'payment_amount': data['payment_amount'],
                'total_amount': data['payment_amount'],  
                'excel_file': str(temp_path),
                'has_excel': True
            }
            
            # 저장
            save_success = self.data_manager.add_record(record, 'vat')
            
            if not save_success:
                return {'success': False, 'error': '데이터 저장 실패'}
            
            logger.info(f"부가세 기록 저장 완료: {year}년 {quarter}분기")
            
            return {
                'success': True,
                'data': data,
                'period': period,
                'is_update': is_update
            }
            
        except Exception as e:
            logger.error(f"부가세 처리 실패: {str(e)}")
            return {'success': False, 'error': str(e)}

    def _check_vat_duplicate(self, year: int, quarter: int) -> Optional[str]:
        """부가세 중복 체크"""
        return self.data_manager.check_duplicate_record(year, quarter=quarter, tax_type='vat')

    def get_vat_records(self) -> List[Dict[str, Any]]:
        """부가세 기록 조회"""
        return self.data_manager.load_records('vat')

    def get_all_records(self, tax_type: str = "withholding_tax") -> List[Dict[str, Any]]:
        """모든 기록 조회"""
        return self.data_manager.load_records(tax_type)
    
    def get_records_by_year(self, year: int, tax_type: str = "withholding_tax") -> List[Dict[str, Any]]:
        """연도별 기록 조회"""
        return self.data_manager.get_records_by_period(year, None, tax_type)
    
    def get_records_by_period(self, year: int, month: int, 
                             tax_type: str = "withholding_tax") -> List[Dict[str, Any]]:
        """특정 기간 기록 조회"""
        return self.data_manager.get_records_by_period(year, month, tax_type)
    
    def get_records_by_date_range(self, start_year: int, start_month: int,
                                  end_year: int, end_month: int,
                                  tax_type: str = "withholding_tax") -> List[Dict[str, Any]]:
        """
        기간 범위로 기록 조회
        
        Args:
            start_year: 시작 연도
            start_month: 시작 월
            end_year: 종료 연도
            end_month: 종료 월
            tax_type: 세목
            
        Returns:
            필터링된 기록 리스트
        """
        all_records = self.data_manager.load_records(tax_type)
        
        filtered = []
        for record in all_records:
            year = record['year']
            month = record['month']
            
            # 날짜 비교
            if (year > start_year or (year == start_year and month >= start_month)) and \
               (year < end_year or (year == end_year and month <= end_month)):
                filtered.append(record)
        
        return filtered
    
    def calculate_vat_changes(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        부가세 전분기 대비 증감 계산
        
        Args:
            records: 부가세 기록 리스트
            
        Returns:
            증감 정보가 추가된 기록 리스트
        """
        if len(records) < 2:
            return records
        
        # 날짜순 정렬 (오래된 것부터)
        sorted_records = sorted(records, key=lambda x: (x['year'], x['quarter']))
        
        result = []
        for i, record in enumerate(sorted_records):
            enhanced_record = record.copy()
            
            # 전분기 대비
            if i > 0:
                prev = sorted_records[i - 1]
                enhanced_record['prev_quarter_change'] = record['payment_amount'] - prev['payment_amount']
                enhanced_record['prev_quarter_change_rate'] = (
                    (record['payment_amount'] - prev['payment_amount']) / prev['payment_amount'] * 100
                    if prev['payment_amount'] > 0 else 0
                )
            
            # 전년 동분기 대비
            for j in range(i):
                prev = sorted_records[j]
                if prev['year'] == record['year'] - 1 and prev['quarter'] == record['quarter']:
                    enhanced_record['prev_year_change'] = record['payment_amount'] - prev['payment_amount']
                    enhanced_record['prev_year_change_rate'] = (
                        (record['payment_amount'] - prev['payment_amount']) / prev['payment_amount'] * 100
                        if prev['payment_amount'] > 0 else 0
                    )
                    break
            
            result.append(enhanced_record)
        
        # 최신순으로 재정렬
        result.sort(key=lambda x: (x['year'], x['quarter']), reverse=True)
        
        return result

    def delete_record(self, record_id: str, tax_type: str = "withholding_tax") -> bool:
        """기록 삭제 (파일 포함)"""
        return self.data_manager.delete_record_with_files(record_id, tax_type)
    
    def get_file_path(self, year: int, month: int, file_type: str) -> Optional[str]:
        """
        저장된 파일 경로 조회
        
        Args:
            year: 연도
            month: 월
            file_type: 'excel' or 'pdf'
            
        Returns:
            파일 경로 (없으면 None)
        """
        return self.data_manager.get_uploaded_file_path(year, month, file_type)
    
    def calculate_changes(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        전월/전년 대비 증감 계산
        
        Args:
            records: 기록 리스트 (시간순 정렬 필요)
            
        Returns:
            증감 정보가 추가된 기록 리스트
        """
        if len(records) < 2:
            return records
        
        # 날짜순 정렬 (오래된 것부터)
        sorted_records = sorted(records, key=lambda x: (x['year'], x.get('month', 0)))
        
        result = []
        for i, record in enumerate(sorted_records):
            enhanced_record = record.copy()
            
            # 금액 필드 통일 처리 (원천세: total_amount, 부가세: payment_amount)
            current_amount = record.get('total_amount', record.get('payment_amount', 0))
            
            # 전월 대비 (월 단위 데이터만)
            if i > 0 and 'month' in record:
                prev = sorted_records[i - 1]
                prev_amount = prev.get('total_amount', prev.get('payment_amount', 0))
                
                enhanced_record['prev_month_change'] = current_amount - prev_amount
                enhanced_record['prev_month_change_rate'] = (
                    (current_amount - prev_amount) / prev_amount * 100
                    if prev_amount > 0 else 0
                )
            
            # 전년 동월 대비
            for j in range(i):
                prev = sorted_records[j]
                if prev['year'] == record['year'] - 1 and prev.get('month') == record.get('month'):
                    prev_amount = prev.get('total_amount', prev.get('payment_amount', 0))
                    enhanced_record['prev_year_change'] = current_amount - prev_amount
                    enhanced_record['prev_year_change_rate'] = (
                        (current_amount - prev_amount) / prev_amount * 100
                        if prev_amount > 0 else 0
                    )
                    break
            
            result.append(enhanced_record)
        
        # 최신순으로 재정렬
        result.sort(key=lambda x: (x['year'], x.get('month', 0)), reverse=True)
        
        return result
    
    def get_summary_statistics(self, tax_type: str = "withholding_tax") -> Dict[str, Any]:
        """데이터 요약 통계"""
        return self.data_manager.get_summary_statistics(tax_type)
    
    def search_records(self, keyword: str, tax_type: str = "withholding_tax") -> List[Dict[str, Any]]:
        """
        키워드로 기록 검색 (챗봇용)
        
        Args:
            keyword: 검색 키워드 (예: "2024년 3월", "원천세", "100만원 이상")
            tax_type: 세목
            
        Returns:
            검색된 기록 리스트
        """
        all_records = self.data_manager.load_records(tax_type)
        results = []
        
        keyword_lower = keyword.lower()
        
        for record in all_records:
            # 연도, 월 매칭
            if str(record['year']) in keyword_lower or f"{record['month']}월" in keyword_lower:
                results.append(record)
                continue
            
            # 금액 범위 검색 (간단한 예시)
            if "만원" in keyword_lower or "원" in keyword_lower:
                # 예: "100만원 이상" 같은 검색어 처리
                # 실제로는 더 정교한 파싱 필요
                results.append(record)
        
        return results