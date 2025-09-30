"""
TAXi - 법인세 서비스
업무용승용차, 감가상각비, 이월결손금 관리 서비스
"""

import pandas as pd
import re
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import io
from pathlib import Path

# 활동 로그 임포트
from utils.activity_logger import (
    log_corporate_vehicle_activity,
    log_file_processing_activity,
    log_excel_generation_activity
)


class CorpTaxService:
    """법인세 관리 서비스 클래스"""
    
    def __init__(self, output_dir: str = "data/outputs/corp_tax"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def process_vehicle_files(self, uploaded_files: List) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """업무용승용차 엑셀 파일들을 처리"""
        try:
            # 처리 시작 로그
            log_corporate_vehicle_activity(
                f"업무용승용차 파일 처리 시작",
                {"file_count": len(uploaded_files)}
            )
            
            result_data = []
            processed_files = []
            error_files = []
            
            for uploaded_file in uploaded_files:
                try:
                    # 개별 파일 처리 로그
                    log_file_processing_activity(
                        f"업무용승용차 파일 처리 중",
                        uploaded_file.name,
                        {"processing_type": "vehicle_data_extraction"}
                    )
                    
                    # 엑셀 파일 읽기
                    df = pd.read_excel(uploaded_file, header=None)
                    
                    # 데이터 추출
                    row_data = self._extract_vehicle_data(df, uploaded_file.name)
                    if row_data:
                        result_data.append(row_data)
                        processed_files.append(uploaded_file.name)
                    else:
                        error_files.append(uploaded_file.name)
                        
                except Exception as e:
                    error_files.append(f"{uploaded_file.name}: {str(e)}")
                    continue
            
            # 결과 데이터프레임 생성
            if result_data:
                result_df = pd.DataFrame(result_data, columns=[
                    "차량번호(뒤4자리)", "차량번호", "차종명", "사용자", 
                    "운행기록부작성여부", "임차기간시작일", "해당연도보유월수", 
                    "총주행거리(km)", "업무용사용거리(km)", "업무사용비율"
                ])
                
                # 성공 로그
                log_corporate_vehicle_activity(
                    f"업무용승용차 파일 처리 완료",
                    {
                        "processed_count": len(processed_files),
                        "error_count": len(error_files),
                        "total_records": len(result_data)
                    }
                )
                
                # 처리 결과 통계
                stats = {
                    "total_files": len(uploaded_files),
                    "processed_files": len(processed_files),
                    "error_files": len(error_files),
                    "total_records": len(result_data),
                    "processed_file_names": processed_files,
                    "error_file_names": error_files
                }
                
                return result_df, stats
            else:
                # 실패 로그
                log_corporate_vehicle_activity(
                    "업무용승용차 파일 처리 실패 - 추출 가능한 데이터 없음",
                    {"error_files": error_files}
                )
                
                raise ValueError("처리할 수 있는 데이터를 찾을 수 없습니다.")
                
        except Exception as e:
            # 전체 처리 실패 로그
            log_corporate_vehicle_activity(
                f"업무용승용차 파일 처리 오류: {str(e)}",
                {"error_type": "processing_error"}
            )
            raise e
    
    def generate_vehicle_excel(self, result_df: pd.DataFrame) -> bytes:
        """업무용승용차 결과를 엑셀로 생성"""
        try:
            # 엑셀 생성 로그
            log_excel_generation_activity(
                "업무용승용차 결과 엑셀 생성",
                {
                    "record_count": len(result_df),
                    "file_type": "vehicle_management"
                }
            )
            
            excel_buffer = io.BytesIO()
            
            # 엑셀 생성 시 서식 적용
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                result_df.to_excel(writer, sheet_name='업무용승용차', index=False)
                
                # 워크시트 가져와서 서식 적용
                worksheet = writer.sheets['업무용승용차']
                
                # 헤더 서식
                for col_num, column_title in enumerate(result_df.columns, 1):
                    cell = worksheet.cell(row=1, column=col_num)
                    cell.font = cell.font.copy(bold=True)
                    cell.fill = cell.fill.copy(fgColor="FFD700")
                
                # 컬럼 너비 자동 조정
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = (max_length + 2) * 1.2
                    worksheet.column_dimensions[column_letter].width = adjusted_width
            
            excel_buffer.seek(0)
            
            log_excel_generation_activity(
                "업무용승용차 엑셀 생성 완료",
                {"status": "success"}
            )
            
            return excel_buffer.getvalue()
            
        except Exception as e:
            log_excel_generation_activity(
                f"업무용승용차 엑셀 생성 실패: {str(e)}",
                {"status": "error"}
            )
            raise e
    
    def _extract_vehicle_data(self, df: pd.DataFrame, filename: str) -> Optional[List[str]]:
        """엑셀 파일에서 업무용승용차 데이터 추출 (내부 메서드)"""
        try:
            # 각 셀에서 데이터 추출 (pandas는 0-based indexing)
            d11_value = df.iloc[10, 3] if len(df) > 10 and len(df.columns) > 3 else ""  # D11
            a11_value = df.iloc[10, 0] if len(df) > 10 else ""  # A11
            j8_value = df.iloc[7, 9] if len(df) > 7 and len(df.columns) > 9 else ""   # J8
            j10_value = df.iloc[9, 9] if len(df) > 9 and len(df.columns) > 9 else ""  # J10
            n9_value = df.iloc[8, 13] if len(df) > 8 and len(df.columns) > 13 else "" # N9
            n11_value = df.iloc[10, 13] if len(df) > 10 and len(df.columns) > 13 else "" # N11
            n13_value = df.iloc[12, 13] if len(df) > 12 and len(df.columns) > 13 else "" # N13
            
            # D11에서 차량번호 뒤 4자리 추출
            vehicle_number_full = str(d11_value) if pd.notna(d11_value) else ""
            vehicle_number_last4 = self._extract_last_4_digits(vehicle_number_full)
            
            # J10 날짜에서 해당연도 보유월수 계산
            months_owned = self._calculate_months_owned(j10_value)
            
            # 데이터 정리
            row_data = [
                vehicle_number_last4,  # 차량번호 뒤4자리
                vehicle_number_full,   # 차량번호 전체
                str(a11_value) if pd.notna(a11_value) else "",  # 차종명
                str(j8_value) if pd.notna(j8_value) else "",    # 사용자
                "여",  # 운행기록부 작성여부 (고정값)
                str(j10_value) if pd.notna(j10_value) else "",  # 임차기간 시작일
                months_owned,  # 해당연도 보유월수
                str(n9_value) if pd.notna(n9_value) else "",    # 총주행거리
                str(n11_value) if pd.notna(n11_value) else "",  # 업무용 사용거리
                str(n13_value) if pd.notna(n13_value) else ""   # 업무사용비율
            ]
            
            return row_data
            
        except Exception as e:
            # 개별 파일 추출 실패는 경고 로그로만 처리
            print(f"파일 {filename} 데이터 추출 중 오류: {str(e)}")
            return None
    
    def _extract_last_4_digits(self, text: str) -> str:
        """텍스트에서 한글 뒤의 숫자 4자리 추출"""
        if not text or pd.isna(text):
            return ""
        
        text_str = str(text)
        # 한글 뒤의 숫자 4자리를 찾는 정규식
        match = re.search(r'[가-힣](\d{4})', text_str)
        if match:
            return match.group(1)
        
        # 패턴이 맞지 않으면 숫자만 추출 시도
        numbers = re.findall(r'\d+', text_str)
        for num in numbers:
            if len(num) == 4:
                return num
        
        return ""
    
    def _calculate_months_owned(self, date_value) -> str:
        """날짜에서 해당 연도 연말까지의 월수 계산"""
        if not date_value or pd.isna(date_value):
            return ""
        
        try:
            # 날짜 파싱 시도
            if isinstance(date_value, str):
                # 문자열인 경우 여러 형식으로 파싱 시도
                date_str = str(date_value).replace("-", "").replace("/", "").replace(".", "")
                if len(date_str) >= 8:
                    year = int(date_str[:4])
                    month = int(date_str[4:6])
                else:
                    return ""
            elif hasattr(date_value, 'year'):
                # datetime 객체인 경우
                year = date_value.year
                month = date_value.month
            else:
                return ""
            
            # 해당 월부터 12월까지의 월수 계산
            months = 12 - month + 1
            return str(months)
            
        except (ValueError, AttributeError):
            return ""
    
    # 향후 확장을 위한 메서드들
    def process_depreciation_files(self, uploaded_files: List) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """감가상각비 파일 처리 (향후 구현)"""
        log_corporate_depreciation_activity("감가상각비 파일 처리 기능 호출", {"status": "not_implemented"})
        raise NotImplementedError("감가상각비 처리 기능은 향후 구현 예정입니다.")
    
    def process_loss_carryforward_files(self, uploaded_files: List) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """이월결손금 파일 처리 (향후 구현)"""
        log_corporate_loss_activity("이월결손금 파일 처리 기능 호출", {"status": "not_implemented"})
        raise NotImplementedError("이월결손금 처리 기능은 향후 구현 예정입니다.")


# 서비스 인스턴스 생성 함수 (싱글톤 패턴)
_corp_tax_service = None

def get_corp_tax_service() -> CorpTaxService:
    """법인세 서비스 인스턴스 반환"""
    global _corp_tax_service
    if _corp_tax_service is None:
        _corp_tax_service = CorpTaxService()
    return _corp_tax_service
