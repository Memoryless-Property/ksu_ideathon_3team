import streamlit as st
import google.generativeai as genai
import json
import pandas as pd
import numpy as np
import altair as alt
from datetime import datetime, date, timedelta
import calendar

# Streamlit의 비밀금고에서 꺼내오겠다는 뜻
MY_GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
# ==============================================================

st.set_page_config(page_title="KSU_IDEATHON_3TEAM", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #F0F2F6; }
    .block-container {
        background-color: #FFFFFF; color: #111111;
        max-width: 410px !important; margin: 20px auto; border-radius: 40px;
        box-shadow: 0px 10px 30px rgba(0,0,0,0.1); padding: 1.5rem 1.5rem 0 1.5rem !important; 
        border: 8px solid #E0E0E0; overflow: hidden; 
    }
    header {visibility: hidden;} footer {visibility: hidden;}
    p, h1, h2, h3, h4, h5, h6 { color: #111111 !important; }
    
    a.header-anchor, .stMarkdown a, svg[title="Link to this heading"] { display: none !important; visibility: hidden !important; pointer-events: none !important; }
    div[data-testid="stVerticalBlockBorderWrapper"] > div::-webkit-scrollbar { display: none; }
    div[data-testid="stVerticalBlockBorderWrapper"] > div { -ms-overflow-style: none; scrollbar-width: none; }
    
    .light-card { background-color: #F9F9FB; padding: 20px; border-radius: 15px; margin-bottom: 15px; border: 1px solid #EFEFEF; }
    .app-title { text-align: center; margin-top: 40px; margin-bottom: 40px; color: #111; font-size: 24px !important; font-weight: 900; white-space: nowrap; letter-spacing: -0.5px; }

    .stButton > button { border-radius: 12px !important; height: 50px !important; width: 100% !important; font-size: 16px !important; padding: 0 20px !important; }
    .stButton > button[kind="primary"] { background-color: #0A84FF !important; color: #FFFFFF !important; border: none !important; }
    .stButton > button[kind="primary"] p { color: #FFFFFF !important; margin: 0 !important; }
    .stButton > button[kind="secondary"] { background-color: #E2E6EA !important; color: #111111 !important; border: none !important; }
    .stButton > button[kind="secondary"] p { color: #111111 !important; margin: 0 !important; }

    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) { gap: 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) div[data-testid="column"] { padding: 0 1px !important; min-width: 0 !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button {
        background-color: #F0F5FA !important; border-radius: 50% !important; width: 38px !important; height: 38px !important; min-height: 38px !important;
        padding: 0 !important; margin: 0 auto !important; display: flex !important; align-items: center !important; justify-content: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button p { color: #111111 !important; font-size: 13px !important; white-space: nowrap !important; }
    div[data-testid="stHorizontalBlock"]:has(> div:nth-child(7)) .stButton > button[kind="primary"] { background-color: #D0E2F5 !important; border: 2px solid #0A84FF !important; }

    .stButton > button:has(p:contains("＜")), .stButton > button:has(p:contains("＞")) { background-color: transparent !important; border: none !important; height: 35px !important; }

    .stButton > button:has(p:contains("🏠")), .stButton > button:has(p:contains("📊")), .stButton > button:has(p:contains("🧸")), .stButton > button:has(p:contains("👤")) {
        background-color: #FFFFFF !important; border-radius: 0 !important; height: 80px !important; border-top: 1px solid #EEEEEE !important; margin-bottom: -15px !important;
    }
    .stButton > button:has(p:contains("🏠")) p, .stButton > button:has(p:contains("📊")) p, .stButton > button:has(p:contains("🧸")) p, .stButton > button:has(p:contains("👤")) p {
        font-size: 32px !important; color: #111111 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 상태 관리 (Session State) 및 초기 더미 데이터
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

# [포인트 2] 발표 및 심사용: 초기 차트를 예쁘게 보여주기 위한 과거 더미 데이터 세팅
if 'diary_data' not in st.session_state: 
    st.session_state.diary_data = {
        "2026-05-11": {"risk_level": "1단계 에너지 저하", "reason": "피로감이 보입니다. 푹 쉬세요.", "action1": "일찍 잠자리에 들기", "action2": "따뜻한 물 한잔 마시기", "action3": "스트레칭하기", "diary_text": "오늘은 조금 피곤했다."},
        "2026-05-12": {"risk_level": "2단계 부정 사고 증가", "reason": "스트레스가 늘고 있습니다.", "action1": "좋아하는 음악 듣기", "action2": "10분 명상", "action3": "친구에게 연락해보기", "diary_text": "회사에서 스트레스를 받았다."},
        "2026-05-13": {"risk_level": "3단계 정서적 침체 심화", "reason": "우울감이 깊어지고 있습니다. 주의가 필요합니다.", "action1": "가벼운 산책 나가기", "action2": "맛있는 음식 먹기", "action3": "감정 일기 쓰기", "diary_text": "아무것도 하기 싫고 무기력하다."},
        "2026-05-14": {"risk_level": "2단계 부정 사고 증가", "reason": "어제보다 나아졌지만 여전히 조심해야 합니다.", "action1": "햇볕 쬐기", "action2": "코미디 영화 보기", "action3": "단것 조금 먹기", "diary_text": "조금 나아졌지만 여전히 우울하다."},
        "2026-05-15": {"risk_level": "1단계 에너지 저하", "reason": "에너지가 회복되고 있습니다. 잘하고 계십니다!", "action1": "나에게 칭찬해주기", "action2": "취미 생활 즐기기", "action3": "독서하기", "diary_text": "오랜만에 친구를 만나서 좋았다."}
    }

def go_to(page_name):
    st.session_state.page = page_name

def change_month(delta):
    month = st.session_state.cal_month + delta
    year = st.session_state.cal_year
    if month > 12: month = 1; year += 1
    elif month < 1: month = 12; year -= 1
    st.session_state.cal_year = year
    st.session_state.cal_month = month
    st.session_state.selected_date = f"{year}-{month:02d}-01"

# ==========================================
# 3. Gemini API 분석 함수 (맞춤형 추천 활동 추가)
# ==========================================
def analyze_diary(diary_text):
    try:
        genai.configure(api_key=MY_GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-2.5-flash')
        # [포인트 1] AI가 일기를 바탕으로 맞춤형 행동 3가지를 추천하도록 프롬프트 수정
        prompt = f"""당신은 공감 능력이 뛰어난 심리 상담 AI입니다. 사용자의 일기를 분석하여 다음 4가지 '단계별 위험도' 중 하나를 선택하고, 그에 맞는 맞춤형 조언과 당장 실천할 수 있는 추천 행동 3가지를 제안해주세요.
        [위험도 기준] 1단계 에너지 저하 / 2단계 부정 사고 증가 / 3단계 정서적 침체 심화 / 4단계 고위험 상태 감지
        반드시 JSON 형식으로만 응답해주세요.
        형식: {{"risk_level": "결과 단계", "reason": "이유와 조언 (3문장 이내)", "action1": "추천행동1", "action2": "추천행동2", "action3": "추천행동3"}}
        [사용자 일기] {diary_text}"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        # 마크다운 텍스트 파싱 오류 방지
        if response_text.startswith("```"): 
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(response_text)
    except Exception as e:
        return {"error": str(e)}

# ==========================================
# 4. 화면 뷰 함수들
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
        cols[i].markdown(f"<div style='text-align:center; color:{color}; font-size:14px; font-weight:bold; margin-bottom:10px;'>{d}</div>", unsafe_allow_html=True)
    
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
                    st.session_state.selected_date = date_key
                    st.rerun()
                    
    st.write("---")

    sel_data = st.session_state.diary_data.get(st.session_state.selected_date)
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    weekday_str = days_header[calendar.weekday(y, m, d) % 7]
    today_mark = " (오늘)" if st.session_state.selected_date == TODAY_STR else ""
    display_title = f"{m}월 {d}일({weekday_str}){today_mark}"
    
    if sel_data:
        level = sel_data.get('risk_level', '')
        text = sel_data.get('diary_text', '')
        
        if "1단계" in level: badge_color, badge_text = "#34C759", "안정 단계"
        elif "2단계" in level: badge_color, badge_text = "#FFCC00", "주의 단계"
        elif "3단계" in level: badge_color, badge_text = "#FF9500", "경고 단계"
        elif "4단계" in level: badge_color, badge_text = "#FF3B30", "위험 단계"
        else: badge_color, badge_text = "#8E8E93", "분석 완료"

        st.markdown(f"""
        <div class="light-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin:0;">{display_title}</h4>
                <span style="color: {badge_color}; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid {badge_color};">{badge_text}</span>
            </div>
            <p style="color:#666666; margin-top:15px; margin-bottom:5px;">감정 상태</p>
            <p style="color:{badge_color}; font-weight:bold; margin-top:0;">{level}</p>
        </div>
        """, unsafe_allow_html=True)
        with st.expander("📝 작성한 일기 전문 보기"): st.write(text)
    else:
        st.markdown(f"""<div class="light-card" style="text-align: center; padding: 20px 10px;"><h4 style="margin:0; margin-bottom:10px;">{display_title}</h4><p style="color:#666666; font-size:14px;">이 날의 기록이 없습니다.</p></div>""", unsafe_allow_html=True)

    btn_text = "➕ 오늘의 일기 작성" if st.session_state.selected_date == TODAY_STR else f"➕ {m}/{d} 일기 작성"
    if st.button(btn_text, type="primary", use_container_width=True):
        go_to('write')
        st.rerun()

def view_write():
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    st.markdown(f"<h3 style='margin-top:0;'>✍️ {m}월 {d}일 일기</h3>", unsafe_allow_html=True)
    
    saved_text = st.session_state.diary_data.get(st.session_state.selected_date, {}).get('diary_text', '')
    diary_input = st.text_area("이 날의 감정을 기록해주세요", value=saved_text, height=200)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("취소", use_container_width=True): go_to('home'); st.rerun()
    with col2:
        if st.button("분석하기", type="primary", use_container_width=True):
            if len(diary_input) < 5: st.error("일기를 조금 더 작성해주세요.")
            else:
                with st.spinner("AI 분석 중..."):
                    result = analyze_diary(diary_input)
                    if "error" not in result:
                        result['diary_text'] = diary_input
                        st.session_state.diary_data[st.session_state.selected_date] = result
                        go_to('report')
                        st.rerun()
                    else: st.error(f"오류가 발생했습니다: {result['error']}")

def view_report():
    st.markdown("<h3 style='margin-top:0;'>감정 분석 리포트</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color:#666; font-size:14px; margin-top:-10px;'>AI가 당신의 감정 흐름을 분석했습니다.</p>", unsafe_allow_html=True)
    
    sel_data = st.session_state.diary_data.get(st.session_state.selected_date)
    y, m, d = map(int, st.session_state.selected_date.split('-'))
    
    if sel_data:
        level = sel_data.get('risk_level', '분석 불가')
        reason = sel_data.get('reason', '')
        
        # [포인트 1 적용] AI가 넘겨준 맞춤형 추천 행동 불러오기
        act1 = sel_data.get('action1', '잠시 눈을 감고 휴식하기')
        act2 = sel_data.get('action2', '심호흡 3번 하기')
        act3 = sel_data.get('action3', '시원한 물 한잔 마시기')
        
        st.info(f"조회 기준: {m}월 {d}일")
        st.markdown(f"<div class='light-card'><p style='color:#666; margin:0;'>우울증 단계 결과</p><h2 style='color:#0A84FF; margin-top:5px;'>{level}</h2></div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-top:20px; margin-bottom:5px; color:#111; font-weight:bold;'>📊 감정 변화 추이</div>", unsafe_allow_html=True)
        
        period = st.selectbox("기간 선택", ["최근 7일", "최근 30일"], label_visibility="collapsed")
        days_sub = 6 if period == "최근 7일" else 29
        
        start_date = date(y, m, d) - timedelta(days=days_sub)
        chart_data = []
        
        for i in range(days_sub + 1):
            cur_d = start_date + timedelta(days=i)
            ds = cur_d.strftime("%Y-%m-%d")
            
            val = None
            if ds in st.session_state.diary_data:
                lvl_str = st.session_state.diary_data[ds].get('risk_level', '')
                if '1단계' in lvl_str: val = 1
                elif '2단계' in lvl_str: val = 2
                elif '3단계' in lvl_str: val = 3
                elif '4단계' in lvl_str: val = 4
            
            if val is not None:
                chart_data.append({"날짜": cur_d.strftime("%m/%d"), "위험도": val})
                
        if len(chart_data) > 0:
            chart = alt.Chart(pd.DataFrame(chart_data)).mark_line(point=True, color="#0A84FF").encode(
                x=alt.X('날짜:N', sort=None, axis=alt.Axis(labelAngle=-45, title=None)),
                y=alt.Y('위험도:Q', scale=alt.Scale(domain=[1, 4]), axis=alt.Axis(tickCount=3, title="위험도 (단계)"))
            ).properties(height=200)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.markdown("<div class='light-card' style='text-align:center;'><p style='color:#8E8E93; font-size:14px; margin:0;'>해당 기간에 작성된 일기가 없습니다.</p></div>", unsafe_allow_html=True)
            
        st.markdown(f"""
        <div class='light-card' style='margin-top:10px;'>
            <p style='color:#666; margin:0;'>AI 심리 분석 결과</p>
            <p style='font-size:14px; margin-top:10px;'>{reason}</p>
            <hr style='border-color:#EEE;'>
            <p style='color:#666; margin:0;'>AI 맞춤 추천 활동</p>
            <ul style='font-size:14px; margin-top:10px; color:#333; line-height: 1.6;'>
                <li>{act1}</li>
                <li>{act2}</li>
                <li>{act3}</li>
            </ul>
        </div>""", unsafe_allow_html=True)
        
        if "3단계" in level or "4단계" in level:
            if st.button("도움 기관 연결하기", type="primary", use_container_width=True): st.info("🚨 시연용 화면: 실제 앱에서는 109 전화 다이얼로 즉시 연결됩니다.")
    else: 
        st.info(f"선택하신 {m}월 {d}일의 기록이 없습니다.\n홈 화면에서 먼저 작성해주세요.")

def view_character():
    st.markdown("""<div style="text-align:center; margin-top: 50px;"><h1 style="font-size: 80px; margin:0;">🎨</h1><h3 style="color:#111;">캐릭터 꾸미기</h3><p style="color:#666; font-size:14px; margin-top:20px;">자신만의 캐릭터를 개성있게 꾸며보세요!<br><br><span style="color:#0A84FF;">* 현재 시안용 페이지입니다.</span></p></div>""", unsafe_allow_html=True)

def view_profile():
    st.markdown("<h3 style='text-align:center; margin-top:0;'>나의 정보</h3>", unsafe_allow_html=True)
    st.markdown(f"""<div style='text-align:center; margin: 30px 0;'><div style='font-size: 60px; background-color:#E0E0E0; width:90px; height:90px; border-radius:50%; margin:0 auto; line-height:90px;'>👩🏻</div><h3 style='margin-top:15px; margin-bottom:5px;'>{st.session_state.current_user}님</h3><span style='background-color:#F0F2F6; padding:5px 15px; border-radius:20px; font-size:14px; color:#111; border:1px solid #E0E0E0;'>⭐ 마음 온도 36.5℃</span></div>""", unsafe_allow_html=True)
    menus = ["알림 설정 〉", "계정 관리 〉", "친구 초대 〉", "앱 설정 〉", "고객 센터 〉", "약관 및 정책 〉"]
    for m in menus: st.markdown(f"<div style='padding: 15px 0; border-bottom: 1px solid #EEE; color: #333;'>{m}</div>", unsafe_allow_html=True)
    st.write("")
    if st.button("🚪 로그아웃", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

def view_login_signup():
    st.markdown("<div class='app-title'>KSU_IDEATHON_3TEAM</div>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["로그인", "회원가입"])
    with tab1:
        login_id = st.text_input("아이디", key="login_id", placeholder="아이디를 입력하세요")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw", placeholder="비밀번호를 입력하세요")
        st.write("")
        if st.button("로그인", type="primary", use_container_width=True):
            if login_id in st.session_state.users_db and st.session_state.users_db[login_id] == login_pw:
                st.session_state.logged_in = True; st.session_state.current_user = login_id; st.session_state.page = 'home'; st.rerun()
            else: st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
        st.info("💡 심사용 임시 계정\n- 아이디: `test`\n- 비밀번호: `1234`\n\n*(새로고침 시 초기화됩니다)*")
    with tab2:
        new_id = st.text_input("새 아이디", key="new_id")
        new_pw = st.text_input("새 비밀번호", type="password", key="new_pw")
        new_pw_check = st.text_input("비밀번호 확인", type="password", key="new_pw_check")
        st.write("")
        if st.button("가입하기", type="primary", use_container_width=True):
            if new_id in st.session_state.users_db: st.error("이미 존재하는 아이디입니다.")
            elif new_pw != new_pw_check: st.error("비밀번호가 일치하지 않습니다.")
            elif len(new_id) < 3 or len(new_pw) < 3: st.error("아이디와 비밀번호는 3자리 이상이어야 합니다.")
            else: st.session_state.users_db[new_id] = new_pw; st.success("회원가입 완료! 로그인 탭에서 로그인해주세요.")

# ==========================================
# 5. 메인 레이아웃 적용
# ==========================================
main_content_area = st.container(height=650, border=False)

with main_content_area:
    if not st.session_state.logged_in: view_login_signup()
    else:
        if st.session_state.page == 'home': view_home()
        elif st.session_state.page == 'write': view_write()
        elif st.session_state.page == 'report': view_report()
        elif st.session_state.page == 'character': view_character()
        elif st.session_state.page == 'profile': view_profile()

if st.session_state.logged_in:
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns([1,1,1,1]) 
    with nav_col1:
        if st.button("🏠", key="nav_home"): go_to('home'); st.rerun()
    with nav_col2:
        if st.button("📊", key="nav_report"): go_to('report'); st.rerun()
    with nav_col3:
        if st.button("🧸", key="nav_char"): go_to('character'); st.rerun()
    with nav_col4:
        if st.button("👤", key="nav_prof"): go_to('profile'); st.rerun()