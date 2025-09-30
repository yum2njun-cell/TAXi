import pandas as pd
import streamlit as st
from io import BytesIO
from pathlib import Path
from utils.activity_logger import log_vat_activity

import logging
logger = logging.getLogger(__name__)

class CardService:
    """법인카드 공제 여부 판정 서비스"""
    
    def __init__(self):
        self.keywords_file = Path("data/keywords.xlsx")
        self.no_vat_keywords = []
        self.vat_exceptions_keywords = []
        self.keywords_loaded_from_upload = False  # 업로드 파일 사용 여부
        self._load_keywords()
    
    def load_keywords_from_file(self, uploaded_file):
        """업로드된 키워드 파일에서 키워드를 로드"""
        try:
            # 업로드된 파일에서 키워드 로드
            no_vat_df = pd.read_excel(uploaded_file, sheet_name="no_vat")
            vat_exceptions_df = pd.read_excel(uploaded_file, sheet_name="vat_exceptions")
            
            self.no_vat_keywords = no_vat_df["keyword"].dropna().tolist()
            self.vat_exceptions_keywords = vat_exceptions_df["keyword"].dropna().tolist()
            self.keywords_loaded_from_upload = True
            
            logger.info(f"업로드 키워드 로딩 완료: 불공제 {len(self.no_vat_keywords)}개, 예외 {len(self.vat_exceptions_keywords)}개")
            
        except Exception as e:
            logger.error(f"업로드 키워드 파일 로딩 중 오류: {e}")
            raise ValueError(f"키워드 파일 형식이 올바르지 않습니다. 'no_vat'과 'vat_exceptions' 시트가 있고, 각각 'keyword' 컬럼이 있는지 확인해주세요.")
    
    @st.cache_data
    def _load_keywords(_self):
        """키워드 파일에서 불공제 및 예외 키워드를 로드"""
        try:
            if _self.keywords_file.exists():
                # keywords.xlsx 파일에서 키워드 로드
                no_vat_df = pd.read_excel(_self.keywords_file, sheet_name="no_vat")
                vat_exceptions_df = pd.read_excel(_self.keywords_file, sheet_name="vat_exceptions")
                
                _self.no_vat_keywords = no_vat_df["keyword"].dropna().tolist()
                _self.vat_exceptions_keywords = vat_exceptions_df["keyword"].dropna().tolist()
                
                logger.info(f"키워드 로딩 완료: 불공제 {len(_self.no_vat_keywords)}개, 예외 {len(_self.vat_exceptions_keywords)}개")
            else:
                # 키워드 파일이 없으면 기본 키워드 사용
                _self.no_vat_keywords = [
                    "골프", "마사지", "접대", "술집", "노래방", "클럽", "바", "펜션", 
                    "모텔", "호텔", "리조트", "온천", "스파", "사우나", "헬스", 
                    "미용", "네일", "화장품", "의류", "신발", "가방", "시계", 
                    "보석", "꽃", "선물", "경조사"
                ]
                _self.vat_exceptions_keywords = [
                    "회의", "세미나", "교육", "연수", "컨퍼런스", "업무", "출장", 
                    "고객", "거래처", "미팅", "상담", "협의", "계약", "프로젝트"
                ]
                
                # 기본 키워드로 파일 생성
                _self._create_default_keywords_file()
                
                logger.warning("키워드 파일이 없어 기본 키워드를 사용합니다.")
                
        except Exception as e:
            logger.error(f"키워드 로딩 중 오류: {e}")
            st.error(f"키워드 파일 로딩 오류: {e}")
            # 기본값으로 대체
            _self.no_vat_keywords = ["골프", "마사지", "접대"]
            _self.vat_exceptions_keywords = ["회의", "업무", "출장"]
    
    def _create_default_keywords_file(self):
        """기본 키워드 파일 생성"""
        try:
            # 디렉토리 생성
            self.keywords_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 기본 키워드 DataFrame 생성
            no_vat_df = pd.DataFrame({"keyword": self.no_vat_keywords})
            vat_exceptions_df = pd.DataFrame({"keyword": self.vat_exceptions_keywords})
            
            # Excel 파일로 저장
            with pd.ExcelWriter(self.keywords_file, engine='openpyxl') as writer:
                no_vat_df.to_excel(writer, sheet_name="no_vat", index=False)
                vat_exceptions_df.to_excel(writer, sheet_name="vat_exceptions", index=False)
            
            logger.info("기본 키워드 파일이 생성되었습니다.")
            
        except Exception as e:
            logger.error(f"키워드 파일 생성 중 오류: {e}")
    
    def process_card_file(self, uploaded_file) -> pd.DataFrame:
        """업로드된 법인카드 파일을 처리하여 공제 여부 판정"""
        try:
            # Excel 파일 읽기
            df = pd.read_excel(uploaded_file)
            
            # 컬럼명 정규화 (가맹점명 → 거래처)
            if "가맹점명" in df.columns:
                df = df.rename(columns={"가맹점명": "거래처"})
            
            # 필수 컬럼 확인
            if "거래처" not in df.columns:
                raise ValueError("'거래처' 컬럼이 없습니다. 가맹점명 컬럼을 '거래처'로 변경해주세요.")
            
            # 공제 여부 판정
            results = []
            for idx, row in df.iterrows():
                store_name = str(row["거래처"]) if pd.notna(row["거래처"]) else ""
                
                # no_vat 키워드 매칭
                matched_no_vat = [kw for kw in self.no_vat_keywords if kw in store_name]
                no_vat_result = matched_no_vat[0] if matched_no_vat else "불포함"
                
                # vat_exceptions 키워드 매칭
                matched_vat_ex = [kw for kw in self.vat_exceptions_keywords if kw in store_name]
                vat_exceptions_result = "업무유관" if matched_vat_ex else "불포함"
                
                # 최종 공제 여부 판정
                if no_vat_result != "불포함" and vat_exceptions_result == "불포함":
                    deduction_result = "불공제"
                else:
                    deduction_result = "공제"
                
                results.append({
                    "no_vat": no_vat_result,
                    "vat_exceptions": vat_exceptions_result,
                    "공제여부": deduction_result
                })
            
            # 결과를 원본 DataFrame에 추가
            result_df = df.copy()
            for col, values in pd.DataFrame(results).items():
                result_df[col] = values
            
            logger.info(f"법인카드 파일 처리 완료: {len(result_df)}건")

            # 활동 로그 저장
            total_count = len(result_df)
            deductible_count = len(result_df[result_df['공제여부'] == '공제'])
            non_deductible_count = len(result_df[result_df['공제여부'] == '불공제'])

            log_vat_activity(
                "법인카드 공제여부 판정 완료",
                {
                    "total_transactions": total_count,
                    "deductible_count": deductible_count,
                    "non_deductible_count": non_deductible_count
                }
            )
            return result_df
            
        except Exception as e:
            logger.error(f"법인카드 파일 처리 중 오류: {e}")
            raise e
    
    def convert_to_excel(self, df: pd.DataFrame) -> bytes:
        """DataFrame을 Excel 파일로 변환"""
        try:
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Result")
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"Excel 변환 중 오류: {e}")
            raise e
    
    def reset_to_default_keywords(self):
        """기본 키워드로 초기화"""
        self.no_vat_keywords = [
            "골프", "마사지", "접대", "술집", "노래방", "클럽", "바", "펜션", 
            "모텔", "호텔", "리조트", "온천", "스파", "사우나", "헬스", 
            "미용", "네일", "화장품", "의류", "신발", "가방", "시계", 
            "보석", "꽃", "선물", "경조사"
        ]
        self.vat_exceptions_keywords = [
            "회의", "세미나", "교육", "연수", "컨퍼런스", "업무", "출장", 
            "고객", "거래처", "미팅", "상담", "협의", "계약", "프로젝트"
        ]
        self.keywords_loaded_from_upload = False
        logger.info("키워드가 기본값으로 초기화되었습니다.")
    
    def export_current_keywords(self) -> bytes:
        """현재 키워드를 Excel 파일로 내보내기"""
        try:
            output = BytesIO()
            
            # 키워드를 DataFrame으로 변환
            no_vat_df = pd.DataFrame({"keyword": self.no_vat_keywords})
            vat_exceptions_df = pd.DataFrame({"keyword": self.vat_exceptions_keywords})
            
            # Excel 파일로 저장
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                no_vat_df.to_excel(writer, sheet_name="no_vat", index=False)
                vat_exceptions_df.to_excel(writer, sheet_name="vat_exceptions", index=False)
            
            return output.getvalue()
            
        except Exception as e:
            logger.error(f"키워드 내보내기 중 오류: {e}")
            raise e
    
    def get_keywords_summary(self) -> dict:
        """현재 로드된 키워드 요약 반환"""
        return {
            "no_vat_count": len(self.no_vat_keywords),
            "vat_exceptions_count": len(self.vat_exceptions_keywords),
            "no_vat_keywords": self.no_vat_keywords[:10],  # 처음 10개만
            "vat_exceptions_keywords": self.vat_exceptions_keywords[:10]  # 처음 10개만
        }