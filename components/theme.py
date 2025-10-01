import json
import streamlit as st
from pathlib import Path

def save_custom_theme(theme):
    """커스텀 테마를 파일로 저장"""
    user_id = st.session_state.get("user", {}).get("user_id", "default")
    theme_dir = Path("data/themes")
    theme_dir.mkdir(parents=True, exist_ok=True)
    
    theme_file = theme_dir / f"{user_id}_theme.json"
    
    with open(theme_file, 'w', encoding='utf-8') as f:
        json.dump(theme, f, ensure_ascii=False, indent=2)

def load_custom_theme():
    """저장된 테마 불러오기"""
    user_id = st.session_state.get("user", {}).get("user_id", "default")
    theme_file = Path("data/themes") / f"{user_id}_theme.json"
    
    if theme_file.exists():
        with open(theme_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def apply_custom_theme():
    """커스텀 테마가 있으면 적용"""
    if 'custom_theme' not in st.session_state:
        loaded_theme = load_custom_theme()
        if loaded_theme:
            st.session_state.custom_theme = loaded_theme
    
    if 'custom_theme' in st.session_state:
        theme = st.session_state.custom_theme
        custom_css = f"""
        <style>
        /* CSS 변수 */
        :root {{
            --gray-900: {theme['text_color']} !important;
            --gray-500: {theme['text_color_light']} !important;
            --gold: {theme['main_color']} !important;
            --gold-600: {theme['main_color_dark']} !important;
            --bg-cream: {theme['bg_color1']} !important;
            --bg-pink: {theme['bg_color2']} !important;
        }}
        
        /* 전체 앱 배경 */
        .stApp {{
            background: linear-gradient(135deg, {theme['bg_color1']} 0%, {theme['bg_color2']} 100%) !important;
        }}
        
        /* 탭 스타일 */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 8px;
        }}
        
        .stTabs [data-baseweb="tab"] {{
            background-color: transparent;
            border-radius: 8px 8px 0 0;
            color: {theme['text_color_light']};
            padding: 10px 20px;
        }}
        
        .stTabs [aria-selected="true"] {{
            background-color: {theme['main_color']} !important;
            color: {theme['text_color']} !important;
            font-weight: 600;
        }}
        
        /* 버튼 스타일 */
        .stButton > button {{
            background-color: {theme['main_color']} !important;
            color: {theme['text_color']} !important;
            border: none !important;
        }}
        
        .stButton > button:hover {{
            background-color: {theme['main_color_dark']} !important;
        }}
        
        /* Primary 버튼 */
        .stButton > button[kind="primary"] {{
            background-color: {theme['main_color_dark']} !important;
        }}
        
        /* 데이터프레임 헤더 */
        .stDataFrame thead tr th {{
            background-color: {theme['main_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* 입력 필드 포커스 */
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > div:focus {{
            border-color: {theme['main_color']} !important;
        }}
        
        /* 사이드바 */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(135deg, {theme['bg_color1']} 0%, {theme['bg_color2']} 100%) !important;
        }}
        
        /* Expander */
        .streamlit-expanderHeader {{
            background-color: {theme['main_color']} !important;
            color: {theme['text_color']} !important;
        }}
        
        /* 메트릭 */
        [data-testid="stMetricValue"] {{
            color: {theme['main_color_dark']} !important;
        }}
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

def load_last_user_theme():
    """마지막 로그인 사용자의 테마 불러오기 (로그인 화면용)"""
    theme_dir = Path("data/themes")
    
    if not theme_dir.exists():
        return None
    
    # 가장 최근에 수정된 테마 파일 찾기
    theme_files = list(theme_dir.glob("*_theme.json"))
    
    if theme_files:
        # 수정 시간 기준 최신 파일
        latest_theme = max(theme_files, key=lambda f: f.stat().st_mtime)
        
        with open(latest_theme, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return None

def apply_theme_to_login():
    """로그인 화면에 테마 적용"""
    theme = load_last_user_theme()
    
    if theme:
        custom_css = f"""
        <style>
        :root {{
            --gray-900: {theme['text_color']} !important;
            --gray-500: {theme['text_color_light']} !important;
            --gold: {theme['main_color']} !important;
            --gold-600: {theme['main_color_dark']} !important;
            --bg-cream: {theme['bg_color1']} !important;
            --bg-pink: {theme['bg_color2']} !important;
        }}
        
        .stApp {{
            background: linear-gradient(135deg, {theme['bg_color1']} 0%, {theme['bg_color2']} 100%) !important;
        }}
        </style>
        """
        st.markdown(custom_css, unsafe_allow_html=True)

def delete_custom_theme():
    """저장된 테마 파일 삭제"""
    user_id = st.session_state.get("user", {}).get("user_id", "default")
    theme_file = Path("data/themes") / f"{user_id}_theme.json"
    
    try:
        if theme_file.exists():
            theme_file.unlink()  # 파일 삭제
        return True
    except Exception as e:
        print(f"테마 파일 삭제 오류: {e}")
        return False