import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, date, timedelta
import calendar

# === [중요] 발급받은 실제 API 키를 아래 따옴표 안에 넣어주세요! ===
MY_GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
# ==============================================================

st.set_page_config(page_title="KSU_IDEATHON_3TEAM", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    /* 기본 배경 및 폰트 */
    .stApp { background-color: #F0F2F6; overflow-x: hidden; }
    p, h1, h2, h3, h4, h5, h6 { color: #111111 !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    a.header-anchor, .stMarkdown a, svg[title="Link to this heading"] { display: none !important; }
    
    /* 화면 너비 제한 */
    .block-container {
        background-color: #FFFFFF; color: #111111;
        width: 100% !important; max-width: 410px !important; 
        margin: 0 auto !important; padding: 1rem 0.5rem 0 0.5rem !important; 
    }
    
    /* ==============================================================
       🚨 [절대 규칙] 모든 컬럼(달력, 하단 탭)을 강제로 가로로 고정!
       ============================================================== */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important; /* 모바일에서도 무조건 가로 배치 */
        flex-wrap: nowrap !important;   /* 줄바꿈 절대 금지 */
        align-items: center !important;
        gap: 2px !important;            /* 간격 최소화 */
        width: 100% !important;
    }
    
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {
        width: 100% !important;
        min-width: 0 !important;        /* 좁은 화면에서 강제로 줄어들게 허용 */
        flex: 1 1 0px !important;       /* 모든 칸을 동일한 비율로 쪼개기 */
        padding: 0 !important;          /* 내부 여백 제거 */
    }

    /* 기본 버튼 디자인 */
    .stButton > button { 
        width: 100% !important; 
        border-radius: 10px !important; 
        padding: 0 !important; 
    }

    /* 달력 동그라미 버튼 강제 고정 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button {
        aspect-ratio: 1 / 1 !important; /* 무조건 1:1 정사각형 */
        height: auto !important; 
        border-radius: 50% !important;
        background-color: #F0F5FA !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button p { 
        font-size: 13px !important; margin: 0 !important; 
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button[kind="primary"] { 
        background-color: #D0E2F5 !important; border: 2px solid #0A84FF !important; 
    }

    /* 상단 < > 화살표 버튼 */
    .stButton > button:has(p:contains("＜")), .stButton > button:has(p:contains("＞")) { 
        background-color: transparent !important; border: none !important; height: 35px !important; 
    }

    /* 하단 네비게이션 탭바 4개 강제 고정 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)) .stButton > button {
        background-color: #FFFFFF !important; border-radius: 0 !important; height: 60px !important; 
        border-top: 1px solid #EEEEEE !important; border-bottom: none !important; border-left: none !important; border-right: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)) .stButton > button p {
        font-size: 26px !important; margin: 0 !important;
    }
    
    .light-card { background-color: #F9F9FB; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #EFEFEF; }
    .app-title { text-align: center; margin-top: 40px; margin-bottom: 40px; color: #111; font-size: 24px !important; font-weight: 900; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 상태 관리 (Session State) 및 초기 데이터
# ==========================================
TODAY_DATE = date(2026, 5, 16)
TODAY_STR = TODAY_DATE.strftime("%Y-%m-%d")

if 'users_db' not in st.session_state: st.session_state.users_db = {'test': '1234'}
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = ""
if 'page' not in st.session_state: st.session_state.page = 'home'

if 'cal_year' not in st.session_state: st.session_state.cal_year = TODAY_DATE.year
if 'cal_month' not in st.session_state: st.session_state.cal_month = TODAY_DATE.month
if 'selected_date' not in st.session_state: st.session_state.selected_date = TODAY_STR

if 'diary_data' not in st.session_state: 
    st.session_state.diary_data = {
        "2026-05-11": {"risk_level": "1단계 에너지 저하", "reason": "피로감이 보입니다. 푹 쉬세요.", "action1": "일찍 잠자리에 들기", "action2": "따뜻한 물 한잔 마시기", "action3": "스트레칭하기", "diary_text": "오늘은 조금 피곤했다."},
        "2026-05-12": {"risk_level": "2단계 부정 사고 증가", "reason": "스트레스가 늘고 있습니다.", "action1": "좋아하는 음악 듣기", "action2": "10분 명상", "action3": "친구에게 연락해보기", "diary_text": "회사에서 스트레스를 받았다."}
    }

def go_to(page_name): st.session_state.page = page_name

def change_month(delta):
    month = st.session_state.cal_month + delta
    year = st.session_state.cal_year
    if month > 12: month = 1; year += 1
    elif month < 1: month = 12; year -= 1
    st.session_state.cal_year = year; st.session_state.cal_month = month
    st.session_state.selected_date = f"{year}-{month:02d}-01"

# ==========================================
# 3. Gemini API 분석 함수
# ==========================================
def analyze_diary(diary_text):
    try:
        genai.configure(api_key=MY_GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""당신은 공감 능력이 뛰어난 심리 상담 AI입니다. 일기를 분석해 1단계/2단계/3단계/4단계 중 하나를 선택하고 조언과 추천행동 3가지를 주세요.
        반드시 JSON 형식으로 응답: {{"risk_level": "결과 단계", "reason": "이유", "action1": "행동1", "action2": "행동2", "action3": "행동3"}}
        [사용자 일기] {diary_text}"""
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```"): response_text = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(response_text)
    except Exception as e: return {"error": str(e)}

# ==========================================
# 4. 화면 뷰 함수들
# ==========================================
def view_home():
    cy, cm = st.session_state.cal_year, st.session_state.cal_month
    
    # 1. 상단 연/월 이동
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1:
        if st.button("＜", key="prev_btn"): change_month(-1); st.rerun()
    h_col2.markdown(f"<h3 style='margin:0; text-align:center; line-height:35px;'>{cy}년 {cm}월</h3>", unsafe_allow_html=True)
    with h_col3:
        if st.button("＞", key="next_btn"): change_month(1); st.rerun()
    
    st.write("") 
    cal = calendar.Calendar(firstweekday=6) 
    month_days = cal.monthdayscalendar(cy, cm)
    
    # 2. 요일 헤더 (강제 7등분 가로)
    days_header = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)
    for i, d in enumerate(days_header):
        color = "#FF3B30" if d == "일" else "#8E8E93"
        cols[i].markdown(f"<div style='text-align:center; color:{color}; font-size:13px; font-weight:bold; margin-bottom:5px;'>{d}</div>", unsafe_allow_html=True)
    
    # 3. 달력 날짜 (강제 7등분 가로)
    for week in month_days:
        cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0:
                cols[i].write("") 
            else:
                date_key = f"{cy}-{cm:02d}-{day:02d}"
                is_selected = (date_key == st.session_state.selected_date)
                btn_label = str(day)
                if date_key in st.session_state.diary_data:
                    lvl = st.session_state.diary_data[date_key].get('risk_level', '')
                    if '1단계' in lvl: btn_label += "🟢"
                    elif '2단계' in lvl: btn_label += "🟡"
                    elif '3단계' in lvl: btn_label += "🟠"
                    elif '4단계' in lvl: btn_label += "🔴"
                btn_type = "primary" if is_selected else "secondary"
                if cols[i].button(btn_label, key=f"cal_{date_key}", type=btn_type):
                    st.session_state.selected_date = date_key; st.rerun()
                    
    st.write("---")
    
    # 4. 하단 분석 결과 요약
    sel_data = st.session_state.diary_data.get(st.session_state.selected_date)
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    weekday_str = days_header[calendar.weekday(y, m, d) % 7]
    display_title = f"{m}월 {d}일({weekday_str})"
    
    if sel_data:
        level = sel_data.get('risk_level', ''); text = sel_data.get('diary_text', '')
        st.markdown(f"""
        <div class="light-card">
            <h4 style="margin:0; font-size:16px;">{display_title}</h4>
            <p style="color:#666666; margin-top:10px; margin-bottom:5px; font-size:14px;">감정 상태</p>
            <p style="color:#0A84FF; font-weight:bold; margin-top:0; font-size:16px;">{level}</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""<div class="light-card" style="text-align: center;"><h4 style="margin:0;">{display_title}</h4><p style="color:#666; font-size:14px;">기록이 없습니다.</p></div>""", unsafe_allow_html=True)

    if st.button("➕ 일기 작성", type="primary"): go_to('write'); st.rerun()

def view_write():
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    st.markdown(f"<h3 style='margin-top:0;'>✍️ {m}월 {d}일 일기</h3>", unsafe_allow_html=True)
    saved_text = st.session_state.diary_data.get(st.session_state.selected_date, {}).get('diary_text', '')
    diary_input = st.text_area("이 날의 감정을 기록해주세요", value=saved_text, height=200)
    
    # 가로 2칸
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소"): go_to('home'); st.rerun()
    with col2:
        if st.button("분석하기", type="primary"):
            if len(diary_input) < 5: st.error("일기를 더 적어주세요.")
            else:
                with st.spinner("AI 분석 중..."):
                    result = analyze_diary(diary_input)
                    if "error" not in result:
                        result['diary_text'] = diary_input
                        st.session_state.diary_data[st.session_state.selected_date] = result
                        go_to('report'); st.rerun()

def view_report():
    st.markdown("<h3>감정 분석 리포트</h3>", unsafe_allow_html=True)
    sel_data = st.session_state.diary_data.get(st.session_state.selected_date)
    
    if sel_data:
        level = sel_data.get('risk_level', '분석 불가'); reason = sel_data.get('reason', '')
        st.markdown(f"<div class='light-card'><h2 style='color:#0A84FF;'>{level}</h2><p>{reason}</p></div>", unsafe_allow_html=True)
    else: st.info("기록이 없습니다.")

def view_character():
    st.markdown("<h3 style='text-align:center;'>🎨 캐릭터</h3>", unsafe_allow_html=True)

def view_profile():
    st.markdown("<h3 style='text-align:center;'>👤 프로필</h3>", unsafe_allow_html=True)
    if st.button("🚪 로그아웃"): st.session_state.logged_in = False; st.rerun()

def view_login_signup():
    st.markdown("<div class='app-title'>KSU_IDEATHON_3TEAM</div>", unsafe_allow_html=True)
    login_id = st.text_input("아이디 (test)", key="login_id")
    login_pw = st.text_input("비밀번호 (1234)", type="password", key="login_pw")
    if st.button("로그인", type="primary"):
        if login_id == 'test' and login_pw == '1234':
            st.session_state.logged_in = True; st.session_state.page = 'home'; st.rerun()

# ==========================================
# 5. 메인 레이아웃 적용
# ==========================================
main_content_area = st.container(border=False) 

with main_content_area:
    if not st.session_state.logged_in: view_login_signup()
    else:
        if st.session_state.page == 'home': view_home()
        elif st.session_state.page == 'write': view_write()
        elif st.session_state.page == 'report': view_report()
        elif st.session_state.page == 'character': view_character()
        elif st.session_state.page == 'profile': view_profile()

if st.session_state.logged_in:
    # 🚨 모바일에서 하단 메뉴 4개가 무조건 가로로 나오도록 강제 적용!
    st.markdown("---", unsafe_allow_html=True)
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4) 
    with nav_col1:
        if st.button("🏠", key="n1"): go_to('home'); st.rerun()
    with nav_col2:
        if st.button("📊", key="n2"): go_to('report'); st.rerun()
    with nav_col3:
        if st.button("🧸", key="n3"): go_to('character'); st.rerun()
    with nav_col4:
        if st.button("👤", key="n4"): go_to('profile'); st.rerun()
