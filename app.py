import streamlit as st
import datetime
import time
import random
import sqlite3

# 匯入規則 (確保 databases 資料夾存在)
try:
    from databases.pds_rules import PDS_CODES, LIFE_PATH_MEANINGS, PERSONAL_YEAR_MEANINGS
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    st.error("⚠️ 找不到 databases 資料夾！請檢查檔案結構。")
    st.stop()

# --- 1. 資料庫管家 (升級版：增加了每日抽牌紀錄表) ---
def init_db():
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    # 日記表 (舊的)
    c.execute('''CREATE TABLE IF NOT EXISTS journals (username TEXT, date TEXT, content TEXT)''')
    
    # 🔥 新增：每日抽牌紀錄表 (欄位：帳號、日期、牌名、詩詞、解釋)
    c.execute('''CREATE TABLE IF NOT EXISTS daily_draws 
                 (username TEXT, draw_date TEXT, title TEXT, poem TEXT, desc TEXT)''')
    
    conn.commit()
    conn.close()

def save_journal(username, content):
    """存日記"""
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute("INSERT INTO journals VALUES (?, ?, ?)", (username, date_str, content))
    conn.commit()
    conn.close()

def get_journals(username):
    """讀日記"""
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    c.execute("SELECT date, content FROM journals WHERE username=? ORDER BY date DESC", (username,))
    data = c.fetchall()
    conn.close()
    return data

# 🔥 新功能：檢查今天有沒有抽過牌
def get_today_draw(username):
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d") # 今天的日期 (例如 2026-01-16)
    
    # 找找看這個人、今天、有沒有資料
    c.execute("SELECT title, poem, desc FROM daily_draws WHERE username=? AND draw_date=?", (username, today_str))
    result = c.fetchone() # 抓一筆資料
    conn.close()
    return result # 如果有抽過會回傳資料，沒抽過會回傳 None

# 🔥 新功能：儲存今天的牌
def save_today_draw(username, card):
    conn = sqlite3.connect('databases/user_journals.db')
    c = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    c.execute("INSERT INTO daily_draws VALUES (?, ?, ?, ?, ?)", 
              (username, today_str, card['title'], card['poem'], card['desc']))
    conn.commit()
    conn.close()

# 啟動時先檢查資料庫
init_db()

# --- 2. PDS 計算核心 (保持不變) ---
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

# --- 3. 介面設定 ---
st.set_page_config(page_title="喬鈞心學 App", page_icon="🧿")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'users_db' not in st.session_state: st.session_state.users_db = {"admin": "8888"}
if 'show_register_hint' not in st.session_state: st.session_state.show_register_hint = False

# --- 4. 頁面視圖 ---

def show_login_page():
    """首頁"""
    st.markdown("<h2 style='text-align: center;'>🧿 喬鈞心學</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: grey;'>探索生命原廠設定</p>", unsafe_allow_html=True)
    
    if st.button("🔮 抽取今日指引 (點我)", type="primary", use_container_width=True):
        st.session_state.show_register_hint = True
    
    if st.session_state.show_register_hint:
        st.warning("🔒 請先登入或註冊會員")
        
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["登入", "註冊"])
    with tab1:
        u = st.text_input("帳號", key="u_login")
        p = st.text_input("密碼", type="password", key="p_login")
        if st.button("登入", use_container_width=True):
            if u in st.session_state.users_db and st.session_state.users_db[u] == p:
                st.session_state.logged_in = True
                st.session_state.username = u
                st.session_state.show_register_hint = False
                st.rerun()
            else:
                st.error("帳號或密碼錯誤 (admin/8888)")
    with tab2:
        new_u = st.text_input("設定帳號")
        email = st.text_input("Gmail", placeholder="name@gmail.com")
        new_p = st.text_input("設定密碼", type="password")
        if st.button("免費註冊", type="primary", use_container_width=True):
            if not email.endswith("@gmail.com"): st.error("限 Gmail 註冊")
            elif new_u and new_p:
                st.session_state.users_db[new_u] = new_p
                st.success("註冊成功！請登入")
            else: st.error("請填寫完整")

def show_member_app():
    """會員 App"""
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown(f"**Hi, {st.session_state.username}** 👋")
    with c2:
        if st.button("登出", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
    tab_pds, tab_card, tab_journal = st.tabs(["📊 運算", "🔮 抽卡", "📔 日記"])
    
    # [Tab 1] PDS 運算
    with tab_pds:
        with st.container(border=True):
            st.caption("輸入資料")
            bd = st.date_input("出生年月日", value=datetime.date(1983, 9, 8), 
                             min_value=datetime.date(1900, 1, 1), 
                             max_value=datetime.date.today())
            run_btn = st.button("🚀 開始分析", type="primary", use_container_width=True)
            
        if run_btn:
            data = calculate_pds_full_codes(bd)
            py, cy = calculate_personal_year(bd)
            lp_text = LIFE_PATH_MEANINGS.get(data['O'], f"{data['O']}號人")
            
            st.markdown("---")
            c1, c2 = st.columns(2)
            c1.metric("主命數", f"{data['O']} 號")
            c2.metric("流年運勢", f"{py}", delta=f"{cy}年")
            st.info(f"💡 {lp_text}")
            
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
                anchor = data['codes']['middle'][0]
                if anchor in PDS_CODES: st.success(f"🚩 **坐鎮碼 {anchor}**: {PDS_CODES[anchor]}")

            with st.container(border=True):
                st.markdown("**🍂 晚年**")
                cols = st.columns(4)
                for i, code in enumerate(data['codes']['late']): cols[i].code(code)
                for code in data['codes']['late']:
                    if code in PDS_CODES: st.caption(f"**{code}**: {PDS_CODES[code]}")

    # [Tab 2] 靈性抽卡 (每日限定版)
    with tab_card:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # 1. 先檢查資料庫，今天有沒有抽過？
        today_record = get_today_draw(st.session_state.username)
        
        if today_record:
            # A. 如果抽過了 -> 顯示舊結果
            title, poem, desc = today_record # 解開資料
            st.warning("⚠️ 你今天已經抽過牌囉！請珍惜宇宙給你的指引，明天再來。")
            
            with st.container(border=True):
                st.markdown(f"<h3 style='text-align: center;'>{title}</h3>", unsafe_allow_html=True)
                st.caption(f"📅 抽取時間：{datetime.date.today()}")
                st.markdown("---")
                st.info(f"📜 {poem}")
                st.success(f"💡 {desc}")
                
        else:
            # B. 如果還沒抽 -> 顯示按鈕
            if st.button("🔮 連結宇宙・抽取今日指引", type="primary", use_container_width=True):
                # 抽牌
                card = random.choice(DIVINATION_CARDS)
                
                # 存入資料庫！ (這步最關鍵)
                save_today_draw(st.session_state.username, card)
                
                # 顯示結果
                st.balloons() # 放個氣球慶祝
                with st.container(border=True):
                    st.markdown(f"<h3 style='text-align: center;'>{card['title']}</h3>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.info(f"📜 {card['poem']}")
                    st.success(f"💡 {card['desc']}")
                
                # 強制刷新頁面，讓按鈕消失，變成「已抽過」狀態
                time.sleep(3)
                st.rerun()

    # [Tab 3] 心靈日記
    with tab_journal:
        with st.form("j_form"):
            txt = st.text_area("寫下此刻的覺察...", height=100)
            if st.form_submit_button("💾 儲存日記", use_container_width=True) and txt:
                save_journal(st.session_state.username, txt)
                st.success("已記錄")
                time.sleep(0.5)
                st.rerun()
        
        st.markdown("### 🗓️ 過往紀錄")
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