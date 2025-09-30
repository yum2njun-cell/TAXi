"""
TAXi - 사용자별 담당 업무 관리
담당자별 맞춤 알림 시스템
"""

from typing import Dict, List, Optional, Any
from datetime import datetime

class UserAssignmentManager:
    """사용자별 담당 업무 관리 클래스"""

    def __init__(self):
        # 사용자별 담당 업무 정의
        # 실제 운영에서는 DB/설정파일에서 로드하는 것을 권장
        self.user_assignments: Dict[str, Dict[str, Any]] = {
            "04362": {
                "name": "문상현",
                # 주 담당 1개(문법상 문자열 하나). 관리자라면 "전체"로 두면 로직 분기 쉬움
                "tax_type": "전체",
                "role": "관리자",
                "priority_tasks": [
                    "세무 SPoC",
                ],
                "responsibilities": ["법인세", "부가세", "원천세", "지방세", "인지세", "국제조세"],
                "icon": ""
            },
            "11698": {
                "name": "김정민",
                "tax_type": "국제조세",
                "role": "담당자",
                "priority_tasks": [
                    "BEPS 보고서 작성",
                    "해외인보이스 발행",
                ],
                "responsibilities": ["국제조세"],
                "icon": ""
            },
            "06488": {
                "name": "김태훈",
                "tax_type": "지방세",
                "role": "담당자",
                "priority_tasks": [
                    "세금계산서 발행",
                    "지방세 신고",
                ],
                "responsibilities": ["지방세", "부가세"],
                "icon": ""
            },
            "11375": {
                "name": "박세빈",
                "tax_type": "부가세",
                "role": "담당자",
                "priority_tasks": [
                    "부가세 신고",
                    "세금계산서 발행",
                ],
                "responsibilities": ["부가세"],
                "icon": ""
            },
            "06337": {
                "name": "윤성은",
                "tax_type": "인지세",
                "role": "담당자",
                "priority_tasks": [
                    "인지세 신고",
                    "세금계산서 발행",
                ],
                "responsibilities": ["인지세", "부가세"],
                "icon": ""
            },
            "11470": {
                "name": "전유민",
                "tax_type": "원천세",
                "role": "담당자",
                "priority_tasks": [
                    "원천세 신고",
                    "해외인보이스 발행",
                ],
                "responsibilities": ["원천세", "국제조세"],
                "icon": ""
            },
            "07261": {
                "name": "최민석",
                "tax_type": "법인세",
                "role": "담당자",
                "priority_tasks": [
                    "법인세 신고",
                ],
                "responsibilities": ["법인세", "국제조세", "원천세"],
                "icon": ""
            },
            "04975": {
                "name": "하영수",
                "tax_type": "부가세",
                "role": "담당자",
                "priority_tasks": [
                    "부가세 관리",
                    "세금계산서 발행",
                ],
                "responsibilities": ["부가세", "인지세", "지방세"],
                "icon": ""
            },
            "guest": {
                "name": "게스트",
                "tax_type": "구경",  # 또는 "체험"
                "role": "게스트",
                "priority_tasks": [
                    "플랫폼 둘러보기",
                ],
                "responsibilities": [],  # 빈 배열 = 담당 없음
                "icon": ""
            },
        }

        # 이름으로도 조회 가능하도록 역인덱스
        self._name_index: Dict[str, str] = {
            v["name"]: k for k, v in self.user_assignments.items()
        }

        # 업무 우선순위 템플릿 (샘플)
        self.task_templates: Dict[str, Dict[str, List[str]]] = {
            "원천세": {
                "urgent": [
                    "원천세 신고 마감 D-1",
                    "지급명세서 제출 준비",
                    "연말정산 오류 수정",
                ],
                "normal": [
                    "월간 원천세 신고서 검토",
                    "이행상황신고서 작성",
                    "외국납부세액공제 검토",
                ],
                "routine": [
                    "급여대장 정리",
                    "원천징수영수증 발급",
                    "세무 서류 정리",
                ],
            },
            "법인세": {
                "urgent": [
                    "법인세 신고 마감 D-3",
                    "중간예납 납부 확인",
                    "세무조정 검토",
                ],
                "normal": [
                    "업무용승용차 관리",
                    "감가상각비 계산",
                    "이월결손금 검토",
                ],
                "routine": [
                    "법인세 관련 서류 정리",
                    "장부 기장 확인",
                    "세무 현황 보고",
                ],
            },
            "부가세": {
                "urgent": [
                    "부가세 신고 마감 D-2",
                    "세금계산서 누락 확인",
                    "과세표준 검토",
                ],
                "normal": [
                    "월간 부가세 예정신고",
                    "세금계산서 관리",
                    "면세사업 현황 확인",
                ],
                "routine": [
                    "매입매출 대조",
                    "부가세 관련 서류 정리",
                    "과세 현황 점검",
                ],
            },
        }

    def _resolve_username(self, username: str) -> Optional[str]:
        """사번/아이디 또는 이름으로 들어와도 내부키(사번 문자열)로 변환."""
        if not username:
            return None
        if username in self.user_assignments:
            return username
        # 이름 매칭
        return self._name_index.get(username)

    def get_user_assignment(self, username: str) -> Optional[Dict[str, Any]]:
        """사용자 담당 업무 정보 반환 (사번 또는 이름 모두 허용)"""
        key = self._resolve_username(username)
        if not key:
            return None

        assignment = dict(self.user_assignments[key])  # 복사본
        # 현재 우선순위 태스크 추가
        current_task = self._get_current_priority_task(key, assignment.get("tax_type", "전체"))
        assignment["current_task"] = current_task
        return assignment

    def get_user_priority_task(self, username: str) -> Optional[Dict[str, str]]:
        """사용자의 현재 우선순위 업무 반환"""
        assignment = self.get_user_assignment(username)
        if not assignment:
            return None

        current_task = assignment.get("current_task") or assignment["priority_tasks"][0]

        return {
            "tax_type": assignment.get("tax_type", "전체"),
            "task": current_task,
            "icon": assignment.get("icon", ""),
            "role": assignment.get("role", ""),
        }

    def get_all_users_status(self) -> List[Dict[str, Any]]:
        """전체 사용자 업무 현황 반환"""
        status_list: List[Dict[str, Any]] = []
        for key, assignment in self.user_assignments.items():
            current_task = self._get_current_priority_task(key, assignment.get("tax_type", "전체"))
            status_list.append({
                "username": key,
                "tax_type": assignment.get("tax_type", "전체"),
                "role": assignment.get("role", ""),
                "current_task": current_task,
                "icon": assignment.get("icon", ""),
                "responsibilities": assignment.get("responsibilities", []),
            })
        return status_list

    def _get_current_priority_task(self, username: str, tax_type: str) -> str:
        """현재 시점에서 가장 중요한 업무(샘플 로직)"""
        today = datetime.now()
        day = today.day

        if tax_type == "원천세":
            if day <= 5:
                return "원천세 신고서 작성 준비"
            elif day <= 10:
                return "원천세 신고·납부 진행"
            elif day <= 15:
                return "지급명세서 검토 및 제출"
            else:
                return "다음 달 원천세 준비"

        elif tax_type == "법인세":
            if day <= 10:
                return "업무용승용차 관리 검토"
            elif day <= 20:
                return "감가상각비 계산 확인"
            else:
                return "법인세 예정신고 준비"

        elif tax_type == "부가세":
            if day <= 20:
                return "부가세 예정신고 검토"
            elif day <= 25:
                return "부가세 예정신고 제출"
            else:
                return "세금계산서 정리"

        elif tax_type == "전체":
            return "전체 세무 일정 점검"

        # 기본값: 해당 사용자 priority_tasks의 첫 항목
        assignment = self.user_assignments.get(username, {})
        return assignment.get("priority_tasks", ["업무 확인 필요"])[0]

    # 아래 메서드들은 향후 DB 연동 시 구현
    def add_user_assignment(self, username: str, tax_type: str, role: str, tasks: List[str]):
        """새 사용자 담당 업무 추가 (향후 구현)"""
        pass

    def update_user_task_status(self, username: str, task: str, status: str):
        """사용자 업무 상태 업데이트 (향후 구현)"""
        pass

    def get_team_workload(self) -> Dict[str, Any]:
        """팀 전체 업무량 분석 (향후 구현)"""
        return {
            "total_users": len(self.user_assignments),
            "tax_types": {
                "원천세": 1,
                "법인세": 1,
                "부가세": 1,
                "전체": 1,
            },
            "urgent_tasks": 3,
            "normal_tasks": 8,
            "routine_tasks": 12,
        }


# 싱글톤 인스턴스
_assignment_manager: Optional[UserAssignmentManager] = None

def get_assignment_manager() -> UserAssignmentManager:
    """사용자 담당 업무 관리자 싱글톤 인스턴스 반환"""
    global _assignment_manager
    if _assignment_manager is None:
        _assignment_manager = UserAssignmentManager()
    return _assignment_manager

# 편의 함수들
def get_user_assignment(username: str) -> Optional[Dict[str, Any]]:
    """사용자 담당 업무 정보 반환"""
    return get_assignment_manager().get_user_assignment(username)

def get_user_priority_task(username: str) -> Optional[Dict[str, str]]:
    """사용자 우선순위 업무 반환"""
    return get_assignment_manager().get_user_priority_task(username)

def get_all_users_status() -> List[Dict[str, Any]]:
    """전체 사용자 상태 반환"""
    return get_assignment_manager().get_all_users_status()
