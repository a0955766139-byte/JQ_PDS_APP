import os
import streamlit as st
import datetime
import time
import random
import smtplib
import requests  # V18 新增：用來跟 LINE 直接溝通
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

# --- 1. 基礎設定 ---
st.set_page_config(page_title="喬鈞心學", page_icon="❤️‍🔥", layout="wide")

# --- Session 初始化 ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'show_register_hint' not in st.session_state: st.session_state.show_register_hint = False
if 'login_view' not in st.session_state: st.session_state.login_view = 'login'

# 救援與驗證相關狀態
if 'otp_code' not in st.session_state: st.session_state.otp_code = None
if 'otp_email' not in st.session_state: st.session_state.otp_email = None
if 'last_send_time' not in st.session_state: st.session_state.last_send_time = 0
if 'is_verified' not in st.session_state: st.session_state.is_verified = False

# 註冊驗證相關狀態
if 'reg_phase' not in st.session_state: st.session_state.reg_phase = 'input' 
if 'reg_otp' not in st.session_state: st.session_state.reg_otp = None
if 'reg_data' not in st.session_state: st.session_state.reg_data = {} 
if 'reg_last_send' not in st.session_state: st.session_state.reg_last_send = 0

# --- 2. CSS 優化 (含 LINE 按鈕) ---
st.markdown("""
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        [data-testid="stHeader"] {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
        
        div[data-baseweb="tab-list"] {
            gap: 0px; background-color: #f8f9fa; padding: 8px; border-radius: 50px; 
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 20px; 
        }
        button[data-baseweb="tab"] {
            background-color: transparent; border: none !important; margin: 0 !important; 
            border-radius: 40px; padding: 10px 25px; font-size: 18px !important; 
            font-weight: 600 !important; color: #666; transition: all 0.3s ease; 
        }
        button[data-baseweb="tab"]:hover { background-color: rgba(0,0,0,0.05); color: #333; }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #FF4B4B 0%, #FF9068 100%) !important; 
            color: white !important; box-shadow: 0 4px 15px rgba(255, 75, 75, 0.35); transform: scale(1.02); 
        }
        button[data-baseweb="tab"][aria-selected="true"] p { color: white !important; }

        /* LINE 按鈕樣式 */
        .line-btn {
            display: inline-flex; align-items: center; justify-content: center;
            width: 100%; background-color: #06C755; color: white; 
            padding: 12px 0; border-radius: 8px; text-decoration: none; 
            font-weight: bold; font-family: sans-serif; margin-bottom: 15px; font-size: 16px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: background 0.3s;
        }
        .line-btn:hover { background-color: #05b34c; color: white; }
        .line-btn img { margin-right: 10px; height: 24px; width: 24px; filter: brightness(0) invert(1); }
    </style>
""", unsafe_allow_html=True)

# 匯入規則
try:
    from databases.pds_rules import PDS_CODES, LIFE_PATH_MEANINGS, PERSONAL_YEAR_MEANINGS
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    st.error("⚠️ 找不到 databases 資料夾！請檢查 GitHub 檔案結構。")
    st.stop()

# --- 3. 資料庫連線 ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
    except:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        st.error("❌ 找不到資料庫連線資訊。")
        st.stop()
    return create_client(url, key)

with st.spinner('🔮 正在連結宇宙資料庫...'):
    supabase = init_connection()
    time.sleep(0.5)

# --- 4. V18 LINE 直連邏輯 (不透過 Supabase Provider) ---
def get_line_auth_url():
    """產生 LINE 登入網址"""
    channel_id = os.environ.get("LINE_CHANNEL_ID")
    if not channel_id: return None # 沒設定變數就不顯示按鈕
    
    redirect_uri = "https://jq-pds-app.onrender.com"
    state = str(random.randint(100000, 999999))
    scope = "profile%20openid%20email"
    
    auth_url = f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={channel_id}&redirect_uri={redirect_uri}&state={state}&scope={scope}"
    return auth_url

def handle_line_callback():
    """處理 LINE 登入回傳"""
    query_params = st.query_params
    if "code" in query_params:
        code = query_params["code"]
        channel_id = os.environ.get("LINE_CHANNEL_ID")
        channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
        redirect_uri = "https://jq-pds-app.onrender.com"
        
        if not channel_id or not channel_secret:
            st.error("❌ LINE 環境變數未設定")
            return

        try:
            # 1. 用 code 換 token
            token_url = "https://api.line.me/oauth2/v2.1/token"
            payload = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": channel_id,
                "client_secret": channel_secret
            }
            headers = {"Content-Type": "application/x-www-form-urlencoded"}
            
            res = requests.post(token_url, data=payload, headers=headers)
            if res.status_code != 200:
                st.error(f"LINE 驗證失敗: {res.text}")
                return

            id_token = res.json().get("id_token")
            
            # 2. 驗證並解碼 id_token 取得使用者資料
            verify_url = "https://api.line.me/oauth2/v2.1/verify"
            verify_payload = {"id_token": id_token, "client_id": channel_id}
            user_res = requests.post(verify_url, data=verify_payload)
            
            if user_res.status_code == 200:
                user_data = user_res.json()
                line_name = user_data.get("name")
                line_email = user_data.get("email")
                
                # 登入成功！
                st.session_state.logged_in = True
                st.session_state.username = line_name
                st.session_state.user_email = line_email
                st.session_state.show_register_hint = False
                
                # 清除網址參數
                st.query_params.clear()
                st.balloons()
                st.success(f"🎉 歡迎回來，{line_name}！")
                time.sleep(1)
                st.rerun()
            else:
                st.error("無法取得使用者資料")
                
        except Exception as e:
            st.error(f"連線錯誤: {e}")
            st.query_params.clear()

# 每次執行檢查回傳
if not st.session_state.logged_in:
    handle_line_callback()

# --- 5. 業務邏輯函式 (保持原樣) ---
# [請務必保留原本的 PDS, Card, Journal 邏輯，這裡省略以節省篇幅]
# 為了避免複製錯誤，我還是把核心函式附上：

def get_taiwan_date_str():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).strftime("%Y-%m-%d")

def get_journals(username):
    try:
        response = supabase.table("journals").select("*").eq("username", username).order("date_str", desc=True).execute()
        return [(item["date_str"], item["content"]) for item in response.data]
    except: return []

def get_today_draw(username):
    today_str = get_taiwan_date_str()
    try:
        response = supabase.table("daily_draws").select("*").eq("username", username).eq("draw_date", today_str).execute()
        if response.data:
            item = response.data[0]
            return (item["title"], item["poem"], item["desc"])
        return None
    except: return None

def save_today_draw(username, card):
    today_str = get_taiwan_date_str()
    data = {"username": username, "draw_date": today_str, "title": card['title'], "poem": card['poem'], "desc": card['desc']}
    try: supabase.table("daily_draws").insert(data).execute()
    except: pass

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

# 傳統登入函式
def login_user(username, password):
    try:
        response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        if response.data: return True
        return False
    except: return False

def find_username(email):
    try:
        response = supabase.table("users").select("username").eq("email", email).execute()
        if response.data: return True, response.data[0]["username"]
        return False, "找不到資料"
    except: return False, "Error"

# --- 6. 頁面視圖 ---
def show_login_page():
    col1, col2 = st.columns([1.5, 1], gap="large")
    with col1:
        st.markdown("# 👁️ 歡迎來到喬鈞心學")
        st.markdown("### 探索你到底是什麼模樣，解開生命的原始設定。")
        st.image("https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=2670&auto=format&fit=crop", caption="數字是世界通用的語言。", width="stretch")
        st.markdown("### 什麼是數字心理學？")
        st.info("這不只是算命，而是一套結合了畢達哥拉斯數學與現代心理學的行為分析系統。")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔮 感到迷惘？先抽張牌試試", use_container_width=True): st.session_state.show_register_hint = True
        if st.session_state.show_register_hint: st.warning("🔒 請先登入解鎖完整功能！")

    with col2:
        with st.container(border=True):
            st.header("🔐 會員專區")
            
            # 🔥 LINE 直連登入按鈕 🔥
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'''
                    <a href="{auth_url}" target="_self" class="line-btn">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg" alt="LINE">
                        使用 LINE 帳號一鍵登入
                    </a>
                ''', unsafe_allow_html=True)
            else:
                st.warning("⚠️ 系統未設定 LINE 連線參數")

            st.markdown("""<div style="text-align: center; color: #888; margin: 10px 0;">或是使用傳統帳號登入</div>""", unsafe_allow_html=True)

            tab1, tab2 = st.tabs(["登入", "找回帳號"])
            
            with tab1:
                u = st.text_input("帳號", key="u_login")
                p = st.text_input("密碼", type="password", key="p_login")
                if st.button("登入系統", type="primary", use_container_width=True):
                    if login_user(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.session_state.show_register_hint = False
                        st.success(f"歡迎，{u}！")
                        time.sleep(1)
                        st.rerun()
                    else: st.error("帳號或密碼錯誤")

            with tab2:
                email = st.text_input("輸入註冊 Email", key="find_u")
                if st.button("🔍 找回帳號"):
                    found, res = find_username(email) 
                    if found: st.info(f"您的帳號是：{res}") 
                    else: st.error(res)

def show_member_app():
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown(f"**Hi, {st.session_state.username}** 👋")
    with c2:
        if st.button("登出", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.user_email = ""
            st.rerun()
            
    # 下方是你的五大功能分頁
    tab_pds, tab_card, tab_journal, tab_reader, tab_shop = st.tabs(["🧬 天賦運勢", "🔮 每日指引卡", "📔 日記", "📜 讀者專屬", "🛒 商城"])
    
    # --- PDS (含下拉選單) ---
    with tab_pds:
        with st.container(border=True):
            st.markdown("##### 🎂 請選擇您的出生年月日")
            c_y, c_m, c_d = st.columns([1, 1, 1])
            with c_y:
                years = list(range(1900, 2026))
                sel_year = st.selectbox("年", years, index=years.index(1983))
            with c_m:
                months = list(range(1, 13))
                sel_month = st.selectbox("月", months, index=months.index(9))
            with c_d:
                days = list(range(1, 32))
                sel_day = st.selectbox("日", days, index=days.index(8))
            
            if st.button("🚀 開始分析", type="primary", use_container_width=True):
                try:
                    bd = datetime.date(sel_year, sel_month, sel_day)
                    data = calculate_pds_full_codes(bd)
                    py, cy = calculate_personal_year(bd)
                    st.markdown("---")
                    c1, c2 = st.columns(2)
                    c1.metric("主命數", f"{data['O']} 號")
                    c2.metric("流年運勢", f"{py}", delta=f"{cy}年")
                    st.info(f"💡 {LIFE_PATH_MEANINGS.get(data['O'], '')}")
                    # ... (顯示戰略地圖)
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
                        if data['codes']['middle'][0] in PDS_CODES: st.success(f"🚩 **坐鎮碼**: {PDS_CODES[data['codes']['middle'][0]]}")
                    with st.container(border=True):
                        st.markdown("**🍂 晚年**")
                        cols = st.columns(4)
                        for i, code in enumerate(data['codes']['late']): cols[i].code(code)
                        for code in data['codes']['late']:
                            if code in PDS_CODES: st.caption(f"**{code}**: {PDS_CODES[code]}")
                except ValueError: st.error("無效日期")

    # --- Daily Card ---
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

    # --- Journal ---
    with tab_journal:
        st.markdown("#### 📔 此刻，與自己對話")
        with st.form("j_form", clear_on_submit=True):
            txt = st.text_area("✍️", height=200, placeholder="親愛的，今天發生了什麼事？")
            submitted = st.form_submit_button("💾 收藏這份記憶", use_container_width=True)
            if submitted and txt:
                today_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                try:
                    supabase.table("journals").insert({"username": st.session_state.username, "content": txt, "date_str": today_str}).execute()
                    st.success("✅ 已保存！")
                    time.sleep(1)
                    st.rerun()
                except: st.error("儲存失敗")
        
        st.divider()
        history = get_journals(st.session_state.username)
        if history:
            for date_str, content in history:
                with st.expander(f"📅 {date_str}", expanded=False):
                    st.write(content)

    with tab_reader: st.info("🚧 讀者專屬功能建置中...")
    with tab_shop: st.success("🚧 商城系統籌備中...")

if st.session_state.logged_in: show_member_app()
else: show_login_page()