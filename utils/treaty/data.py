# utils/treaty/data.py
"""조세조약 데이터 저장 및 조회"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from .constants import TREATY_PROCESSED_DIR, TREATY_INDEX_DIR

class TreatyDataManager:
    """조세조약 데이터 관리 클래스"""
    
    def __init__(self):
        self.processed_dir = TREATY_PROCESSED_DIR
        self.index_dir = TREATY_INDEX_DIR
        
    def save_treaty_data(self, country: str, data: Dict) -> bool:
        """추출된 조약 데이터 저장"""
        try:
            # JSON 형태로 저장
            filename = f"{country}_treaty.json"
            filepath = self.processed_dir / filename
            
            # 메타데이터 추가
            data["metadata"] = {
                "country": country,
                "processed_date": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 인덱스 업데이트
            self._update_index(country, filepath)
            
            return True
        except Exception as e:
            print(f"데이터 저장 실패 ({country}): {e}")
            return False
    
    def load_treaty_data(self, country: str) -> Optional[Dict]:
        """특정 국가의 조약 데이터 로드"""
        try:
            filename = f"{country}_treaty.json"
            filepath = self.processed_dir / filename
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"데이터 로드 실패 ({country}): {e}")
            return None
    
    def load_all_treaties(self) -> Dict[str, Dict]:
        """모든 처리된 조약 데이터 로드"""
        treaties = {}
        
        for filepath in self.processed_dir.glob("*_treaty.json"):
            country = filepath.stem.replace("_treaty", "")
            data = self.load_treaty_data(country)
            if data:
                treaties[country] = data
        
        return treaties
    
    def get_available_countries(self) -> List[str]:
        """처리된 조약이 있는 국가 목록 반환"""
        countries = []
        
        for filepath in self.processed_dir.glob("*_treaty.json"):
            country = filepath.stem.replace("_treaty", "")
            countries.append(country)
        
        return sorted(countries)
    
    def delete_treaty(self, country: str) -> bool:
        """특정 국가 조약 데이터 삭제"""
        try:
            filename = f"{country}_treaty.json"
            filepath = self.processed_dir / filename
            
            if filepath.exists():
                filepath.unlink()
                self._remove_from_index(country)
                return True
            return False
        except Exception as e:
            print(f"데이터 삭제 실패 ({country}): {e}")
            return False
    
    def _update_index(self, country: str, filepath: Path):
        """인덱스 파일 업데이트"""
        index_file = self.index_dir / "treaty_index.json"
        
        # 기존 인덱스 로드
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
        else:
            index = {}
        
        # 새 항목 추가
        index[country] = {
            "filepath": str(filepath),
            "updated_at": datetime.now().isoformat()
        }
        
        # 저장
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def _remove_from_index(self, country: str):
        """인덱스에서 항목 제거"""
        index_file = self.index_dir / "treaty_index.json"
        
        if not index_file.exists():
            return
        
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
        
        if country in index:
            del index[country]
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    
    def get_treaty_stats(self) -> Dict:
        """조약 데이터 통계"""
        countries = self.get_available_countries()
        
        stats = {
            "total_countries": len(countries),
            "countries": countries,
            "last_updated": None
        }
        
        # 가장 최근 업데이트 시간 찾기
        index_file = self.index_dir / "treaty_index.json"
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
                if index:
                    latest = max(index.values(), key=lambda x: x["updated_at"])
                    stats["last_updated"] = latest["updated_at"]
        
        return stats
