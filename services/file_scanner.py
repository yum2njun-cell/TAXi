"""
동적 폴더 검색 기반 파일 스캐너
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from utils.path_mapper import PathMapper

@dataclass
class ScanResult:
    """스캔 결과"""
    found: bool
    path: Optional[Path] = None
    paths: List[Path] = None
    error: Optional[str] = None
    candidates: List[Path] = None
    
    def __post_init__(self):
        if self.paths is None:
            self.paths = []
        if self.candidates is None:
            self.candidates = []

class FileScanner:
    """동적 폴더 검색 스캐너"""
    
    def __init__(self, path_mapper: PathMapper):
        self.mapper = path_mapper
    def _find_year_folder_flexible(self, parent: Path, year: int, keyword: str = "") -> Optional[Path]:
        """
        연도 폴더를 유연하게 찾기
        2024년, 24년 등 다양한 패턴 지원
        
        Args:
            parent: 검색할 부모 폴더
            year: 연도 (예: 2024)
            keyword: 추가 키워드 (예: "세무조정")
        """
        short_year = str(year)[2:]
        patterns = [
            f"{year}년 {keyword}".strip(),
            f"{short_year}년 {keyword}".strip(),
        ]
        
        for pattern in patterns:
            folder = self._find_folder_by_keyword(parent, pattern)
            if folder:
                return folder
        
        return None

    def scan_work_folder(self, work_type: str, period_str: str) -> ScanResult:
        """
        작업 폴더 동적 검색
        기본경로 → 연도 → 신고업무 → 월 귀속
        """
        if not self.mapper.base_path:
            return ScanResult(
                found=False,
                error=f"{work_type} 폴더가 설정되지 않았습니다. 설정 페이지에서 경로를 지정하세요."
            )
        
        # 기간 파싱
        period_vars = self.mapper.parse_period(period_str)
        year = period_vars.get("full_year")
        month = period_vars.get("month")
        
        if not year or not month:
            return ScanResult(found=False, error="기간 형식이 올바르지 않습니다")
        
        # 1. 연도 폴더 찾기 (2024년, 24년 모두 인식)
        year_folder = self._find_year_folder_flexible(self.mapper.base_path, int(year))

        if not year_folder:
            short_year = str(year)[2:]
            return ScanResult(
                found=False,
                error=f"{year}년 또는 {short_year}년 폴더를 찾을 수 없습니다: {self.mapper.base_path}",
                candidates=self._find_similar_folders(self.mapper.base_path, str(year)[2:])
            )
        
        # 2. 신고업무 폴더 찾기 (키워드 검색)
        report_folder = self._find_folder_by_keyword(year_folder, "신고업무")
        if not report_folder:
            return ScanResult(
                found=False,
                error=f"신고업무 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(year_folder, "신고업무")
            )
        
        # 3. 월 귀속 폴더 찾기 (키워드 검색)
        month_keyword = f"{month:02d}월 귀속"
        month_folder = self._find_folder_by_keyword(report_folder, month_keyword)
        
        if month_folder:
            return ScanResult(found=True, path=month_folder)
        else:
            return ScanResult(
                found=False,
                error=f"'{month_keyword}' 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(report_folder, f"{month}월")
            )
    
    def scan_files(self, work_type: str, period_str: str, file_type: str = None) -> Dict[str, ScanResult]:
        """파일들 스캔"""
        results = {}
        
        # 작업 폴더 찾기
        work_folder_result = self.scan_work_folder(work_type, period_str)
        if not work_folder_result.found:
            return {"_work_folder_error": work_folder_result}
        
        work_folder = work_folder_result.path
        
        # 회사별 폴더 및 파일 검색
        file_types = ["AKT", "INC", "MR", "AX"] if not file_type else [file_type]
        
        for ftype in file_types:
            results[ftype] = self._scan_company_files(work_folder, ftype, period_str)
        
        return results
    
    def _scan_company_files(self, work_folder: Path, file_type: str, period_str: str) -> ScanResult:
        """회사별 파일 스캔"""
        # 1. 회사 폴더 찾기
        company_folder = self._find_company_folder(work_folder, file_type)
        if not company_folder:
            return ScanResult(
                found=False,
                error=f"{file_type} 회사 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(work_folder, file_type)
            )
        
        # 2. 파일 찾기
        matching_files = self._find_files_by_keywords(company_folder, file_type, period_str)
        
        if len(matching_files) == 1:
            return ScanResult(found=True, path=matching_files[0])
        elif len(matching_files) > 1:
            return ScanResult(
                found=True,
                paths=matching_files,
                error=f"여러 개의 {file_type} 파일이 발견되었습니다"
            )
        else:
            return ScanResult(
                found=False,
                error=f"{file_type} 파일을 찾을 수 없습니다",
                candidates=self._find_similar_files(company_folder, file_type)
            )
    
    def _find_folder_by_keyword(self, parent: Path, keyword: str) -> Optional[Path]:
        """키워드로 폴더 찾기"""
        try:
            for item in parent.iterdir():
                if item.is_dir() and keyword in item.name:
                    return item
        except:
            pass
        return None
    
    def _find_company_folder(self, work_folder: Path, file_type: str) -> Optional[Path]:
        """회사 폴더 찾기"""
        keyword_map = {
            "AKT": ["AKT"],
            "INC": ["HC", "MR", "INC"],
            "MR": ["HC", "MR"],
            "AX": ["HR", "AX"]
        }
        
        keywords = keyword_map.get(file_type, [])
        
        try:
            for item in work_folder.iterdir():
                if item.is_dir():
                    item_name_upper = item.name.upper()
                    if any(kw.upper() in item_name_upper for kw in keywords):
                        return item
        except:
            pass
        return None
    
    def _find_files_by_keywords(self, folder: Path, file_type: str, period_str: str) -> List[Path]:
        """파일 키워드 검색"""
        if not folder.exists():
            return []
        
        period_vars = self.mapper.parse_period(period_str)
        month = period_vars.get("month", 0)
        
        file_keywords = {
            "AKT": [f"{month}월귀속"],
            "INC": ["INC"],
            "MR": ["MR"],
            "AX": ["AX"]
        }
        
        keywords = file_keywords.get(file_type, [])
        matching_files = []
        
        for ext in ["*.xlsx", "*.xls"]:
            for file_path in folder.glob(ext):
                file_name_upper = file_path.name.upper()
                if all(kw.upper() in file_name_upper for kw in keywords):
                    matching_files.append(file_path)
        
        return matching_files
    
    def _find_similar_folders(self, parent: Path, target_name: str) -> List[Path]:
        """비슷한 폴더 찾기"""
        if not parent.exists():
            return []
        
        candidates = []
        try:
            for item in parent.iterdir():
                if item.is_dir():
                    candidates.append(item)
        except:
            pass
        
        return candidates[:5]
    
    def _find_similar_files(self, folder: Path, file_type: str) -> List[Path]:
        """비슷한 파일 찾기"""
        if not folder.exists():
            return []
        
        candidates = []
        for ext in ["*.xlsx", "*.xls"]:
            for file_path in folder.glob(ext):
                candidates.append(file_path)
        
        return candidates[:10]
    
    def validate_scan_results(self, results: Dict[str, ScanResult]) -> Tuple[bool, List[str]]:
        """스캔 결과 검증"""
        errors = []
        found_count = 0
        
        for file_type, result in results.items():
            if file_type.startswith("_"):
                continue
            if result.found:
                found_count += 1
            else:
                errors.append(f"{file_type}: {result.error}")
        
        return found_count > 0, errors
    
    def get_final_file_paths(self, results: Dict[str, ScanResult]) -> Dict[str, Path]:
        """최종 파일 경로 추출"""
        final_paths = {}
        
        for file_type, result in results.items():
            if file_type.startswith("_"):
                continue
            
            if result.found:
                if result.path:
                    final_paths[file_type] = result.path
                elif result.paths:
                    final_paths[file_type] = result.paths[0]
        
        return final_paths
    
    def scan_vehicle_folders(self, work_type: str, period_str: str) -> ScanResult:
        """
        업무용승용차 폴더 및 파일 동적 검색
        경로: 법인세 세무조정 > nn년 세무조정 > nn년 n분기 > 
            업무용승용차 폴더 > 업무용승용차 폴더 > 운행일지 폴더들
        """
        if not self.mapper.base_path:
            return ScanResult(
                found=False,
                error=f"법인세 세무조정 폴더가 설정되지 않았습니다. 설정 페이지에서 경로를 지정하세요."
            )
        
        # 기간 파싱
        period_vars = self.mapper.parse_period(period_str)
        year = period_vars.get("full_year")
        quarter = period_vars.get("quarter")
        
        if not year or not quarter:
            return ScanResult(found=False, error="기간 형식이 올바르지 않습니다 (예: 2025년 1분기)")
        
        # 1. {year}년 세무조정 폴더 찾기 (2024년, 24년 모두 인식)
        year_folder = self._find_year_folder_flexible(self.mapper.base_path, int(year), "세무조정")

        if not year_folder:
            short_year = str(year)[2:]
            return ScanResult(
                found=False,
                error=f"{year}년 또는 {short_year}년 세무조정 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(self.mapper.base_path, "세무조정")
            )
        
        # 2. {year}년 {quarter}분기 폴더 찾기 (2024년 4분기, 24년 4분기 등 모두 인식)
        short_year = str(year)[2:]
        quarter_patterns = [
            f"{year}년 {quarter}분기",      # 2024년 4분기
            f"{year}년{quarter}분기",       # 2024년4분기
            f"{short_year}년 {quarter}분기", # 24년 4분기
            f"{short_year}년{quarter}분기",  # 24년4분기
            f"{quarter}분기",                # 4분기 (연도 없이)
        ]

        quarter_folder = None
        for pattern in quarter_patterns:
            quarter_folder = self._find_folder_by_keyword(year_folder, pattern)
            if quarter_folder:
                break

        if not quarter_folder:
            return ScanResult(
                found=False,
                error=f"{year}년 또는 {short_year}년 {quarter}분기 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(year_folder, "분기")
            )
        
        # 3. 업무용승용차 폴더 찾기 (1단계)
        vehicle_folder_1 = self._find_folder_by_keyword(quarter_folder, "업무용승용차")
        if not vehicle_folder_1:
            return ScanResult(
                found=False,
                error="업무용승용차 폴더를 찾을 수 없습니다 (1단계)",
                candidates=self._find_similar_folders(quarter_folder, "승용차")
            )
        
        # 4. 업무용승용차 폴더 찾기 (2단계)
        vehicle_folder_2 = self._find_folder_by_keyword(vehicle_folder_1, "업무용승용차")
        if not vehicle_folder_2:
            return ScanResult(
                found=False,
                error="업무용승용차 폴더를 찾을 수 없습니다 (2단계)",
                candidates=self._find_similar_folders(vehicle_folder_1, "승용차")
            )
        
        # 5. 운행일지 폴더들 모두 찾기
        log_folders = self._find_all_folders_by_keyword(vehicle_folder_2, "운행일지")
        if not log_folders:
            return ScanResult(
                found=False,
                error="운행일지 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(vehicle_folder_2, "")
            )
        
        # 6. 각 운행일지 폴더에서 파일들 수집
        all_files = []
        for log_folder in log_folders:
            files = self._find_vehicle_files(log_folder)
            all_files.extend(files)
        
        if not all_files:
            return ScanResult(
                found=False,
                error="업무차량 또는 운행일지 파일을 찾을 수 없습니다",
                candidates=[]
            )
        
        return ScanResult(found=True, paths=all_files)


    def _find_all_folders_by_keyword(self, parent: Path, keyword: str) -> List[Path]:
        """키워드로 모든 폴더 찾기"""
        folders = []
        try:
            for item in parent.iterdir():
                if item.is_dir() and keyword in item.name:
                    folders.append(item)
        except:
            pass
        return folders


    def _find_vehicle_files(self, folder: Path) -> List[Path]:
        """업무차량/운행일지 파일 찾기"""
        if not folder.exists():
            return []
        
        keywords = ["업무차량", "운행일지"]
        matching_files = []
        
        for ext in ["*.xlsx", "*.xls"]:
            for file_path in folder.glob(ext):
                if any(kw in file_path.name for kw in keywords):
                    matching_files.append(file_path)
        
        return matching_files
    
    def scan_foreign_currency_folders(self, work_type: str, period_str: str) -> Dict[str, ScanResult]:
        """
        외화획득명세서 폴더 및 파일 동적 검색
        
        구조:
        02_ 국제조세 자료/
        └── 인보이스 발행/
            ├── 해외인보이스발행내역 (2025).xlsx  ← 3단계
            └── 외화획득명세서 작업/
                └── 25년 2분기/
                    ├── A2리스트.xlsx              ← 4단계
                    ├── Unipass실적조회/           ← 1단계
                    └── 환율조회/                  ← 2단계
        """
        if not self.mapper.base_path:
            return {
                "_error": ScanResult(
                    found=False,
                    error="국제조세 폴더가 설정되지 않았습니다. 설정 페이지에서 경로를 지정하세요."
                )
            }
        
        # 기간 파싱
        period_vars = self.mapper.parse_period(period_str)
        year = period_vars.get("full_year")
        quarter = period_vars.get("quarter")
        short_year = period_vars.get("year")
        
        if not year or not quarter:
            return {
                "_error": ScanResult(
                    found=False, 
                    error="기간 형식이 올바르지 않습니다 (예: 2025년 1분기)"
                )
            }
        
        results = {}
        
        # 1단계: 기본 경로가 "02_ 국제조세 자료"인지 확인
        base_path = self.mapper.base_path
        
        # 2단계: "인보이스 발행" 폴더 찾기
        invoice_base_folder = self._find_folder_by_keyword(base_path, "인보이스")
        if not invoice_base_folder:
            return {
                "_error": ScanResult(
                    found=False,
                    error=f"'인보이스 발행' 폴더를 찾을 수 없습니다: {base_path}",
                    candidates=self._find_similar_folders(base_path, "인보이스")
                )
            }
        
        # 3번 작업: 해외인보이스발행내역 (연도).xlsx 파일 찾기
        invoice_files = self._find_files_by_pattern(invoice_base_folder, "해외인보이스", year)
        if invoice_files:
            results['invoice'] = ScanResult(found=True, paths=invoice_files)
        else:
            results['invoice'] = ScanResult(
                found=False,
                error=f"'해외인보이스발행내역 ({year}).xlsx' 파일을 찾을 수 없습니다",
                candidates=self._find_similar_files_in_folder(invoice_base_folder, "인보이스")
            )
        
        # 3단계: "외화획득명세서 작업" 폴더 찾기
        work_folder = self._find_folder_by_keyword(invoice_base_folder, "외화획득명세서")
        if not work_folder:
            results['_work_folder_error'] = ScanResult(
                found=False,
                error=f"'외화획득명세서 작업' 폴더를 찾을 수 없습니다: {invoice_base_folder}",
                candidates=self._find_similar_folders(invoice_base_folder, "외화")
            )
            return results
        
        # 4단계: "25년 2분기" 폴더 찾기 (다양한 패턴 지원)
        quarter_patterns = [
            f"{short_year}년 {quarter}분기",      # 25년 2분기
            f"{short_year}년{quarter}분기",       # 25년2분기
            f"{year}년 {quarter}분기",            # 2025년 2분기
            f"{year}년{quarter}분기",             # 2025년2분기
        ]

        quarter_folder = None
        for pattern in quarter_patterns:
            quarter_folder = self._find_folder_by_keyword(work_folder, pattern)
            if quarter_folder:
                break

        if not quarter_folder:
            results['_quarter_error'] = ScanResult(
                found=False,
                error=f"'{short_year}년 {quarter}분기' 또는 '{year}년 {quarter}분기' 폴더를 찾을 수 없습니다: {work_folder}",
                candidates=self._find_similar_folders(work_folder, "분기")
            )
            return results
        
        # 1번 작업: Unipass실적조회 폴더 → 수출이행내역기간조회 파일들
        unipass_folder = self._find_folder_by_keyword(quarter_folder, "Unipass")
        if unipass_folder:
            export_files = self._find_files_by_pattern(unipass_folder, "수출이행내역")
            if export_files:
                results['export'] = ScanResult(found=True, paths=export_files)
            else:
                results['export'] = ScanResult(
                    found=False,
                    error="'수출이행내역기간조회' 파일을 찾을 수 없습니다",
                    candidates=self._find_similar_files_in_folder(unipass_folder, "")
                )
        else:
            results['export'] = ScanResult(
                found=False,
                error="'Unipass실적조회' 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(quarter_folder, "Unipass")
            )
        
        # 2번 작업: 환율조회 폴더 → 환율 파일들
        exchange_folder = self._find_folder_by_keyword(quarter_folder, "환율")
        if exchange_folder:
            exchange_files = self._find_files_by_pattern(exchange_folder, "")  # 폴더 내 모든 엑셀 파일
            if exchange_files:
                results['exchange'] = ScanResult(found=True, paths=exchange_files)
            else:
                results['exchange'] = ScanResult(
                    found=False,
                    error="환율 파일을 찾을 수 없습니다"
                )
        else:
            results['exchange'] = ScanResult(
                found=False,
                error="'환율조회' 폴더를 찾을 수 없습니다",
                candidates=self._find_similar_folders(quarter_folder, "환율")
            )
        
        # 4번 작업: A2리스트 파일 (분기 폴더 바로 아래에서 키워드 검색)
        a2_files = self._find_files_by_pattern(quarter_folder, "A2리스트")
        if a2_files:
            results['a2'] = ScanResult(found=True, paths=a2_files)
        else:
            results['a2'] = ScanResult(
                found=False,
                error="파일명에 'A2리스트'가 포함된 파일을 찾을 수 없습니다",
                candidates=self._find_similar_files_in_folder(quarter_folder, "A2")
            )
        
        return results


    def _find_files_by_pattern(self, folder: Path, *keywords) -> List[Path]:
        """키워드 패턴으로 파일 찾기 (모든 키워드 포함)"""
        if not folder.exists():
            return []
        
        matching_files = []
        
        for ext in ["*.xlsx", "*.xls"]:
            for file_path in folder.glob(ext):
                if all(kw in file_path.name for kw in keywords):
                    matching_files.append(file_path)
        
        return matching_files


    def _find_similar_files_in_folder(self, folder: Path, keyword: str = "") -> List[Path]:
        """폴더 내 비슷한 파일 찾기"""
        if not folder.exists():
            return []
        
        candidates = []
        for ext in ["*.xlsx", "*.xls"]:
            for file_path in folder.glob(ext):
                if not keyword or keyword in file_path.name:
                    candidates.append(file_path)
        
        return candidates[:10]