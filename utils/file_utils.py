"""
파일 처리 공통 유틸리티
"""
from pathlib import Path
from typing import Dict, Any

def create_mock_uploaded_file(file_path: str) -> Any:
    """파일 경로로부터 Mock UploadedFile 객체 생성"""
    class MockUploadedFile:
        def __init__(self, content, name):
            self.content = content
            self.name = name
        def getvalue(self):
            return self.content
        def getbuffer(self):
            return self.content
    
    if Path(file_path).exists():
        with open(file_path, 'rb') as f:
            file_content = f.read()
        return MockUploadedFile(file_content, Path(file_path).name)
    else:
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")

def get_file_type_to_company_mapping() -> Dict[str, int]:
    """파일 타입별 회사 매핑 반환"""
    return {
        "AKT": 1,  # 애커튼
        "INC": 2,  # SK INC
        "MR": 3,   # SK MRCIC
        "AX": 4    # SK AX
    }