# utils/treaty/processor.py
"""PDF 처리 및 검색 엔진"""

import re
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import PyPDF2
from .constants import TREATY_RAW_DIR, CONTEXT_CHARS
from .data import TreatyDataManager

class TreatyPDFProcessor:
    """조세조약 PDF 처리 클래스"""
    
    def __init__(self):
        self.raw_dir = TREATY_RAW_DIR
        self.data_manager = TreatyDataManager()
    
    def extract_from_pdf(self, pdf_path: Path, country: str) -> Dict:
        """PDF에서 텍스트 추출 및 구조화 - pdfplumber 사용"""
        import pdfplumber
        
        try:
            # pdfplumber로 텍스트 추출 (한글/특수문자 처리 개선)
            full_text = ""
            pages = []
            
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):
                    # layout=True로 레이아웃 보존
                    page_text = page.extract_text(layout=True) or ""
                    full_text += page_text + "\n"
                    pages.append({
                        "page_num": page_num,
                        "text": page_text
                    })
                
                total_pages = len(pdf.pages)
                
                # 조항별로 파싱
                articles = self._parse_articles(full_text)
                
                # 데이터 구조화
                treaty_data = {
                    "country": country,
                    "filename": pdf_path.name,
                    "pdf_path": str(pdf_path),  # 원본 PDF 경로 추가 ⭐
                    "total_pages": total_pages,
                    "full_text": full_text,
                    "pages": pages,
                    "articles": articles
                }
                
                return treaty_data
        
        except Exception as e:
            raise Exception(f"PDF 추출 실패: {e}")
    
    def _parse_articles(self, text: str) -> List[Dict]:
        """조문 구조 파싱 - 개선 버전"""
        articles = []
        
        # 모든 조문 시작 위치 찾기
        pattern = r'제\s*(\d+)\s*조\s*(?:의\s*\d+)?\s*[:\-\.]?\s*(?:\([^)]*\)|【[^】]*】)?'
        matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
        
        for i, match in enumerate(matches):
            article_num = match.group(1)
            
            # 조문 제목 추출
            title_match = re.search(r'조\s*(?:의\s*\d+)?\s*(.+?)(?:\n|$)', text[match.start():match.start()+200])
            article_title = title_match.group(1).strip() if title_match else "제목 없음"
            
            # 조문 내용: 현재 조문부터 다음 조문 직전까지
            start_pos = match.end()
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                # 마지막 조문은 텍스트 끝까지
                end_pos = len(text)
            
            content = text[start_pos:end_pos].strip()
            
            # 너무 짧거나 긴 내용 필터링
            if len(content) < 10:
                continue
            
            # 페이지 번호 추정
            page_num = text[:match.start()].count('\f') + 1
            
            articles.append({
                "number": article_num,
                "title": article_title,
                "content": content,
                "page": page_num,
                "position": match.start()
            })
        
        return articles
    
    def save_pdf(self, uploaded_file, country: str) -> Path:
        """업로드된 PDF 저장"""
        filename = f"{country}_treaty.pdf"
        filepath = self.raw_dir / filename
        
        with open(filepath, 'wb') as f:
            f.write(uploaded_file.getbuffer())
        
        return filepath
    
    def process_and_save(self, pdf_path: Path, country: str) -> bool:
        """PDF 처리 및 저장 (전체 프로세스)"""
        try:
            # PDF 추출
            treaty_data = self.extract_from_pdf(pdf_path, country)
            
            # 데이터 저장
            success = self.data_manager.save_treaty_data(country, treaty_data)
            
            return success
        except Exception as e:
            print(f"처리 실패: {e}")
            return False


class TreatySearchEngine:
    """조세조약 검색 엔진"""
    
    def __init__(self):
        self.data_manager = TreatyDataManager()
    
    def search(
        self, 
        keyword: str, 
        countries: Optional[List[str]] = None,
        search_in_articles: bool = True,
        search_in_full_text: bool = False
    ) -> List[Dict]:
        """조약 검색"""
        
        results = []
        
        # 검색 대상 국가 결정
        if countries:
            target_countries = countries
        else:
            target_countries = self.data_manager.get_available_countries()
        
        # 각 국가별 검색
        for country in target_countries:
            treaty_data = self.data_manager.load_treaty_data(country)
            
            if not treaty_data:
                continue
            
            country_results = []
            
            # 조항별 검색
            if search_in_articles and "articles" in treaty_data:
                for article in treaty_data["articles"]:
                    # 제목 또는 내용에서 검색
                    if (keyword.lower() in article["title"].lower() or 
                        keyword.lower() in article["content"].lower()):
                        
                        # 하이라이트 텍스트 생성
                        highlighted = self._highlight_keyword(
                            article["content"], 
                            keyword
                        )
                        
                        country_results.append({
                            "type": "article",
                            "article_num": article["number"],
                            "article_title": article["title"],
                            "content": article["content"],
                            "highlighted": highlighted,
                            "page": article["page"]
                        })
            
            # 전체 텍스트 검색 (옵션)
            if search_in_full_text and "full_text" in treaty_data:
                matches = self._find_all_matches(
                    treaty_data["full_text"], 
                    keyword
                )
                
                for match_text, position in matches:
                    country_results.append({
                        "type": "full_text",
                        "content": match_text,
                        "position": position
                    })
            
            # 결과가 있는 경우만 추가
            if country_results:
                results.append({
                    "country": country,
                    "filename": treaty_data.get("filename", ""),
                    "total_pages": treaty_data.get("total_pages", 0),
                    "matches": country_results,
                    "match_count": len(country_results)
                })
        
        # 국가명 가나다순 정렬
        results.sort(key=lambda x: x["country"])
        
        return results
    
    def _highlight_keyword(self, text: str, keyword: str) -> str:
        """키워드 하이라이트 (문맥 포함)"""
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        # 키워드 위치 찾기
        pos = text_lower.find(keyword_lower)
        
        if pos == -1:
            return text[:200] + "..." if len(text) > 200 else text
        
        # 문맥 추출
        start = max(0, pos - CONTEXT_CHARS)
        end = min(len(text), pos + len(keyword) + CONTEXT_CHARS)
        
        context = text[start:end]
        
        # 키워드 강조
        highlighted = re.sub(
            f'({re.escape(keyword)})',
            r'**\1**',
            context,
            flags=re.IGNORECASE
        )
        
        # 앞뒤 생략 표시
        if start > 0:
            highlighted = "..." + highlighted
        if end < len(text):
            highlighted = highlighted + "..."
        
        return highlighted
    
    def _find_all_matches(self, text: str, keyword: str) -> List[Tuple[str, int]]:
        """텍스트에서 모든 매칭 위치 찾기"""
        matches = []
        keyword_lower = keyword.lower()
        text_lower = text.lower()
        
        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            
            # 문맥 추출
            context_start = max(0, pos - CONTEXT_CHARS)
            context_end = min(len(text), pos + len(keyword) + CONTEXT_CHARS)
            context = text[context_start:context_end]
            
            matches.append((context, pos))
            start = pos + 1
        
        return matches
    
    def format_article_content(self, content: str) -> str:
        """조항 내용 포맷팅 - 가독성 개선"""
        import re
        
        # 1. 숫자. 패턴 앞에서 줄바꿈 (1. 2. 3. 등)
        content = re.sub(r'(?<!\n)(\d+\.)', r'\n\1', content)
        
        # 2. 한글-영어 전환 시 줄바꿈
        # 한글 다음 영어 대문자 (예: "규정The" -> "규정\nThe")
        content = re.sub(r'([가-힣])\s*([A-Z])', r'\1\n\2', content)
        
        # 영어 다음 한글 (예: "tax 과세" -> "tax\n과세")
        content = re.sub(r'([a-zA-Z])\s*([가-힣])', r'\1\n\2', content)
        
        # 3. 연속된 줄바꿈 정리 (3개 이상을 2개로)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # 4. 앞뒤 공백 제거
        content = content.strip()
        
        return content
    
    def extract_relevant_section(self, content: str, keyword: str) -> str:
        """키워드가 포함된 관련 섹션만 추출"""
        import re
        
        # 키워드 위치 찾기
        keyword_lower = keyword.lower()
        content_lower = content.lower()
        keyword_pos = content_lower.find(keyword_lower)
        
        if keyword_pos == -1:
            return content[:500] + "..."  # 키워드 없으면 앞부분만
        
        # 패턴 정의: 제 X 조, 제X조 (숫자/한글), 【...】 등
        section_patterns = [
            r'제\s*[0-9]+\s*조\s*(?:의\s*[0-9]+)?\s*(?:\([가-힣0-9]+\))?\s*(?:【[^】]+】)?',  # 제1조, 제1조의2, 제1조(정의), 제1조【정의】
            r'[0-9]+\.\s*[^\n]{0,100}',  # 1. 항목
            r'[가-힣]\.\s*[^\n]{0,100}',  # 가. 항목
            r'\([0-9]+\)\s*[^\n]{0,100}',  # (1) 항목
            r'[①-⑳]\s*[^\n]{0,100}',  # ① 항목
        ]
        
        # 키워드 이전 텍스트에서 가장 가까운 섹션 헤더 찾기
        before_text = content[:keyword_pos]
        section_start = 0
        section_title = ""
        
        for pattern in section_patterns:
            matches = list(re.finditer(pattern, before_text))
            if matches:
                last_match = matches[-1]
                section_start = last_match.start()
                section_title = last_match.group()
                break
        
        # 키워드 이후 텍스트에서 다음 섹션 헤더 찾기
        after_text = content[keyword_pos:]
        section_end = len(content)
        
        for pattern in section_patterns:
            match = re.search(pattern, after_text[len(keyword):])  # 키워드 직후부터 검색
            if match:
                section_end = keyword_pos + len(keyword) + match.start()
                break
        
        # 섹션 추출
        section_content = content[section_start:section_end].strip()
        
        # 너무 짧으면 조금 더 넓게
        if len(section_content) < 100:
            section_start = max(0, section_start - 200)
            section_end = min(len(content), section_end + 200)
            section_content = content[section_start:section_end].strip()
        
        # 포맷팅 적용
        section_content = self.format_article_content(section_content)
        
        return section_content
