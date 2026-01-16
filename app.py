import streamlit as st
import datetime
import time
import random
import sqlite3

# 匯入規則
try:
    from databases.pds_rules import PDS_CODES, LIFE_PATH_MEANINGS, PERSONAL_YEAR_MEANINGS
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    st.error("⚠️ 找不到 databases 資料夾！請檢查檔案結構。")
    st.stop()

# --- 資料庫管家 ---
def init_db():
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS journals (username TEXT, date TEXT, content TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_draws (username TEXT, draw_date TEXT, title TEXT, poem TEXT, desc TEXT)''')
    conn.commit()
    conn.close()

def save_journal(username, content):
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO journals VALUES (?, ?, ?)", (username, date_str, content))
    conn.commit()
    conn.close()

def get_journals(username):
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    c.execute("SELECT date, content FROM journals WHERE username=? ORDER BY date DESC", (username,))
    data = c.fetchall()
    conn.close()
    return data

def get_today_draw(username):
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    c.execute("SELECT title, poem, desc FROM daily_draws WHERE username=? AND draw_date=?", (username, today_str))
    result = c.fetchone()
    conn.close()
    return result

def save_today_draw(username, card):
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    c.execute("INSERT INTO daily_draws VALUES (?, ?, ?, ?, ?)", (username, today_str, card['title'], card['poem'], card['desc']))
    conn.commit()
    conn.close()

init_db()

# --- PDS 計算核心 ---
def get_digit_sum(n):
    while n > 9: n = sum(int(d) for d in str(n))
    return n

def calculate_pds_full_codes(birthdate):
    y, m, d = birthdate.year, birthdate.month, birthdate.day
    sy, sm, sd = f"{y:04d}", f"{m:02d}", f"{d:02d}"
    A, B = int(sd[0]), int(sd[1])
    C, D = int(sm[0]), int(sm[1])
    E, F, G, H = int(sy[0]), int(sy[1]), int(sy[2]), int(sy[3])
    I, J = get_digit_sum(A+B), get_digit_sum(C+D)
    K, L = get_digit_sum(E+F), get_digit_sum(G+H)
    M, N = get_digit_sum(I+J), get_digit_sum(K+L)
    O = get_digit_sum(M+N)
    P, Q = get_digit_sum(I+M), get_digit_sum(J+M)
    R = get_digit_sum(P+Q)
    V, W = get_digit_sum(K+N), get_digit_sum(L+N)
    X = get_digit_sum(V+W)
    S, T = get_digit_sum(N+O), get_digit_sum(M+O)
    U = get_digit_sum(S+T)
    early = [f"{I}{J}{M}", f"{I}{M}{P}", f"{J}{M}{Q}", f"{P}{Q}{R}"]
    mid = [f"{M}{N}{O}", f"{M}{O}{T}", f"{N}{O}{S}", f"{S}{T}{U}"]
    late = [f"{K}{L}{N}", f"{K}{N}{V}", f"{L}{N}{W}", f"{V}{W}{X}"]
    return {"O": O, "codes": {"early": early, "middle": mid, "late": late}, "params": {"M": M, "N": N, "O": O, "U": U}}

def calculate_personal_year(birthdate):
    total = datetime.date.today().year + birthdate.month + birthdate.day
    return get_digit_sum(total), datetime.date.today().year

# --- 介面設定 ---
st.set_page_config(page_title="喬鈞心學", page_icon="👁️", layout="wide")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'users_db' not in st.session_state: st.session_state.users_db = {"admin": "8888"}
if 'show_register_hint' not in st.session_state: st.session_state.show_register_hint = False

# --- 頁面視圖 ---

def show_login_page():
    """首頁設計 (Split Screen Layout)"""
    
    # 使用 columns 把畫面切成左右兩邊
    # [1.5, 1] 代表左邊寬度是 1.5，右邊是 1 (左寬右窄)
    col1, col2 = st.columns([1.5, 1], gap="large")

    # --- 左側：品牌故事與介紹 ---
    with col1:
        st.markdown("# 👁️ 歡迎來到喬鈞心學")
        st.markdown("### 探索你到底是什麼模樣，解開生命的原始設定。")
        
        # 插入一張更有質感的圖片 (類似你截圖中的筆記本風格)
        st.image("https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=2670&auto=format&fit=crop", 
                 caption="數字是世界通用的語言。", use_container_width=True)
        
        st.markdown("### 什麼是數字心理學？")
        # 使用 info 藍色區塊來強調
        st.info("這不只是算命，而是一套結合了畢達哥拉斯數學與現代心理學的行為分析系統。幫助你看見天賦、理解挑戰、規劃未來。")

        # 這裡放一個誘餌按鈕 (Lead Magnet)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔮 感到迷惘？先抽張牌試試 (每日指引)", use_container_width=True):
             st.session_state.show_register_hint = True
        
        if st.session_state.show_register_hint:
            st.warning("🔒 請先在右側註冊或登入會員，即可免費解鎖完整功能！")

    # --- 右側：登入/註冊卡片 ---
    with col2:
        # 加上 border=True 讓它看起來像一張浮起來的卡片
        with st.container(border=True):
            st.header("🔐 會員登入")
            
            tab1, tab2 = st.tabs(["登入", "註冊新帳號"])
            
            with tab1:
                st.write("") # 空一行
                u = st.text_input("帳號 (使用者名稱)", key="u_login")
                p = st.text_input("密碼", type="password", key="p_login")
                
                st.write("") 
                # primary button 通常是紅/橘色系 (視主題而定)
                if st.button("登入系統", type="primary", use_container_width=True):
                    if u in st.session_state.users_db and st.session_state.users_db[u] == p:
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.session_state.show_register_hint = False
                        st.rerun()
                    else:
                        st.error("帳號或密碼錯誤 (admin/8888)")
                        
            with tab2:
                st.write("")
                new_u = st.text_input("設定帳號")
                email = st.text_input("Email (限 Gmail)", placeholder="name@gmail.com")
                new_p = st.text_input("設定密碼", type="password")
                
                st.write("")
                if st.button("立即註冊", use_container_width=True):
                    if not email.endswith("@gmail.com"): st.error("限 Gmail 註冊")
                    elif new_u and new_p:
                        st.session_state.users_db[new_u] = new_p
                        st.success("註冊成功！請切換到「登入」分頁。")
                    else: st.error("請填寫完整資訊")

def show_member_app():
    """會員 App (保持之前的 V7 版本)"""
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown(f"**Hi, {st.session_state.username}** 👋")
    with c2:
        if st.button("登出", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
    tab_pds, tab_card, tab_journal = st.tabs(["📊 運算", "🔮 抽卡", "📔 日記"])
    
    with tab_pds:
        with st.container(border=True):
            bd = st.date_input("出生年月日", value=datetime.date(1983, 9, 8), 
                             min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
            run_btn = st.button("🚀 開始分析", type="primary", use_container_width=True)
            
        if run_btn:
            data = calculate_pds_full_codes(bd)
            py, cy = calculate_personal_year(bd)
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("主命數", f"{data['O']} 號")
            c2.metric("流年運勢", f"{py}", delta=f"{cy}年")
            st.info(f"💡 {LIFE_PATH_MEANINGS.get(data['O'], '')}")
            
            st.markdown("#### 📍 人生戰略地圖")
            with st.container(border=True):
                st.markdown("**🌱 早年**")
                cols = st.columns(4)
                for i, code in enumerate(data['codes']['early']): cols[i].code(code)
                for code in data['codes']['early']:
                    if code in PDS_CODES: st.caption(f"**{code}**: {PDS_CODES[code]}")

            with st.container(border=True):
                st.markdown("**☀️ 中年**")
                cols = st.columns(4)
                for i, code in enumerate(data['codes']['middle']):
                    if i == 0: cols[i].error(code)
                    else: cols[i].code(code)
                if data['codes']['middle'][0] in PDS_CODES:
                    st.success(f"🚩 **坐鎮碼**: {PDS_CODES[data['codes']['middle'][0]]}")

            with st.container(border=True):
                st.markdown("**🍂 晚年**")
                cols = st.columns(4)
                for i, code in enumerate(data['codes']['late']): cols[i].code(code)
                for code in data['codes']['late']:
                    if code in PDS_CODES: st.caption(f"**{code}**: {PDS_CODES[code]}")

    with tab_card:
        st.markdown("<br>", unsafe_allow_html=True)
        today_record = get_today_draw(st.session_state.username)
        if today_record:
            st.warning("⚠️ 你今天已經抽過牌囉！")
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align: center;'>{today_record[0]}</h3>", unsafe_allow_html=True)
                st.info(f"📜 {today_record[1]}")
                st.success(f"💡 {today_record[2]}")
        else:
            if st.button("🔮 連結宇宙・抽取今日指引", type="primary", use_container_width=True):
                card = random.choice(DIVINATION_CARDS)
                save_today_draw(st.session_state.username, card)
                st.balloons()
                with st.container(border=True):
                    st.markdown(f"<h3 style='text-align: center;'>{card['title']}</h3>", unsafe_allow_html=True)
                    st.info(f"📜 {card['poem']}")
                    st.success(f"💡 {card['desc']}")
                time.sleep(3)
                st.rerun()

    with tab_journal:
        with st.form("j_form"):
            txt = st.text_area("寫下此刻的覺察...", height=100)
            if st.form_submit_button("💾 儲存日記", use_container_width=True) and txt:
                save_journal(st.session_state.username, txt)
                st.success("已記錄")
                time.sleep(0.5)
                st.rerun()
        history = get_journals(st.session_state.username)
        if history:
            for date, content in history:
                with st.container(border=True):
                    st.caption(f"📅 {date}")
                    st.markdown(content)
        else:
            st.caption("尚無紀錄")

if st.session_state.logged_in:
    show_member_app()
else:
    show_login_page()
