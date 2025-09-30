import json
import os
from datetime import datetime
from utils.settings import settings

class TemplateService:
    def __init__(self):
        # data 디렉토리 기본 경로 설정
        data_dir = getattr(settings, 'DATA_DIR', 'data')
        self.templates_file = os.path.join(data_dir, 'mail_templates.json')
        self._ensure_templates_file()
    
    def _ensure_templates_file(self):
        """템플릿 파일이 존재하지 않으면 생성"""
        if not os.path.exists(self.templates_file):
            os.makedirs(os.path.dirname(self.templates_file), exist_ok=True)
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump({}, f, ensure_ascii=False, indent=4)
    
    def get_all_templates(self):
        """모든 템플릿 조회"""
        try:
            with open(self.templates_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def save_template(self, subject, body):
        """새 템플릿 저장"""
        templates = self.get_all_templates()
        
        # 템플릿 이름 생성 (제목 + 현재 시간)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        template_name = f"{subject}_{timestamp}"
        
        # 중복 이름 방지
        counter = 1
        original_name = template_name
        while template_name in templates:
            template_name = f"{original_name}_{counter}"
            counter += 1
        
        # 템플릿 저장
        templates[template_name] = {
            'subject': subject,
            'body': body,
            'created_at': datetime.now().isoformat(),
            'last_used': None
        }
        
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=4)
        
        return template_name
    
    def get_template(self, template_name):
        """특정 템플릿 조회"""
        templates = self.get_all_templates()
        return templates.get(template_name)
    
    def update_last_used(self, template_name):
        """템플릿 최근 사용 시간 업데이트"""
        templates = self.get_all_templates()
        
        if template_name in templates:
            templates[template_name]['last_used'] = datetime.now().isoformat()
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=4)
    
    def delete_template(self, template_name):
        """템플릿 삭제"""
        templates = self.get_all_templates()
        
        if template_name in templates:
            del templates[template_name]
            
            with open(self.templates_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=4)
            
            return True
        return False
    
    def get_recent_templates(self, limit=5):
        """최근 사용한 템플릿 조회"""
        templates = self.get_all_templates()
        
        # 최근 사용 시간으로 정렬
        sorted_templates = sorted(
            templates.items(),
            key=lambda x: x[1].get('last_used', '1900-01-01'),
            reverse=True
        )
        
        return dict(sorted_templates[:limit])