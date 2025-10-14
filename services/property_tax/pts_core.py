"""
TAXi 지방세 관리 시스템 - 재산세 핵심 관리자 v1.5.2
services/property_tax/pts_core.py

변경사항:
- v1.5.1 → v1.5.2 (긴급 패치: session_state 키 불일치 수정)
- property_calculations → property_tax_calculations 통일 (8곳)
- 데이터 휘발 문제 해결

기능:
- 자산 관리 (CRUD)
- 세율 관리 (CRUD)
- 연도 관리 (2021-2025)
- 데이터 저장/조회
- 통계 분석
- 정밀도 처리 유틸리티
- 영속성 관리 (JSON 파일 저장/로드: 세율 + 자산 + 계산)
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import copy
from decimal import Decimal, ROUND_HALF_UP
import os
import json

class PtsCoreManager:
    """재산세 핵심 데이터 관리자"""
    
    # 상수 정의
    INFINITY_VALUE = 1000000000000
    
    # 영속성 관련 상수
    DATA_DIR = "data"
    RATES_JSON_PATH = os.path.join(DATA_DIR, "property_tax_rates.json")
    ASSETS_JSON_PATH = os.path.join(DATA_DIR, "property_tax_assets.json")
    CALCULATIONS_JSON_PATH = os.path.join(DATA_DIR, "property_tax_calculations.json")
    
    def __init__(self):
        """코어 매니저 초기화"""
        pass
    
    # ===========================================
    # 영속성 관리 (Phase 2 + Phase 3)
    # ===========================================
    
    def save_rates_to_json(self) -> Tuple[bool, str]:
        """세율 데이터를 JSON 파일로 저장 (공정시장가액비율 포함)"""
        try:
            os.makedirs(self.DATA_DIR, exist_ok=True)
            
            rates_data = {
                "재산세": st.session_state.property_tax_rates.get("재산세", {}),
                "재산세_도시지역분": st.session_state.property_tax_rates.get("재산세_도시지역분", {}),
                "지방교육세": st.session_state.property_tax_rates.get("지방교육세", {}),
                "지역자원시설세": st.session_state.property_tax_rates.get("지역자원시설세", {}),
                "공정시장가액비율": st.session_state.fair_market_ratios
            }
            
            with open(self.RATES_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(rates_data, f, ensure_ascii=False, indent=2)
            
            return True, f"세율 데이터가 {self.RATES_JSON_PATH}에 저장되었습니다."
        
        except PermissionError:
            return False, f"파일 쓰기 권한이 없습니다: {self.RATES_JSON_PATH}"
        except Exception as e:
            return False, f"세율 데이터 저장 중 오류: {str(e)}"
    
    def load_rates_from_json(self) -> Tuple[bool, Dict[str, Any], str]:
        """JSON 파일에서 세율 데이터 로드 (공정시장가액비율 포함)"""
        try:
            if not os.path.exists(self.RATES_JSON_PATH):
                return False, {}, f"세율 JSON 파일이 존재하지 않습니다: {self.RATES_JSON_PATH}"
            
            with open(self.RATES_JSON_PATH, 'r', encoding='utf-8') as f:
                rates_data = json.load(f)
            
            required_keys = ["재산세", "재산세_도시지역분", "지방교육세", "지역자원시설세", "공정시장가액비율"]
            if not all(key in rates_data for key in required_keys):
                return False, {}, "JSON 파일에 필수 키가 누락되었습니다."
            
            return True, rates_data, "세율 데이터가 성공적으로 로드되었습니다."
        
        except json.JSONDecodeError as e:
            return False, {}, f"JSON 파일 형식 오류: {str(e)}"
        except PermissionError:
            return False, {}, f"파일 읽기 권한이 없습니다: {self.RATES_JSON_PATH}"
        except Exception as e:
            return False, {}, f"세율 데이터 로드 중 오류: {str(e)}"
    
    def save_assets_to_json(self) -> Tuple[bool, str]:
        """자산 데이터를 JSON 파일로 저장"""
        try:
            os.makedirs(self.DATA_DIR, exist_ok=True)
            
            assets_data = st.session_state.property_tax_assets
            
            with open(self.ASSETS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(assets_data, f, ensure_ascii=False, indent=2)
            
            return True, f"자산 데이터가 {self.ASSETS_JSON_PATH}에 저장되었습니다."
        
        except PermissionError:
            return False, f"파일 쓰기 권한이 없습니다: {self.ASSETS_JSON_PATH}"
        except Exception as e:
            return False, f"자산 데이터 저장 중 오류: {str(e)}"
    
    def load_assets_from_json(self) -> Tuple[bool, Dict[str, Any], str]:
        """JSON 파일에서 자산 데이터 로드"""
        try:
            if not os.path.exists(self.ASSETS_JSON_PATH):
                return False, {}, f"자산 JSON 파일이 존재하지 않습니다: {self.ASSETS_JSON_PATH}"
            
            with open(self.ASSETS_JSON_PATH, 'r', encoding='utf-8') as f:
                assets_data = json.load(f)
            
            if not isinstance(assets_data, dict):
                return False, {}, "JSON 파일 형식이 올바르지 않습니다 (dict 타입 필요)."
            
            return True, assets_data, "자산 데이터가 성공적으로 로드되었습니다."
        
        except json.JSONDecodeError as e:
            return False, {}, f"JSON 파일 형식 오류: {str(e)}"
        except PermissionError:
            return False, {}, f"파일 읽기 권한이 없습니다: {self.ASSETS_JSON_PATH}"
        except Exception as e:
            return False, {}, f"자산 데이터 로드 중 오류: {str(e)}"
    
    def save_calculations_to_json(self) -> Tuple[bool, str]:
        """계산 결과를 JSON 파일로 저장 (Phase 3 신규)"""
        try:
            os.makedirs(self.DATA_DIR, exist_ok=True)
            
            calculations_data = st.session_state.get('property_tax_calculations', {})
            
            with open(self.CALCULATIONS_JSON_PATH, 'w', encoding='utf-8') as f:
                json.dump(calculations_data, f, ensure_ascii=False, indent=2)
            
            return True, f"계산 결과가 {self.CALCULATIONS_JSON_PATH}에 저장되었습니다."
        
        except PermissionError:
            return False, f"파일 쓰기 권한이 없습니다: {self.CALCULATIONS_JSON_PATH}"
        except Exception as e:
            return False, f"계산 결과 저장 중 오류: {str(e)}"
    
    def load_calculations_from_json(self) -> Tuple[bool, Dict[str, Any], str]:
        """JSON 파일에서 계산 결과 로드 (Phase 3 신규)"""
        try:
            if not os.path.exists(self.CALCULATIONS_JSON_PATH):
                return False, {}, f"계산 결과 JSON 파일이 존재하지 않습니다: {self.CALCULATIONS_JSON_PATH}"
            
            with open(self.CALCULATIONS_JSON_PATH, 'r', encoding='utf-8') as f:
                calculations_data = json.load(f)
            
            if not isinstance(calculations_data, dict):
                return False, {}, "JSON 파일 형식이 올바르지 않습니다 (dict 타입 필요)."
            
            return True, calculations_data, "계산 결과가 성공적으로 로드되었습니다."
        
        except json.JSONDecodeError as e:
            return False, {}, f"JSON 파일 형식 오류: {str(e)}"
        except PermissionError:
            return False, {}, f"파일 읽기 권한이 없습니다: {self.CALCULATIONS_JSON_PATH}"
        except Exception as e:
            return False, {}, f"계산 결과 로드 중 오류: {str(e)}"
    
    def get_calculation_history(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """저장된 계산 결과 이력 조회 (Phase 3 신규)"""
        try:
            calculations = st.session_state.get('property_tax_calculations', {})
            
            if not filters:
                return [{"calc_key": k, **v} for k, v in calculations.items()]
            
            filtered_results = []
            for calc_key, calc_data in calculations.items():
                match = True
                
                if 'year' in filters and calc_data.get('계산연도') != filters['year']:
                    match = False
                
                if 'group_id' in filters and calc_data.get('그룹ID') != filters['group_id']:
                    match = False
                
                if match:
                    filtered_results.append({"calc_key": calc_key, **calc_data})
            
            return filtered_results
        
        except Exception as e:
            print(f"계산 결과 이력 조회 중 오류: {str(e)}")
            return []
    
    # ===========================================
    # 데이터 초기화
    # ===========================================
    
    def initialize_default_data(self) -> None:
        """기본 데이터 초기화 (JSON 우선 로드)"""
        
        if 'property_tax_assets' not in st.session_state:
            success, loaded_assets, msg = self.load_assets_from_json()
            
            if success:
                st.session_state.property_tax_assets = loaded_assets
                print(f"✅ {msg}")
            else:
                st.session_state.property_tax_assets = self._get_default_assets()
                print(f"⚠️ {msg} - 기본 자산 사용")
                
                save_success, save_msg = self.save_assets_to_json()
                if save_success:
                    print(f"✅ {save_msg}")
                else:
                    print(f"⚠️ {save_msg}")
        
        if 'property_tax_rates' not in st.session_state:
            success, loaded_rates, msg = self.load_rates_from_json()
            
            if success:
                st.session_state.property_tax_rates = {
                    "재산세": loaded_rates.get("재산세", {}),
                    "재산세_도시지역분": loaded_rates.get("재산세_도시지역분", {}),
                    "지방교육세": loaded_rates.get("지방교육세", {}),
                    "지역자원시설세": loaded_rates.get("지역자원시설세", {})
                }
                print(f"✅ {msg}")
            else:
                st.session_state.property_tax_rates = self._get_default_rates()
                print(f"⚠️ {msg} - 기본 세율 사용")
                
                save_success, save_msg = self.save_rates_to_json()
                if save_success:
                    print(f"✅ {save_msg}")
                else:
                    print(f"⚠️ {save_msg}")
        
        if 'fair_market_ratios' not in st.session_state:
            success, loaded_rates, msg = self.load_rates_from_json()
            
            if success and "공정시장가액비율" in loaded_rates:
                st.session_state.fair_market_ratios = loaded_rates["공정시장가액비율"]
                print(f"✅ 공정시장가액비율 JSON에서 로드 완료")
            else:
                st.session_state.fair_market_ratios = self._get_default_ratios()
                print(f"⚠️ 공정시장가액비율 기본값 사용")
        
        if 'property_tax_calculations' not in st.session_state:
            success, loaded_calculations, msg = self.load_calculations_from_json()
            
            if success:
                st.session_state.property_tax_calculations = loaded_calculations
                print(f"✅ {msg}")
            else:
                st.session_state.property_tax_calculations = {}
                print(f"⚠️ {msg} - 빈 계산 결과로 시작")
        
        if 'property_calculations' not in st.session_state:
            st.session_state.property_tax_calculations = {}
        
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
        """실제 적용 세율 데이터 반환"""
        years = ["2021", "2022", "2023", "2024", "2025"]
        rates_data = {
            "재산세": {},
            "재산세_도시지역분": {},
            "지방교육세": {},
            "지역자원시설세": {}
        }
        
        for year in years:
            rates_data["재산세"][year] = {
                "토지": {
                    "종합합산": [
                        {"하한": 0, "상한": 50000000, "기본세액": 0, "세율": self.format_tax_rate(0.2, 3)},
                        {"하한": 50000000, "상한": 100000000, "기본세액": 100000, "세율": self.format_tax_rate(0.3, 3)},
                        {"하한": 100000000, "상한": self.INFINITY_VALUE, "기본세액": 250000, "세율": self.format_tax_rate(0.5, 3)}
                    ],
                    "별도합산": [
                        {"하한": 0, "상한": 200000000, "기본세액": 0, "세율": self.format_tax_rate(0.2, 3)},
                        {"하한": 200000000, "상한": 1000000000, "기본세액": 400000, "세율": self.format_tax_rate(0.3, 3)},
                        {"하한": 1000000000, "상한": self.INFINITY_VALUE, "기본세액": 2800000, "세율": self.format_tax_rate(0.4, 3)}
                    ],
                    "분리과세": [
                        {"하한": 0, "상한": self.INFINITY_VALUE, "기본세액": 0, "세율": self.format_tax_rate(0.2, 3)}
                    ]
                },
                "건축물": {
                    "기타": [
                        {"하한": 0, "상한": self.INFINITY_VALUE, "기본세액": 0, "세율": self.format_tax_rate(0.25, 3)}
                    ]
                },
                "주택": {
                    "기타": [
                        {"하한": 0, "상한": 60000000, "기본세액": 0, "세율": self.format_tax_rate(0.1, 3)},
                        {"하한": 60000000, "상한": 150000000, "기본세액": 60000, "세율": self.format_tax_rate(0.15, 3)},
                        {"하한": 150000000, "상한": 300000000, "기본세액": 195000, "세율": self.format_tax_rate(0.25, 3)},
                        {"하한": 300000000, "상한": self.INFINITY_VALUE, "기본세액": 570000, "세율": self.format_tax_rate(0.4, 3)}
                    ]
                }
            }
            
            rates_data["재산세_도시지역분"][year] = {"비율": self.format_tax_rate(0.14, 3)}
            rates_data["지방교육세"][year] = {"비율": self.format_tax_rate(0.2, 3)}
            
            rates_data["지역자원시설세"][year] = [
                {"하한": 0, "상한": 6000000, "기본세액": 0, "세율": self.format_tax_rate(0.04, 4)},
                {"하한": 6000000, "상한": 13000000, "기본세액": 2400, "세율": self.format_tax_rate(0.05, 4)},
                {"하한": 13000000, "상한": 26000000, "기본세액": 5900, "세율": self.format_tax_rate(0.06, 4)},
                {"하한": 26000000, "상한": 39000000, "기본세액": 13700, "세율": self.format_tax_rate(0.08, 4)},
                {"하한": 39000000, "상한": 64000000, "기본세액": 24100, "세율": self.format_tax_rate(0.1, 4)},
                {"하한": 64000000, "상한": self.INFINITY_VALUE, "기본세액": 49100, "세율": self.format_tax_rate(0.12, 4)}
            ]
        
        return rates_data
    
    def _get_default_ratios(self) -> Dict[str, Any]:
        """기본 공정시장가액비율 반환 (2021-2025)"""
        ratios = {}
        years = ["2021", "2022", "2023", "2024", "2025"]
        
        for year in years:
            ratios[year] = {
                "토지": 70.0,
                "건축물": 70.0,
                "주택": 60.0
            }
        
        return ratios
    
    # ===========================================
    # 무제한값 처리 및 정밀도 유틸리티
    # ===========================================
    
    def convert_infinity_for_display(self, value: Any) -> str:
        """표시용 무제한값 변환"""
        try:
            if isinstance(value, (int, float)) and value >= self.INFINITY_VALUE:
                return "무제한"
            return f"{int(value):,}"
        except (ValueError, TypeError):
            return str(value)
    
    def convert_infinity_for_calculation(self, value: Any) -> float:
        """계산용 무제한값 변환"""
        try:
            if isinstance(value, (int, float)) and value >= self.INFINITY_VALUE:
                return float('inf')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def convert_display_to_infinity(self, display_value: str) -> Any:
        """표시값을 저장값으로 변환"""
        if display_value in ["무제한", "∞", "infinity", ""]:
            return self.INFINITY_VALUE
        try:
            clean_value = display_value.replace(",", "").replace(" ", "")
            return int(float(clean_value))
        except (ValueError, TypeError):
            return self.INFINITY_VALUE
    
    def format_tax_rate(self, rate: float, precision: int = 3) -> float:
        """세율 정밀도 포맷팅 (Decimal 기반 정확한 반올림)"""
        try:
            if rate is None:
                return 0.0
            
            rate_str = str(float(rate))
            decimal_rate = Decimal(rate_str)
            quantize_target = Decimal('0.' + '0' * precision)
            rounded_decimal = decimal_rate.quantize(quantize_target, rounding=ROUND_HALF_UP)
            
            return float(rounded_decimal)
            
        except (ValueError, TypeError, Exception):
            return 0.0
    
    def format_tax_rate_for_display(self, rate: float, precision: int = 3, trim_zeros: bool = True) -> str:
        """세율 표시용 포맷팅"""
        try:
            formatted_rate = self.format_tax_rate(rate, precision)
            
            if trim_zeros:
                format_str = f"{{:.{precision}f}}"
                display_str = format_str.format(formatted_rate).rstrip('0').rstrip('.')
                
                if '.' not in display_str and formatted_rate != int(formatted_rate):
                    display_str = f"{formatted_rate:.1f}"
                    
                return display_str
            else:
                format_str = f"{{:.{precision}f}}"
                return format_str.format(formatted_rate)
                
        except (ValueError, TypeError, Exception):
            return "0.0"
    
    def validate_and_format_tax_rate_input(self, input_rate: float, precision: int = 3) -> Tuple[bool, float, str]:
        """세율 입력값 검증 및 포맷팅"""
        try:
            if input_rate < 0:
                return False, 0.0, "세율은 0 이상이어야 합니다."
            
            if input_rate > 100:
                return False, 0.0, "세율은 100% 이하여야 합니다."
            
            formatted_rate = self.format_tax_rate(input_rate, precision)
            
            return True, formatted_rate, ""
            
        except (ValueError, TypeError, Exception) as e:
            return False, 0.0, f"세율 형식이 올바르지 않습니다: {str(e)}"
    
    # ===========================================
    # 연도 관리 서비스
    # ===========================================
    
    def get_all_available_years(self) -> List[int]:
        """모든 사용 가능한 연도 목록 조회"""
        try:
            years = set()
            
            tax_types = ["재산세", "재산세_도시지역분", "지방교육세", "지역자원시설세"]
            for tax_type in tax_types:
                if tax_type in st.session_state.property_tax_rates:
                    years.update(int(year) for year in st.session_state.property_tax_rates[tax_type].keys())
            
            for asset in st.session_state.property_tax_assets.values():
                for year in asset["연도별데이터"].keys():
                    years.add(int(year))
            
            if not years:
                years.add(datetime.now().year)
            
            return sorted(list(years), reverse=True)
        
        except Exception as e:
            print(f"연도 목록 조회 중 오류: {str(e)}")
            return [datetime.now().year]
    
    def validate_year_input(self, year: int) -> Tuple[bool, str]:
        """연도 입력값 유효성 검증"""
        current_year = datetime.now().year
        
        if year < 2020 or year > current_year + 10:
            return False, f"연도는 2020년부터 {current_year + 10}년 사이여야 합니다."
        
        if str(year) in st.session_state.property_tax_rates.get("재산세", {}):
            return False, f"{year}년 세율 데이터가 이미 존재합니다."
        
        return True, ""
    
    def create_default_year_rates(self, year: int, base_year: int = None) -> Dict[str, Any]:
        """새 연도 기본 세율 데이터 생성"""
        year_str = str(year)
        base_year_str = str(base_year) if base_year else None
        
        if base_year_str and base_year_str in st.session_state.property_tax_rates.get("재산세", {}):
            return {
                "재산세": {year_str: copy.deepcopy(st.session_state.property_tax_rates["재산세"][base_year_str])},
                "재산세_도시지역분": {year_str: copy.deepcopy(st.session_state.property_tax_rates["재산세_도시지역분"][base_year_str])},
                "지방교육세": {year_str: copy.deepcopy(st.session_state.property_tax_rates["지방교육세"][base_year_str])},
                "지역자원시설세": {year_str: copy.deepcopy(st.session_state.property_tax_rates["지역자원시설세"][base_year_str])}
            }
        
        return {
            "재산세": {
                year_str: {
                    "토지": {
                        "종합합산": [
                            {"하한": 0, "상한": 50000000, "기본세액": 0, "세율": self.format_tax_rate(0.2, 3)},
                            {"하한": 50000000, "상한": 100000000, "기본세액": 100000, "세율": self.format_tax_rate(0.3, 3)},
                            {"하한": 100000000, "상한": self.INFINITY_VALUE, "기본세액": 250000, "세율": self.format_tax_rate(0.5, 3)}
                        ],
                        "별도합산": [
                            {"하한": 0, "상한": 200000000, "기본세액": 0, "세율": self.format_tax_rate(0.2, 3)},
                            {"하한": 200000000, "상한": 1000000000, "기본세액": 400000, "세율": self.format_tax_rate(0.3, 3)},
                            {"하한": 1000000000, "상한": self.INFINITY_VALUE, "기본세액": 2800000, "세율": self.format_tax_rate(0.4, 3)}
                        ],
                        "분리과세": [
                            {"하한": 0, "상한": self.INFINITY_VALUE, "기본세액": 0, "세율": self.format_tax_rate(0.2, 3)}
                        ]
                    },
                    "건축물": {
                        "기타": [
                            {"하한": 0, "상한": self.INFINITY_VALUE, "기본세액": 0, "세율": self.format_tax_rate(0.25, 3)}
                        ]
                    },
                    "주택": {
                        "기타": [
                            {"하한": 0, "상한": 60000000, "기본세액": 0, "세율": self.format_tax_rate(0.1, 3)},
                            {"하한": 60000000, "상한": 150000000, "기본세액": 60000, "세율": self.format_tax_rate(0.15, 3)},
                            {"하한": 150000000, "상한": 300000000, "기본세액": 195000, "세율": self.format_tax_rate(0.25, 3)},
                            {"하한": 300000000, "상한": self.INFINITY_VALUE, "기본세액": 570000, "세율": self.format_tax_rate(0.4, 3)}
                        ]
                    }
                }
            },
            "재산세_도시지역분": {year_str: {"비율": self.format_tax_rate(0.14, 3)}},
            "지방교육세": {year_str: {"비율": self.format_tax_rate(0.2, 3)}},
            "지역자원시설세": {
                year_str: [
                    {"하한": 0, "상한": 6000000, "기본세액": 0, "세율": self.format_tax_rate(0.04, 4)},
                    {"하한": 6000000, "상한": 13000000, "기본세액": 2400, "세율": self.format_tax_rate(0.05, 4)},
                    {"하한": 13000000, "상한": 26000000, "기본세액": 5900, "세율": self.format_tax_rate(0.06, 4)},
                    {"하한": 26000000, "상한": 39000000, "기본세액": 13700, "세율": self.format_tax_rate(0.08, 4)},
                    {"하한": 39000000, "상한": 64000000, "기본세액": 24100, "세율": self.format_tax_rate(0.1, 4)},
                    {"하한": 64000000, "상한": self.INFINITY_VALUE, "기본세액": 49100, "세율": self.format_tax_rate(0.12, 4)}
                ]
            }
        }
    
    def add_tax_year(self, new_year: int, base_year: int = None) -> Tuple[bool, str]:
        """새 연도 세율 데이터 추가 (자동 저장 포함)"""
        try:
            is_valid, error_msg = self.validate_year_input(new_year)
            if not is_valid:
                return False, error_msg
            
            if base_year:
                available_years = self.get_all_available_years()
                if base_year not in available_years:
                    return False, f"기준 연도 {base_year}년 데이터가 존재하지 않습니다."
            
            new_year_data = self.create_default_year_rates(new_year, base_year)
            
            for rate_type, year_data in new_year_data.items():
                if rate_type not in st.session_state.property_tax_rates:
                    st.session_state.property_tax_rates[rate_type] = {}
                st.session_state.property_tax_rates[rate_type].update(year_data)
            
            year_str = str(new_year)
            if year_str not in st.session_state.fair_market_ratios:
                if base_year and str(base_year) in st.session_state.fair_market_ratios:
                    st.session_state.fair_market_ratios[year_str] = copy.deepcopy(
                        st.session_state.fair_market_ratios[str(base_year)]
                    )
                else:
                    st.session_state.fair_market_ratios[year_str] = {
                        "토지": 70.0, "건축물": 70.0, "주택": 60.0
                    }
            
            save_success, save_msg = self.save_rates_to_json()
            if not save_success:
                print(f"⚠️ {save_msg}")
            
            base_msg = f"기준: {base_year}년 복사" if base_year else "기준: 실제 적용 세율"
            return True, f"{new_year}년 세율 데이터가 성공적으로 추가되었습니다. ({base_msg})"
        
        except Exception as e:
            return False, f"연도 추가 중 오류가 발생했습니다: {str(e)}"
    
    def check_year_dependencies(self, year: int) -> List[str]:
        """연도 삭제 전 의존성 체크"""
        dependencies = []
        year_str = str(year)
        
        for asset_id, asset_data in st.session_state.property_tax_assets.items():
            if year_str in asset_data.get("연도별데이터", {}):
                dependencies.append(f"자산 '{asset_data['자산명']}' ({asset_id})에서 사용 중")
        
        for calc_key, calc_data in st.session_state.property_tax_calculations.items():
            if calc_data.get("연도") == year:
                dependencies.append(f"계산 결과 '{calc_key}'에서 사용 중")
        
        return dependencies
    
    def delete_tax_year(self, year: int) -> Tuple[bool, str]:
        """연도 세율 데이터 삭제 (자동 저장 포함)"""
        try:
            year_str = str(year)
            available_years = self.get_all_available_years()
            
            if year not in available_years:
                return False, f"{year}년 세율 데이터가 존재하지 않습니다."
            
            if len(available_years) <= 1:
                return False, "최소 1개 연도의 세율 데이터는 유지되어야 합니다."
            
            dependencies = self.check_year_dependencies(year)
            if dependencies:
                return False, f"{year}년 데이터를 삭제할 수 없습니다. 다음에서 사용 중입니다:\n" + "\n".join(dependencies)
            
            tax_types = ["재산세", "재산세_도시지역분", "지방교육세", "지역자원시설세"]
            for tax_type in tax_types:
                if tax_type in st.session_state.property_tax_rates:
                    if year_str in st.session_state.property_tax_rates[tax_type]:
                        del st.session_state.property_tax_rates[tax_type][year_str]
            
            if year_str in st.session_state.fair_market_ratios:
                del st.session_state.fair_market_ratios[year_str]
            
            save_success, save_msg = self.save_rates_to_json()
            if not save_success:
                print(f"⚠️ {save_msg}")
            
            return True, f"{year}년 세율 데이터가 성공적으로 삭제되었습니다."
        
        except Exception as e:
            return False, f"연도 삭제 중 오류가 발생했습니다: {str(e)}"
    
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
        
        required_fields = ["자산ID", "자산명", "자산유형", "그룹ID", "시도", "시군구", "면적"]
        for field in required_fields:
            if not asset_data.get(field):
                errors.append(f"{field}은(는) 필수 입력 항목입니다.")
        
        valid_asset_types = ["토지", "건축물", "주택"]
        if asset_data.get("자산유형") not in valid_asset_types:
            errors.append("자산유형은 토지, 건축물, 주택 중 하나여야 합니다.")
        
        asset_type = asset_data.get("자산유형")
        taxation_type = asset_data.get("과세유형")
        valid_taxation_types = self.get_taxation_types_for_asset_type(asset_type)
        
        if taxation_type not in valid_taxation_types:
            errors.append(f"{asset_type}의 과세유형은 {', '.join(valid_taxation_types)} 중 하나여야 합니다.")
        
        urban_area = asset_data.get("재산세_도시지역분")
        if urban_area not in ["Y", "N"]:
            errors.append("재산세 도시지역분은 Y 또는 N이어야 합니다.")
        
        try:
            area = float(asset_data.get("면적", 0))
            if area <= 0:
                errors.append("면적은 0보다 큰 값이어야 합니다.")
        except (ValueError, TypeError):
            errors.append("면적은 숫자여야 합니다.")
        
        return len(errors) == 0, errors
    
    def create_asset(self, asset_data: Dict[str, Any]) -> Tuple[bool, str]:
        """자산 생성 (자동 저장 포함)"""
        is_valid, errors = self.validate_asset_data(asset_data)
        if not is_valid:
            return False, "; ".join(errors)
        
        asset_id = asset_data["자산ID"]
        
        if asset_id in st.session_state.property_tax_assets:
            return False, f"자산ID '{asset_id}'는 이미 존재합니다."
        
        st.session_state.property_tax_assets[asset_id] = asset_data
        
        save_success, save_msg = self.save_assets_to_json()
        if not save_success:
            print(f"⚠️ {save_msg}")
        
        return True, f"자산 '{asset_data['자산명']}' ({asset_id})이 성공적으로 등록되었습니다."
    
    def update_asset(self, asset_id: str, asset_data: Dict[str, Any]) -> Tuple[bool, str]:
        """자산 수정 (자동 저장 포함)"""
        if asset_id not in st.session_state.property_tax_assets:
            return False, f"자산ID '{asset_id}'를 찾을 수 없습니다."
        
        is_valid, errors = self.validate_asset_data(asset_data)
        if not is_valid:
            return False, "; ".join(errors)
        
        st.session_state.property_tax_assets[asset_id] = asset_data
        
        save_success, save_msg = self.save_assets_to_json()
        if not save_success:
            print(f"⚠️ {save_msg}")
        
        return True, f"자산 '{asset_data['자산명']}' ({asset_id})이 성공적으로 수정되었습니다."
    
    def delete_asset(self, asset_id: str) -> Tuple[bool, str]:
        """자산 삭제 (자동 저장 포함)"""
        if asset_id not in st.session_state.property_tax_assets:
            return False, f"자산ID '{asset_id}'를 찾을 수 없습니다."
        
        asset_name = st.session_state.property_tax_assets[asset_id]["자산명"]
        del st.session_state.property_tax_assets[asset_id]
        
        save_success, save_msg = self.save_assets_to_json()
        if not save_success:
            print(f"⚠️ {save_msg}")
        
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
        """재산세율 수정 (정밀도 개선 + 자동 저장)"""
        try:
            year_str = str(year)
            
            if "재산세" not in st.session_state.property_tax_rates:
                st.session_state.property_tax_rates["재산세"] = {}
            
            if year_str not in st.session_state.property_tax_rates["재산세"]:
                st.session_state.property_tax_rates["재산세"][year_str] = {}
            
            if asset_type not in st.session_state.property_tax_rates["재산세"][year_str]:
                st.session_state.property_tax_rates["재산세"][year_str][asset_type] = {}
            
            validated_rates = []
            for i, rate in enumerate(rates):
                try:
                    required_keys = ["하한", "상한", "기본세액", "세율"]
                    if not all(key in rate for key in required_keys):
                        return False, f"구간 {i+1}에서 필수 항목이 누락되었습니다."
                    
                    is_valid, formatted_rate, error_msg = self.validate_and_format_tax_rate_input(rate["세율"], 3)
                    if not is_valid:
                        return False, f"구간 {i+1} {error_msg}"
                    
                    lower_limit = int(float(rate["하한"])) if rate["하한"] != self.INFINITY_VALUE else 0
                    
                    upper_limit = rate["상한"]
                    if isinstance(upper_limit, (int, float)) and upper_limit >= self.INFINITY_VALUE:
                        upper_limit = self.INFINITY_VALUE
                    elif upper_limit == float('inf'):
                        upper_limit = self.INFINITY_VALUE
                    else:
                        upper_limit = int(float(upper_limit))
                    
                    validated_rate = {
                        "하한": lower_limit,
                        "상한": upper_limit,
                        "기본세액": int(float(rate["기본세액"])),
                        "세율": formatted_rate
                    }
                    
                    if validated_rate["하한"] < 0:
                        return False, f"구간 {i+1}의 하한은 0 이상이어야 합니다."
                    
                    if validated_rate["기본세액"] < 0:
                        return False, f"구간 {i+1}의 기본세액은 0 이상이어야 합니다."
                    
                    if i > 0 and validated_rates:
                        prev_upper = validated_rates[i-1]["상한"]
                        if prev_upper != self.INFINITY_VALUE and validated_rate["하한"] != prev_upper:
                            return False, f"구간 {i+1}의 하한({validated_rate['하한']:,})이 이전 구간의 상한({prev_upper:,})과 연결되지 않습니다."
                    
                    validated_rates.append(validated_rate)
                    
                except (ValueError, TypeError) as e:
                    return False, f"구간 {i+1}에서 숫자 형식 오류: {str(e)}"
            
            st.session_state.property_tax_rates["재산세"][year_str][asset_type][taxation_type] = validated_rates
            
            save_success, save_msg = self.save_rates_to_json()
            if not save_success:
                print(f"⚠️ {save_msg}")
            
            return True, f"{year}년 {asset_type} {taxation_type} 세율이 성공적으로 수정되었습니다."
        
        except Exception as e:
            return False, f"세율 수정 중 오류가 발생했습니다: {str(e)}"
    
    def get_urban_area_tax_rate(self, year: int) -> float:
        """재산세 도시지역분 세율 조회"""
        try:
            rate = st.session_state.property_tax_rates["재산세_도시지역분"][str(year)]["비율"]
            return self.format_tax_rate(rate, 3)
        except KeyError:
            return self.format_tax_rate(0.14, 3)
    
    def update_urban_area_tax_rate(self, year: int, rate: float) -> Tuple[bool, str]:
        """재산세 도시지역분 세율 수정 (자동 저장 포함)"""
        try:
            is_valid, formatted_rate, error_msg = self.validate_and_format_tax_rate_input(rate, 3)
            if not is_valid:
                return False, error_msg
            
            if formatted_rate > 1:
                return False, "세율은 1% 이하여야 합니다."
            
            st.session_state.property_tax_rates["재산세_도시지역분"][str(year)]["비율"] = formatted_rate
            
            save_success, save_msg = self.save_rates_to_json()
            if not save_success:
                print(f"⚠️ {save_msg}")
            
            return True, f"{year}년 재산세 도시지역분 세율이 {self.format_tax_rate_for_display(formatted_rate, 3)}%로 수정되었습니다."
        
        except Exception as e:
            return False, f"세율 수정 중 오류가 발생했습니다: {str(e)}"
    
    def get_fair_market_ratio(self, year: int, asset_type: str) -> float:
        """공정시장가액비율 조회"""
        try:
            ratio = st.session_state.fair_market_ratios[str(year)][asset_type]
            return self.format_tax_rate(ratio, 1)
        except KeyError:
            return 70.0
    
    def update_fair_market_ratios(self, ratios: Dict[str, Dict[str, float]]) -> Tuple[bool, str]:
        """공정시장가액비율 수정 (자동 저장 포함)"""
        try:
            formatted_ratios = {}
            
            for year, year_ratios in ratios.items():
                formatted_ratios[year] = {}
                for asset_type, ratio in year_ratios.items():
                    formatted_ratio = self.format_tax_rate(ratio, 1)
                    if formatted_ratio < 0 or formatted_ratio > 100:
                        return False, f"{year}년 {asset_type}의 비율은 0과 100 사이여야 합니다."
                    formatted_ratios[year][asset_type] = formatted_ratio
            
            st.session_state.fair_market_ratios = formatted_ratios
            
            save_success, save_msg = self.save_rates_to_json()
            if not save_success:
                print(f"⚠️ {save_msg}")
            
            return True, "공정시장가액비율이 성공적으로 수정되었습니다."
        
        except Exception as e:
            return False, f"비율 수정 중 오류가 발생했습니다: {str(e)}"
    
    # ===========================================
    # 통계 및 분석 서비스 (v1.5.1 복원)
    # ===========================================
    
    def get_asset_statistics(self) -> Dict[str, Any]:
        """자산 통계 조회 (한글 키 사용)"""
        assets = self.get_all_assets()
        
        if not assets:
            return {
                "총_자산수": 0,
                "자산유형별": {},
                "과세유형별": {},
                "도시지역분별": {},
                "그룹별": {},
                "지역별": {},
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
            asset_type = asset_data["자산유형"]
            type_counts[asset_type] = type_counts.get(asset_type, 0) + 1
            
            taxation_type = asset_data.get("과세유형", "기타")
            taxation_counts[taxation_type] = taxation_counts.get(taxation_type, 0) + 1
            
            urban_area = asset_data.get("재산세_도시지역분", "N")
            urban_area_counts[urban_area] = urban_area_counts.get(urban_area, 0) + 1
            
            group_id = asset_data["그룹ID"]
            group_counts[group_id] = group_counts.get(group_id, 0) + 1
            
            region = asset_data["시도"]
            region_counts[region] = region_counts.get(region, 0) + 1
            
            if asset_data["연도별데이터"]:
                latest_year = max(asset_data["연도별데이터"].keys())
                latest_data = asset_data["연도별데이터"][latest_year]
                total_value += latest_data["시가표준액"]
        
        return {
            "총_자산수": len(assets),
            "자산유형별": type_counts,
            "과세유형별": taxation_counts,
            "도시지역분별": urban_area_counts,
            "그룹별": group_counts,
            "지역별": region_counts,
            "총_시가표준액": total_value,
            "평균_자산가액": total_value // len(assets) if len(assets) > 0 else 0
        }
    
    # ===========================================
    # 결과 관리 서비스
    # ===========================================
    
    def save_calculation_result(self, calc_key: str, calculation_data: Dict[str, Any]) -> bool:
        """계산 결과 저장"""
        try:
            st.session_state.property_tax_calculations[calc_key] = calculation_data
            return True
        except Exception as e:
            print(f"계산 결과 저장 중 오류: {str(e)}")
            return False
    
    def get_calculation_result(self, calc_key: str) -> Optional[Dict[str, Any]]:
        """계산 결과 조회"""
        return st.session_state.property_tax_calculations.get(calc_key)
    
    def get_all_calculation_results(self) -> Dict[str, Any]:
        """모든 계산 결과 조회"""
        return st.session_state.property_tax_calculations
    
    def delete_calculation_result(self, calc_key: str) -> bool:
        """계산 결과 삭제"""
        try:
            if calc_key in st.session_state.property_tax_calculations:
                del st.session_state.property_tax_calculations[calc_key]
                return True
            return False
        except Exception as e:
            print(f"계산 결과 삭제 중 오류: {str(e)}")
            return False
    
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
    # 유틸리티 메서드 (v1.5.1 복원)
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
    
    def clear_all_data(self) -> bool:
        """모든 데이터 초기화"""
        try:
            st.session_state.property_tax_assets = {}
            st.session_state.property_tax_calculations = {}
            st.session_state.property_comparisons = {}
            st.session_state.property_finalizations = {}
            return True
        except Exception as e:
            print(f"데이터 초기화 중 오류: {str(e)}")
            return False