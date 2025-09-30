# utils/treaty/__init__.py
"""조세조약 검색 모듈"""

from .constants import (
    TREATY_COUNTRIES,
    COUNTRY_REGIONS,
    ARTICLE_CATEGORIES,
    TREATY_BASE_DIR,
    TREATY_RAW_DIR,
    TREATY_PROCESSED_DIR,
    TREATY_INDEX_DIR
)

from .data import TreatyDataManager
from .processor import TreatyPDFProcessor, TreatySearchEngine

__all__ = [
    # 상수
    'TREATY_COUNTRIES',
    'COUNTRY_REGIONS',
    'ARTICLE_CATEGORIES',
    'TREATY_BASE_DIR',
    'TREATY_RAW_DIR',
    'TREATY_PROCESSED_DIR',
    'TREATY_INDEX_DIR',
    
    # 클래스
    'TreatyDataManager',
    'TreatyPDFProcessor',
    'TreatySearchEngine',
]

__version__ = '1.0.0'
