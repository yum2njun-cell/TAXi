import streamlit as st
import pandas as pd
from datetime import datetime, time as dt_time
from components.layout import page_header, sidebar_menu
from services.mail_service import MailService
from services.template_service import TemplateService
from utils.state import is_authenticated
from components.theme import apply_custom_theme
from utils.auth import is_guest, check_permission

# 기본 페이지 네비게이션만 숨기고, 커스텀 메뉴는 살리기
st.markdown("""
<style>
/* 멀티페이지 네비 컨테이너는 유지하되, 그 안의 항목만 숨김 */
[data-testid="stSidebarNav"] ul,
[data-testid="stSidebarNav"] li,
[data-testid="stSidebarNav"] a {
    display: none !important;
}

/* 혹시 이전에 + div 를 숨기는 규칙을 넣었다면 무력화 */
[data-testid="stSidebarNav"] + div {
    display: block !important;
    visibility: visible !important;
}
</style>
""", unsafe_allow_html=True)

# 페이지 설정
st.set_page_config(
    page_title="TAXⓘ | TAXtok",
    page_icon="",
    layout="wide"
)

# 스타일 로드 후에
with open("assets/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 커스텀 테마 적용
apply_custom_theme()

# 인증 확인 (수정됨)
if not is_authenticated():
    st.error("로그인이 필요합니다.")
    st.stop()

# 사이드바 메뉴 (수정됨)
with st.sidebar:
    sidebar_menu()

# 페이지 헤더 (수정됨)
page_header("TAXtok", "")

# 서비스 초기화
mail_service = MailService()
template_service = TemplateService()

# 템플릿 관리 (메인 화면에 표시)
st.markdown('<div class="menu-section-title"> 템플릿 관리</div>', unsafe_allow_html=True)

templates = template_service.get_all_templates()
if templates:
    template_col1, template_col2, template_col3, template_col4 = st.columns([0.4, 0.2, 0.2, 0.2])
    
    with template_col1:
        template_options = list(templates.keys())
        chosen_template = st.selectbox("저장된 템플릿", options=template_options, key="template_selector")
    
    with template_col2:
        if st.button(" 미리보기", use_container_width=True, key="preview_template"):
            if chosen_template:
                template_data = templates[chosen_template]
                st.info(f"**제목:** {template_data['subject']}")
                with st.expander("본문 미리보기"):
                    st.text_area("", value=template_data['body'], height=100, disabled=True, key="preview_body")
    
    with template_col3:
        if st.button(" 적용", use_container_width=True, key="apply_template", disabled=is_guest()):
            template_data = templates[chosen_template]
            st.session_state.subject = template_data['subject']
            st.session_state.body = template_data['body']
            st.success("템플릿이 적용되었습니다!")
            st.rerun()
    
    with template_col4:
        if st.button(" 삭제", use_container_width=True, key="delete_template", disabled=is_guest()):
            if check_permission("템플릿 삭제"):
                template_service.delete_template(chosen_template)
                st.success(f"템플릿 '{chosen_template}'이 삭제되었습니다!")
                st.rerun()
else:
    st.info(" 저장된 템플릿이 없습니다. 메일 내용 작성 후 '템플릿저장' 버튼으로 저장하세요.")

# 사용법 안내
with st.expander(" TAXtok 사용 방법"):
    st.markdown("""
    **TAXtok**은 대량 메일 발송을 위한 스마트한 도구입니다.
    
    **1. 엑셀 파일 준비:**
    - 이메일 주소와 수신자 정보가 포함된 엑셀 파일을 준비합니다.
    - 첫 번째 행은 반드시 헤더(컬럼명)여야 합니다.
    
    **2. 발송 정보 설정:**
    - 이메일 주소 컬럼을 선택합니다 (필수)
    - 수신자 이름 컬럼을 선택합니다 (선택사항)
    - 참조(CC), 숨은참조(BCC) 컬럼을 선택합니다 (선택사항)
    
    **3. 메일 내용 작성:**
    - 제목과 본문을 입력합니다
    - 자주 사용하는 내용은 템플릿으로 저장할 수 있습니다
    
    **4. 발송 옵션 설정:**
    - 개별 데이터 첨부 여부를 결정합니다
    - 중요도 설정이 가능합니다
    - 예약 발송을 설정할 수 있습니다
    
    **⚠️ 주의사항:**
    - PC와 Outlook이 실행 상태여야 합니다
    - 예약 발송 시 지정된 시간에 PC가 켜져 있어야 합니다
    """)

# 1. 파일 업로드
st.markdown('<div class="menu-section-title"> 데이터 업로드</div>', unsafe_allow_html=True)

uploaded_file = st.file_uploader(
    "메일 발송 대상 엑셀 파일을 업로드하세요", 
    type=['xlsx', 'xls'],
    help="이메일 주소와 수신자 정보가 포함된 엑셀 파일",
    disabled=is_guest()
)

if uploaded_file is not None:
    try:
        # 파일 읽기
        engine = 'xlrd' if uploaded_file.name.endswith('.xls') else 'openpyxl'
        df = pd.read_excel(uploaded_file, engine=engine)
        
        st.success(f" 파일 업로드 완료: {len(df)}행의 데이터")
        
        # 데이터 미리보기
        with st.expander(" 데이터 미리보기"):
            st.dataframe(df.head(10), use_container_width=True)
        
        column_list = df.columns.tolist()
        optional_column_list = ['(선택 안 함)'] + column_list
        
        # 2. 발송 정보 설정
        st.markdown('<div class="menu-section-title"> 발송 설정</div>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            email_column = st.selectbox(
                " 이메일 주소 컬럼", 
                column_list,
                help="실제 이메일 주소가 들어있는 컬럼을 선택하세요"
            )
        
        with col2:
            name_column = st.selectbox(
                " 수신자 이름 컬럼", 
                optional_column_list,
                help="받는 사람 이름이 들어있는 컬럼을 선택하세요"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            cc_column = st.selectbox(
                " 참조(CC) 컬럼", 
                optional_column_list,
                help="참조로 보낼 이메일 주소가 들어있는 컬럼"
            )
        
        with col4:
            bcc_column = st.selectbox(
                " 숨은참조(BCC) 컬럼", 
                optional_column_list,
                help="숨은참조로 보낼 이메일 주소가 들어있는 컬럼"
            )
        
        attachment_name_format = st.text_input(
            " 첨부파일명 형식",
            value="{이름}_세금계산서",
            help="{이름} 키워드는 수신자 이름으로 자동 치환됩니다"
        )
        
        # 3. 메일 내용 작성
        st.markdown('<div class="menu-section-title"> 메일 내용</div>', unsafe_allow_html=True)
        
        # 세션 상태 초기화
        if 'subject' not in st.session_state:
            st.session_state.subject = ""
        if 'body' not in st.session_state:
            st.session_state.body = ""
        
        subject_input = st.text_input(
            " 메일 제목", 
            value=st.session_state.subject,
            key="subject_widget"
        )
        
        body_input = st.text_area(
            " 메일 본문", 
            value=st.session_state.body,
            height=200,
            key="body_widget"
        )
        
        # 템플릿 저장 버튼
        col_save1, col_save2, col_save3 = st.columns([0.6, 0.2, 0.2])
        with col_save2:
            if st.button(" 임시저장", use_container_width=True, disabled=is_guest()):
                st.session_state.subject = subject_input
                st.session_state.body = body_input
                st.toast(" 내용이 임시저장되었습니다!")
        
        with col_save3:
            if st.button(" 템플릿저장", use_container_width=True, disabled=is_guest()):
                if check_permission("템플릿 저장"):
                    if subject_input.strip():
                        template_name = template_service.save_template(subject_input, body_input)
                        st.toast(f" 템플릿 '{template_name}'이 저장되었습니다!")
                        st.rerun()
                    else:
                        st.warning(" 제목을 입력해야 템플릿을 저장할 수 있습니다.")
        
        # 4. 발송 옵션
        st.markdown('<div class="menu-section-title"> 발송 옵션</div>', unsafe_allow_html=True)
        
        col_opt1, col_opt2 = st.columns(2)
        with col_opt1:
            attach_files = st.checkbox(" 개별 데이터 첨부", value=True)
            set_high_importance = st.checkbox("❗ 중요 메일로 표시")
        
        with col_opt2:
            use_schedule = st.checkbox(" 예약 발송")
            if use_schedule:
                schedule_date = st.date_input(" 발송 날짜", min_value=datetime.today().date())
                
                time_col1, time_col2 = st.columns(2)
                with time_col1:
                    schedule_hour = st.number_input("시간", min_value=0, max_value=23, value=9)
                with time_col2:
                    schedule_minute = st.number_input("분", min_value=0, max_value=59, value=0)
                
                try:
                    schedule_time = dt_time(schedule_hour, schedule_minute)
                    schedule_datetime = datetime.combine(schedule_date, schedule_time)
                    st.info(f" 예약시간: {schedule_datetime.strftime('%Y-%m-%d %H:%M')}")
                except ValueError:
                    st.error(" 잘못된 시간 형식입니다.")
                    schedule_datetime = None
            else:
                schedule_datetime = None
        
        # 5. 발송 실행
        st.markdown('<div class="menu-section-title"> 발송 실행</div>', unsafe_allow_html=True)
        
        if st.button(" 메일 발송 시작", type="primary", use_container_width=True, disabled=is_guest()):
            if check_permission("메일 발송"):
                # 입력 검증
                errors = []
                
                if not subject_input.strip():
                    errors.append("메일 제목을 입력해주세요.")
                
                if not body_input.strip():
                    errors.append("메일 본문을 입력해주세요.")
                
                if use_schedule and schedule_datetime and schedule_datetime < datetime.now():
                    errors.append("예약 시간이 현재 시간보다 이전입니다.")
                
                if errors:
                    for error in errors:
                        st.error(f" {error}")
                else:
                    # 메일 발송 실행
                    with st.spinner(" 메일 발송 작업을 등록하고 있습니다..."):
                        try:
                            result = mail_service.schedule_bulk_email_jobs(
                                df=df,
                                subject=subject_input,
                                body=body_input,
                                email_column=email_column,
                                name_column=name_column,
                                cc_column=cc_column,
                                bcc_column=bcc_column,
                                attachment_name_format=attachment_name_format,
                                attach_files=attach_files,
                                use_schedule=use_schedule,
                                schedule_datetime=schedule_datetime,
                                set_high_importance=set_high_importance
                            )
                            
                            st.success(" 메일 발송 작업이 성공적으로 등록되었습니다!")
                            
                            # 결과 로그 표시
                            if result.get('logs'):
                                with st.expander(" 상세 로그 보기"):
                                    st.text_area(
                                        "발송 결과",
                                        "\n".join(result['logs']),
                                        height=200,
                                        key="result_logs"
                                    )
                        
                        except Exception as e:
                            st.error(f"❌ 메일 발송 중 오류가 발생했습니다: {str(e)}")
    except Exception as e:
        st.error(f"❌ 파일 처리 중 오류가 발생했습니다: {str(e)}")

else:
    st.info(" 엑셀 파일을 업로드하여 시작하세요.")