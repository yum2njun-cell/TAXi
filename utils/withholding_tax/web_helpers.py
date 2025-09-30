"""
TAXi - 원천세 웹 헬퍼 유틸리티
기존 원천세 시스템의 헬퍼 함수들을 TAXi 구조에 맞게 수정
"""

import pandas as pd
import streamlit as st
import io
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

import logging
logger = logging.getLogger(__name__)

def create_empty_data() -> Dict[str, int]:
    """빈 데이터 구조 생성"""
    return {'인원': 0, '과세소득': 0, '제출비과세': 0, '총지급액': 0, '소득세': 0, '주민세': 0}

def safe_float(value: Any, default: float = 0) -> float:
    """안전한 float 변환"""
    try:
        return float(value) if not pd.isna(value) else default
    except (ValueError, TypeError):
        return default

def format_number(value: Any) -> str:
    """숫자 포맷팅: 천의 자리 콤마, 마이너스는 △로 표시"""
    if value == 0 or value is None:
        return ""

    if isinstance(value, (int, float)):
        if value < 0:
            return f"△{abs(value):,.0f}"
        else:
            return f"{value:,.0f}"

    return value

def find_row_by_keywords(df: pd.DataFrame, keywords: List[str], search_columns: List[int] = [0, 1, 2]) -> Optional[int]:
    """키워드로 행 찾기 - 여러 대안 키워드 지원 (부분 문자열 검색)"""
    if isinstance(keywords, str):
        keywords = [keywords]
    
    for col in search_columns:
        if col in df.columns:
            for keyword in keywords:
                mask = df[col].astype(str).str.contains(keyword, na=False, case=False)
                if mask.any():
                    return mask.idxmax()
    return None

def aggregate_data(source_data: Dict[str, Dict], item_names: List[str]) -> Dict[str, int]:
    """데이터를 집계하는 함수"""
    result = {'인원': 0, '소득세': 0, '주민세': 0}
    
    for item_name in item_names:
        if item_name in source_data:
            item_data = source_data[item_name]
            result['인원'] += item_data.get('인원', 0)
            result['소득세'] += item_data.get('소득세', 0)
            result['주민세'] += item_data.get('주민세', 0)
    
    return result

def validate_uploaded_file(uploaded_file) -> Tuple[bool, str]:
    """업로드된 파일 유효성 검증"""
    if uploaded_file is None:
        return False, "파일이 업로드되지 않았습니다."
    
    if not uploaded_file.name.lower().endswith(('.xlsx', '.xls')):
        return False, "Excel 파일(.xlsx, .xls)만 지원됩니다."
    
    # 파일 크기 검증 (100MB 제한)
    file_size = len(uploaded_file.getvalue())
    if file_size > 100 * 1024 * 1024:  # 100MB
        return False, "파일 크기가 100MB를 초과합니다."
    
    return True, ""

def get_sheet_names(uploaded_file) -> List[str]:
    """업로드된 엑셀 파일의 시트명 목록 반환"""
    try:
        excel_file = pd.ExcelFile(uploaded_file)
        return excel_file.sheet_names
    except Exception as e:
        logger.error(f"시트명 읽기 오류: {e}")
        return []

def validate_sheet_exists(uploaded_file, sheet_name: str) -> Tuple[bool, str]:
    """시트 존재 여부 검증"""
    try:
        sheet_names = get_sheet_names(uploaded_file)
        if sheet_name not in sheet_names:
            available_sheets = ", ".join(sheet_names)
            return False, f"시트 '{sheet_name}'이 존재하지 않습니다. 사용 가능한 시트: {available_sheets}"
        return True, ""
    except Exception as e:
        return False, f"파일을 읽는 중 오류가 발생했습니다: {str(e)}"

def create_summary_dataframe(data_summary: Dict[str, Dict], company_type: int) -> pd.DataFrame:
    """요약 데이터를 데이터프레임으로 변환"""
    try:
        from config.withholding_tax_config import COMPANY_CONFIGS
        
        # 출력 순서 정의
        output_order = get_output_order_with_totals(company_type, data_summary)
        
        # 데이터프레임 생성
        rows = []
        for item in output_order:
            if item in data_summary:
                data = data_summary[item]
                row = {
                    '항목': item,
                    '인원': data.get('인원', 0),
                    '과세소득': data.get('과세소득', 0),
                    '제출비과세': data.get('제출비과세', 0),
                    '총지급액': data.get('총지급액', 0),
                    '소득세': data.get('소득세', 0),
                    '주민세': data.get('주민세', 0)
                }
                rows.append(row)
        
        return pd.DataFrame(rows)
    except Exception as e:
        logger.error(f"데이터프레임 생성 중 오류: {e}")
        return pd.DataFrame()

def get_output_order_with_totals(company_type: int, data_summary: Dict[str, Dict]) -> List[str]:
    """회사별 출력 순서 반환 (합계를 적절한 위치에 배치)"""
    orders = {
        1: [
            # 급여 관련
            '급여(종로)', '사이닝보너스', '중도퇴사', '일용근로', '급여 총합계',
            # 퇴직소득 관련
            '퇴직소득 과세이연', '퇴직소득 과세', '퇴직소득 총합계',
            # 기타소득
            '국내원천소득', '이자소득', '배당소득', '사업소득', '기타소득',
            # 연말정산
            '연말정산(합계)', '연말정산(분납액)', '연말정산(1월퇴사)', '연말정산(납부액)', '연말정산 전체 합계',
            '총합계'
        ],
        2: [
            # 급여 관련
            '급여(INC 본점)', '급여(이천)', '일용근로소득', '급여 총합계',
            # 중도퇴사
            '중도퇴사연말정산(INC 본점)', '중도퇴사연말정산(이천)', '중도퇴사연말정산 총합계',
            '근로소득 총합계',
            # 퇴직소득
            '퇴직소득 과세', '퇴직소득 과세이연', '퇴직소득 총합계',
            # 기타소득
            '배당소득', '기타소득', '법인원천소득', '사업소득',
            # 연말정산
            '연말정산납부금액', '연말정산분납금액', '연말정산이천', '연말정산 총합계',
            '총합계'
        ],
        3: [
            # 급여 관련
            '급여(MR 본점)', '급여(세종)', '급여(영주)', '급여(동탄)', '급여(상주)', '일용근로소득', '급여 총합계',
            # 중도퇴사
            '중도퇴사연말정산(MR 본점)', '중도퇴사연말정산(세종)', '중도퇴사연말정산(영주)', 
            '중도퇴사연말정산(동탄)', '중도퇴사연말정산(상주)', '중도퇴사연말정산 총합계',
            '근로소득 총합계',
            # 퇴직소득
            '퇴직소득 과세', '퇴직소득 과세이연(MR 본점)', '퇴직소득 과세이연(세종)', '퇴직소득 총합계',
            # 기타소득
            '법인원천소득', '배당소득', '이자소득', '기타소득', '사업소득',
            # 연말정산
            '연말정산(MR 본점)', '연말정산(세종)', '연말정산(영주)', '연말정산(동탄)', '연말정산(상주)', '연말정산 총합계',
            '총합계', '최종 총합계'
        ],
        4: [
            # 급여 관련
            '급여(분당)', '급여(충무로)', '급여(대덕)', '일용직(3개월이상)', '일용근로소득', '급여 총합계',
            # 중도퇴사
            '중도퇴사연말정산(분당)', '중도퇴사연말정산 총합계',
            # 우리사주
            '우리사주(분당)', '우리사주 총합계',
            '근로소득 총합계',
            # 퇴직소득
            '퇴직소득 과세', '퇴직소득 과세이연', '퇴직소득 총합계',
            # 기타소득
            '국내원천소득', '배당소득', '기타소득', '사업소득',
            # 연말정산
            '연말정산(분당)', '연말정산(충무로)', '연말정산(대덕)', '연말정산 합계',
            '총합계', '최종 총합계'
        ]
    }

    order = orders.get(company_type, [])
    return [item for item in order if item in data_summary]

def display_processing_progress(current_step: int, total_steps: int, step_description: str = ""):
    """처리 진행률 표시"""
    progress = current_step / total_steps
    st.progress(progress)
    if step_description:
        st.text(f"진행 중: {step_description} ({current_step}/{total_steps})")

def format_currency(value: Any) -> str:
    """통화 형식으로 포맷팅"""
    if value == 0 or value is None:
        return "0원"
    return f"{value:,.0f}원"

def convert_dataframe_to_excel_bytes(dataframes_dict: Dict[str, pd.DataFrame], sheet_names: Optional[List[str]] = None) -> Optional[bytes]:
    """데이터프레임들을 엑셀 바이트로 변환"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for i, (name, df) in enumerate(dataframes_dict.items()):
                sheet_name = sheet_names[i] if sheet_names and i < len(sheet_names) else name
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        return output.getvalue()
    except Exception as e:
        logger.error(f"엑셀 변환 중 오류: {e}")
        return None

def cleanup_temp_files():
    """임시 파일들 정리"""
    try:
        temp_dir = os.path.join(os.getcwd(), 'data', 'temp')
        if os.path.exists(temp_dir):
            current_time = datetime.now()
            for file in os.listdir(temp_dir):
                file_path = os.path.join(temp_dir, file)
                if os.path.isfile(file_path):
                    # 1시간 이상 된 파일 삭제
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if (current_time - file_time).seconds > 3600:
                        os.remove(file_path)
                        logger.info(f"임시 파일 삭제: {file}")
    except Exception as e:
        logger.error(f"임시 파일 정리 중 오류: {e}")

def validate_data_integrity(data_summary: Dict[str, Dict]) -> List[str]:
    """데이터 무결성 검증"""
    warnings = []
    
    try:
        # 총합계가 있는지 확인
        if '총합계' not in data_summary:
            warnings.append("총합계 데이터가 누락되었습니다.")
        
        # 음수 값 확인
        for item_name, data in data_summary.items():
            for field, value in data.items():
                if isinstance(value, (int, float)) and value < 0:
                    warnings.append(f"{item_name}의 {field}이 음수입니다: {value}")
        
        # 인원수와 세액 일관성 확인
        for item_name, data in data_summary.items():
            if '합계' not in item_name:  # 합계 항목 제외
                personnel = data.get('인원', 0)
                income_tax = data.get('소득세', 0)
                
                # 인원이 있는데 세액이 없는 경우 (일부 예외 제외)
                if personnel > 0 and income_tax == 0 and '과세이연' not in item_name and '배당소득' not in item_name:
                    warnings.append(f"{item_name}: 인원은 있으나 소득세가 0입니다.")
                
                # 인원이 없는데 세액이 있는 경우
                if personnel == 0 and income_tax > 0:
                    warnings.append(f"{item_name}: 인원이 0이나 소득세가 있습니다.")
    
    except Exception as e:
        logger.error(f"데이터 무결성 검증 중 오류: {e}")
        warnings.append(f"데이터 검증 중 오류 발생: {str(e)}")
    
    return warnings

def calculate_summary_statistics(data_summary: Dict[str, Dict]) -> Dict[str, Any]:
    """요약 통계 계산"""
    try:
        stats = {
            'total_items': len(data_summary),
            'items_with_personnel': 0,
            'items_with_tax': 0,
            'total_personnel': 0,
            'total_income_tax': 0,
            'total_resident_tax': 0,
            'total_taxable_income': 0,
            'average_tax_per_person': 0
        }
        
        for item_name, data in data_summary.items():
            if '합계' not in item_name:  # 합계 항목 제외하고 계산
                personnel = data.get('인원', 0)
                income_tax = data.get('소득세', 0)
                resident_tax = data.get('주민세', 0)
                taxable_income = data.get('과세소득', 0)
                
                if personnel > 0:
                    stats['items_with_personnel'] += 1
                    stats['total_personnel'] += personnel
                
                if income_tax > 0:
                    stats['items_with_tax'] += 1
                
                stats['total_income_tax'] += income_tax
                stats['total_resident_tax'] += resident_tax
                stats['total_taxable_income'] += taxable_income
        
        # 평균 세액 계산
        if stats['total_personnel'] > 0:
            stats['average_tax_per_person'] = (stats['total_income_tax'] + stats['total_resident_tax']) / stats['total_personnel']
        
        return stats
        
    except Exception as e:
        logger.error(f"요약 통계 계산 중 오류: {e}")
        return {}

def export_data_to_json(data_summary: Dict[str, Dict], filename: str = None) -> str:
    """데이터를 JSON으로 내보내기"""
    try:
        import json
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"withholding_tax_data_{timestamp}.json"
        
        # JSON 직렬화 가능하도록 데이터 정리
        json_data = {
            'export_time': datetime.now().isoformat(),
            'data': data_summary
        }
        
        json_string = json.dumps(json_data, ensure_ascii=False, indent=2)
        return json_string
        
    except Exception as e:
        logger.error(f"JSON 내보내기 중 오류: {e}")
        return ""

def import_data_from_json(json_string: str) -> Dict[str, Dict]:
    """JSON에서 데이터 가져오기"""
    try:
        import json
        
        json_data = json.loads(json_string)
        return json_data.get('data', {})
        
    except Exception as e:
        logger.error(f"JSON 가져오기 중 오류: {e}")
        return {}

def create_backup_data(data_summary: Dict[str, Dict], company_type: int) -> Dict[str, Any]:
    """백업용 데이터 생성"""
    try:
        from config.withholding_tax_config import COMPANY_CONFIGS
        
        backup_data = {
            'backup_time': datetime.now().isoformat(),
            'company_type': company_type,
            'company_name': COMPANY_CONFIGS.get(company_type, {}).get('name', '알 수 없음'),
            'data': data_summary,
            'statistics': calculate_summary_statistics(data_summary),
            'warnings': validate_data_integrity(data_summary)
        }
        
        return backup_data
        
    except Exception as e:
        logger.error(f"백업 데이터 생성 중 오류: {e}")
        return {}
