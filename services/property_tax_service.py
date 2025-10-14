"""
TAXi 지방세 관리 시스템 - 재산세 서비스 v1.4.0 (파사드)
services/property_tax_service.py

변경사항:
- v1.3.0 → v1.4.0 (Phase 3-C: 계산 결과 영속성 파사드 노출)
- save_calculations_to_json() 파사드 메서드 추가
- load_calculations_from_json() 파사드 메서드 추가
- get_calculation_history() 파사드 메서드 추가
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from .property_tax.pts_core import PtsCoreManager
from .property_tax.pts_calculator import PtsCalculator

class PropertyTaxService:
    """재산세 비즈니스 로직 서비스 (파사드)
    
    v1.4.0: 계산 결과 영속성 파사드 노출
    - pts_core: 자산관리 + 세율관리 + 데이터저장 + JSON 영속성 (세율+자산+계산)
    - pts_calculator: 세액계산 + 엑셀처리
    """
    
    def __init__(self):
        """서비스 초기화 (파사드 패턴)"""
        self.core = PtsCoreManager()
        self.calculator = PtsCalculator(self.core)
        
        self.INFINITY_VALUE = self.core.INFINITY_VALUE
    
    # ===========================================
    # 영속성 관리 (Phase 2 + Phase 3-C) - v1.4.0 확장
    # ===========================================
    
    def save_rates_to_json(self) -> Tuple[bool, str]:
        """세율 데이터를 JSON 파일로 저장 (공정시장가액비율 포함)
        
        Returns:
            (성공 여부, 메시지)
        """
        return self.core.save_rates_to_json()
    
    def load_rates_from_json(self) -> Tuple[bool, Dict[str, Any], str]:
        """JSON 파일에서 세율 데이터 로드 (공정시장가액비율 포함)
        
        Returns:
            (성공 여부, 로드된 데이터, 메시지)
        """
        return self.core.load_rates_from_json()
    
    def save_assets_to_json(self) -> Tuple[bool, str]:
        """자산 데이터를 JSON 파일로 저장
        
        Returns:
            (성공 여부, 메시지)
        """
        return self.core.save_assets_to_json()
    
    def load_assets_from_json(self) -> Tuple[bool, Dict[str, Any], str]:
        """JSON 파일에서 자산 데이터 로드
        
        Returns:
            (성공 여부, 로드된 데이터, 메시지)
        """
        return self.core.load_assets_from_json()
    
    def save_calculations_to_json(self) -> Tuple[bool, str]:
        """계산 결과를 JSON 파일로 저장 (Phase 3-C 신규)
        
        Returns:
            (성공 여부, 메시지)
        """
        return self.core.save_calculations_to_json()
    
    def load_calculations_from_json(self) -> Tuple[bool, Dict[str, Any], str]:
        """JSON 파일에서 계산 결과 로드 (Phase 3-C 신규)
        
        Returns:
            (성공 여부, 로드된 데이터, 메시지)
        """
        return self.core.load_calculations_from_json()
    
    def get_calculation_history(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """저장된 계산 결과 이력 조회 (Phase 3-C 신규)
        
        Args:
            filters: 필터 조건 (예: {'year': 2024, 'group_id': 'GROUP_A'})
        
        Returns:
            필터링된 계산 결과 리스트
        """
        return self.core.get_calculation_history(filters)
    
    # ===========================================
    # 데이터 초기화 (Core 위임)
    # ===========================================
    
    def initialize_default_data(self) -> None:
        """기본 데이터 초기화"""
        return self.core.initialize_default_data()
    
    # ===========================================
    # 무제한값 처리 유틸리티 (Core 위임)
    # ===========================================
    
    def convert_infinity_for_display(self, value: Any) -> str:
        """표시용 무제한값 변환"""
        return self.core.convert_infinity_for_display(value)
    
    def convert_infinity_for_calculation(self, value: Any) -> float:
        """계산용 무제한값 변환"""
        return self.core.convert_infinity_for_calculation(value)
    
    def convert_display_to_infinity(self, display_value: str) -> Any:
        """표시값을 저장값으로 변환"""
        return self.core.convert_display_to_infinity(display_value)
    
    def format_tax_rate(self, rate: float, precision: int = 3) -> float:
        """세율 정밀도 포맷팅"""
        return self.core.format_tax_rate(rate, precision)
    
    def format_tax_rate_for_display(self, rate: float, precision: int = 3, trim_zeros: bool = True) -> str:
        """세율 표시용 포맷팅"""
        return self.core.format_tax_rate_for_display(rate, precision, trim_zeros)
    
    def validate_and_format_tax_rate_input(self, input_rate: float, precision: int = 3) -> Tuple[bool, float, str]:
        """세율 입력값 검증 및 포맷팅"""
        return self.core.validate_and_format_tax_rate_input(input_rate, precision)
    
    # ===========================================
    # 연도 관리 서비스 (Core 위임)
    # ===========================================
    
    def get_all_available_years(self) -> List[int]:
        """모든 사용 가능한 연도 목록 조회"""
        return self.core.get_all_available_years()
    
    def get_available_tax_years(self) -> List[int]:
        """세율 연도 목록 조회 (하위 호환성)"""
        return self.core.get_all_available_years()
    
    def get_available_years(self) -> List[int]:
        """자산 연도 목록 조회 (하위 호환성)"""
        return self.core.get_all_available_years()
    
    def validate_year_input(self, year: int) -> Tuple[bool, str]:
        """연도 입력값 유효성 검증"""
        return self.core.validate_year_input(year)
    
    def create_default_year_rates(self, year: int, base_year: int = None) -> Dict[str, Any]:
        """새 연도 기본 세율 데이터 생성"""
        return self.core.create_default_year_rates(year, base_year)
    
    def add_tax_year(self, new_year: int, base_year: int = None) -> Tuple[bool, str]:
        """새 연도 세율 데이터 추가"""
        return self.core.add_tax_year(new_year, base_year)
    
    def add_year(self, new_year: int, base_year: int = None) -> Tuple[bool, str]:
        """새 연도 추가 (하위 호환성 메서드)"""
        return self.add_tax_year(new_year, base_year)
    
    def check_year_dependencies(self, year: int) -> List[str]:
        """연도 삭제 전 의존성 체크"""
        return self.core.check_year_dependencies(year)
    
    def delete_tax_year(self, year: int) -> Tuple[bool, str]:
        """연도 세율 데이터 삭제"""
        return self.core.delete_tax_year(year)
    
    def copy_year_rates(self, from_year: int, to_year: int) -> Tuple[bool, str]:
        """연도간 세율 데이터 복사"""
        try:
            from_year_str = str(from_year)
            to_year_str = str(to_year)
            
            if from_year not in self.get_all_available_years():
                return False, f"복사할 {from_year}년 세율 데이터가 존재하지 않습니다."
            
            if to_year not in self.get_all_available_years():
                return False, f"대상 {to_year}년 세율 데이터가 존재하지 않습니다."
            
            import copy
            tax_types = ["재산세", "재산세_도시지역분", "지방교육세", "지역자원시설세"]
            for tax_type in tax_types:
                if (tax_type in st.session_state.property_tax_rates and 
                    from_year_str in st.session_state.property_tax_rates[tax_type]):
                    
                    st.session_state.property_tax_rates[tax_type][to_year_str] = copy.deepcopy(
                        st.session_state.property_tax_rates[tax_type][from_year_str]
                    )
            
            if from_year_str in st.session_state.fair_market_ratios:
                st.session_state.fair_market_ratios[to_year_str] = copy.deepcopy(
                    st.session_state.fair_market_ratios[from_year_str]
                )
            
            return True, f"{from_year}년 세율 데이터가 {to_year}년으로 성공적으로 복사되었습니다."
        
        except Exception as e:
            return False, f"데이터 복사 중 오류가 발생했습니다: {str(e)}"
    
    def validate_year_data_integrity(self, year: int) -> Tuple[bool, List[str]]:
        """연도별 데이터 무결성 검증"""
        errors = []
        year_str = str(year)
        
        required_tax_types = ["재산세", "재산세_도시지역분", "지방교육세", "지역자원시설세"]
        
        for tax_type in required_tax_types:
            if tax_type not in st.session_state.property_tax_rates:
                errors.append(f"{tax_type} 데이터가 없습니다.")
            elif year_str not in st.session_state.property_tax_rates[tax_type]:
                errors.append(f"{tax_type}의 {year}년 데이터가 없습니다.")
        
        if (year_str in st.session_state.property_tax_rates.get("재산세", {}) and
            "재산세" in st.session_state.property_tax_rates):
            
            property_tax_data = st.session_state.property_tax_rates["재산세"][year_str]
            required_asset_types = ["토지", "건축물", "주택"]
            
            for asset_type in required_asset_types:
                if asset_type not in property_tax_data:
                    errors.append(f"{year}년 재산세 {asset_type} 데이터가 없습니다.")
        
        if year_str not in st.session_state.fair_market_ratios:
            errors.append(f"{year}년 공정시장가액비율 데이터가 없습니다.")
        
        return len(errors) == 0, errors
    
    # ===========================================
    # 자산 관리 서비스 (Core 위임)
    # ===========================================
    
    def get_taxation_types_for_asset_type(self, asset_type: str) -> List[str]:
        """자산유형별 과세유형 반환"""
        return self.core.get_taxation_types_for_asset_type(asset_type)
    
    def validate_asset_data(self, asset_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """자산 데이터 유효성 검증"""
        return self.core.validate_asset_data(asset_data)
    
    def create_asset(self, asset_data: Dict[str, Any]) -> Tuple[bool, str]:
        """자산 생성"""
        return self.core.create_asset(asset_data)
    
    def add_asset(self, asset_data: Dict[str, Any]) -> Tuple[bool, str]:
        """자산 추가 (하위 호환성 메서드)"""
        return self.create_asset(asset_data)
    
    def update_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> Tuple[bool, str]:
        """자산 수정"""
        return self.core.update_asset(asset_id, asset_data)
    
    def delete_asset(self, asset_id: str) -> Tuple[bool, str]:
        """자산 삭제"""
        return self.core.delete_asset(asset_id)
    
    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """자산 조회"""
        return self.core.get_asset(asset_id)
    
    def get_all_assets(self) -> Dict[str, Any]:
        """모든 자산 조회"""
        return self.core.get_all_assets()
    
    def filter_assets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """자산 필터링"""
        return self.core.filter_assets(filters)
    
    # ===========================================
    # 세율 관리 서비스 (Core 위임)
    # ===========================================
    
    def get_property_tax_rates(self, year: int, asset_type: str, taxation_type: str) -> List[Dict[str, Any]]:
        """재산세율 조회"""
        return self.core.get_property_tax_rates(year, asset_type, taxation_type)
    
    def get_tax_rates(self, year: int, asset_type: str, taxation_type: str) -> List[Dict[str, Any]]:
        """재산세율 조회 (하위 호환성 메서드)"""
        return self.get_property_tax_rates(year, asset_type, taxation_type)
    
    def update_property_tax_rates(self, year: int, asset_type: str, taxation_type: str, 
                                 rates: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """재산세율 수정"""
        return self.core.update_property_tax_rates(year, asset_type, taxation_type, rates)
    
    def update_tax_rates(self, year: int, asset_type: str, taxation_type: str, 
                        rates: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """재산세율 수정 (하위 호환성 메서드)"""
        return self.update_property_tax_rates(year, asset_type, taxation_type, rates)
    
    def add_rate_bracket(self, year: int, asset_type: str, taxation_type: str, new_bracket: Dict[str, Any] = None) -> bool:
        """세율 구간 추가"""
        return self.calculator.add_rate_bracket(year, asset_type, taxation_type, new_bracket)
    
    def remove_last_rate_bracket(self, year: int, asset_type: str, taxation_type: str) -> bool:
        """마지막 세율 구간 삭제"""
        return self.calculator.remove_last_rate_bracket(year, asset_type, taxation_type)
    
    def get_urban_area_tax_rate(self, year: int) -> float:
        """재산세 도시지역분 세율 조회"""
        return self.core.get_urban_area_tax_rate(year)
    
    def update_urban_area_tax_rate(self, year: int, rate: float) -> Tuple[bool, str]:
        """재산세 도시지역분 세율 수정"""
        return self.core.update_urban_area_tax_rate(year, rate)
    
    def get_fair_market_ratio(self, year: int, asset_type: str) -> float:
        """공정시장가액비율 조회"""
        return self.core.get_fair_market_ratio(year, asset_type)
    
    def update_fair_market_ratios(self, ratios: Dict[str, Dict[str, float]]) -> Tuple[bool, str]:
        """공정시장가액비율 수정"""
        return self.core.update_fair_market_ratios(ratios)
    
    # ===========================================
    # 세액 계산 서비스 (Calculator 위임)
    # ===========================================
    
    def calculate_progressive_tax(self, base_amount: float, tax_brackets: List[Dict[str, Any]]) -> float:
        """누진세 계산"""
        return self.calculator.calculate_progressive_tax(base_amount, tax_brackets)
    
    def calculate_property_tax_for_asset(self, asset_id: str, year: int) -> Optional[Dict[str, Any]]:
        """개별 자산 재산세 계산"""
        return self.calculator.calculate_property_tax_for_asset(asset_id, year)
    
    def calculate_property_tax_for_group(self, group_id: str, year: int) -> Dict[str, Any]:
        """그룹별 재산세 계산"""
        return self.calculator.calculate_property_tax_for_group(group_id, year)
    
    # ===========================================
    # 통계 및 분석 서비스 (Core 위임)
    # ===========================================
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """자산 통계 조회"""
        return self.core.get_asset_statistics()
    
    # ===========================================
    # 엑셀 처리 서비스 (Calculator 위임)
    # ===========================================
    
    def validate_excel_data(self, df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
        """엑셀 데이터 유효성 검증 및 보정"""
        return self.calculator.validate_excel_data(df)
    
    def validate_excel_format(self, df: pd.DataFrame) -> List[str]:
        """엑셀 형식 검증 (하위 호환성 메서드)"""
        is_valid, errors, _ = self.validate_excel_data(df)
        return errors if not is_valid else []
    
    def import_assets_from_excel(self, df: pd.DataFrame) -> Tuple[bool, str, Dict[str, int]]:
        """엑셀에서 자산 일괄 가져오기"""
        return self.calculator.import_assets_from_excel(df)
    
    # ===========================================
    # 계산 결과 관리 서비스 (Core 위임)
    # ===========================================
    
    def save_calculation_result(self, calc_key: str, calculation_data: Dict[str, Any]) -> bool:
        """계산 결과 저장"""
        return self.core.save_calculation_result(calc_key, calculation_data)
    
    def get_calculation_result(self, calc_key: str) -> Optional[Dict[str, Any]]:
        """계산 결과 조회"""
        return self.core.get_calculation_result(calc_key)
    
    def get_all_calculation_results(self) -> Dict[str, Any]:
        """모든 계산 결과 조회"""
        return self.core.get_all_calculation_results()
    
    def delete_calculation_result(self, calc_key: str) -> bool:
        """계산 결과 삭제"""
        return self.core.delete_calculation_result(calc_key)
    
    # ===========================================
    # 비교 분석 서비스 (Core 위임)
    # ===========================================
    
    def save_comparison_result(self, calc_key: str, comparison_data: Dict[str, Any]) -> bool:
        """비교 분석 결과 저장"""
        return self.core.save_comparison_result(calc_key, comparison_data)
    
    def get_comparison_result(self, calc_key: str) -> Optional[Dict[str, Any]]:
        """비교 분석 결과 조회"""
        return self.core.get_comparison_result(calc_key)
    
    # ===========================================
    # 최종 확정 서비스 (Core 위임)
    # ===========================================
    
    def save_finalization_result(self, calc_key: str, finalization_data: Dict[str, Any]) -> bool:
        """최종 확정 결과 저장"""
        return self.core.save_finalization_result(calc_key, finalization_data)
    
    def get_finalization_result(self, calc_key: str) -> Optional[Dict[str, Any]]:
        """최종 확정 결과 조회"""
        return self.core.get_finalization_result(calc_key)
    
    # ===========================================
    # 유틸리티 메서드 (Core 위임)
    # ===========================================
    
    def export_assets_to_dataframe(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """자산을 DataFrame으로 내보내기"""
        return self.core.export_assets_to_dataframe(filters)
    
    def get_available_groups(self) -> List[str]:
        """사용 가능한 그룹 목록 조회"""
        return self.core.get_available_groups()
    
    def clear_all_data(self) -> bool:
        """모든 데이터 초기화"""
        return self.core.clear_all_data()
    
    # ===========================================
    # 확장 기능 (Calculator의 추가 기능)
    # ===========================================
    
    def update_regional_resource_tax_rates(self, year: int, rates: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """지역자원시설세율 수정"""
        return self.calculator.update_regional_resource_tax_rates(year, rates)
    
    def add_regional_resource_bracket(self, year: int, new_bracket: Dict[str, Any] = None) -> bool:
        """지역자원시설세 구간 추가"""
        return self.calculator.add_regional_resource_bracket(year, new_bracket)
    
    def remove_last_regional_resource_bracket(self, year: int) -> bool:
        """지역자원시설세 마지막 구간 삭제"""
        return self.calculator.remove_last_regional_resource_bracket(year)
    
    # ===========================================
    # 버전 정보
    # ===========================================
    
    def get_version_info(self) -> Dict[str, str]:
        """버전 정보 반환"""
        return {
            "version": "1.4.0",
            "architecture": "Facade Pattern",
            "modules": {
                "pts_core": "자산관리 + 세율관리 + 데이터저장 + JSON 영속성 (세율+자산+계산)",
                "pts_calculator": "세액계산 + 엑셀처리"
            },
            "changes": "v1.3.0 → v1.4.0 계산 결과 영속성 파사드 노출 (save_calculations_to_json, load_calculations_from_json, get_calculation_history)"
        }
