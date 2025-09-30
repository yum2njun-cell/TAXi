"""
TAXi 지방세 관리 시스템 - 재산세 서비스
services/property_tax_service.py
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import json
import copy
from utils.activity_logger import log_excel_generation_activity, log_file_processing_activity

try:
    from services.property_tax.pts_core import PtsCoreManager
    from services.property_tax.pts_calculator import PtsCalculator
    MODULES_AVAILABLE = True
except ImportError:
    print("WARNING: pts_core 또는 pts_calculator를 찾을 수 없습니다.")
    MODULES_AVAILABLE = False

class PropertyTaxService:
    """재산세 비즈니스 로직 서비스"""
    
    def __init__(self):
        """서비스 초기화"""
        if MODULES_AVAILABLE:
            try:
                self.core = PtsCoreManager()
                self.calculator = PtsCalculator(self.core)
                self.INFINITY_VALUE = self.core.INFINITY_VALUE
                print("PropertyTaxService 초기화 완료 - Core + Calculator 모드")
            except Exception as e:
                print(f"모듈 초기화 실패: {str(e)}")
                self._use_basic_mode()
        else:
            self._use_basic_mode()
    
    def _use_basic_mode(self):
        """기본 모드 (모듈 없이)"""
        self.core = None
        self.calculator = None
        self.INFINITY_VALUE = 1000000000000
        print("PropertyTaxService 기본 모드로 초기화")

    def initialize_default_data(self) -> None:
        """기본 데이터 초기화"""
        if 'property_tax_assets' not in st.session_state:
            st.session_state.property_tax_assets = self._get_default_assets()
        
        if 'property_tax_rates' not in st.session_state:
            st.session_state.property_tax_rates = self._get_default_rates()
        
        if 'fair_market_ratios' not in st.session_state:
            st.session_state.fair_market_ratios = self._get_default_ratios()
        
        if 'property_calculations' not in st.session_state:
            st.session_state.property_calculations = {}
        
        if 'property_comparisons' not in st.session_state:
            st.session_state.property_comparisons = {}
        
        if 'property_finalizations' not in st.session_state:
            st.session_state.property_finalizations = {}
    
    def _get_default_assets(self) -> Dict[str, Any]:
        """기본 자산 데이터 반환"""
        return {
            "ASSET_001": {
                "자산ID": "ASSET_001",
                "자산명": "본사 부지",
                "자산유형": "토지",
                "상세유형": "일반토지",
                "과세유형": "종합합산",
                "재산세_도시지역분": "Y",
                "그룹ID": "GROUP_A",
                "시도": "서울특별시",
                "시군구": "강남구",
                "상세주소": "테헤란로 123번지",
                "면적": 1000.5,
                "연도별데이터": {
                    "2024": {
                        "적용연도": 2024,
                        "공시지가": 800000000,
                        "시가표준액": 850000000,
                        "감면율": 0,
                        "중과세율": 0,
                        "유효기간": "2024-12-31"
                    }
                }
            }
        }
    
    def _get_default_rates(self) -> Dict[str, Any]:
        """기본 세율 데이터 반환"""
        return {
            "재산세": {
                "2024": {
                    "토지": {
                        "종합합산": [
                            {"하한": 0, "상한": 60000000, "기본세액": 0, "세율": 0.1},
                            {"하한": 60000000, "상한": 150000000, "기본세액": 60000, "세율": 0.15},
                            {"하한": 150000000, "상한": 300000000, "기본세액": 195000, "세율": 0.25},
                            {"하한": 300000000, "상한": float('inf'), "기본세액": 570000, "세율": 0.4}
                        ],
                        "별도합산": [
                            {"하한": 0, "상한": 60000000, "기본세액": 0, "세율": 0.2},
                            {"하한": 60000000, "상한": 150000000, "기본세액": 120000, "세율": 0.3},
                            {"하한": 150000000, "상한": 300000000, "기본세액": 390000, "세율": 0.5},
                            {"하한": 300000000, "상한": float('inf'), "기본세액": 1140000, "세율": 0.7}
                        ],
                        "분리과세": [
                            {"하한": 0, "상한": float('inf'), "기본세액": 0, "세율": 2.0}
                        ]
                    },
                    "건축물": {
                        "기타": [
                            {"하한": 0, "상한": 60000000, "기본세액": 0, "세율": 0.1},
                            {"하한": 60000000, "상한": 150000000, "기본세액": 60000, "세율": 0.15},
                            {"하한": 150000000, "상한": 300000000, "기본세액": 195000, "세율": 0.25},
                            {"하한": 300000000, "상한": float('inf'), "기본세액": 570000, "세율": 0.4}
                        ]
                    },
                    "주택": {
                        "기타": [
                            {"하한": 0, "상한": 60000000, "기본세액": 0, "세율": 0.1},
                            {"하한": 60000000, "상한": 150000000, "기본세액": 60000, "세율": 0.15},
                            {"하한": 150000000, "상한": 300000000, "기본세액": 195000, "세율": 0.25},
                            {"하한": 300000000, "상한": float('inf'), "기본세액": 570000, "세율": 0.4}
                        ]
                    }
                }
            },
            "재산세_도시지역분": {
                "2024": {"비율": 0.14}
            },
            "지방교육세": {
                "2024": {"비율": 0.2}
            },
            "지역자원시설세": {
                "2024": [
                    {"하한": 0, "상한": 60000000, "기본세액": 0, "세율": 0.01},
                    {"하한": 60000000, "상한": 150000000, "기본세액": 600, "세율": 0.015},
                    {"하한": 150000000, "상한": 300000000, "기본세액": 1950, "세율": 0.02},
                    {"하한": 300000000, "상한": float('inf'), "기본세액": 4950, "세율": 0.025}
                ]
            }
        }
    
    def _get_default_ratios(self) -> Dict[str, Any]:
        """기본 공정시장가액비율 반환"""
        return {
            "2024": {
                "토지": 70.0,
                "건축물": 70.0,
                "주택": 60.0
            },
            "2023": {
                "토지": 70.0,
                "건축물": 70.0,
                "주택": 60.0
            }
        }
    
    # ===========================================
    # 자산 관리 서비스
    # ===========================================
    
    def get_taxation_types_for_asset_type(self, asset_type: str) -> List[str]:
        """자산유형별 과세유형 반환"""
        if asset_type == "토지":
            return ["종합합산", "별도합산", "분리과세"]
        else:
            return ["기타"]
    
    def validate_asset_data(self, asset_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """자산 데이터 유효성 검증"""
        errors = []
        
        # 필수 필드 검증
        required_fields = ["자산ID", "자산명", "자산유형", "그룹ID", "시도", "시군구", "면적"]
        for field in required_fields:
            if not asset_data.get(field):
                errors.append(f"{field}은(는) 필수 입력 항목입니다.")
        
        # 자산유형 검증
        valid_asset_types = ["토지", "건축물", "주택"]
        if asset_data.get("자산유형") not in valid_asset_types:
            errors.append("자산유형은 토지, 건축물, 주택 중 하나여야 합니다.")
        
        # 과세유형 검증
        asset_type = asset_data.get("자산유형")
        taxation_type = asset_data.get("과세유형")
        valid_taxation_types = self.get_taxation_types_for_asset_type(asset_type)
        
        if taxation_type not in valid_taxation_types:
            errors.append(f"{asset_type}의 과세유형은 {', '.join(valid_taxation_types)} 중 하나여야 합니다.")
        
        # 재산세 도시지역분 검증
        urban_area = asset_data.get("재산세_도시지역분")
        if urban_area not in ["Y", "N"]:
            errors.append("재산세 도시지역분은 Y 또는 N이어야 합니다.")
        
        # 면적 검증
        try:
            area = float(asset_data.get("면적", 0))
            if area <= 0:
                errors.append("면적은 0보다 큰 값이어야 합니다.")
        except (ValueError, TypeError):
            errors.append("면적은 숫자여야 합니다.")
        
        return len(errors) == 0, errors
    
    def create_asset(self, asset_data: Dict[str, Any]) -> Tuple[bool, str]:
        """자산 생성"""
        # 유효성 검증
        is_valid, errors = self.validate_asset_data(asset_data)
        if not is_valid:
            return False, "; ".join(errors)
        
        asset_id = asset_data["자산ID"]
        
        # 중복 검증
        if asset_id in st.session_state.property_tax_assets:
            return False, f"자산ID '{asset_id}'는 이미 존재합니다."
        
        # 자산 저장
        st.session_state.property_tax_assets[asset_id] = asset_data
        
        return True, f"자산 '{asset_data['자산명']}' ({asset_id})이 성공적으로 등록되었습니다."
    
    def update_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> Tuple[bool, str]:
        """자산 수정"""
        # 존재 여부 확인
        if asset_id not in st.session_state.property_tax_assets:
            return False, f"자산ID '{asset_id}'를 찾을 수 없습니다."
        
        # 유효성 검증
        is_valid, errors = self.validate_asset_data(asset_data)
        if not is_valid:
            return False, "; ".join(errors)
        
        # 자산 수정
        st.session_state.property_tax_assets[asset_id] = asset_data
        
        return True, f"자산 '{asset_data['자산명']}' ({asset_id})이 성공적으로 수정되었습니다."
    
    def delete_asset(self, asset_id: str) -> Tuple[bool, str]:
        """자산 삭제"""
        if asset_id not in st.session_state.property_tax_assets:
            return False, f"자산ID '{asset_id}'를 찾을 수 없습니다."
        
        asset_name = st.session_state.property_tax_assets[asset_id]["자산명"]
        del st.session_state.property_tax_assets[asset_id]
        
        return True, f"자산 '{asset_name}' ({asset_id})이 성공적으로 삭제되었습니다."
    
    def get_asset(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """자산 조회"""
        return st.session_state.property_tax_assets.get(asset_id)
    
    def get_all_assets(self) -> Dict[str, Any]:
        """모든 자산 조회"""
        return st.session_state.property_tax_assets
    
    def filter_assets(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """자산 필터링"""
        filtered_assets = []
        
        for asset_id, asset_data in st.session_state.property_tax_assets.items():
            # 필터 조건 확인
            if filters.get("asset_type") and asset_data["자산유형"] != filters["asset_type"]:
                continue
            if filters.get("taxation_type") and asset_data.get("과세유형") != filters["taxation_type"]:
                continue
            if filters.get("urban_area") and asset_data.get("재산세_도시지역분") != filters["urban_area"]:
                continue
            if filters.get("group_id") and asset_data["그룹ID"] != filters["group_id"]:
                continue
            if filters.get("region") and asset_data["시도"] != filters["region"]:
                continue
            
            # 연도 필터
            if filters.get("year"):
                year_str = str(filters["year"])
                if year_str not in asset_data["연도별데이터"]:
                    continue
            
            filtered_assets.append({
                "asset_id": asset_id,
                **asset_data
            })
        
        return filtered_assets
    
    # ===========================================
    # 세율 관리 서비스
    # ===========================================
    
    def get_property_tax_rates(self, year: int, asset_type: str, taxation_type: str) -> List[Dict[str, Any]]:
        """재산세율 조회"""
        try:
            return st.session_state.property_tax_rates["재산세"][str(year)][asset_type][taxation_type]
        except KeyError:
            return []
    
    def update_property_tax_rates(self, year: int, asset_type: str, taxation_type: str, 
                                 rates: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """재산세율 수정"""
        try:
            # 유효성 검증
            for rate in rates:
                required_keys = ["하한", "상한", "기본세액", "세율"]
                if not all(key in rate for key in required_keys):
                    return False, "세율 구간에 필수 항목이 누락되었습니다."
                
                if rate["하한"] < 0 or rate["기본세액"] < 0 or rate["세율"] < 0:
                    return False, "세율 구간의 값은 0 이상이어야 합니다."
            
            # 세율 저장
            st.session_state.property_tax_rates["재산세"][str(year)][asset_type][taxation_type] = rates
            
            return True, f"{year}년 {asset_type} {taxation_type} 세율이 성공적으로 수정되었습니다."
        
        except Exception as e:
            return False, f"세율 수정 중 오류가 발생했습니다: {str(e)}"
    
    def get_urban_area_tax_rate(self, year: int) -> float:
        """재산세 도시지역분 세율 조회"""
        try:
            return st.session_state.property_tax_rates["재산세_도시지역분"][str(year)]["비율"]
        except KeyError:
            return 0.14  # 기본값
    
    def update_urban_area_tax_rate(self, year: int, rate: float) -> Tuple[bool, str]:
        """재산세 도시지역분 세율 수정"""
        try:
            if rate < 0 or rate > 1:
                return False, "세율은 0과 1 사이의 값이어야 합니다."
            
            st.session_state.property_tax_rates["재산세_도시지역분"][str(year)]["비율"] = rate
            
            return True, f"{year}년 재산세 도시지역분 세율이 {rate}%로 수정되었습니다."
        
        except Exception as e:
            return False, f"세율 수정 중 오류가 발생했습니다: {str(e)}"
    
    def get_fair_market_ratio(self, year: int, asset_type: str) -> float:
        """공정시장가액비율 조회"""
        try:
            return st.session_state.fair_market_ratios[str(year)][asset_type]
        except KeyError:
            return 70.0  # 기본값
    
    def update_fair_market_ratios(self, ratios: Dict[str, Dict[str, float]]) -> Tuple[bool, str]:
        """공정시장가액비율 수정"""
        try:
            for year, year_ratios in ratios.items():
                for asset_type, ratio in year_ratios.items():
                    if ratio < 0 or ratio > 100:
                        return False, f"{year}년 {asset_type}의 비율은 0과 100 사이여야 합니다."
            
            st.session_state.fair_market_ratios = ratios
            
            return True, "공정시장가액비율이 성공적으로 수정되었습니다."
        
        except Exception as e:
            return False, f"비율 수정 중 오류가 발생했습니다: {str(e)}"
    
    # ===========================================
    # 세액 계산 서비스
    # ===========================================
    
    # calculate_progressive_tax - calculator 사용하도록 수정
    def calculate_progressive_tax(self, base_amount: float, tax_brackets: List[Dict[str, Any]]) -> float:
        """누진세 계산"""
        if self.calculator:
            return self.calculator.calculate_progressive_tax(base_amount, tax_brackets)
        
        # 기존 Document 2의 폴백 코드
        total_tax = 0
        remaining_amount = base_amount
        
        for bracket in tax_brackets:
            if remaining_amount <= 0:
                break
            
            bracket_size = bracket["상한"] - bracket["하한"] if bracket["상한"] != float('inf') else remaining_amount
            taxable_in_bracket = min(remaining_amount, bracket_size)
            
            bracket_tax = bracket["기본세액"] + (taxable_in_bracket * bracket["세율"] / 100)
            total_tax += bracket_tax
            remaining_amount -= taxable_in_bracket
            
            if bracket["상한"] == float('inf'):
                break
        
        return total_tax
    
    # calculate_property_tax_for_asset - calculator 사용하도록 수정
    def calculate_property_tax_for_asset(self, asset_id: str, year: int) -> Optional[Dict[str, Any]]:
        """개별 자산 재산세 계산"""
        if self.calculator:
            return self.calculator.calculate_property_tax_for_asset(asset_id, year)
        
        try:
            # 자산 데이터 조회
            asset_data = self.get_asset(asset_id)
            if not asset_data:
                return None
            
            year_str = str(year)
            if year_str not in asset_data["연도별데이터"]:
                return None
            
            year_data = asset_data["연도별데이터"][year_str]
            asset_type = asset_data["자산유형"]
            taxation_type = asset_data.get("과세유형", "기타")
            
            calculation_process = []
            
            # 1. 기준금액 설정
            if asset_type == "주택" and "건물시가" in year_data:
                base_amount = year_data["건물시가"]
                calculation_process.append(f"1. 기준금액 = 건물시가 = {base_amount:,}원 (주택)")
            else:
                base_amount = year_data["시가표준액"]
                calculation_process.append(f"1. 기준금액 = 시가표준액 = {base_amount:,}원")
            
            # 2. 공정시장가액비율 적용
            ratio = self.get_fair_market_ratio(year, asset_type) / 100
            calculation_process.append(f"2. 공정시장가액비율 = {ratio*100:.1f}%")
            
            taxable_amount_before_reduction = base_amount * ratio
            calculation_process.append(f"3. 과세표준(감면전) = {base_amount:,} × {ratio*100:.1f}% = {taxable_amount_before_reduction:,.0f}원")
            
            # 3. 감면 적용
            reduction_rate = year_data.get("감면율", 0) / 100
            if reduction_rate > 0:
                reduction_amount = taxable_amount_before_reduction * reduction_rate
                calculation_process.append(f"4. 감면액 = {taxable_amount_before_reduction:,.0f} × {reduction_rate*100:.2f}% = {reduction_amount:,.0f}원")
                taxable_amount = taxable_amount_before_reduction - reduction_amount
                calculation_process.append(f"5. 과세표준(최종) = {taxable_amount_before_reduction:,.0f} - {reduction_amount:,.0f} = {taxable_amount:,.0f}원")
            else:
                taxable_amount = taxable_amount_before_reduction
                calculation_process.append(f"4. 감면 없음, 과세표준(최종) = {taxable_amount:,.0f}원")
            
            # 4. 재산세 계산
            tax_brackets = self.get_property_tax_rates(year, asset_type, taxation_type)
            if not tax_brackets:
                return None
            
            calculation_process.append(f"5. 재산세 계산 ({asset_type} - {taxation_type} 과세유형):")
            
            property_tax_before_surcharge = self.calculate_progressive_tax(taxable_amount, tax_brackets)
            calculation_process.append(f"6. 재산세(중과전) = {property_tax_before_surcharge:,.0f}원")
            
            # 5. 중과세 적용
            surcharge_rate = year_data.get("중과세율", 0) / 100
            if surcharge_rate > 0:
                surcharge_amount = property_tax_before_surcharge * surcharge_rate
                calculation_process.append(f"7. 중과세액 = {property_tax_before_surcharge:,.0f} × {surcharge_rate*100:.2f}% = {surcharge_amount:,.0f}원")
                property_tax = property_tax_before_surcharge + surcharge_amount
                calculation_process.append(f"8. 재산세(최종) = {property_tax_before_surcharge:,.0f} + {surcharge_amount:,.0f} = {property_tax:,.0f}원")
            else:
                property_tax = property_tax_before_surcharge
                calculation_process.append(f"7. 중과세 없음, 재산세(최종) = {property_tax:,.0f}원")
            
            # 6. 부대세 계산
            # 재산세 도시지역분
            urban_area_tax = 0
            if asset_data.get("재산세_도시지역분", "N") == "Y":
                urban_area_rate = self.get_urban_area_tax_rate(year) / 100
                urban_area_tax = property_tax * urban_area_rate
                calculation_process.append(f"9. 재산세 도시지역분 = {property_tax:,.0f} × {urban_area_rate*100:.3f}% = {urban_area_tax:,.0f}원 (도시지역 적용)")
            else:
                calculation_process.append(f"9. 재산세 도시지역분 = 0원 (도시지역 미적용)")
            
            # 지방교육세
            education_tax_rate = st.session_state.property_tax_rates["지방교육세"][str(year)]["비율"]
            education_tax = property_tax * education_tax_rate
            calculation_process.append(f"10. 지방교육세 = {property_tax:,.0f} × {education_tax_rate*100:.1f}% = {education_tax:,.0f}원")
            
            # 지역자원시설세
            regional_brackets = st.session_state.property_tax_rates["지역자원시설세"][str(year)]
            regional_tax = self.calculate_progressive_tax(base_amount, regional_brackets)
            calculation_process.append(f"11. 지역자원시설세 = {regional_tax:,.0f}원 (기준금액 {base_amount:,}원 기준 누진계산)")
            
            # 총세액
            total_tax = property_tax + urban_area_tax + education_tax + regional_tax
            calculation_process.append(f"12. 총세액 = {property_tax:,.0f} + {urban_area_tax:,.0f} + {education_tax:,.0f} + {regional_tax:,.0f} = {total_tax:,.0f}원")
            
            return {
                "자산ID": asset_id,
                "자산명": asset_data["자산명"],
                "자산유형": asset_type,
                "과세유형": taxation_type,
                "계산연도": year,
                "기준금액": base_amount,
                "과세표준": taxable_amount,
                "재산세": property_tax,
                "재산세_도시지역분": urban_area_tax,
                "지방교육세": education_tax,
                "지역자원시설세": regional_tax,
                "총세액": total_tax,
                "계산과정": calculation_process,
                "계산일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
        except Exception as e:
            print(f"세액 계산 중 오류 발생: {str(e)}")
            return None
    
    def calculate_property_tax_for_group(self, group_id: str, year: int) -> Dict[str, Any]:
        """그룹별 재산세 계산"""
        try:
            # 그룹에 해당하는 자산 조회
            if group_id == "전체":
                group_assets = {asset_id: asset for asset_id, asset in st.session_state.property_tax_assets.items() 
                               if str(year) in asset["연도별데이터"]}
            else:
                group_assets = {asset_id: asset for asset_id, asset in st.session_state.property_tax_assets.items() 
                               if asset["그룹ID"] == group_id and str(year) in asset["연도별데이터"]}
            
            if not group_assets:
                return {
                    "그룹ID": group_id,
                    "연도": year,
                    "자산별계산": {},
                    "그룹총세액": 0,
                    "계산일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "오류": f"{group_id} 그룹에 {year}년 데이터가 있는 자산이 없습니다."
                }
            
            calculations = {}
            total_tax = 0
            
            for asset_id in group_assets.keys():
                calc_result = self.calculate_property_tax_for_asset(asset_id, year)
                
                if calc_result:
                    calculations[asset_id] = calc_result
                    total_tax += calc_result["총세액"]
            
            log_excel_generation_activity(
                f"재산세 계산 완료 - {group_id}",
                {
                    "group_id": group_id,
                    "year": year,
                    "asset_count": len(calculations),
                    "total_tax": total_tax
                }
            )
            
            return {
                "그룹ID": group_id,
                "연도": year,
                "계산일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "자산별계산": calculations,
                "그룹총세액": total_tax
            }
            
        except Exception as e:
            return {
                "그룹ID": group_id,
                "연도": year,
                "자산별계산": {},
                "그룹총세액": 0,
                "계산일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "오류": f"계산 중 오류 발생: {str(e)}"
            }
    
    # ===========================================
    # 통계 및 분석 서비스
    # ===========================================
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """자산 통계 조회"""
        assets = self.get_all_assets()
        
        if not assets:
            return {
                "총_자산수": 0,
                "자산유형별_분포": {},
                "과세유형별_분포": {},
                "도시지역분별_분포": {},
                "그룹별_분포": {},
                "지역별_분포": {},
                "총_시가표준액": 0,
                "평균_자산가액": 0
            }
        
        type_counts = {}
        taxation_counts = {}
        urban_area_counts = {}
        group_counts = {}
        region_counts = {}
        total_value = 0
        
        for asset_data in assets.values():
            # 자산유형별
            asset_type = asset_data["자산유형"]
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            
            # 과세유형별
            taxation_type = asset_data.get("과세유형", "기타")
            taxation_counts[taxation_type] = taxation_counts.get(taxation_type, 0) + 1
            
            # 도시지역분별
            urban_area = asset_data.get("재산세_도시지역분", "N")
            urban_area_counts[urban_area] = urban_area_counts.get(urban_area, 0) + 1
            
            # 그룹별
            group_id = asset_data["그룹ID"]
            group_counts[group_id] = group_counts.get(group_id, 0) + 1
            
            # 지역별
            region = asset_data["시도"]
            region_counts[region] = region_counts.get(region, 0) + 1
            
            # 총 시가표준액 계산 (최신 연도 기준)
            if asset_data["연도별데이터"]:
                latest_year = max(asset_data["연도별데이터"].keys())
                latest_data = asset_data["연도별데이터"][latest_year]
                total_value += latest_data["시가표준액"]
        
        return {
            "총_자산수": len(assets),
            "자산유형별_분포": type_counts,
            "과세유형별_분포": taxation_counts,
            "도시지역분별_분포": urban_area_counts,
            "그룹별_분포": group_counts,
            "지역별_분포": region_counts,
            "총_시가표준액": total_value,
            "평균_자산가액": total_value // len(assets) if len(assets) > 0 else 0
        }
    
    # ===========================================
    # 엑셀 처리 서비스
    # ===========================================
    
    def validate_excel_data(self, df: pd.DataFrame) -> Tuple[bool, List[str], pd.DataFrame]:
        """엑셀 데이터 유효성 검증 및 보정"""
        errors = []
        corrected_df = df.copy()
        
        # 필수 컬럼 검증
        required_columns = [
            '자산ID', '자산명', '자산유형', '과세유형', '재산세_도시지역분', 
            '그룹ID', '시도', '시군구', '상세주소', '면적', '연도', '시가표준액'
        ]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"필수 컬럼이 누락되었습니다: {', '.join(missing_columns)}")
            return False, errors, corrected_df
        
        # 데이터 보정
        for idx, row in corrected_df.iterrows():
            try:
                # 과세유형 보정
                asset_type = str(row['자산유형'])
                taxation_type = str(row['과세유형'])
                
                if asset_type == "토지":
                    if taxation_type not in ["종합합산", "별도합산", "분리과세"]:
                        corrected_df.at[idx, '과세유형'] = "종합합산"
                        errors.append(f"행 {idx+1}: 토지 과세유형을 '종합합산'으로 보정")
                else:
                    if taxation_type != "기타":
                        corrected_df.at[idx, '과세유형'] = "기타"
                        errors.append(f"행 {idx+1}: {asset_type} 과세유형을 '기타'로 보정")
                
                # 재산세 도시지역분 보정
                urban_area = str(row['재산세_도시지역분'])
                if urban_area not in ["Y", "N"]:
                    corrected_df.at[idx, '재산세_도시지역분'] = "N"
                    errors.append(f"행 {idx+1}: 재산세_도시지역분을 'N'으로 보정")
                
                # 숫자 데이터 검증
                try:
                    float(row['면적'])
                except (ValueError, TypeError):
                    errors.append(f"행 {idx+1}: 면적이 숫자가 아닙니다")
                
                try:
                    int(row['시가표준액'])
                except (ValueError, TypeError):
                    errors.append(f"행 {idx+1}: 시가표준액이 숫자가 아닙니다")
                
            except Exception as e:
                errors.append(f"행 {idx+1}: 데이터 처리 중 오류 - {str(e)}")
        
        return len([e for e in errors if "보정" not in e]) == 0, errors, corrected_df
    
    def import_assets_from_excel(self, df: pd.DataFrame) -> Tuple[bool, str, Dict[str, int]]:
        """엑셀에서 자산 일괄 가져오기"""
        try:
            # 데이터 유효성 검증
            is_valid, errors, corrected_df = self.validate_excel_data(df)
            
            success_count = 0
            error_count = 0
            update_count = 0
            
            for idx, row in corrected_df.iterrows():
                try:
                    asset_id = str(row['자산ID'])
                    year = str(int(row['연도']))
                    asset_type = str(row['자산유형'])
                    
                    year_data = {
                        "적용연도": int(row['연도']),
                        "공시지가": int(row.get('공시지가', 0)),
                        "시가표준액": int(row['시가표준액']),
                        "감면율": float(row.get('감면율', 0)),
                        "중과세율": float(row.get('중과세율', 0)),
                        "유효기간": f"{int(row['연도'])}-12-31"
                    }
                    
                    # 주택의 경우 건물시가 추가
                    if asset_type == "주택" and '건물시가' in row and pd.notna(row['건물시가']):
                        year_data["건물시가"] = int(row['건물시가'])
                    
                    # 기존 자산 업데이트 또는 신규 생성
                    if asset_id in st.session_state.property_tax_assets:
                        st.session_state.property_tax_assets[asset_id]["연도별데이터"][year] = year_data
                        st.session_state.property_tax_assets[asset_id]["재산세_도시지역분"] = str(row['재산세_도시지역분'])
                        update_count += 1
                    else:
                        new_asset = {
                            "자산ID": asset_id,
                            "자산명": str(row['자산명']),
                            "자산유형": asset_type,
                            "상세유형": str(row.get('상세유형', '')),
                            "과세유형": str(row['과세유형']),
                            "재산세_도시지역분": str(row['재산세_도시지역분']),
                            "그룹ID": str(row['그룹ID']),
                            "시도": str(row['시도']),
                            "시군구": str(row['시군구']),
                            "상세주소": str(row['상세주소']),
                            "면적": float(row['면적']),
                            "연도별데이터": {year: year_data}
                        }
                        st.session_state.property_tax_assets[asset_id] = new_asset
                        success_count += 1
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"행 {idx+1} 처리 중 오류: {str(e)}")
            
            result_message = f"일괄 처리 완료: 신규 등록 {success_count}건, 업데이트 {update_count}건, 실패 {error_count}건"
            if errors:
                result_message += f"\n주요 오류/보정 사항:\n" + "\n".join(errors[:10])  # 최대 10개만 표시
                if len(errors) > 10:
                    result_message += f"\n... 외 {len(errors)-10}건 더"
            
            # 여기에 활동 로그 추가
            log_file_processing_activity(
                "재산세 자산 일괄 가져오기 완료",
                "Excel 파일",
                {
                    "success_count": success_count,
                    "update_count": update_count, 
                    "error_count": error_count,
                    "total_rows": len(corrected_df)
                }
            )
            
            return True, result_message, {
                "success": success_count,
                "update": update_count,
                "error": error_count
            }
            
        except Exception as e:
            return False, f"엑셀 가져오기 중 오류 발생: {str(e)}", {"success": 0, "update": 0, "error": 0}
    
    # ===========================================
    # 계산 결과 관리 서비스
    # ===========================================
    
    def save_calculation_result(self, calc_key: str, calculation_data: Dict[str, Any]) -> bool:
        """계산 결과 저장"""
        try:
            st.session_state.property_calculations[calc_key] = calculation_data
            return True
        except Exception as e:
            print(f"계산 결과 저장 중 오류: {str(e)}")
            return False
    
    def get_calculation_result(self, calc_key: str) -> Optional[Dict[str, Any]]:
        """계산 결과 조회"""
        return st.session_state.property_calculations.get(calc_key)
    
    def get_all_calculation_results(self) -> Dict[str, Any]:
        """모든 계산 결과 조회"""
        return st.session_state.property_calculations
    
    def delete_calculation_result(self, calc_key: str) -> bool:
        """계산 결과 삭제"""
        try:
            if calc_key in st.session_state.property_calculations:
                del st.session_state.property_calculations[calc_key]
                return True
            return False
        except Exception as e:
            print(f"계산 결과 삭제 중 오류: {str(e)}")
            return False
    
    # ===========================================
    # 비교 분석 서비스
    # ===========================================
    
    def save_comparison_result(self, calc_key: str, comparison_data: Dict[str, Any]) -> bool:
        """비교 분석 결과 저장"""
        try:
            st.session_state.property_comparisons[calc_key] = comparison_data
            return True
        except Exception as e:
            print(f"비교 결과 저장 중 오류: {str(e)}")
            return False
    
    def get_comparison_result(self, calc_key: str) -> Optional[Dict[str, Any]]:
        """비교 분석 결과 조회"""
        return st.session_state.property_comparisons.get(calc_key)
    
    # ===========================================
    # 최종 확정 서비스
    # ===========================================
    
    def save_finalization_result(self, calc_key: str, finalization_data: Dict[str, Any]) -> bool:
        """최종 확정 결과 저장"""
        try:
            st.session_state.property_finalizations[calc_key] = finalization_data
            return True
        except Exception as e:
            print(f"최종 확정 저장 중 오류: {str(e)}")
            return False
    
    def get_finalization_result(self, calc_key: str) -> Optional[Dict[str, Any]]:
        """최종 확정 결과 조회"""
        return st.session_state.property_finalizations.get(calc_key)
    
    # ===========================================
    # 유틸리티 메서드
    # ===========================================
    
    def export_assets_to_dataframe(self, filters: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """자산을 DataFrame으로 내보내기"""
        if filters:
            filtered_assets = self.filter_assets(filters)
        else:
            filtered_assets = [{"asset_id": k, **v} for k, v in st.session_state.property_tax_assets.items()]
        
        export_data = []
        
        for asset in filtered_assets:
            asset_id = asset.get("asset_id") or asset["자산ID"]
            
            for year, year_data in asset["연도별데이터"].items():
                row = {
                    "자산ID": asset_id,
                    "자산명": asset["자산명"],
                    "자산유형": asset["자산유형"],
                    "상세유형": asset.get("상세유형", ""),
                    "과세유형": asset.get("과세유형", "기타"),
                    "재산세_도시지역분": asset.get("재산세_도시지역분", "N"),
                    "그룹ID": asset["그룹ID"],
                    "시도": asset["시도"],
                    "시군구": asset["시군구"],
                    "상세주소": asset["상세주소"],
                    "면적": asset["면적"],
                    "연도": year,
                    "공시지가": year_data.get("공시지가", 0),
                    "시가표준액": year_data["시가표준액"],
                    "감면율": year_data.get("감면율", 0),
                    "중과세율": year_data.get("중과세율", 0),
                    "유효기간": year_data.get("유효기간", "")
                }
                
                # 주택의 경우 건물시가 추가
                if asset["자산유형"] == "주택" and "건물시가" in year_data:
                    row["건물시가"] = year_data["건물시가"]
                
                export_data.append(row)
        
        return pd.DataFrame(export_data)
    
    def get_available_groups(self) -> List[str]:
        """사용 가능한 그룹 목록 조회"""
        groups = set()
        for asset in st.session_state.property_tax_assets.values():
            groups.add(asset["그룹ID"])
        return sorted(list(groups))
    
    def get_all_available_years(self) -> List[int]:
        """모든 사용 가능한 연도 목록 조회 (세율 데이터 포함)"""
        if self.core:
            return self.core.get_all_available_years()
        
        # 폴백: 세율과 자산에서 연도 수집
        years = set()
        
        # 세율 데이터에서 연도 추출
        if 'property_tax_rates' in st.session_state:
            for tax_type in ["재산세", "재산세_도시지역분", "지방교육세", "지역자원시설세"]:
                if tax_type in st.session_state.property_tax_rates:
                    years.update(int(year) for year in st.session_state.property_tax_rates[tax_type].keys())
        
        # 자산 데이터에서 연도 추출
        for asset in st.session_state.property_tax_assets.values():
            for year in asset["연도별데이터"].keys():
                years.add(int(year))
        
        if not years:
            years.add(datetime.now().year)
        
        return sorted(list(years), reverse=True)

    def get_available_years(self) -> List[int]:
        """사용 가능한 연도 목록 조회 (하위 호환성)"""
        return self.get_all_available_years()
    
    def clear_all_data(self) -> bool:
        """모든 데이터 초기화"""
        try:
            st.session_state.property_tax_assets = {}
            st.session_state.property_calculations = {}
            st.session_state.property_comparisons = {}
            st.session_state.property_finalizations = {}
            return True
        except Exception as e:
            print(f"데이터 초기화 중 오류: {str(e)}")
            return False
        
    # ===========================================
    # 연도 관리 서비스
    # ===========================================
    
    def add_tax_year(self, new_year: int, base_year: int = None) -> Tuple[bool, str]:
        """새 연도 세율 데이터 추가"""
        if self.core:
            return self.core.add_tax_year(new_year, base_year)
        
        # 폴백: 기본 연도 추가
        year_str = str(new_year)
        
        # 이미 존재하는지 확인
        if year_str in st.session_state.property_tax_rates.get("재산세", {}):
            return False, f"{new_year}년 세율 데이터가 이미 존재합니다."
        
        # 기준 연도에서 복사
        if base_year and str(base_year) in st.session_state.property_tax_rates.get("재산세", {}):
            st.session_state.property_tax_rates["재산세"][year_str] = copy.deepcopy(
                st.session_state.property_tax_rates["재산세"][str(base_year)]
            )
        else:
            # 기본 세율 생성
            st.session_state.property_tax_rates["재산세"][year_str] = self._get_default_rates()["재산세"]["2024"]
        
        # 다른 세율도 추가
        st.session_state.property_tax_rates["재산세_도시지역분"][year_str] = {"비율": 0.14}
        st.session_state.property_tax_rates["지방교육세"][year_str] = {"비율": 0.2}
        st.session_state.property_tax_rates["지역자원시설세"][year_str] = self._get_default_rates()["지역자원시설세"]["2024"]
        
        # 공정시장가액비율 추가
        st.session_state.fair_market_ratios[year_str] = {"토지": 70.0, "건축물": 70.0, "주택": 60.0}
        
        return True, f"{new_year}년 세율 데이터가 추가되었습니다."
    
    def delete_tax_year(self, year: int) -> Tuple[bool, str]:
        """연도 세율 데이터 삭제"""
        if self.core:
            return self.core.delete_tax_year(year)
        
        year_str = str(year)
        
        # 존재 여부 확인
        if year_str not in st.session_state.property_tax_rates.get("재산세", {}):
            return False, f"{year}년 세율 데이터가 존재하지 않습니다."
        
        # 최소 1개 연도 유지
        if len(st.session_state.property_tax_rates.get("재산세", {})) <= 1:
            return False, "최소 1개 연도의 세율 데이터는 유지되어야 합니다."
        
        # 삭제
        for tax_type in ["재산세", "재산세_도시지역분", "지방교육세", "지역자원시설세"]:
            if year_str in st.session_state.property_tax_rates.get(tax_type, {}):
                del st.session_state.property_tax_rates[tax_type][year_str]
        
        if year_str in st.session_state.fair_market_ratios:
            del st.session_state.fair_market_ratios[year_str]
        
        return True, f"{year}년 세율 데이터가 삭제되었습니다."
    
    def check_year_dependencies(self, year: int) -> List[str]:
        """연도 삭제 전 의존성 체크"""
        if self.core:
            return self.core.check_year_dependencies(year)
        
        dependencies = []
        year_str = str(year)
        
        # 자산에서 사용 중인지 확인
        for asset_id, asset_data in st.session_state.property_tax_assets.items():
            if year_str in asset_data.get("연도별데이터", {}):
                dependencies.append(f"자산 '{asset_data['자산명']}' ({asset_id})에서 사용 중")
        
        # 계산 결과에서 사용 중인지 확인
        for calc_key, calc_data in st.session_state.property_calculations.items():
            if calc_data.get("연도") == year:
                dependencies.append(f"계산 결과 '{calc_key}'에서 사용 중")
        
        return dependencies
    
    def validate_year_data_integrity(self, year: int) -> Tuple[bool, List[str]]:
        """연도 데이터 무결성 검증"""
        if self.core:
            # core에 이 메서드가 있다면 사용
            return True, []
        
        errors = []
        year_str = str(year)
        
        # 재산세율 확인
        if year_str not in st.session_state.property_tax_rates.get("재산세", {}):
            errors.append(f"{year}년 재산세율이 없습니다.")
        
        # 도시지역분 확인
        if year_str not in st.session_state.property_tax_rates.get("재산세_도시지역분", {}):
            errors.append(f"{year}년 재산세 도시지역분이 없습니다.")
        
        # 공정시장가액비율 확인
        if year_str not in st.session_state.fair_market_ratios:
            errors.append(f"{year}년 공정시장가액비율이 없습니다.")
        
        return len(errors) == 0, errors
    
    def copy_year_rates(self, from_year: int, to_year: int) -> Tuple[bool, str]:
        """연도 간 세율 복사"""
        from_year_str = str(from_year)
        to_year_str = str(to_year)
        
        # 원본 연도 확인
        if from_year_str not in st.session_state.property_tax_rates.get("재산세", {}):
            return False, f"{from_year}년 세율 데이터가 존재하지 않습니다."
        
        # 대상 연도 덮어쓰기 확인
        if to_year_str in st.session_state.property_tax_rates.get("재산세", {}):
            # 이미 존재하면 덮어쓰기
            pass
        
        # 세율 복사
        st.session_state.property_tax_rates["재산세"][to_year_str] = copy.deepcopy(
            st.session_state.property_tax_rates["재산세"][from_year_str]
        )
        st.session_state.property_tax_rates["재산세_도시지역분"][to_year_str] = copy.deepcopy(
            st.session_state.property_tax_rates["재산세_도시지역분"][from_year_str]
        )
        st.session_state.property_tax_rates["지방교육세"][to_year_str] = copy.deepcopy(
            st.session_state.property_tax_rates["지방교육세"][from_year_str]
        )
        st.session_state.property_tax_rates["지역자원시설세"][to_year_str] = copy.deepcopy(
            st.session_state.property_tax_rates["지역자원시설세"][from_year_str]
        )
        
        # 공정시장가액비율 복사
        if from_year_str in st.session_state.fair_market_ratios:
            st.session_state.fair_market_ratios[to_year_str] = copy.deepcopy(
                st.session_state.fair_market_ratios[from_year_str]
            )
        
        return True, f"{from_year}년 세율을 {to_year}년으로 복사했습니다."
    
    # ===========================================
    # 세율 구간 관리 서비스 (Calculator 연동)
    # ===========================================
    
    def add_rate_bracket(self, year: int, asset_type: str, taxation_type: str, 
                        new_bracket: Dict[str, Any] = None) -> bool:
        """세율 구간 추가"""
        if self.calculator:
            return self.calculator.add_rate_bracket(year, asset_type, taxation_type, new_bracket)
        
        # 폴백: 기본 구간 추가
        year_str = str(year)
        try:
            current_rates = st.session_state.property_tax_rates["재산세"][year_str][asset_type][taxation_type]
            
            if not new_bracket:
                # 마지막 구간 기준으로 새 구간 생성
                if current_rates:
                    last_upper = current_rates[-1]["상한"]
                    new_bracket = {
                        "하한": last_upper if last_upper != float('inf') else 0,
                        "상한": float('inf'),
                        "기본세액": 0,
                        "세율": 0.5
                    }
            
            current_rates.append(new_bracket)
            return True
        except:
            return False
    
    def remove_last_rate_bracket(self, year: int, asset_type: str, taxation_type: str) -> bool:
        """마지막 세율 구간 삭제"""
        if self.calculator:
            return self.calculator.remove_last_rate_bracket(year, asset_type, taxation_type)
        
        # 폴백
        year_str = str(year)
        try:
            current_rates = st.session_state.property_tax_rates["재산세"][year_str][asset_type][taxation_type]
            if len(current_rates) > 1:
                current_rates.pop()
                return True
            return False
        except:
            return False
    
    # ===========================================
    # 무제한값 처리 유틸리티
    # ===========================================
    
    def convert_infinity_for_display(self, value: Any) -> str:
        """표시용 무제한값 변환"""
        if self.core:
            return self.core.convert_infinity_for_display(value)
        
        try:
            if isinstance(value, (int, float)) and value >= self.INFINITY_VALUE:
                return "무제한"
            if value == float('inf'):
                return "무제한"
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)
    
    def format_tax_rate(self, rate: float, precision: int = 3) -> float:
        """세율 정밀도 포맷팅"""
        if self.core:
            return self.core.format_tax_rate(rate, precision)
        
        try:
            from decimal import Decimal, ROUND_HALF_UP
            rate_str = str(float(rate))
            decimal_rate = Decimal(rate_str)
            quantize_target = Decimal('0.' + '0' * precision)
            rounded_decimal = decimal_rate.quantize(quantize_target, rounding=ROUND_HALF_UP)
            return float(rounded_decimal)
        except:
            return round(rate, precision)
    
    def format_tax_rate_for_display(self, rate: float, precision: int = 3, trim_zeros: bool = True) -> str:
        """세율 표시용 포맷팅"""
        if self.core:
            return self.core.format_tax_rate_for_display(rate, precision, trim_zeros)
        
        formatted_rate = self.format_tax_rate(rate, precision)
        
        if trim_zeros:
            format_str = f"{{:.{precision}f}}"
            display_str = format_str.format(formatted_rate).rstrip('0').rstrip('.')
            return display_str
        else:
            return f"{formatted_rate:.{precision}f}"
    
    def validate_and_format_tax_rate_input(self, input_rate: float, precision: int = 3) -> Tuple[bool, float, str]:
        """세율 입력값 검증 및 포맷팅"""
        if self.core:
            return self.core.validate_and_format_tax_rate_input(input_rate, precision)
        
        try:
            if input_rate < 0:
                return False, 0.0, "세율은 0 이상이어야 합니다."
            
            if input_rate > 100:
                return False, 0.0, "세율은 100% 이하여야 합니다."
            
            formatted_rate = self.format_tax_rate(input_rate, precision)
            return True, formatted_rate, ""
        except Exception as e:
            return False, 0.0, f"세율 형식이 올바르지 않습니다: {str(e)}"
            