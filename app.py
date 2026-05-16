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
    /* 1. 기본 배경 및 스크롤 숨기기 */
    .stApp { background-color: #F0F2F6; overflow-x: hidden; }
    p, h1, h2, h3, h4, h5, h6 { color: #111111 !important; }
    header {visibility: hidden;} footer {visibility: hidden;}
    a.header-anchor, .stMarkdown a, svg[title="Link to this heading"] { display: none !important; }
    
    /* 2. PC 환경 (스마트폰처럼 예쁜 프레임, 그림자 효과 복구!) */
    .block-container {
        background-color: #FFFFFF;
        max-width: 410px !important; 
        margin: 20px auto !important; 
        border-radius: 40px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.1); 
        padding: 1.5rem 1rem 0 1rem !important; 
        border: 8px solid #E0E0E0; 
    }

    /* 3. 모바일(아이폰 SE) 환경: 좌우 스크롤의 원인인 여백을 완전히 제거! */
    @media (max-width: 450px) {
        .block-container {
            max-width: 100% !important;
            margin: 0 !important;
            border: none !important;
            border-radius: 0 !important;
            box-shadow: none !important;
            padding: 1rem 0.2rem 0 0.2rem !important; /* 좌우 여백을 거의 0으로 만듦 */
        }
    }

    /* 4. [핵심] 모든 가로 배치(달력, 버튼)가 모바일에서 무너지지 않도록 강제 고정 */
    div[data-testid="stHorizontalBlock"] {
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
        width: 100% !important;
    }

    /* 5. 달력(7칸)과 하단탭(4칸)은 화면 폭에 맞춰 1:1 비율로 정밀하게 쪼개기 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) div[data-testid="column"],
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)) div[data-testid="column"] {
        flex: 1 1 0px !important; 
        width: auto !important;
        min-width: 0 !important;
        padding: 0 !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) { gap: 2px !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)) { gap: 0px !important; }

    /* 6. 공통 예쁜 디자인 (카드 테두리, 일반 버튼) 복구 */
    .light-card { background-color: #F9F9FB; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #EFEFEF; }
    .app-title { text-align: center; margin-top: 40px; margin-bottom: 40px; color: #111; font-size: 24px !important; font-weight: 900; }
    
    .stButton > button { border-radius: 12px !important; height: 50px !important; width: 100% !important; font-size: 16px !important; }
    .stButton > button[kind="primary"] { background-color: #0A84FF !important; color: #FFFFFF !important; border: none !important; }
    .stButton > button[kind="secondary"] { background-color: #E2E6EA !important; color: #111111 !important; border: none !important; }

    /* 7. 달력 동그라미 버튼 (아이폰 SE에서도 안 찌그러지게 글씨 크기 조절) */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button {
        height: auto !important;
        aspect-ratio: 1 / 1 !important; /* 완벽한 정사각형 유지 */
        border-radius: 50% !important;
        background-color: #F0F5FA !important;
        padding: 0 !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button p { 
        font-size: 11px !important; /* 아이폰 SE를 위한 글꼴 축소 */
        letter-spacing: -0.5px !important; 
        margin: 0 !important; 
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button[kind="primary"] { 
        background-color: #D0E2F5 !important; border: 2px solid #0A84FF !important; 
    }

    /* 8. 하단 네비게이션 탭바 디자인 복구 */
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)) .stButton > button {
        background-color: #FFFFFF !important; border-radius: 0 !important; height: 65px !important; 
        border-top: 1px solid #EEEEEE !important; border-bottom: none !important; border-left: none !important; border-right: none !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(4)) .stButton > button p {
        font-size: 26px !important; margin: 0 !important;
    }

    /* 상단 < > 화살표 버튼 투명화 */
    .stButton > button:has(p:contains("＜")), .stButton > button:has(p:contains("＞")) { 
        background-color: transparent !important; border: none !important; height: 35px !important; 
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 상태 관리 및 초기 더미 데이터 (삭제했던 부분 모두 복구)
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
        "2026-05-12": {"risk_level": "2단계 부정 사고 증가", "reason": "스트레스가 늘고 있습니다.", "action1": "좋아하는 음악 듣기", "action2": "10분 명상", "action3": "친구에게 연락해보기", "diary_text": "회사에서 스트레스를 받았다."},
        "2026-05-13": {"risk_level": "3단계 정서적 침체 심화", "reason": "우울감이 깊어지고 있습니다. 주의가 필요합니다.", "action1": "가벼운 산책 나가기", "action2": "맛있는 음식 먹기", "action3": "감정 일기 쓰기", "diary_text": "아무것도 하기 싫고 무기력하다."},
        "2026-05-14": {"risk_level": "2단계 부정 사고 증가", "reason": "어제보다 나아졌지만 여전히 조심해야 합니다.", "action1": "햇볕 쬐기", "action2": "코미디 영화 보기", "action3": "단것 조금 먹기", "diary_text": "조금 나아졌지만 여전히 우울하다."},
        "2026-05-15": {"risk_level": "1단계 에너지 저하", "reason": "에너지가 회복되고 있습니다. 잘하고 계십니다!", "action1": "나에게 칭찬해주기", "action2": "취미 생활 즐기기", "action3": "독서하기", "diary_text": "오랜만에 친구를 만나서 좋았다."}
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
# AI 분석 함수
# ==========================================
def analyze_diary(diary_text):
    try:
        genai.configure(api_key=MY_GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        prompt = f"""당신은 공감 능력이 뛰어난 심리 상담 AI입니다. 사용자의 일기를 분석하여 다음 4가지 '단계별 위험도' 중 하나를 선택하고, 그에 맞는 맞춤형 조언과 추천 행동 3가지를 제안해주세요.
        [위험도 기준] 1단계 에너지 저하 / 2단계 부정 사고 증가 / 3단계 정서적 침체 심화 / 4단계 고위험 상태 감지
        반드시 JSON 형식으로만 응답해주세요.
        형식: {{"risk_level": "결과 단계", "reason": "이유 (3문장 이내)", "action1": "추천행동1", "action2": "추천행동2", "action3": "추천행동3"}}
        [사용자 일기] {diary_text}"""
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```"): response_text = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(response_text)
    except Exception as e: return {"error": str(e)}

# ==========================================
# 화면 뷰 함수들 (예쁜 UI, 리포트 차트 모두 복구)
# ==========================================
def view_home():
    cy, cm = st.session_state.cal_year, st.session_state.cal_month
    h_col1, h_col2, h_col3 = st.columns([1, 4, 1])
    with h_col1:
        if st.button("＜", key="prev_btn"): change_month(-1); st.rerun()
    h_col2.markdown(f"<h3 style='margin:0; text-align:center; line-height:35px;'>{cy}년 {cm}월</h3>", unsafe_allow_html=True)
    with h_col3:
        if st.button("＞", key="next_btn"): change_month(1); st.rerun()
    
    st.write("") 
    cal = calendar.Calendar(firstweekday=6) 
    month_days = cal.monthdayscalendar(cy, cm)
    
    days_header = ["일", "월", "화", "수", "목", "금", "토"]
    cols = st.columns(7)
    for i, d in enumerate(days_header):
        color = "#FF3B30" if d == "일" else "#8E8E93"
        cols[i].markdown(f"<div style='text-align:center; color:{color}; font-size:12px; font-weight:bold; margin-bottom:5px;'>{d}</div>", unsafe_allow_html=True)
    
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
    sel_data = st.session_state.diary_data.get(st.session_state.selected_date)
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    weekday_str = days_header[calendar.weekday(y, m, d) % 7]
    display_title = f"{m}월 {d}일({weekday_str})"
    
    if sel_data:
        level = sel_data.get('risk_level', ''); text = sel_data.get('diary_text', '')
        if "1단계" in level: badge_color, badge_text = "#34C759", "안정 단계"
        elif "2단계" in level: badge_color, badge_text = "#FFCC00", "주의 단계"
        elif "3단계" in level: badge_color, badge_text = "#FF9500", "경고 단계"
        elif "4단계" in level: badge_color, badge_text = "#FF3B30", "위험 단계"
        else: badge_color, badge_text = "#8E8E93", "분석 완료"

        st.markdown(f"""
        <div class="light-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin:0; font-size:16px;">{display_title}</h4>
                <span style="color: {badge_color}; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid {badge_color};">{badge_text}</span>
            </div>
            <p style="color:#666666; margin-top:15px; margin-bottom:5px; font-size:13px;">감정 상태</p>
            <p style="color:{badge_color}; font-weight:bold; margin-top:0;">{level}</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📝 작성한 일기 전문 보기"): st.write(text)
    else:
        st.markdown(f"""<div class="light-card" style="text-align: center;"><h4 style="margin:0; margin-bottom:10px;">{display_title}</h4><p style="color:#666666; font-size:14px;">이 날의 기록이 없습니다.</p></div>""", unsafe_allow_html=True)

    if st.button("➕ 일기 작성 / 수정", type="primary"): go_to('write'); st.rerun()

def view_write():
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    st.markdown(f"<h3 style='margin-top:0;'>✍️ {m}월 {d}일 일기</h3>", unsafe_allow_html=True)
    saved_text = st.session_state.diary_data.get(st.session_state.selected_date, {}).get('diary_text', '')
    diary_input = st.text_area("이 날의 감정을 기록해주세요", value=saved_text, height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소"): go_to('home'); st.rerun()
    with col2:
        if st.button("분석하기", type="primary"):
            if len(diary_input) < 5: st.error("일기를 조금 더 작성해주세요.")
            else:
                with st.spinner("AI 분석 중..."):
                    result = analyze_diary(diary_input)
                    if "error" not in result:
                        result['diary_text'] = diary_input
                        st.session_state.diary_data[st.session_state.selected_date] = result
                        go_to('report'); st.rerun()
                    else: st.error("오류가 발생했습니다.")

def view_report():
    st.markdown("<h3 style='margin-top:0;'>감정 분석 리포트</h3>", unsafe_allow_html=True)
    sel_data = st.session_state.diary_data.get(st.session_state.selected_date)
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    
    if sel_data:
        level = sel_data.get('risk_level', '분석 불가'); reason = sel_data.get('reason', '')
        act1 = sel_data.get('action1', '휴식하기'); act2 = sel_data.get('action2', '심호흡하기'); act3 = sel_data.get('action3', '물 마시기')
        
        st.info(f"조회 기준: {m}월 {d}일")
        st.markdown(f"<div class='light-card'><p style='color:#666; margin:0; font-size:14px;'>우울증 단계 결과</p><h2 style='color:#0A84FF; margin-top:5px; font-size:22px;'>{level}</h2></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:20px; margin-bottom:5px; color:#111; font-weight:bold;'>📊 감정 변화 추이</div>", unsafe_allow_html=True)
        
        start_date = date(y, m, d) - timedelta(days=6)
        chart_data = []
        for i in range(7):
            cur_d = start_date + timedelta(days=i)
            ds = cur_d.strftime("%Y-%m-%d")
            val = None
            if ds in st.session_state.diary_data:
                lvl_str = st.session_state.diary_data[ds].get('risk_level', '')
                if '1단계' in lvl_str: val = 1
                elif '2단계' in lvl_str: val = 2
                elif '3단계' in lvl_str: val = 3
                elif '4단계' in lvl_str: val = 4
            if val is not None: chart_data.append({"날짜": cur_d.strftime("%m/%d"), "위험도": val})
                
        if len(chart_data) > 0:
            chart = alt.Chart(pd.DataFrame(chart_data)).mark_line(point=True, color="#0A84FF").encode(
                x=alt.X('날짜:N', sort=None, axis=alt.Axis(labelAngle=-45, title=None)),
                y=alt.Y('위험도:Q', scale=alt.Scale(domain=[1, 4]), axis=alt.Axis(tickCount=3, title="위험도(단계)"))
            ).properties(height=200)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.markdown("<div class='light-card' style='text-align:center;'><p style='color:#8E8E93; font-size:14px; margin:0;'>해당 기간의 기록이 없습니다.</p></div>", unsafe_allow_html=True)
            
        st.markdown(f"""
        <div class='light-card' style='margin-top:10px;'>
            <p style='color:#666; margin:0; font-size:14px;'>AI 심리 분석 결과</p>
            <p style='font-size:14px; margin-top:10px;'>{reason}</p>
            <hr style='border-color:#EEE;'>
            <p style='color:#666; margin:0; font-size:14px;'>AI 맞춤 추천 활동</p>
            <ul style='font-size:14px; margin-top:10px; color:#333; line-height: 1.6;'>
                <li>{act1}</li><li>{act2}</li><li>{act3}</li>
            </ul>
        </div>""", unsafe_allow_html=True)
        if "3단계" in level or "4단계" in level:
            st.error("🚨 위험 상태가 감지되었습니다. 109(자살예방상담전화)로 즉시 연락 바랍니다.")
    else: st.info("기록이 없습니다. 홈 화면에서 먼저 작성해주세요.")

def view_character():
    st.markdown("""<div style="text-align:center; margin-top: 50px;"><h1 style="font-size: 80px; margin:0;">🎨</h1><h3 style="color:#111;">캐릭터 꾸미기</h3><p style="color:#666; font-size:14px; margin-top:20px;">자신만의 캐릭터를 개성있게 꾸며보세요!</p></div>""", unsafe_allow_html=True)

def view_profile():
    st.markdown("<h3 style='text-align:center; margin-top:0;'>나의 정보</h3>", unsafe_allow_html=True)
    st.markdown(f"""<div style='text-align:center; margin: 30px 0;'><div style='font-size: 60px; background-color:#E0E0E0; width:90px; height:90px; border-radius:50%; margin:0 auto; line-height:90px;'>👩🏻</div><h3 style='margin-top:15px; margin-bottom:5px;'>{st.session_state.current_user}님</h3><span style='background-color:#F0F2F6; padding:5px 15px; border-radius:20px; font-size:14px; color:#111; border:1px solid #E0E0E0;'>⭐ 마음 온도 36.5℃</span></div>""", unsafe_allow_html=True)
    for m in ["알림 설정 〉", "계정 관리 〉", "고객 센터 〉"]: 
        st.markdown(f"<div style='padding: 15px 0; border-bottom: 1px solid #EEE; color: #333;'>{m}</div>", unsafe_allow_html=True)
    st.write("")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False; st.session_state.current_user = ""; st.rerun()

def view_login_signup():
    st.markdown("<div class='app-title'>KSU_IDEATHON_3TEAM</div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    with tab1:
        login_id = st.text_input("아이디", key="login_id", placeholder="아이디를 입력하세요")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw", placeholder="비밀번호를 입력하세요")
        st.write("")
        if st.button("로그인", type="primary"):
            if login_id in st.session_state.users_db and st.session_state.users_db[login_id] == login_pw:
                st.session_state.logged_in = True; st.session_state.current_user = login_id; st.session_state.page = 'home'; st.rerun()
            else: st.error("정보가 일치하지 않습니다.")
        st.info("💡 테스트용 계정: 아이디 `test` / 비번 `1234`")
    with tab2:
        new_id = st.text_input("새 아이디", key="new_id")
        new_pw = st.text_input("새 비밀번호", type="password", key="new_pw")
        if st.button("가입하기", type="primary"):
            st.session_state.users_db[new_id] = new_pw; st.success("가입 완료! 로그인 탭으로 이동하세요.")

# ==========================================
# 메인 레이아웃 적용
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
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4) 
    with nav_col1:
        if st.button("🏠", key="n1"): go_to('home'); st.rerun()
    with nav_col2:
        if st.button("📊", key="n2"): go_to('report'); st.rerun()
    with nav_col3:
        if st.button("🧸", key="n3"): go_to('character'); st.rerun()
    with nav_col4:
        if st.button("👤", key="n4"): go_to('profile'); st.rerun()
