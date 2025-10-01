"""
세금 데이터 관리자 (JSON 저장/로드)
"""

import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import shutil

logger = logging.getLogger(__name__)


class TaxDataManager:
    """세금 데이터 JSON 관리"""
    
    def __init__(self, base_dir: str = "data/tax_records"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 업로드 파일 저장 디렉토리
        self.upload_dir = self.base_dir / "uploads"
        self.upload_dir.mkdir(exist_ok=True)
        
        # 백업 디렉토리
        self.backup_dir = Path("data/backups/tax_records")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_filename_date(self, filename: str) -> Optional[Tuple[int, int]]:
        """
        파일명에서 연도와 월 추출
        예: "25년03월 이행상황신고서.xlsx" → (2025, 3)
        
        Args:
            filename: 파일명
            
        Returns:
            (year, month) 또는 None
        """
        try:
            # 패턴: YY년MM월 형식
            pattern = r'(\d{2})년\s*(\d{1,2})월'
            match = re.search(pattern, filename)
            
            if match:
                year_2digit = int(match.group(1))
                month = int(match.group(2))
                
                # 2자리 연도를 4자리로 변환 (20XX 또는 19XX)
                # 50 이상이면 1900년대, 미만이면 2000년대
                year = 2000 + year_2digit if year_2digit < 50 else 1900 + year_2digit
                
                # 월 유효성 검사
                if 1 <= month <= 12:
                    logger.info(f"파일명에서 날짜 추출: {filename} → {year}년 {month}월")
                    return (year, month)
            
            return None
            
        except Exception as e:
            logger.error(f"파일명 파싱 실패: {filename}, {str(e)}")
            return None
    
    def get_data_file_path(self, tax_type: str) -> Path:
        """세목별 JSON 파일 경로"""
        return self.base_dir / f"{tax_type}.json"
    
    def load_records(self, tax_type: str = "withholding_tax") -> List[Dict[str, Any]]:
        """
        저장된 세금 기록 로드
        
        Args:
            tax_type: 세목 (withholding_tax, vat, corporate_tax 등)
            
        Returns:
            세금 기록 리스트
        """
        file_path = self.get_data_file_path(tax_type)
        
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    logger.info(f"{tax_type} 데이터 로드 완료: {len(data)}건")
                    return data
            else:
                logger.info(f"{tax_type} 데이터 파일 없음, 빈 리스트 반환")
                return []
                
        except Exception as e:
            logger.error(f"데이터 로드 실패: {str(e)}")
            return []
    
    def save_records(self, records: List[Dict[str, Any]], tax_type: str = "withholding_tax") -> bool:
        """
        세금 기록 저장
        
        Args:
            records: 저장할 기록 리스트
            tax_type: 세목
            
        Returns:
            저장 성공 여부
        """
        file_path = self.get_data_file_path(tax_type)
        
        try:
            # 기존 파일 백업
            if file_path.exists():
                self._backup_file(file_path)
            
            # JSON 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, ensure_ascii=False, indent=2)
            
            logger.info(f"{tax_type} 데이터 저장 완료: {len(records)}건")
            return True
            
        except Exception as e:
            logger.error(f"데이터 저장 실패: {str(e)}")
            return False
    
    def add_record(self, record: Dict[str, Any], tax_type: str = "withholding_tax") -> bool:
        """
        새 기록 추가
        
        Args:
            record: 추가할 기록
            tax_type: 세목
            
        Returns:
            저장 성공 여부
        """
        records = self.load_records(tax_type)
        
        # 고유 ID 생성 (연월 + 타임스탬프)
        record['id'] = f"{record['year']}_{record['month']:02d}_{datetime.now().strftime('%H%M%S')}"
        record['created_at'] = datetime.now().isoformat()
        record['updated_at'] = datetime.now().isoformat()
        
        records.append(record)
        
        # 날짜순 정렬 (최신순)
        records.sort(key=lambda x: (x['year'], x['month']), reverse=True)
        
        return self.save_records(records, tax_type)
    
    def update_record(self, record_id: str, updated_data: Dict[str, Any], 
                     tax_type: str = "withholding_tax") -> bool:
        """
        기존 기록 수정
        
        Args:
            record_id: 수정할 기록 ID
            updated_data: 수정할 데이터
            tax_type: 세목
            
        Returns:
            수정 성공 여부
        """
        records = self.load_records(tax_type)
        
        for i, record in enumerate(records):
            if record['id'] == record_id:
                # 기존 데이터 유지하면서 업데이트
                records[i].update(updated_data)
                records[i]['updated_at'] = datetime.now().isoformat()
                
                logger.info(f"기록 수정 완료: {record_id}")
                return self.save_records(records, tax_type)
        
        logger.warning(f"수정할 기록 없음: {record_id}")
        return False
    
    def check_duplicate_record(self, year: int, month: int, tax_type: str = "withholding_tax") -> Optional[str]:
        """
        중복 기록 확인
        
        Args:
            year: 연도
            month: 월
            tax_type: 세목
            
        Returns:
            중복 레코드의 ID (없으면 None)
        """
        records = self.load_records(tax_type)
        
        for record in records:
            if record['year'] == year and record['month'] == month:
                return record['id']
        
        return None
    
    def delete_record_with_files(self, record_id: str, tax_type: str = "withholding_tax") -> bool:
        """
        기록 삭제 (원본 파일 포함)
        
        Args:
            record_id: 삭제할 기록 ID
            tax_type: 세목
            
        Returns:
            삭제 성공 여부
        """
        records = self.load_records(tax_type)
        
        # 삭제할 레코드 찾기
        target_record = None
        for record in records:
            if record['id'] == record_id:
                target_record = record
                break
        
        if not target_record:
            logger.warning(f"삭제할 기록 없음: {record_id}")
            return False
        
        # 원본 파일 삭제
        excel_path = target_record.get('excel_file')
        pdf_path = target_record.get('pdf_file')
        
        if excel_path and Path(excel_path).exists():
            try:
                Path(excel_path).unlink()
                logger.info(f"엑셀 파일 삭제: {excel_path}")
            except Exception as e:
                logger.error(f"엑셀 파일 삭제 실패: {str(e)}")
        
        if pdf_path and Path(pdf_path).exists():
            try:
                Path(pdf_path).unlink()
                logger.info(f"PDF 파일 삭제: {pdf_path}")
            except Exception as e:
                logger.error(f"PDF 파일 삭제 실패: {str(e)}")
        
        # JSON에서 레코드 삭제
        records = [r for r in records if r['id'] != record_id]
        
        return self.save_records(records, tax_type)
    
    def get_records_by_period(self, year: int, month: int = None, 
                             tax_type: str = "withholding_tax") -> List[Dict[str, Any]]:
        """
        기간별 기록 조회
        
        Args:
            year: 연도
            month: 월 (None이면 연도 전체)
            tax_type: 세목
            
        Returns:
            필터링된 기록 리스트
        """
        records = self.load_records(tax_type)
        
        if month is None:
            # 연도 전체
            return [r for r in records if r['year'] == year]
        else:
            # 특정 월
            return [r for r in records if r['year'] == year and r['month'] == month]
    
    def save_uploaded_file(self, uploaded_file, year: int, month: int, 
                          file_type: str) -> Optional[str]:
        """
        업로드된 파일 저장
        
        Args:
            uploaded_file: Streamlit UploadedFile 객체
            year: 연도
            month: 월
            file_type: 'excel' or 'pdf'
            
        Returns:
            저장된 파일 경로 (실패 시 None)
        """
        try:
            # 파일명 생성: withholding_2024_03_excel.xlsx
            ext = Path(uploaded_file.name).suffix
            filename = f"withholding_{year}_{month:02d}_{file_type}{ext}"
            file_path = self.upload_dir / filename
            
            # 파일 저장
            with open(file_path, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            logger.info(f"파일 저장 완료: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"파일 저장 실패: {str(e)}")
            return None
    
    def get_uploaded_file_path(self, year: int, month: int, file_type: str) -> Optional[str]:
        """
        저장된 파일 경로 조회
        
        Args:
            year: 연도
            month: 월
            file_type: 'excel' or 'pdf'
            
        Returns:
            파일 경로 (없으면 None)
        """
        # 가능한 확장자들
        extensions = ['.xlsx', '.xls'] if file_type == 'excel' else ['.pdf']
        
        for ext in extensions:
            filename = f"withholding_{year}_{month:02d}_{file_type}{ext}"
            file_path = self.upload_dir / filename
            
            if file_path.exists():
                return str(file_path)
        
        return None
    
    def _backup_file(self, file_path: Path):
        """파일 백업"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{file_path.stem}_{timestamp}{file_path.suffix}"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(file_path, backup_path)
            logger.info(f"백업 완료: {backup_path}")
            
        except Exception as e:
            logger.warning(f"백업 실패: {str(e)}")
    
    def get_summary_statistics(self, tax_type: str = "withholding_tax") -> Dict[str, Any]:
        """
        데이터 요약 통계
        
        Returns:
            {
                'total_records': int,
                'years': List[int],
                'latest_record': Dict,
                'total_tax_amount': float
            }
        """
        records = self.load_records(tax_type)
        
        if not records:
            return {
                'total_records': 0,
                'years': [],
                'latest_record': None,
                'total_tax_amount': 0
            }
        
        years = sorted(list(set(r['year'] for r in records)), reverse=True)
        total_amount = sum(r.get('total_amount', 0) for r in records)
        
        return {
            'total_records': len(records),
            'years': years,
            'latest_record': records[0],  # 이미 정렬되어 있음
            'total_tax_amount': total_amount
        }