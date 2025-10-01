# 파일 이름: monitor.py

import sys
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options as EdgeOptions

# taxtok 서비스 임포트
from services.tax_law_service import get_tax_law_service
from services.announcement_service import get_announcement_service


# --- 메인 실행 로직 ---
def main():
    print(f"--- 세법 자동 모니터링 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")

    # 서비스 초기화
    tax_service = get_tax_law_service()
    announcement_service = get_announcement_service()

    # Selenium 드라이버 설정
    driver = None
    created_count = 0
    
    try:
        # Edge 드라이버 경로 (프로젝트 루트 기준)
        driver_path = project_root / "drivers" / "msedgedriver.exe"
        
        if not driver_path.exists():
            print(f"오류: Edge 드라이버를 찾을 수 없습니다: {driver_path}")
            return
        
        service = Service(executable_path=str(driver_path))
        options = EdgeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument(
            'user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0'
        )
        options.add_argument("--log-level=3")
        
        driver = webdriver.Edge(service=service, options=options)
        
        # 각 세법에 대해 분석 실행
        for law in tax_service.target_laws:
            print(f"\n'{law}' 분석 중...")
            
            try:
                result = tax_service.analyze_single_law(law, driver)
                
                if result:
                    report_df, summary = result
                    print(f"✓ '{law}'에서 변경사항 발견!")
                    
                    # HTML 형식으로 변환
                    html_content = tax_service.format_report_to_html(report_df, summary)
                    
                    # 공지사항 제목 생성
                    today_str = datetime.now().strftime('%Y년 %m월 %d일')
                    title = f"[자동] {law} 개정사항 ({today_str})"
                    
                    # 공지사항 자동 생성
                    success = announcement_service.create_announcement(
                        title=title,
                        content=html_content,
                        category="세법",
                        author_override={
                            "user_id": "system",
                            "name": "자동 모니터링 시스템"
                        }
                    )
                    
                    if success:
                        created_count += 1
                        print(f"  → 공지사항 생성 완료: {title}")
                    else:
                        print(f"  → 공지사항 생성 실패: {title}")
                else:
                    print(f"  → '{law}' 변경사항 없음")
                    
            except Exception as e:
                print(f"  ✗ '{law}' 분석 중 오류 발생: {e}")
                continue
    
    except Exception as e:
        print(f"오류: 드라이버 초기화 실패 - {e}")
    
    finally:
        if driver:
            driver.quit()
    
    # 결과 요약
    print(f"\n--- 모니터링 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
    print(f"총 {created_count}개의 세법 공지사항이 생성되었습니다.")
    
    if created_count == 0:
        print("새로운 변경사항이 없습니다.")


if __name__ == "__main__":
    main()