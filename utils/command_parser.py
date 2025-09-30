import re
from datetime import datetime
from typing import Dict, Optional, List

class CommandParser:
    """자연어 명령을 파싱하여 구조화된 데이터로 변환"""
    
    def __init__(self):
        # 업무 타입 키워드 매핑
        self.task_keywords = {
            "원천세": ["원천세", "원천징수", "급여", "salary"],
            "외화획득": ["외화", "외화획득", "명세서", "외화명세서","외화획득명세서"],
            "부가세": ["부가세", "부가가치세", "vat"],
            "법인세": ["법인세", "corporate"],
            "지방세": ["지방세", "local"],
            "인지세": ["인지세", "stamp"],
            "국제조세": ["국제조세", "international"],
            "업무용승용차": ["업무용승용차", "승용차", "업무차량", "차량"],
        }
        
        # 액션 키워드 매핑
        self.action_keywords = {
            "process": ["처리", "실행", "해줘", "부탁", "진행"],
            "view": ["조회", "확인", "보여", "검색", "찾아"],
            "create": ["생성", "만들", "작성"],
            "download": ["다운", "내려", "받기"],
        }
    
    def parse(self, user_input: str) -> Dict:
        """
        사용자 입력을 파싱하여 명령 정보 추출
        
        Args:
            user_input: 사용자가 입력한 자연어 명령
            
        Returns:
            파싱된 명령 정보를 담은 딕셔너리
        """
        result = {
            "year": None,
            "month": None,
            "quarter": None,
            "task": None,
            "action": None,
            "companies": [],  # 회사명 리스트 추가
            "raw_input": user_input,
            "confidence": 0.0,
        }
        
        confidence_score = 0.0
        
        # 년도 추출 (25년, 2025년)
        year_match = re.search(r'(\d{2,4})년', user_input)
        if year_match:
            year = int(year_match.group(1))
            result["year"] = 2000 + year if year < 100 else year
            confidence_score += 0.3
        
        # 월 추출 (8월, 08월, 8월분)
        month_match = re.search(r'(\d{1,2})월', user_input)
        if month_match:
            month = int(month_match.group(1))
            if 1 <= month <= 12:
                result["month"] = month
                confidence_score += 0.2
        
        # 분기 추출 (1분기, 2분기, 3분기, 4분기)
        quarter_match = re.search(r'([1-4])분기', user_input)
        if quarter_match:
            result["quarter"] = int(quarter_match.group(1))
            confidence_score += 0.2
        
        # 회사명 추출 (추가)
        company_keywords = {
            "애커튼": ["애커튼", "akt", "AKT"],
            "잉크": ["잉크", "inc", "INC", "sk inc", "SK INC", "HC"],
            "엠알": ["엠알", "mr", "MR", "mrcic", "MRCIC","머티", "머티리얼즈"],
            "에이엑스": ["에이엑스", "ax", "AX", "sk ax", "SK AX", "C&C", "c&c", "cc", "Ax"]
        }
        
        for company_name, keywords in company_keywords.items():
            if any(kw in user_input for kw in keywords):
                result["companies"].append(company_name)
        
        # 업무 타입 추출
        for task, keywords in self.task_keywords.items():
            if any(kw in user_input for kw in keywords):
                result["task"] = task
                confidence_score += 0.3
                break
        
        # 액션 추출
        for action, keywords in self.action_keywords.items():
            if any(kw in user_input for kw in keywords):
                result["action"] = action
                confidence_score += 0.2
                break
        
        result["confidence"] = min(confidence_score, 1.0)
        
        return result
    
    def validate_command(self, parsed: Dict) -> tuple[bool, str]:
        """파싱된 명령의 유효성 검증"""
        if not parsed["task"]:
            return False, "어떤 업무를 처리하시겠어요? (원천세, 외화획득명세서, 부가세 등)"
        
        # ========== 인지세는 연도/월/분기 불필요 ==========
        if parsed["task"] == "인지세":
            if not parsed["action"]:
                parsed["action"] = "process"
            return True, "OK"
        # ==============================================
        
        if not parsed["year"]:
            return False, f"{parsed['task']} 처리를 위한 연도를 알려주세요."
        
        if not parsed["month"] and not parsed["quarter"]:
            return False, f"{parsed['year']}년 {parsed['task']} 처리를 위한 월 또는 분기를 알려주세요."
        
        if not parsed["action"]:
            parsed["action"] = "process"
        
        if parsed["confidence"] < 0.5:
            return False, "명령을 정확히 이해하지 못했습니다. 더 구체적으로 말씀해주세요."
        
        return True, "OK"
    
    def get_period_string(self, parsed: Dict) -> str:
        """기간 정보를 문자열로 변환"""
        if parsed["month"]:
            return f"{parsed['year']}년 {parsed['month']}월"
        elif parsed["quarter"]:
            return f"{parsed['year']}년 {parsed['quarter']}분기"
        return f"{parsed['year']}년"
    
    def suggest_commands(self) -> List[str]:
        """사용 가능한 명령 예시 제공"""
        return [
            "25년 8월 원천세 처리해줘",
            "2025년 1분기 외화획득명세서 조회",
            "24년 12월 부가세 처리",
            "2025년 2분기 법인세 확인",
        ]


# 싱글톤 인스턴스 생성
_parser_instance = None

def get_command_parser() -> CommandParser:
    """CommandParser 싱글톤 인스턴스 반환"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = CommandParser()
    return _parser_instance
