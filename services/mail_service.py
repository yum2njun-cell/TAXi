import pandas as pd
import os
import subprocess
import sys
import time
from datetime import datetime
from utils.settings import settings
import streamlit as st

class MailService:
    def __init__(self):
        # data 디렉토리 기본 경로 설정
        data_dir = getattr(settings, 'DATA_DIR', 'data')
        self.attachment_dir = os.path.join(data_dir, 'mail_attachments')
        self.body_temp_dir = os.path.join(data_dir, 'body_temp')
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        os.makedirs(self.attachment_dir, exist_ok=True)
        os.makedirs(self.body_temp_dir, exist_ok=True)
    
    def schedule_bulk_email_jobs(self, df, subject, body, email_column, name_column, 
                               cc_column, bcc_column, attachment_name_format, 
                               attach_files, use_schedule, schedule_datetime, set_high_importance):
        """대량 메일 발송 작업 스케줄링"""
        
        logs = []
        
        # 유효하지 않은 이메일 주소 필터링
        invalid_email_mask = (
            pd.isna(df[email_column]) | 
            (df[email_column].astype(str).str.contains('@') == False)
        )
        invalid_df = df[invalid_email_mask]
        valid_df = df[~invalid_email_mask].copy()
        
        # 무효한 이메일 로깅
        if not invalid_df.empty:
            logs.append("--- 무효한 이메일 주소 목록 ---")
            for index, row in invalid_df.iterrows():
                name = self._get_name_from_row(row, name_column)
                email_val = row.get(email_column, '비어있음')
                logs.append(f"⏩ SKIPPED: '{name}'님의 이메일이 유효하지 않습니다. (값: {email_val})")
            logs.append("--------------------------------")
        
        if valid_df.empty:
            logs.append("❌ 발송할 유효한 이메일 주소가 없습니다.")
            return {'success': False, 'logs': logs}
        
        # 이름 컬럼 처리
        if name_column != '(선택 안 함)':
            valid_df[name_column] = valid_df[name_column].fillna('이름없음')
        
        # 이메일 주소로 그룹화 (중복 이메일 통합)
        grouped = valid_df.groupby(email_column)
        
        # 프로그레스 바 초기화
        progress_bar = st.progress(0, text="메일 발송 작업을 등록하고 있습니다...")
        
        success_count = 0
        total_groups = len(grouped)
        
        for i, (email, group_df) in enumerate(grouped):
            try:
                # 그룹의 첫 번째 행에서 대표 이름 가져오기
                receiver_name = self._get_name_from_row(group_df.iloc[0], name_column)
                
                # CC, BCC 통합
                cc_recipients = self._collect_recipients(group_df, cc_column)
                bcc_recipients = self._collect_recipients(group_df, bcc_column)
                
                # 첨부파일 생성
                attachment_path = "None"
                if attach_files:
                    attachment_path = self._create_attachment(
                        group_df, receiver_name, attachment_name_format
                    )
                
                # 본문 임시 파일 생성
                body_path = self._create_body_temp_file(body, i)
                
                # 중요도 설정
                importance_flag = '2' if set_high_importance else '1'
                
                # 발송 시간 결정
                effective_schedule_time = (
                    schedule_datetime if use_schedule 
                    else datetime.now() + pd.Timedelta(seconds=10)
                )
                
                # 워커 프로세스 실행
                self._start_worker_process(
                    email, subject, body_path, attachment_path,
                    importance_flag, cc_recipients, bcc_recipients,
                    effective_schedule_time
                )
                
                success_count += 1
                logs.append(
                    f"✅ SUCCESS: {receiver_name}({email})님에게 "
                    f"{len(group_df)}건의 데이터를 통합하여 작업 등록 완료 "
                    f"(첨부: {'O' if attach_files else 'X'})"
                )
                
            except Exception as e:
                logs.append(f"❌ FAILED: {email} 주소의 작업 등록 중 오류 발생 - {e}")
            
            # 프로그레스 업데이트
            progress_bar.progress(
                (i + 1) / total_groups, 
                text=f"작업 등록 진행: {i+1}/{total_groups}"
            )
        
        # 최종 요약
        summary = f"총 {success_count}명에게 메일 발송 작업이 등록되었습니다."
        logs.insert(0, f"--- 작업 등록 요약 ---\n{summary}\n-----------------")
        
        return {
            'success': True,
            'total_sent': success_count,
            'total_invalid': len(invalid_df),
            'logs': logs
        }
    
    def _get_name_from_row(self, row, name_column):
        """행에서 이름 추출"""
        if name_column == '(선택 안 함)':
            return '이름없음'
        return row.get(name_column, '이름없음')
    
    def _collect_recipients(self, group_df, column):
        """그룹에서 수신자 목록 수집 (중복 제거)"""
        if column == '(선택 안 함)':
            return ""
        
        recipients = set(group_df[column].dropna().astype(str))
        return "; ".join(recipients)
    
    def _create_attachment(self, group_df, receiver_name, attachment_name_format):
        """첨부파일 생성"""
        try:
            # 안전한 파일명 생성
            safe_name = "".join(
                c for c in str(receiver_name) 
                if c.isalnum() or c in "._- "
            ) if receiver_name != '이름없음' else ""
            
            attachment_filename = attachment_name_format.format(이름=safe_name)
            if not attachment_filename.lower().endswith('.xlsx'):
                attachment_filename += '.xlsx'
            
            attachment_path = os.path.join(self.attachment_dir, attachment_filename)
            
            # 엑셀 파일 생성
            group_df.to_excel(attachment_path, index=False, engine='openpyxl')
            return attachment_path
            
        except Exception as e:
            raise Exception(f"첨부파일 생성 실패: {e}")
    
    def _create_body_temp_file(self, body, index):
        """본문 임시 파일 생성"""
        body_filename = f"body_{index}_{int(time.time())}.txt"
        body_path = os.path.join(self.body_temp_dir, body_filename)
        
        with open(body_path, 'w', encoding='utf-8') as f:
            f.write(body)
        
        return body_path
    
    def _start_worker_process(self, email, subject, body_path, attachment_path,
                            importance, cc, bcc, schedule_time):
        """워커 프로세스 시작"""
        worker_script = os.path.join(os.getcwd(), "services", "mail_worker.py")
        
        command = [
            sys.executable, worker_script,
            "--schedule_time", schedule_time.isoformat(),
            "--to_email", str(email),
            "--subject", subject,
            "--body_path", body_path,
            "--attachment_path", attachment_path,
            "--importance", importance,
            "--cc", cc,
            "--bcc", bcc
        ]
        
        # Windows에서 백그라운드 프로세스로 실행
        if os.name == 'nt':
            subprocess.Popen(
                command, 
                creationflags=subprocess.DETACHED_PROCESS,
                close_fds=True
            )
        else:
            subprocess.Popen(command, start_new_session=True)