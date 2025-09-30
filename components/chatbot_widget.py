import streamlit as st
from utils.command_parser import get_command_parser
from typing import Dict, Optional
from datetime import datetime
import io

def render_chatbot_interface():
    """
    대시보드용 챗봇 인터페이스 렌더링
    자연어 명령을 입력받아 파싱하고 실행
    """
    # 페이지 전환 대기 체크 (맨 처음에 추가)
    if 'pending_page_switch' in st.session_state:
        target_page = st.session_state.pending_page_switch
        del st.session_state.pending_page_switch
        st.switch_page(target_page)

    # 챗봇 섹션
    st.markdown("### 오늘은 어떤 업무를 도와드릴까요?")
    
    # 명령 파서 초기화
    parser = get_command_parser()
    
    # 입력창과 버튼을 같은 행에 배치
    col_input, col_btn = st.columns([8, 2])
    
    with col_input:
        user_input = st.text_input(
            "명령을 입력하세요",
            placeholder="예: 25년 8월 원천세 처리해줘",
            label_visibility="collapsed",
            key="chatbot_input"
        )
    
    with col_btn:
        execute_button = st.button("실행", type="primary", use_container_width=True)
    
    # 실행 버튼 클릭 또는 엔터 입력 시 처리
    if execute_button and user_input:
        process_command(user_input, parser)
    
    # 최근 명령 기록 표시 (세션에 저장된 경우)
    if "recent_commands" in st.session_state and st.session_state.recent_commands:
        with st.expander("최근 명령 기록"):
            for cmd in st.session_state.recent_commands[-5:]:  # 최근 5개만
                st.caption(f"• {cmd}")


def process_command(user_input: str, parser):
    """
    사용자 명령을 파싱하고 처리
    
    Args:
        user_input: 사용자가 입력한 명령
        parser: CommandParser 인스턴스
    """
    
    # 명령 파싱
    parsed = parser.parse(user_input)
    
    # 명령 검증
    is_valid, message = parser.validate_command(parsed)
    
    if not is_valid:
        st.warning(message)
        return
    
    # 명령 정보 표시
    period_str = parser.get_period_string(parsed)
    
    # 회사명 표시
    if parsed["companies"]:
        company_str = ", ".join(parsed["companies"])
        st.info(f"**{period_str} {company_str} {parsed['task']}** 작업을 시작합니다...")
    else:
        st.info(f"**{period_str} {parsed['task']} 통합** 작업을 시작합니다...")
    
    # 최근 명령 기록에 추가
    if "recent_commands" not in st.session_state:
        st.session_state.recent_commands = []
    st.session_state.recent_commands.append(user_input)
    
    # 세션 상태에 명령 저장 (다른 컴포넌트에서 사용)
    st.session_state.chatbot_command = {
        "task": parsed["task"],
        "year": parsed["year"],
        "month": parsed["month"],
        "quarter": parsed["quarter"],
        "action": parsed["action"],
        "companies": parsed["companies"],  # 회사 리스트 추가
        "period_str": period_str,
        "raw_input": user_input,
    }
    
    # 명령 실행
    execute_task(st.session_state.chatbot_command)


def execute_task(command: Dict):
    """
    파싱된 명령을 실제로 실행
    
    Args:
        command: 파싱된 명령 정보
    """
    
    task = command["task"]
    action = command["action"]
    
    try:
        if task == "원천세":
            if action == "process":
                execute_withholding_tax(command)
            elif action == "view":
                view_withholding_tax(command)
                
        elif task == "외화획득":
            if action == "process":
                execute_foreign_exchange(command)
            elif action == "view":
                view_foreign_exchange(command)
                
        elif task == "부가세":
            if action == "process":
                execute_vat(command)
            elif action == "view":
                view_vat(command)
                
        elif task == "법인세":
            if action == "process":
                execute_corporate_tax(command)
            elif action == "view":
                view_corporate_tax(command)

        elif task == "업무용승용차":  # 추가
            if action == "process":
                execute_vehicle(command)
            elif action == "view":
                view_vehicle(command)

        elif task == "인지세":
            if action == "process":
                execute_stamp_tax(command)
            elif action == "view":
                view_stamp_tax(command)
        
        else:
            st.warning(f"{task}은(는) 아직 지원하지 않는 업무입니다.")
            
    except Exception as e:
        st.error(f"명령 실행 중 오류가 발생했습니다: {str(e)}")


def execute_withholding_tax(command: Dict):
    """원천세 처리 실행"""
    
    with st.spinner("원천세 자동 처리를 시작합니다..."):
        
        # 1단계: 파일 자동 탐색
        st.info(f"**1단계:** {command['period_str']} 원천세 파일을 자동으로 탐색 중...")
        
        try:
            from utils.path_mapper import PathMapper
            from services.file_scanner import FileScanner
            from pathlib import Path
            
            mapper = PathMapper(work_type="원천세")
            scanner = FileScanner(mapper)
            
            # 파일 스캔
            file_results = scanner.scan_files("원천세", command['period_str'])
            is_valid, errors = scanner.validate_scan_results(file_results)
            final_paths = scanner.get_final_file_paths(file_results)
            
            if not final_paths:
                st.error("해당 기간의 원천세 파일을 찾을 수 없습니다.")
                for error in errors:
                    st.warning(error)
                st.info("수동으로 파일을 업로드하려면 원천세 처리 페이지로 이동해주세요.")
                return
            
            st.success(f"파일 탐색 완료! ({len(final_paths)}개 파일)")
            
            # 2단계: 파일 처리
            st.info("**2단계:** 원천세 자동 처리 중...")
            
            # 세션에 파일 경로 저장
            st.session_state.wt_auto_scan_results = {
                'files': final_paths,
                'period': command['period_str'],
                'scan_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            from services.withholding_tax_service import WithholdingTaxService
            service = WithholdingTaxService()
            
            # 회사명 확인
            companies = command.get('companies', [])
            
            if companies:
                # 지정된 회사들만 개별 처리
                process_selected_companies(final_paths, companies, service, command)
            else:
                # 통합 처리
                process_combined_companies(final_paths, service, command)
                
        except Exception as e:
            st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
            import traceback
            with st.expander("상세 오류"):
                st.code(traceback.format_exc())


def process_selected_companies(final_paths, companies, service, command):
    """지정된 회사들만 개별 처리"""
    from pathlib import Path
    
    # 회사명 매핑
    company_mapping = {
        "애커튼": ("AKT", 1),
        "인크": ("INC", 2),
        "엠알": ("MR", 3),
        "에이엑스": ("AX", 4),
    }
    
    if 'wt_processed_files' not in st.session_state:
        st.session_state.wt_processed_files = {}
    
    success_count = 0
    processed_companies = []
    
    for company_name in companies:
        company_key = company_mapping.get(company_name)
        
        if not company_key:
            st.warning(f"'{company_name}'은(는) 인식할 수 없는 회사명입니다.")
            continue
        
        file_type, company_type = company_key
        file_path = final_paths.get(file_type)
        
        if not file_path:
            st.warning(f"{company_name} 회사의 파일을 찾을 수 없습니다.")
            continue
        
        try:
            if Path(file_path).exists():
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                class MockUploadedFile:
                    def __init__(self, content, name):
                        self.content = content
                        self.name = name
                    def getvalue(self):
                        return self.content
                    def getbuffer(self):
                        return self.content
                
                mock_file = MockUploadedFile(file_content, Path(file_path).name)
                result = service.process_file(mock_file, company_type, None)
                
                if result['success']:
                    file_id = str(len(st.session_state.wt_processed_files) + 1)
                    
                    st.session_state.wt_processed_files[file_id] = {
                        'filename': mock_file.name,
                        'company_type': company_type,
                        'company_name': result['company_name'],
                        'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'result_data': result['data'],
                        'excel_data': result['excel_data'],
                        'errors': result.get('errors', []),
                        'source': 'chatbot_auto'
                    }
                    success_count += 1
                    processed_companies.append(result['company_name'])
                    st.success(f"✓ {result['company_name']} 처리 완료")
        
        except Exception as e:
            st.error(f"{company_name} 처리 중 오류: {e}")
    
    if success_count > 0:
        company_list = ", ".join(processed_companies)
        st.success(f"개별 처리가 완료되었습니다! ({company_list})")
        
        # 처리 결과를 세션에 저장
        st.session_state.processing_result = {
            "task": "원천세",
            "period": command["period_str"],
            "companies": processed_companies,
            "status": "success",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files_processed": success_count,
            "from_chatbot": True,
            "processing_type": "individual"
        }
        
        # 버튼으로 이동
        st.session_state.pending_page_switch = "pages/withholding_salary.py"
        
        if st.button("처리 결과 확인하기", type="primary", key="view_result_individual"):
            st.rerun()

    else:
        st.error("지정된 회사들의 처리에 모두 실패했습니다.")


def process_combined_companies(final_paths, service, command):
    """모든 회사 통합 처리"""
    from pathlib import Path
    
    file_type_to_company = {"AKT": 1, "INC": 2, "MR": 3, "AX": 4}
    file_company_mappings = []
    
    for file_type, file_path in final_paths.items():
        try:
            if Path(file_path).exists():
                company_type = file_type_to_company.get(file_type, 1)
                
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                class MockUploadedFile:
                    def __init__(self, content, name):
                        self.content = content
                        self.name = name
                    def getvalue(self):
                        return self.content
                    def getbuffer(self):
                        return self.content
                
                mock_file = MockUploadedFile(file_content, Path(file_path).name)
                file_company_mappings.append((mock_file, company_type, None))
        
        except Exception as e:
            st.error(f"{file_type} 파일 로드 중 오류: {e}")
    
    if not file_company_mappings:
        st.error("처리할 파일이 없습니다.")
        return
    
    # 통합 처리 실행
    try:
        result = service.process_combined_files(file_company_mappings)
        
        if result['success']:
            st.session_state.wt_all_companies_data = result['data']
            st.session_state.wt_combined_excel_data = result['excel_data']
            
            st.success(f"통합 처리가 완료되었습니다! ({len(result['data'])}개 회사)")
            
            # 처리 결과를 세션에 저장
            st.session_state.processing_result = {
                "task": "원천세",
                "period": command["period_str"],
                "status": "success",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "files_processed": len(result['data']),
                "from_chatbot": True,
                "processing_type": "combined"
            }
            
            # 페이지 전환 대기 플래그 설정
            st.session_state.pending_page_switch = "pages/withholding_salary.py"
            
            # 버튼으로 이동
            if st.button("처리 결과 확인하기", type="primary", key="view_result_combined"):
                st.rerun()  # 버튼 클릭 시 rerun으로 페이지 전환 트리거
        else:
            st.error(f"통합 처리 실패: {result.get('error', '알 수 없는 오류')}")
    
    except Exception as e:
        st.error(f"통합 처리 중 오류: {e}")


def view_withholding_tax(command: Dict):
    """원천세 조회"""
    st.info(f"{command['period_str']} 원천세 내역을 조회합니다.")
    # TODO: 조회 로직 구현


def execute_foreign_exchange(command: Dict):
    """외화획득명세서 처리 실행"""
    
    with st.spinner("외화획득명세서 자동 처리를 시작합니다..."):
        
        # 1단계: 파일 자동 탐색
        st.info(f"**1단계:** {command['period_str']} 외화획득명세서 파일을 자동으로 탐색 중...")
        
        try:
            from utils.path_mapper import PathMapper
            from services.file_scanner import FileScanner
            from pathlib import Path
            
            mapper = PathMapper(work_type="국제조세")
            scanner = FileScanner(mapper)
            
            # 파일 스캔
            results = scanner.scan_foreign_currency_folders("국제조세", command['period_str'])
            
            # 오류 체크
            if '_error' in results:
                st.error(f"파일 탐색 실패: {results['_error'].error}")
                st.info("수동으로 파일을 업로드하려면 외화획득명세서 페이지로 이동해주세요.")
                return
            
            # 결과 정리
            found_files = {}
            errors = []
            
            for file_type in ['export', 'exchange', 'invoice', 'a2']:
                if file_type in results:
                    result = results[file_type]
                    if result.found:
                        if result.paths:
                            found_files[file_type] = result.paths
                        elif result.path:
                            found_files[file_type] = result.path
                    else:
                        errors.append(f"{file_type}: {result.error}")
            
            if not found_files:
                st.error("해당 기간의 외화획득명세서 파일을 찾을 수 없습니다.")
                for error in errors:
                    st.warning(error)
                return
            
            st.success(f"파일 탐색 완료! (총 {len(found_files)}개 항목)")
            
            # 2단계: 파일 처리
            st.info("**2단계:** 외화획득명세서 자동 처리 중...")
            
            # Mock 파일 생성 함수
            def create_mock_files(file_paths):
                import io
                
                mock_files = []
                if not isinstance(file_paths, list):
                    file_paths = [file_paths]
                
                for file_path in file_paths:
                    file_path = Path(file_path)
                    
                    if not file_path.exists():
                        continue
                    
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    # io.BytesIO 사용 (완전한 파일 객체)
                    file_obj = io.BytesIO(file_content)
                    file_obj.name = file_path.name
                    
                    mock_files.append(file_obj)
                
                return mock_files
            
            # 서비스 초기화
            from services.foreign_currency_service import ForeignCurrencyService
            service = ForeignCurrencyService()
            
            # 기간 설정
            year = command.get('year')
            quarter = command.get('quarter')
            service.set_period(year, quarter)
            
            # 세션에 서비스 저장
            st.session_state.foreign_currency_service = service
            st.session_state.fc_year = year
            st.session_state.fc_quarter = quarter
            
            processed_stages = []
            
            # 1단계: 수출이행내역
            if 'export' in found_files:
                export_files = create_mock_files(found_files['export'])
                result = service.process_export_data(export_files)
                if 'error' not in result:
                    processed_stages.append("수출이행내역")
            
            # 2단계: 환율정보
            if 'exchange' in found_files:
                exchange_files = create_mock_files(found_files['exchange'])
                result = service.process_exchange_data(exchange_files)
                if 'error' not in result:
                    processed_stages.append("환율정보")
            
            # 3단계: 인보이스 발행내역
            if 'invoice' in found_files:
                invoice_files = create_mock_files(found_files['invoice'])
                export_data = service.get_processed_data('export')
                result = service.process_invoice_data(invoice_files, export_data)
                if 'error' not in result:
                    processed_stages.append("인보이스 발행내역")
            
            # 4단계: A2 데이터
            if 'a2' in found_files:
                a2_files = create_mock_files(found_files['a2'])
                invoice_data = service.get_processed_data('invoice')
                result = service.process_a2_data(a2_files, invoice_data)
                if 'error' not in result:
                    processed_stages.append("A2 데이터")
            
            # ✨ 5단계: 최종 명세서 생성 (추가)
            st.info("**5단계:** 최종 외화획득명세서 생성 중...")
            
            raw_data = service.get_all_data()
            
            # 인보이스 데이터가 있어야 최종 명세서 생성 가능
            if 'invoice' in raw_data and 'data' in raw_data['invoice']:
                invoice_data = raw_data['invoice']['data']
                exchange_data = raw_data.get('exchange', {}).get('data')
                a2_data = raw_data.get('a2', {}).get('data')
                
                final_result = service.generate_final_report(invoice_data, exchange_data, a2_data)
                
                if 'error' not in final_result:
                    processed_stages.append("최종 명세서 생성")
                    st.success("✅ 5단계: 최종 명세서 생성 완료")
                else:
                    st.warning(f"⚠️ 5단계 실패: {final_result['error']}")
            else:
                st.warning("⚠️ 인보이스 데이터가 없어 최종 명세서를 생성할 수 없습니다")
            
            if processed_stages:
                st.success(f"외화획득명세서 처리가 완료되었습니다! ({len(processed_stages)}개 단계)")
                
                # 처리 결과를 세션에 저장
                st.session_state.processing_result = {
                    "task": "외화획득명세서",
                    "period": command["period_str"],
                    "status": "success",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "stages_processed": len(processed_stages),
                    "stages": processed_stages,
                    "from_chatbot": True
                }
                
                # 페이지 전환 대기 플래그 설정
                st.session_state.pending_page_switch = "pages/foreign_currency.py"
                
                if st.button("처리 결과 확인하기", type="primary", key="view_foreign_result"):
                    st.rerun()
            else:
                st.error("모든 파일 처리에 실패했습니다.")
                
        except Exception as e:
            st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
            import traceback
            with st.expander("상세 오류"):
                st.code(traceback.format_exc())


def view_foreign_exchange(command: Dict):
    """외화획득명세서 조회"""
    st.info(f"{command['period_str']} 외화획득명세서를 조회합니다.")
    # TODO: 조회 로직 구현


def execute_vat(command: Dict):
    """부가세 처리 실행"""
    st.success("부가세 자동 처리를 시작합니다.")
    # TODO: 부가세 처리 로직 구현


def view_vat(command: Dict):
    """부가세 조회"""
    st.info(f"{command['period_str']} 부가세를 조회합니다.")
    # TODO: 조회 로직 구현


def execute_corporate_tax(command: Dict):
    """법인세 처리 실행"""
    st.success("법인세 자동 처리를 시작합니다.")
    # TODO: 법인세 처리 로직 구현


def view_corporate_tax(command: Dict):
    """법인세 조회"""
    st.info(f"{command['period_str']} 법인세를 조회합니다.")
    # TODO: 조회 로직 구현

def execute_vehicle(command: Dict):
    """업무용승용차 처리 실행"""
    
    with st.spinner("업무용승용차 자동 처리를 시작합니다..."):
        
        # 1단계: 파일 자동 탐색
        st.info(f"**1단계:** {command['period_str']} 업무용승용차 파일을 자동으로 탐색 중...")
        
        try:
            from utils.path_mapper import PathMapper
            from services.file_scanner import FileScanner
            from pathlib import Path
            
            mapper = PathMapper(work_type="법인세")
            scanner = FileScanner(mapper)
            
            # 파일 스캔
            result = scanner.scan_vehicle_folders("법인세", command['period_str'])
            
            if not result.found or not result.paths:
                st.error("해당 기간의 업무용승용차 파일을 찾을 수 없습니다.")
                if result.error:
                    st.warning(result.error)
                st.info("수동으로 파일을 업로드하려면 업무용승용차 페이지로 이동해주세요.")
                return
            
            st.success(f"파일 탐색 완료! ({len(result.paths)}개 파일)")
            
            # 2단계: 파일 처리
            st.info("**2단계:** 업무용승용차 자동 처리 중...")
            
            # 파일을 BytesIO로 변환
            mock_files = []
            for file_path in result.paths:
                with open(file_path, 'rb') as f:
                    file_content = f.read()
                
                file_obj = io.BytesIO(file_content)
                file_obj.name = file_path.name
                mock_files.append(file_obj)
            
            # 서비스로 처리
            from services.corp_tax_service import get_corp_tax_service
            corp_service = get_corp_tax_service()
            result_df, stats = corp_service.process_vehicle_files(mock_files)
            
            # 세션에 결과 저장
            st.session_state.vehicle_processed_data = {
                'dataframe': result_df,
                'stats': stats,
                'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'chatbot_auto'
            }
            
            st.success(f"업무용승용차 처리가 완료되었습니다! (성공: {stats['processed_files']}개)")
            
            # 처리 결과를 세션에 저장
            st.session_state.processing_result = {
                "task": "업무용승용차",
                "period": command["period_str"],
                "status": "success",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "files_processed": stats['processed_files'],
                "total_records": stats['total_records'],
                "from_chatbot": True
            }
            
            # 페이지 전환 대기 플래그 설정
            st.session_state.pending_page_switch = "pages/corp_workingcar.py"
            
            if st.button("처리 결과 확인하기", type="primary", key="view_vehicle_result"):
                st.rerun()
                
        except Exception as e:
            st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
            import traceback
            with st.expander("상세 오류"):
                st.code(traceback.format_exc())


def view_vehicle(command: Dict):
    """업무용승용차 조회"""
    st.info(f"{command['period_str']} 업무용승용차 내역을 조회합니다.")
    # TODO: 조회 로직 구현

def execute_stamp_tax(command: Dict):
    """인지세 처리 실행 - 설정된 폴더에서 바로 파일 탐색"""
    
    with st.spinner("인지세 자동 처리를 시작합니다..."):
        
        st.info("**1단계:** 인지세 설정 폴더에서 파일을 탐색 중...")
        
        try:
            from pathlib import Path
            from services.stamp_service import get_stamp_tax_service
            from services.folder_service import FolderService
            
            # 사용자가 설정한 인지세 폴더 경로 가져오기
            folder_service = FolderService()
            user_id = st.session_state.get("user", {}).get("user_id", "user")
            
            stamp_structure = folder_service.load_user_folder_structure(user_id, "인지세")
            
            if not stamp_structure or not stamp_structure.get('base_path'):
                st.error("인지세 폴더 경로가 설정되지 않았습니다.")
                st.info("설정 페이지에서 인지세 폴더 경로를 먼저 설정해주세요.")
                
                if st.button("설정 페이지로 이동", key="goto_settings"):
                    st.session_state.pending_page_switch = "pages/settings.py"
                    st.rerun()
                return
            
            stamp_folder = Path(stamp_structure['base_path'])
            
            if not stamp_folder.exists():
                st.error(f"설정된 인지세 폴더가 존재하지 않습니다: {stamp_folder}")
                st.info("설정 페이지에서 올바른 경로로 수정해주세요.")
                return
            
            st.success(f"인지세 폴더: {stamp_folder}")
            
            # 2단계: raw와 total 파일 찾기
            st.info("**2단계:** raw 및 total 파일을 탐색 중...")
            
            raw_file = None
            total_file = None
            
            for file in stamp_folder.glob("*.xlsx"):
                filename_lower = file.name.lower()
                
                if 'raw' in filename_lower and not raw_file:
                    raw_file = file
                elif 'total' in filename_lower and not total_file:
                    total_file = file
            
            if not raw_file:
                st.error("raw 파일을 찾을 수 없습니다.")
                st.info("폴더 내 파일 목록:")
                xlsx_files = list(stamp_folder.glob("*.xlsx"))
                if xlsx_files:
                    for file in xlsx_files:
                        st.write(f"- {file.name}")
                else:
                    st.write("엑셀 파일이 없습니다.")
                return
            
            st.success(f"✓ Raw 파일: {raw_file.name}")
            if total_file:
                st.success(f"✓ Total 파일: {total_file.name}")
            else:
                st.warning("Total 파일이 없습니다 (선택사항)")
            
            # 3단계: 파일 처리
            st.info("**3단계:** 인지세 자동 처리 중...")
            
            stamp_service = get_stamp_tax_service()
            
            # 처리 실행
            df_raw, df_pivot, excel_data = stamp_service.process_files(
                raw_file=raw_file,
                total_file=total_file,
                fill_zero=False
            )
            
            # 세션에 결과 저장
            st.session_state.stamp_processed_data = {
                'raw': df_raw,
                'pivot': df_pivot,
                'excel': excel_data,
                'processed_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'source': 'chatbot_auto',
                'folder_path': str(stamp_folder)
            }
            
            st.success("인지세 처리가 완료되었습니다!")
            st.success(f"✓ Raw 데이터: {len(df_raw)}개 행")
            st.success(f"✓ Pivot 데이터: {len(df_pivot)}개 행")
            
            # 처리 결과를 세션에 저장
            st.session_state.processing_result = {
                "task": "인지세",
                "period": "설정 폴더",
                "status": "success",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "raw_rows": len(df_raw),
                "pivot_rows": len(df_pivot),
                "folder_path": str(stamp_folder),
                "from_chatbot": True
            }
            
            # 페이지 전환 대기 플래그 설정
            st.session_state.pending_page_switch = "pages/stamp_management.py"
            
            if st.button("처리 결과 확인하기", type="primary", key="view_stamp_result"):
                st.rerun()
                
        except Exception as e:
            st.error(f"처리 중 오류가 발생했습니다: {str(e)}")
            import traceback
            with st.expander("상세 오류"):
                st.code(traceback.format_exc())


def view_stamp_tax(command: Dict):
    """인지세 조회"""
    st.info("설정된 인지세 폴더의 내역을 조회합니다.")
    # TODO: 조회 로직 구현