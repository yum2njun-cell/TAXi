# services/one_on_one_service.py

import sqlite3
from datetime import date
from pathlib import Path
from typing import Optional

class OneOnOneService:
    """1on1 미팅 관리 서비스"""
    
    # 관리자 권한을 가진 사용자 목록
    ADMIN_USERS = ["문상현"]
    
    def __init__(self, current_user_name: Optional[str] = None):
        self.db_file = Path("data/one_on_one.db")
        self.db_file.parent.mkdir(parents=True, exist_ok=True)
        self.current_user_name = current_user_name
        self._init_db()
    
    def _get_connection(self):
        """데이터베이스 연결"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """데이터베이스 초기화"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # 팀원 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS team_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 미팅 기록 테이블
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS meetings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                meeting_date TEXT NOT NULL,
                summary TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (member_id) REFERENCES team_members (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def is_admin(self) -> bool:
        """현재 사용자가 관리자인지 확인"""
        return self.current_user_name in self.ADMIN_USERS
    
    def can_view_member(self, member_name: str) -> bool:
        """특정 팀원의 기록을 볼 수 있는 권한 확인"""
        # 관리자는 모든 팀원 기록 조회 가능
        if self.is_admin():
            return True
        # 일반 사용자는 자기 자신의 기록만 조회 가능
        return self.current_user_name == member_name
    
    def add_team_member(self, name: str, email: str = "") -> tuple[bool, str]:
        """팀원 추가 (관리자만 가능)"""
        if not self.is_admin():
            return False, " 팀원 추가 권한이 없습니다."
        
        try:
            conn = self._get_connection()
            conn.execute(
                "INSERT INTO team_members (name, email) VALUES (?, ?)",
                (name, email)
            )
            conn.commit()
            conn.close()
            return True, f" '{name}' 팀원이 추가되었습니다."
        except sqlite3.IntegrityError:
            return False, f" '{name}' 팀원은 이미 존재합니다."
        except Exception as e:
            return False, f" 오류 발생: {str(e)}"
    
    def get_team_members(self) -> list:
        """팀원 목록 조회 (권한에 따라 필터링)"""
        conn = self._get_connection()
        members = conn.execute(
            "SELECT * FROM team_members ORDER BY name"
        ).fetchall()
        conn.close()
        
        all_members = [dict(m) for m in members]
        
        # 관리자는 모든 팀원 조회 가능
        if self.is_admin():
            return all_members
        
        # 일반 사용자는 자기 자신만 조회 가능
        return [m for m in all_members if m['name'] == self.current_user_name]
    
    def add_meeting(self, member_id: int, meeting_date: date, summary: str) -> tuple[bool, str]:
        """미팅 기록 추가"""
        # 해당 팀원 정보 조회
        conn = self._get_connection()
        member = conn.execute(
            "SELECT name FROM team_members WHERE id = ?",
            (member_id,)
        ).fetchone()
        
        if not member:
            conn.close()
            return False, " 존재하지 않는 팀원입니다."
        
        member_name = member['name']
        
        # 권한 확인: 관리자 또는 본인의 기록만 추가 가능
        if not self.can_view_member(member_name):
            conn.close()
            return False, " 해당 팀원의 기록을 추가할 권한이 없습니다."
        
        try:
            conn.execute(
                "INSERT INTO meetings (member_id, meeting_date, summary) VALUES (?, ?, ?)",
                (member_id, meeting_date.isoformat(), summary)
            )
            conn.commit()
            conn.close()
            return True, " 미팅 내용이 저장되었습니다."
        except Exception as e:
            conn.close()
            return False, f" 오류 발생: {str(e)}"
    
    def get_meetings_by_member(self, member_id: int) -> list:
        """특정 팀원의 미팅 기록 조회 (권한 확인)"""
        conn = self._get_connection()
        
        # 팀원 이름 조회
        member = conn.execute(
            "SELECT name FROM team_members WHERE id = ?",
            (member_id,)
        ).fetchone()
        
        if not member:
            conn.close()
            return []
        
        member_name = member['name']
        
        # 권한 확인
        if not self.can_view_member(member_name):
            conn.close()
            return []
        
        # 미팅 기록 조회
        meetings = conn.execute(
            """
            SELECT * FROM meetings 
            WHERE member_id = ? 
            ORDER BY meeting_date DESC, created_at DESC
            """,
            (member_id,)
        ).fetchall()
        conn.close()
        return [dict(m) for m in meetings]
    
    def delete_meeting(self, meeting_id: int) -> tuple[bool, str]:
        """미팅 기록 삭제 (권한 확인)"""
        conn = self._get_connection()
        
        # 미팅 정보 조회 (어느 팀원의 기록인지 확인)
        meeting = conn.execute(
            """
            SELECT m.*, t.name as member_name 
            FROM meetings m
            JOIN team_members t ON m.member_id = t.id
            WHERE m.id = ?
            """,
            (meeting_id,)
        ).fetchone()
        
        if not meeting:
            conn.close()
            return False, " 존재하지 않는 미팅 기록입니다."
        
        member_name = meeting['member_name']
        
        # 권한 확인
        if not self.can_view_member(member_name):
            conn.close()
            return False, " 해당 기록을 삭제할 권한이 없습니다."
        
        try:
            conn.execute("DELETE FROM meetings WHERE id = ?", (meeting_id,))
            conn.commit()
            conn.close()
            return True, " 미팅 기록이 삭제되었습니다."
        except Exception as e:
            conn.close()
            return False, f" 오류 발생: {str(e)}"
    
    def get_all_meetings(self) -> list:
        """모든 미팅 기록 조회 (관리자만 가능)"""
        if not self.is_admin():
            return []
        
        conn = self._get_connection()
        meetings = conn.execute(
            """
            SELECT m.*, t.name as member_name 
            FROM meetings m
            JOIN team_members t ON m.member_id = t.id
            ORDER BY m.meeting_date DESC
            """
        ).fetchall()
        conn.close()
        return [dict(m) for m in meetings]