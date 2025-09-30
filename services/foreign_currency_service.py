# services/foreign_currency_service.py
"""외화획득명세서 비즈니스 로직 서비스"""

import streamlit as st
from utils.vat.foreign_currency_processor import ForeignCurrencyProcessor
from utils.activity_logger import log_vat_activity
import logging

logger = logging.getLogger(__name__)

class ForeignCurrencyService:
    """외화획득명세서 처리 서비스"""
    
    def __init__(self):
        self.processor = ForeignCurrencyProcessor()
    
    def set_period(self, year: int, quarter: int):
        """처리 기간 설정"""
        self.processor.set_period(year, quarter)
        logger.info(f"처리 기간 설정: {year}년 {quarter}분기")
    
    def process_export_data(self, files):
        """수출이행내역 처리"""
        try:
            result = self.processor.process_export_data(files)
            
            if 'error' not in result:
                # 세션에 저장
                if 'fc_raw_data' not in st.session_state:
                    st.session_state.fc_raw_data = {}
                st.session_state.fc_raw_data['export'] = result
                st.session_state.fc_processing_stage = max(
                    st.session_state.get('fc_processing_stage', 0), 1
                )
                
                # 활동 로그 저장
                log_vat_activity(
                    "외화획득명세서 - 수출이행내역 취합 완료",
                    {"total_rows": result['summary']['total_rows'], "files_processed": result['summary']['success_files']}
                )
                
                logger.info(f"수출이행내역 처리 완료: {result['summary']['total_rows']}행")
            
            return result
            
        except Exception as e:
            logger.error(f"수출이행내역 처리 실패: {str(e)}")
            return {'error': str(e), 'data': None}
    
    def process_exchange_data(self, files):
        """환율정보 처리"""
        try:
            result = self.processor.process_exchange_data(files)
            
            if 'error' not in result:
                if 'fc_raw_data' not in st.session_state:
                    st.session_state.fc_raw_data = {}
                st.session_state.fc_raw_data['exchange'] = result
                st.session_state.fc_processing_stage = max(
                    st.session_state.get('fc_processing_stage', 0), 2
                )
                
                # 활동 로그 저장
                log_vat_activity(
                    "외화획득명세서 - 환율정보 취합 완료",
                    {"currency_count": result['summary']['currency_count'], "currencies": result['summary']['currencies']}
                )
                
                logger.info(f"환율정보 처리 완료: {result['summary']['currency_count']}개 통화")
            
            return result
            
        except Exception as e:
            logger.error(f"환율정보 처리 실패: {str(e)}")
            return {'error': str(e), 'data': None}
    
    def process_invoice_data(self, files, export_data=None):
        """인보이스 발행내역 처리"""
        try:
            result = self.processor.process_invoice_data(files, export_data)
            
            if 'error' not in result:
                if 'fc_raw_data' not in st.session_state:
                    st.session_state.fc_raw_data = {}
                st.session_state.fc_raw_data['invoice'] = result
                st.session_state.fc_processing_stage = max(
                    st.session_state.get('fc_processing_stage', 0), 3
                )
                
                # 활동 로그 저장
                log_vat_activity(
                    "외화획득명세서 - 인보이스 발행내역 처리 완료",
                    {"total_rows": result['summary']['total_rows'], "service_rows": result['summary']['service_rows'], "goods_rows": result['summary']['goods_rows']}
                )
                
                logger.info(f"인보이스 처리 완료: {result['summary']['total_rows']}행")
            
            return result
            
        except Exception as e:
            logger.error(f"인보이스 처리 실패: {str(e)}")
            return {'error': str(e), 'data': None}
    
    def process_a2_data(self, files, invoice_data=None):
        """A2 데이터 처리"""
        try:
            result = self.processor.process_a2_data(files, invoice_data)
            
            if 'error' not in result:
                if 'fc_raw_data' not in st.session_state:
                    st.session_state.fc_raw_data = {}
                st.session_state.fc_raw_data['a2'] = result
                st.session_state.fc_processing_stage = max(
                    st.session_state.get('fc_processing_stage', 0), 4
                )
                
                # 활동 로그 저장
                log_vat_activity(
                    "외화획득명세서 - A2 데이터 정리 완료",
                    {"processed_rows": result['summary']['processed_rows'], "original_rows": result['summary']['original_rows']}
                )
                
                logger.info(f"A2 데이터 처리 완료: {result['summary']['processed_rows']}행")
            
            return result
            
        except Exception as e:
            logger.error(f"A2 데이터 처리 실패: {str(e)}")
            return {'error': str(e), 'data': None}
    
    def generate_final_report(self, invoice_data, exchange_data=None, a2_data=None):
        """최종 명세서 생성"""
        try:
            result = self.processor.generate_final_report(invoice_data, exchange_data, a2_data)
            
            if 'error' not in result:
                if 'fc_raw_data' not in st.session_state:
                    st.session_state.fc_raw_data = {}
                st.session_state.fc_raw_data['final_report'] = result
                st.session_state.fc_processing_stage = 5
                
                year = st.session_state.get('fc_year', 2025)
                quarter = st.session_state.get('fc_quarter', 1)
                total_rows = result.get('summary', {}).get('total_rows', 0)
                
                # 활동 로그 저장
                log_vat_activity(
                    f"외화획득명세서 - {year}년 {quarter}분기 최종 명세서 생성 완료",
                    {"total_rows": total_rows, "year": year, "quarter": quarter}
                )
                
                logger.info(f"최종 명세서 생성 완료: {total_rows}행")
            
            return result
            
        except Exception as e:
            logger.error(f"최종 명세서 생성 실패: {str(e)}")
            return {'error': str(e)}
    
    def get_processed_data(self, data_type: str):
        """처리된 데이터 조회"""
        raw_data = st.session_state.get('fc_raw_data', {})
        return raw_data.get(data_type, {}).get('data', None)
    
    def get_all_data(self):
        """모든 처리된 데이터 조회"""
        return st.session_state.get('fc_raw_data', {})
    
    def reset_all_data(self):
        """모든 데이터 초기화"""
        keys_to_remove = ['fc_raw_data', 'fc_processing_stage']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]
        logger.info("외화획득명세서 데이터 초기화 완료")
    
    def get_processing_stage(self):
        """현재 처리 단계 조회"""
        return st.session_state.get('fc_processing_stage', 0)