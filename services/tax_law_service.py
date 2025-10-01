"""
세법 개정 모니터링 및 분석 서비스
"""

import pandas as pd
import requests
import xml.etree.ElementTree as ET
import re
import difflib
from datetime import datetime
from typing import Tuple, List, Dict, Optional
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

from utils.settings import settings

# 대기업 관련 키워드 목록
KEYWORD_LIST = [
    # A. 지배구조 및 주주 관련
    "지주회사", "자회사", "손자회사", "수입배당금", "익금불산입", "주식보유비율",
    "의결권", "지분법", "주식양도", "주식평가", "명의신탁", "최대주주", "과점주주",
    # B. 특수관계자 거래 및 이전가격
    "특수관계자", "특수관계인", "부당행위계산부인", "정상가격", "시가", "자금대여",
    "가지급금", "업무무관", "자산 저가 양도", "용역거래", "이전가격", "상표권",
    "로열티", "APA",
    # C. 기업 구조조정 및 M&A
    "합병", "분할", "물적분할", "인적분할", "사업양수도", "적격합병", "적격분할",
    "영업권", "구조조정", "이월결손금 승계",
    # D. 투자 및 재무 활동
    "투자세액공제", "연구인력개발비", "R&D", "대손금", "대손충당금", "감가상각",
    "내용연수", "외화환산", "지급이자", "수입이자",
    # E. 대기업 관련 중요 제도
    "연결납세", "최저한세", "일감 몰아주기", "상호출자", "기업소득환류세제",
    "투자상생협력촉진세제", "글로벌최저한세"
]

class TaxLawService:
    """세법 개정사항 모니터링 및 분석 서비스"""
    
    def __init__(self):
        self.api_key = self._get_api_key()
        self.target_laws = ["법인세법", "소득세법", "부가가치세법", "상속세 및 증여세법", "종합부동산세법", "국세기본법"]
    
    def _get_api_key(self) -> str:
        """API 키 로드"""
        try:
            import streamlit as st
            return st.secrets.get("api_key", "")
        except:
            # secrets 파일에서 직접 로드
            import toml
            secrets_path = Path(".streamlit/secrets.toml")
            if secrets_path.exists():
                with open(secrets_path, "r", encoding="utf-8") as f:
                    secrets = toml.load(f)
                    return secrets.get("api_key", "")
            return ""
    
    def get_law_versions_via_api(self, law_name: str) -> List[Dict]:
        """국가법령정보 API를 통해 특정 세법의 모든 버전 목록 수집"""
        try:
            base_url = "https://open.law.go.kr/DRF/lawSearch.do"
            params = {
                'OC': self.api_key,
                'target': 'law',
                'type': 'XML',
                'query': law_name,
                'display': '100'
            }
            response = requests.get(base_url, params=params, verify=False, timeout=10)
            
            if response.status_code != 200:
                print(f"API 호출 실패: {response.status_code}")
                return []
            
            root = ET.fromstring(response.content)
            versions = []
            
            for law in root.findall('law'):
                title = law.find('법령명').text
                date_str = law.find('시행일자').text
                link = law.find('법령상세링크').text
                law_id = link.split('LSW=')[1].split('&')[0]
                
                versions.append({
                    "title": title,
                    "date": pd.to_datetime(date_str, format='%Y%m%d'),
                    "law_id": law_id
                })
            
            return [v for v in versions if law_name in v['title']]
        except Exception as e:
            print(f"API 처리 중 오류: {e}")
            return []
    
    def get_law_content_via_api(self, law_id: str) -> str:
        """API를 통해 법령 ID에 해당하는 본문 내용 가져오기"""
        try:
            base_url = "https://open.law.go.kr/DRF/lawService.do"
            params = {
                'OC': self.api_key,
                'target': 'law',
                'ID': law_id,
                'type': 'XML'
            }
            response = requests.get(base_url, params=params, verify=False, timeout=10)
            
            if response.status_code != 200:
                return "법령 본문 내용을 가져오는 데 실패했습니다."
            
            root = ET.fromstring(response.content)
            reason = root.find('제개정이유')
            
            if reason is not None and reason.text and reason.text.strip():
                return reason.text.strip()
            else:
                content_elements = root.findall('.//조문내용')
                content = "\n\n".join([jo.text.strip() for jo in content_elements if jo.text])
                return content if content else "본문 내용 없음"
        except Exception as e:
            print(f"법령 본문 처리 중 오류: {e}")
            return "법령 본문 내용을 처리하는 중 오류가 발생했습니다."
    
    def get_proposed_amendment_from_moef(self, keyword: str, driver) -> str:
        """기획재정부에서 최신 세법개정안 내용 스크래핑"""
        try:
            url = "https://www.moef.go.kr/nw/nes/nesdta.do?bbsId=MOSFBBS_000000000028"
            driver.get(url)
            wait = WebDriverWait(driver, 10)
            
            search_box = wait.until(EC.presence_of_element_located((By.ID, "search_str")))
            search_box.send_keys(f"{keyword} 개정안")
            search_box.send_keys(Keys.RETURN)
            time.sleep(2)
            
            results = driver.find_elements(By.CSS_SELECTOR, "ul.board_list > li")
            if not results:
                return "관련 개정안 없음"
            
            latest_link = results[0].find_element(By.TAG_NAME, "a").get_attribute("href")
            driver.get(latest_link)
            
            content_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.view_con")))
            content = content_element.text.strip()
            
            return content
        except Exception as e:
            print(f"기획재정부 스크래핑 중 오류: {e}")
            return "개정안을 가져오는 데 실패했습니다."
    
    def highlight_diffs(self, before: str, after: str) -> Tuple[str, str]:
        """두 텍스트의 차이점을 HTML 태그로 감싸서 반환"""
        matcher = difflib.SequenceMatcher(None, before, after)
        
        before_html, after_html = [], []
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                before_html.append(before[i1:i2])
                after_html.append(after[j1:j2])
            elif tag == 'delete':
                before_html.append(f"<del>{before[i1:i2]}</del>")
            elif tag == 'insert':
                after_html.append(f"<ins>{after[j1:j2]}</ins>")
            elif tag == 'replace':
                before_html.append(f"<del>{before[i1:i2]}</del>")
                after_html.append(f"<ins>{after[j1:j2]}</ins>")
        
        return "".join(before_html), "".join(after_html)
    
    def compare_law_texts(self, text_before: str, text_after: str) -> pd.DataFrame:
        """두 법령 텍스트를 비교하여 변경된 조항 목록 반환"""
        if not text_before or not text_after or "없음" in text_before or "없음" in text_after:
            return pd.DataFrame([["비교 불가", text_before, text_after, ""]],
                              columns=["구분", "변경 전 (As-Is)", "변경 후 (To-Be)", "관련 키워드"])
        
        articles_before = {
            re.split(r'[\s(]', item)[0]: item 
            for item in re.split(r'\n\s*(?=제\d+조)', text_before) 
            if item.strip()
        }
        articles_after = {
            re.split(r'[\s(]', item)[0]: item 
            for item in re.split(r'\n\s*(?=제\d+조)', text_after) 
            if item.strip()
        }
        
        changed_articles = []
        all_article_keys = sorted(
            list(set(articles_before.keys()) | set(articles_after.keys())),
            key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)]
        )
        
        for key in all_article_keys:
            before = articles_before.get(key, "(조항 없음)")
            after = articles_after.get(key, "(조항 없음)")
            
            if before != after:
                combined_text = before + " " + after
                found_keywords = [kw for kw in KEYWORD_LIST if kw in combined_text]
                keywords_str = ", ".join(found_keywords) if found_keywords else ""
                
                if before == "(조항 없음)":
                    changed_articles.append(["신설", before, f"<ins>{after}</ins>", keywords_str])
                elif after == "(조항 없음)":
                    changed_articles.append(["삭제", f"<del>{before}</del>", after, keywords_str])
                else:
                    highlighted_before, highlighted_after = self.highlight_diffs(before, after)
                    changed_articles.append(["수정", highlighted_before, highlighted_after, keywords_str])
        
        if not changed_articles:
            return pd.DataFrame([["변경 없음", "변경된 조항이 없습니다.", "", ""]],
                              columns=["구분", "변경 전 (As-Is)", "변경 후 (To-Be)", "관련 키워드"])
        
        return pd.DataFrame(changed_articles, columns=["구분", "변경 전 (As-Is)", "변경 후 (To-Be)", "관련 키워드"])
    
    def analyze_single_law(self, law_name: str, driver) -> Optional[Tuple[pd.DataFrame, Dict]]:
        """
        단일 세법 분석 (현재 법령 vs 최종안)
        
        Returns:
            (비교 결과 DataFrame, 요약 정보) 또는 None
        """
        try:
            all_versions = self.get_law_versions_via_api(law_name)
            if not all_versions:
                print(f"'{law_name}' 버전 정보 수집 실패")
                return None
            
            today = pd.to_datetime(datetime.now().strftime("%Y-%m-%d"))
            past_versions = sorted([v for v in all_versions if v['date'] <= today], key=lambda x: x['date'], reverse=True)
            future_versions = sorted([v for v in all_versions if v['date'] > today], key=lambda x: x['date'])
            
            current_law = past_versions[0] if past_versions else None
            future_law = future_versions[0] if future_versions else None
            
            if not current_law:
                print(f"'{law_name}' 현재 시행 중인 법령 없음")
                return None
            
            if not future_law:
                print(f"'{law_name}' 시행 예정 법령 없음")
                return None
            
            current_law_content = self.get_law_content_via_api(current_law['law_id'])
            future_law_content = self.get_law_content_via_api(future_law['law_id'])
            
            # 현재 법령 vs 최종안 비교
            report = self.compare_law_texts(current_law_content, future_law_content)
            
            # 변경사항이 없는 경우
            if "변경된 조항이 없습니다." in report.iloc[0, 1]:
                return None
            
            summary = {
                "law_name": law_name,
                "current_law_title": current_law['title'],
                "future_law_title": future_law['title'],
                "current_law_date": current_law['date'].strftime('%Y-%m-%d'),
                "future_law_date": future_law['date'].strftime('%Y-%m-%d')
            }
            
            return report, summary
            
        except Exception as e:
            print(f"'{law_name}' 분석 중 오류: {e}")
            return None
    
    def format_report_to_html(self, report_df: pd.DataFrame, summary: Dict) -> str:
        """분석 결과를 HTML 형식으로 변환 (공지사항용)"""
        html = f"""
        <div style='font-family: sans-serif; line-height: 1.6;'>
            <h3>{summary['law_name']} 개정사항 분석</h3>
            <p><strong>현재 법령:</strong> {summary['current_law_title']} (시행일: {summary['current_law_date']})</p>
            <p><strong>변경 후:</strong> {summary['future_law_title']} (시행일: {summary['future_law_date']})</p>
            <hr>
        """
        
        # 테이블 스타일
        html += """
        <style>
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f2f2f2; font-weight: bold; }
            del { background-color: #ffcdd2; text-decoration: none; padding: 2px 4px; }
            ins { background-color: #c8e6c9; text-decoration: none; padding: 2px 4px; }
            tr:hover { background-color: #f5f5f5; }
        </style>
        """
        
        html += report_df.to_html(escape=False, index=False)
        html += "</div>"
        
        return html

# 싱글톤 인스턴스
_tax_law_service = None

def get_tax_law_service() -> TaxLawService:
    """세법 서비스 싱글톤 반환"""
    global _tax_law_service
    if _tax_law_service is None:
        _tax_law_service = TaxLawService()
    return _tax_law_service