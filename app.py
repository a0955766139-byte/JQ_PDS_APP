import os
import streamlit as st
import datetime
import time
import random
from supabase import create_client, Client

# 匯入規則
try:
    from databases.pds_rules import PDS_CODES, LIFE_PATH_MEANINGS, PERSONAL_YEAR_MEANINGS
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    st.error("⚠️ 找不到 databases 資料夾！請檢查 GitHub 檔案結構。")
    st.stop()

# --- 資料庫管家 (Supabase 版) ---

# --- 資料庫管家 (通用版：支援 Streamlit Cloud 與 Render) ---
@st.cache_resource
def init_connection():
    try:
        # 1. 優先嘗試讀取 Streamlit 專屬 Secrets (本地或 Streamlit Cloud)
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except:
        # 2. 如果失敗，改為讀取系統環境變數 (Render 適用)
        # 這裡使用 os.environ.get 來抓取我們等一下在 Render 設定的變數
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        st.error("❌ 找不到資料庫連線資訊，請檢查 Secrets 或環境變數設定。")
        st.stop()
        
    return create_client(url, key)
supabase = init_connection()

# 2. 存日記
def save_journal(username, content):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"username": username, "content": content, "date_str": date_str}
    try:
        supabase.table("journals").insert(data).execute()
    except Exception as e:
        st.error(f"儲存失敗: {e}")

# 3. 讀日記
def get_journals(username):
    try:
        response = supabase.table("journals").select("*").eq("username", username).order("created_at", desc=True).execute()
        return [(item["date_str"], item["content"]) for item in response.data]
    except Exception as e:
        st.error(f"讀取失敗: {e}")
        return []

# 4. 檢查今日抽牌
def get_today_draw(username):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    try:
        response = supabase.table("daily_draws").select("*").eq("username", username).eq("draw_date", today_str).execute()
        if response.data:
            item = response.data[0]
            return (item["title"], item["poem"], item["desc"])
        return None
    except Exception:
        return None # 如果表格還沒建，先略過錯誤

# 5. 存今日抽牌
def save_today_draw(username, card):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    data = {
        "username": username, 
        "draw_date": today_str, 
        "title": card['title'], 
        "poem": card['poem'], 
        "desc": card['desc']
    }
    try:
        supabase.table("daily_draws").insert(data).execute()
    except Exception as e:
        pass # 暫時忽略錯誤

# --- PDS 計算核心 (保持不變) ---
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
st.set_page_config(page_title="喬鈞心學", page_icon="❤️‍🔥", layout="wide")

# --- 隱藏 Streamlit 預設選單、頁尾與頂部導覽列 (強力版) ---
hide_st_style = """
    <style>
        /* 隱藏頂部工具列 (包含三個點點) */
        [data-testid="stToolbar"] {
            visibility: hidden !important;
            display: none !important;
        }
        /* 隱藏舊版選單 ID (以防萬一) */
        #MainMenu {
            visibility: hidden !important;
            display: none !important;
        }
        /* 隱藏頁首裝飾條 */
        header {
            visibility: hidden !important;
        }
        /* 隱藏頁尾 "Made with Streamlit" */
        footer {
            visibility: hidden !important;
            display: none !important;
        }
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
# 這裡還是用簡單的字典存帳號，如果要改用 Supabase 存帳號也可以，但先不急
if 'users_db' not in st.session_state: st.session_state.users_db = {"admin": "8888"}
if 'show_register_hint' not in st.session_state: st.session_state.show_register_hint = False

# --- 頁面視圖 ---

def show_login_page():
    """首頁設計 (Split Screen Layout)"""
    col1, col2 = st.columns([1.5, 1], gap="large")
    with col1:
        st.markdown("# 👁️ 歡迎來到喬鈞心學")
        st.markdown("### 探索你到底是什麼模樣，解開生命的原始設定。")
        st.image("https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=2670&auto=format&fit=crop", 
                 caption="數字是世界通用的語言。", use_container_width=True)
        st.markdown("### 什麼是數字心理學？")
        st.info("這不只是算命，而是一套結合了畢達哥拉斯數學與現代心理學的行為分析系統。幫助你看見天賦、理解挑戰、規劃未來。")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔮 感到迷惘？先抽張牌試試 (每日指引)", use_container_width=True):
             st.session_state.show_register_hint = True
        if st.session_state.show_register_hint:
            st.warning("🔒 請先註冊或登入會員，即可免費解鎖完整功能！")

    with col2:
        with st.container(border=True):
            st.header("🔐 會員登入")
            tab1, tab2 = st.tabs(["登入", "註冊新帳號"])
            with tab1:
                st.write("")
                u = st.text_input("帳號 (使用者名稱)", key="u_login")
                p = st.text_input("密碼", type="password", key="p_login")
                st.write("") 
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
                st.success("已記錄 (雲端保存)")
                time.sleep(0.5)
                st.rerun()
        
        # 讀取日記 (從 Supabase)
        history = get_journals(st.session_state.username)
        if history:
            for date_str, content in history:
                with st.container(border=True):
                    st.caption(f"📅 {date_str}")
                    st.markdown(content)
        else:
            st.caption("尚無紀錄")

if st.session_state.logged_in:
    show_member_app()
else:
    show_login_page()