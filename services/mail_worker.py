"""
TAXtok 메일 발송 워커
백그라운드에서 실행되어 예약된 시간에 메일을 발송합니다.
"""

import win32com.client as win32
import pythoncom
import time
from datetime import datetime
import argparse
import os
import sys

def send_email_worker(to_email, subject, body, attachment_path, importance, cc, bcc):
    """Outlook을 통해 메일 발송"""
    pythoncom.CoInitialize()
    
    try:
        # Outlook 연결
        outlook = win32.Dispatch('outlook.application')
        mail = outlook.CreateItem(0)  # MailItem
        
        # 기본 메일 정보 설정
        mail.To = to_email
        mail.Subject = subject
        mail.Body = body
        
        # 참조, 숨은참조 설정
        if cc:
            mail.CC = cc
        if bcc:
            mail.BCC = bcc
        
        # 첨부파일 추가
        if (attachment_path and 
            attachment_path.lower() != 'none' and 
            os.path.exists(attachment_path)):
            mail.Attachments.Add(os.path.abspath(attachment_path))
        
        # 중요도 설정 (2=높음, 1=보통, 0=낮음)
        if importance == '2':
            mail.Importance = 2
        
        # 메일 발송
        mail.Send()
        
        print(f"[{datetime.now()}] ✅ SUCCESS: 메일 발송 완료 - {to_email}")
        
        # 첨부파일 정리 (임시 파일인 경우)
        if (attachment_path and 
            attachment_path.lower() != 'none' and 
            os.path.exists(attachment_path) and
            'mail_attachments' in attachment_path):
            try:
                os.remove(attachment_path)
                print(f"[{datetime.now()}] 🗑️ 첨부파일 정리 완료: {attachment_path}")
            except Exception as cleanup_error:
                print(f"[{datetime.now()}] ⚠️ 첨부파일 정리 실패: {cleanup_error}")
    
    except Exception as e:
        print(f"[{datetime.now()}] ❌ FAILED: 메일 발송 실패 - {to_email}. 오류: {e}")
    
    finally:
        pythoncom.CoUninitialize()


def main():
    """메인 워커 함수"""
    parser = argparse.ArgumentParser(description="TAXtok 메일 발송 워커")
    parser.add_argument("--schedule_time", required=True, help="발송 예약 시간 (ISO 형식)")
    parser.add_argument("--to_email", required=True, help="수신자 이메일")
    parser.add_argument("--subject", required=True, help="메일 제목")
    parser.add_argument("--body_path", required=True, help="본문 임시 파일 경로")
    parser.add_argument("--attachment_path", required=True, help="첨부파일 경로")
    parser.add_argument("--importance", required=True, help="중요도 (1=보통, 2=높음)")
    parser.add_argument("--cc", default="", help="참조 이메일")
    parser.add_argument("--bcc", default="", help="숨은참조 이메일")
    
    args = parser.parse_args()
    
    try:
        # 예약 시간 파싱
        scheduled_time = datetime.fromisoformat(args.schedule_time)
        now = datetime.now()
        
        # 대기 시간 계산
        wait_seconds = (scheduled_time - now).total_seconds()
        
        if wait_seconds > 0:
            print(f"[{now}] ⏰ 예약 발송 대기 중... {wait_seconds:.0f}초 후 발송")
            time.sleep(wait_seconds)
        
        # 본문 내용 읽기
        if not os.path.exists(args.body_path):
            raise FileNotFoundError(f"본문 파일을 찾을 수 없습니다: {args.body_path}")
        
        with open(args.body_path, 'r', encoding='utf-8') as f:
            body_content = f.read()
        
        # 메일 발송
        send_email_worker(
            to_email=args.to_email,
            subject=args.subject,
            body=body_content,
            attachment_path=args.attachment_path,
            importance=args.importance,
            cc=args.cc,
            bcc=args.bcc
        )
    
    except Exception as e:
        print(f"[{datetime.now()}] ❌ 워커 실행 실패: {e}")
    
    finally:
        # 본문 임시 파일 정리
        try:
            if os.path.exists(args.body_path):
                os.remove(args.body_path)
                print(f"[{datetime.now()}] 🗑️ 본문 임시 파일 정리 완료")
        except Exception as cleanup_error:
            print(f"[{datetime.now()}] ⚠️ 임시 파일 정리 실패: {cleanup_error}")


if __name__ == "__main__":
    main()