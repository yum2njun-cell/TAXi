"""
TAXi 지방세 관리 시스템 - 재산세 계산기 v1.1.0
services/property_tax/pts_calculator.py

기능:
- 세액 계산 (개별/그룹)
- 누진세 계산
- 엑셀 데이터 처리
- 유효성 검증
- 활동 로깅
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from utils.activity_logger import log_excel_generation_activity, log_file_processing_activity

class PtsCalculator:
    """재산세 계산 엔진"""
    
    # 상수 정의
    INFINITY_VALUE = 1000000000000  # 1조원 (무제한 구간 대체값)
    
    def __init__(self, core_manager):
        """계산기 초기화"""
        self.core = core_manager
    
    # ===========================================
    # 무제한값 처리 유틸리티
    # ===========================================
    
    def convert_infinity_for_calculation(self, value: Any) -> float:
        """계산용 무제한값 변환"""
        try:
            if isinstance(value, (int, float)) and value >= self.INFINITY_VALUE:
                return float('inf')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    # ===========================================
    # 세액 계산 서비스
    # ===========================================
    
    def calculate_progressive_tax(self, base_amount: float, tax_brackets: List[Dict[str, Any]]) -> float:
        """누진세 계산 (INFINITY_VALUE 처리)"""
        total_tax = 0
        remaining_amount = base_amount
        
        for bracket in tax_brackets:
            if remaining_amount <= 0:
                break
            
            # INFINITY_VALUE를 계산시에는 float('inf')로 변환
            upper_limit = self.convert_infinity_for_calculation(bracket["상한"])
            bracket_size = upper_limit - bracket["하한"] if upper_limit != float('inf') else remaining_amount
            taxable_in_bracket = min(remaining_amount, bracket_size)
            
            bracket_tax = bracket["기본세액"] + (taxable_in_bracket * bracket["세율"] / 100)
            total_tax += bracket_tax
            remaining_amount -= taxable_in_bracket
            
            if upper_limit == float('inf'):
                break
        
        return total_tax
    
    def calculate_property_tax_for_asset(self, asset_id: str, year: int) -> Optional[Dict[str, Any]]:
        """개별 자산 재산세 계산 (중과세 로직 유지)"""
        try:
            # 자산 데이터 조회
            asset_data = self.core.get_asset(asset_id)
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
            ratio = self.core.get_fair_market_ratio(year, asset_type) / 100
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
            
            # 4. 재산세 계산 (중과세 적용 제거)
            tax_brackets = self.core.get_property_tax_rates(year, asset_type, taxation_type)
            if not tax_brackets:
                return None
            
            calculation_process.append(f"5. 재산세 계산 ({asset_type} - {taxation_type} 과세유형):")
            
            property_tax = self.calculate_progressive_tax(taxable_amount, tax_brackets)
            calculation_process.append(f"6. 재산세 = {property_tax:,.0f}원")
            
            # 중과세율은 참고용으로만 표시 (적용하지 않음)
            surcharge_rate = year_data.get("중과세율", 0)
            if surcharge_rate > 0:
                calculation_process.append(f"   * 참고: 중과세율 {surcharge_rate:.2f}% 설정됨 (재산세에는 미적용)")
            
            # 5. 부대세 계산
            # 재산세 도시지역분
            urban_area_tax = 0
            if asset_data.get("재산세_도시지역분", "N") == "Y":
                urban_area_rate = self.core.get_urban_area_tax_rate(year) / 100
                urban_area_tax = property_tax * urban_area_rate
                calculation_process.append(f"7. 재산세 도시지역분 = {property_tax:,.0f} × {urban_area_rate*100:.3f}% = {urban_area_tax:,.0f}원 (도시지역 적용)")
            else:
                calculation_process.append(f"7. 재산세 도시지역분 = 0원 (도시지역 미적용)")
            
            # 지방교육세
            education_tax_rate = st.session_state.property_tax_rates["지방교육세"][str(year)]["비율"]
            education_tax = property_tax * education_tax_rate
            calculation_process.append(f"8. 지방교육세 = {property_tax:,.0f} × {education_tax_rate*100:.1f}% = {education_tax:,.0f}원")
            
            # 지역자원시설세 (중과세 적용)
            regional_brackets = st.session_state.property_tax_rates["지역자원시설세"][str(year)]
            regional_tax_before_surcharge = self.calculate_progressive_tax(base_amount, regional_brackets)
            
            # 지역자원시설세에 중과세 적용
            surcharge_rate = year_data.get("중과세율", 0) / 100
            if surcharge_rate > 0:
                surcharge_amount = regional_tax_before_surcharge * surcharge_rate
                regional_tax = regional_tax_before_surcharge + surcharge_amount
                calculation_process.append(f"9. 지역자원시설세(중과전) = {regional_tax_before_surcharge:,.0f}원 (기준금액 {base_amount:,}원 기준 누진계산)")
                calculation_process.append(f"10. 지역자원시설세 중과세액 = {regional_tax_before_surcharge:,.0f} × {surcharge_rate*100:.2f}% = {surcharge_amount:,.0f}원")
                calculation_process.append(f"11. 지역자원시설세(최종) = {regional_tax_before_surcharge:,.0f} + {surcharge_amount:,.0f} = {regional_tax:,.0f}원")
            else:
                regional_tax = regional_tax_before_surcharge
                calculation_process.append(f"9. 지역자원시설세 = {regional_tax:,.0f}원 (기준금액 {base_amount:,}원 기준 누진계산, 중과세 없음)")
            
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
            
            # 활동 로그 추가
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
    # 세율 구간 관리
    # ===========================================
    
    def add_rate_bracket(self, year: int, asset_type: str, taxation_type: str, new_bracket: Dict[str, Any] = None) -> bool:
        """세율 구간 추가 (정밀도 처리 버전)"""
        try:
            year_str = str(year)
            
            # 경로 존재 확인
            if (year_str not in st.session_state.property_tax_rates.get("재산세", {}) or
                asset_type not in st.session_state.property_tax_rates["재산세"][year_str] or
                taxation_type not in st.session_state.property_tax_rates["재산세"][year_str][asset_type]):
                return False
            
            # 현재 구간 목록
            current_brackets = st.session_state.property_tax_rates["재산세"][year_str][asset_type][taxation_type]
            
            # 기본 새 구간 생성
            if not new_bracket:
                if current_brackets:
                    # 마지막 구간의 상한을 새 구간의 하한으로
                    last_bracket = current_brackets[-1]
                    last_upper = last_bracket["상한"]
                    
                    if last_upper == self.INFINITY_VALUE:
                        # 마지막이 무제한이면 그 앞에 구간 삽입
                        new_lower = last_bracket["하한"] + 100000000  # 1억원씩 증가
                        new_bracket = {
                            "하한": new_lower,
                            "상한": self.INFINITY_VALUE,
                            "기본세액": 0,
                            "세율": self.core.format_tax_rate(0.5, 3)  # 정밀도 처리
                        }
                        # 기존 마지막 구간의 상한을 조정
                        current_brackets[-1]["상한"] = new_lower
                    else:
                        new_bracket = {
                            "하한": last_upper,
                            "상한": last_upper + 100000000,
                            "기본세액": 0,
                            "세율": self.core.format_tax_rate(0.5, 3)  # 정밀도 처리
                        }
                else:
                    new_bracket = {
                        "하한": 0,
                        "상한": 100000000,
                        "기본세액": 0,
                        "세율": self.core.format_tax_rate(0.1, 3)  # 정밀도 처리
                    }
            
            # 새 구간 추가
            current_brackets.append(new_bracket)
            
            return True
        
        except Exception as e:
            print(f"구간 추가 중 오류: {str(e)}")
            return False
    
    def remove_last_rate_bracket(self, year: int, asset_type: str, taxation_type: str) -> bool:
        """마지막 세율 구간 삭제 (개선된 버전)"""
        try:
            year_str = str(year)
            
            # 경로 존재 확인
            if (year_str not in st.session_state.property_tax_rates.get("재산세", {}) or
                asset_type not in st.session_state.property_tax_rates["재산세"][year_str] or
                taxation_type not in st.session_state.property_tax_rates["재산세"][year_str][asset_type]):
                return False
            
            current_brackets = st.session_state.property_tax_rates["재산세"][year_str][asset_type][taxation_type]
            
            # 최소 1개 구간은 유지
            if len(current_brackets) <= 1:
                return False
            
            # 마지막 구간 삭제
            deleted_bracket = current_brackets.pop()
            
            # 삭제된 구간이 무제한 구간이었다면, 새로운 마지막 구간을 무제한으로 변경
            if deleted_bracket["상한"] == self.INFINITY_VALUE and current_brackets:
                current_brackets[-1]["상한"] = self.INFINITY_VALUE
            
            return True
        
        except Exception as e:
            print(f"구간 삭제 중 오류: {str(e)}")
            return False
    
    # ===========================================
    # 다른 세율 관리 (지역자원시설세)
    # ===========================================
    
    def update_regional_resource_tax_rates(self, year: int, rates: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """지역자원시설세율 수정"""
        try:
            year_str = str(year)
            
            # 데이터 타입 검증 및 변환
            validated_rates = []
            for i, rate in enumerate(rates):
                try:
                    required_keys = ["하한", "상한", "기본세액", "세율"]
                    if not all(key in rate for key in required_keys):
                        return False, f"구간 {i+1}에서 필수 항목이 누락되었습니다."
                    
                    # 세율 정밀도 검증 및 포맷팅
                    is_valid, formatted_rate, error_msg = self.core.validate_and_format_tax_rate_input(rate["세율"], 4)
                    if not is_valid:
                        return False, f"구간 {i+1} {error_msg}"
                    
                    # 데이터 타입 변환
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
                    
                    # 값 범위 검증
                    if validated_rate["하한"] < 0:
                        return False, f"구간 {i+1}의 하한은 0 이상이어야 합니다."
                    
                    if validated_rate["기본세액"] < 0:
                        return False, f"구간 {i+1}의 기본세액은 0 이상이어야 합니다."
                    
                    # 구간 연속성 검증
                    if i > 0 and validated_rates:
                        prev_upper = validated_rates[i-1]["상한"]
                        if prev_upper != self.INFINITY_VALUE and validated_rate["하한"] != prev_upper:
                            return False, f"구간 {i+1}의 하한({validated_rate['하한']:,})이 이전 구간의 상한({prev_upper:,})과 연결되지 않습니다."
                    
                    validated_rates.append(validated_rate)
                    
                except (ValueError, TypeError) as e:
                    return False, f"구간 {i+1}에서 숫자 형식 오류: {str(e)}"
            
            # 검증된 세율 저장
            if "지역자원시설세" not in st.session_state.property_tax_rates:
                st.session_state.property_tax_rates["지역자원시설세"] = {}
            
            st.session_state.property_tax_rates["지역자원시설세"][year_str] = validated_rates
            
            return True, f"{year}년 지역자원시설세율이 성공적으로 수정되었습니다."
        
        except Exception as e:
            return False, f"지역자원시설세율 수정 중 오류가 발생했습니다: {str(e)}"
    
    def add_regional_resource_bracket(self, year: int, new_bracket: Dict[str, Any] = None) -> bool:
        """지역자원시설세 구간 추가"""
        try:
            year_str = str(year)
            
            if "지역자원시설세" not in st.session_state.property_tax_rates:
                st.session_state.property_tax_rates["지역자원시설세"] = {}
            
            if year_str not in st.session_state.property_tax_rates["지역자원시설세"]:
                st.session_state.property_tax_rates["지역자원시설세"][year_str] = []
            
            current_brackets = st.session_state.property_tax_rates["지역자원시설세"][year_str]
            
            if not new_bracket:
                if current_brackets:
                    last_bracket = current_brackets[-1]
                    last_upper = last_bracket["상한"]
                    
                    if last_upper == self.INFINITY_VALUE:
                        new_lower = last_bracket["하한"] + 100000000
                        new_bracket = {
                            "하한": new_lower,
                            "상한": self.INFINITY_VALUE,
                            "기본세액": 0,
                            "세율": self.core.format_tax_rate(0.03, 4)
                        }
                        current_brackets[-1]["상한"] = new_lower
                    else:
                        new_bracket = {
                            "하한": last_upper,
                            "상한": last_upper + 100000000,
                            "기본세액": 0,
                            "세율": self.core.format_tax_rate(0.03, 4)
                        }
                else:
                    new_bracket = {
                        "하한": 0,
                        "상한": 100000000,
                        "기본세액": 0,
                        "세율": self.core.format_tax_rate(0.01, 4)
                    }
            
            current_brackets.append(new_bracket)
            return True
        
        except Exception as e:
            print(f"지역자원시설세 구간 추가 중 오류: {str(e)}")
            return False
    
    def remove_last_regional_resource_bracket(self, year: int) -> bool:
        """지역자원시설세 마지막 구간 삭제"""
        try:
            year_str = str(year)
            
            if (year_str not in st.session_state.property_tax_rates.get("지역자원시설세", {})):
                return False
            
            current_brackets = st.session_state.property_tax_rates["지역자원시설세"][year_str]
            
            if len(current_brackets) <= 1:
                return False
            
            deleted_bracket = current_brackets.pop()
            
            if deleted_bracket["상한"] == self.INFINITY_VALUE and current_brackets:
                current_brackets[-1]["상한"] = self.INFINITY_VALUE
            
            return True
        
        except Exception as e:
            print(f"지역자원시설세 구간 삭제 중 오류: {str(e)}")
            return False