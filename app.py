import os
import streamlit as st
import datetime
import time
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client

# --- 1. 基礎設定 ---
st.set_page_config(page_title="喬鈞心學", page_icon="❤️‍🔥", layout="wide")

# --- Session 初始化 ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
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

# --- 2. 介面優化 CSS ---
st.markdown("""
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        [data-testid="stHeader"] {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
        .stApp { margin-top: -80px; }
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

# --- 4. 業務邏輯函式 ---
def get_taiwan_date_str():
    tz = datetime.timezone(datetime.timedelta(hours=8))
    return datetime.datetime.now(tz).strftime("%Y-%m-%d")

def get_journals(username):
    try:
        response = supabase.table("journals").select("*").eq("username", username).order("date_str", desc=True).execute()
        return [(item["date_str"], item["content"]) for item in response.data]
    except:
        return []

def get_today_draw(username):
    today_str = get_taiwan_date_str()
    try:
        response = supabase.table("daily_draws").select("*").eq("username", username).eq("draw_date", today_str).execute()
        if response.data:
            item = response.data[0]
            return (item["title"], item["poem"], item["desc"])
        return None
    except:
        return None

def save_today_draw(username, card):
    today_str = get_taiwan_date_str()
    data = {"username": username, "draw_date": today_str, "title": card['title'], "poem": card['poem'], "desc": card['desc']}
    try:
        supabase.table("daily_draws").insert(data).execute()
    except:
        pass

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

# --- 5. 會員與驗證函式 ---
def check_user_exists(username, email):
    try:
        check_u = supabase.table("users").select("username").eq("username", username).execute()
        if check_u.data: return True, "❌ 這個帳號已經有人用了，請換一個！"
        check_e = supabase.table("users").select("email").eq("email", email).execute()
        if check_e.data: return True, "❌ 這個 Email 已經註冊過了，請直接登入。"
        return False, ""
    except Exception as e:
        return True, f"系統檢查失敗: {e}"

def create_user_in_db(username, password, email):
    data = {"username": username, "password": password, "email": email}
    try:
        supabase.table("users").insert(data).execute()
        return True, "✅ 註冊成功！歡迎加入。"
    except Exception as e:
        return False, f"註冊失敗: {e}"

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
        return False, "找不到這個 Email 的註冊資料。"
    except Exception as e: return False, str(e)

# 🔥🔥🔥 V15 修正版：發信函式 (含 Logs 強力追蹤) 🔥🔥🔥
def send_verification_email(to_email, otp_code, purpose="register"):
    print(f"🚀 [Log] 開始嘗試寄信給: {to_email} (Purpose: {purpose})") # 這裡會顯示在 Render Logs
    
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    
    sender_email = None
    sender_password = None
    
    # 1. 優先嘗試從 secrets 讀取
    try:
        if st.secrets.get("email"):
            sender_email = st.secrets["email"]["sender"]
            sender_password = st.secrets["email"]["password"]
    except:
        pass 

    # 2. 嘗試從環境變數讀取
    if not sender_email:
        sender_email = os.environ.get("EMAIL_SENDER")
    if not sender_password:
        sender_password = os.environ.get("EMAIL_PASSWORD")

    # 3. 防呆檢查與 Log
    if not sender_email:
        print("❌ [Log] 失敗：EMAIL_SENDER 未設定")
        return False, "❌ 系統錯誤：Render 環境變數 EMAIL_SENDER 未設定"
    
    if not sender_password:
         print("❌ [Log] 失敗：EMAIL_PASSWORD 未設定")
         return False, "❌ 系統錯誤：Render 環境變數 EMAIL_PASSWORD 未設定"
    
    print(f"ℹ️ [Log] 使用寄件帳號: {sender_email}") # 確認抓到了什麼帳號

    if purpose == "register":
        subject = "【喬鈞心學】歡迎註冊 - 您的驗證碼"
        content_text = f"歡迎來到喬鈞心學！\n\n您的註冊驗證碼是：【 {otp_code} 】\n\n請回到網頁輸入此代碼以完成註冊。"
    else:
        subject = "【喬鈞心學】密碼重設驗證碼"
        content_text = f"親愛的會員您好：\n\n我們收到了您的密碼重設請求。\n您的驗證碼是：【 {otp_code} 】\n\n若您未申請，請忽略此信。"

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(content_text, 'plain'))

    try:
        print("🔄 [Log] 正在連線 SMTP...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        
        print("🔐 [Log] 正在登入...")
        server.login(sender_email, sender_password)
        
        print("📨 [Log] 正在發送...")
        server.sendmail(sender_email, to_email, msg.as_string())
        
        print("✅ [Log] 寄信成功！")
        server.quit()
        return True, "📧 驗證碼已發送至您的信箱！"
    except Exception as e:
        print(f"❌ [Log] 寄信發生錯誤: {str(e)}") # 這裡會把詳細錯誤印出來
        return False, f"寄信失敗 (請檢查 Render Logs): {e}"

# --- 6. 頁面視圖 ---
def show_login_page():
    col1, col2 = st.columns([1.5, 1], gap="large")
    with col1:
        st.markdown("# 👁️ 歡迎來到喬鈞心學")
        st.markdown("### 探索你到底是什麼模樣，解開生命的原始設定。")
        # 🔥 V15 關鍵修正：width="stretch" (修正之前寫錯的 None)
        st.image("https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=2670&auto=format&fit=crop", caption="數字是世界通用的語言。", width="stretch")
        st.markdown("### 什麼是數字心理學？")
        st.info("這不只是算命，而是一套結合了畢達哥拉斯數學與現代心理學的行為分析系統。幫助你看見天賦、理解挑戰、規劃未來。")
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔮 感到迷惘？先抽張牌試試 (每日指引)", use_container_width=True): st.session_state.show_register_hint = True
        if st.session_state.show_register_hint: st.warning("🔒 請先註冊或登入會員，即可免費解鎖完整功能！")

    with col2:
        with st.container(border=True):
            st.header("🔐 會員專區")
            tab1, tab2 = st.tabs(["登入", "註冊新帳號"])
            
            # --- Tab 1: 登入 ---
            with tab1:
                if st.session_state.login_view == 'login':
                    st.write("")
                    u = st.text_input("帳號", key="u_login")
                    p = st.text_input("密碼", type="password", key="p_login")
                    st.write("") 
                    if st.button("登入系統", type="primary", use_container_width=True):
                        if login_user(u, p):
                            st.session_state.logged_in = True
                            st.session_state.username = u
                            st.session_state.show_register_hint = False
                            st.success(f"歡迎回來，{u}！")
                            time.sleep(1)
                            st.rerun()
                        else: st.error("帳號不存在或密碼錯誤")
                    st.write("") 
                    c_spacer, c_btn = st.columns([1.2, 1])
                    with c_btn:
                        if st.button("🆘 忘記帳號 / 密碼 ?", use_container_width=True):
                            st.session_state.login_view = 'recovery' 
                            st.rerun()
                else:
                    # 救援模式
                    st.markdown("##### 🛠️ 帳號救援中心")
                    if st.button("🔙 返回登入頁面", use_container_width=True):
                        st.session_state.login_view = 'login'
                        st.rerun()
                    st.divider()
                    mode = st.radio("協助項目", ["找回帳號", "重設密碼 (Email驗證)"])
                    if mode == "找回帳號":
                        email = st.text_input("輸入註冊 Email", key="find_u")
                        if st.button("🔍 查詢"):
                            found, res = find_username(email) 
                            if found: st.info(f"您的帳號是：{res}") 
                            else: st.error(res)
                    elif mode == "重設密碼 (Email驗證)":
                        if not st.session_state.is_verified:
                            email_input = st.text_input("請輸入您的註冊 Email", key="rst_email")
                            if st.button("📩 發送驗證碼"):
                                current_time = time.time()
                                if current_time - st.session_state.last_send_time < 60:
                                    wait_time = 60 - int(current_time - st.session_state.last_send_time)
                                    st.warning(f"⏳ 請勿頻繁發送，請再等待 {wait_time} 秒。")
                                else:
                                    found, _ = find_username(email_input)
                                    if not found: st.error("❌ 找不到這個 Email")
                                    else:
                                        code = str(random.randint(100000, 999999))
                                        success, msg = send_verification_email(email_input, code, purpose="reset")
                                        if success:
                                            st.session_state.otp_code = code 
                                            st.session_state.otp_email = email_input
                                            st.session_state.last_send_time = current_time 
                                            st.success(msg)
                                        else: st.error(msg)
                            if st.session_state.otp_code:
                                st.info("驗證碼已寄出")
                                user_code = st.text_input("輸入 6 位數驗證碼", key="u_code")
                                if st.button("✅ 驗證身分"):
                                    if user_code == st.session_state.otp_code:
                                        st.success("驗證成功！")
                                        st.session_state.is_verified = True
                                        st.rerun()
                                    else: st.error("❌ 驗證碼錯誤")
                        else:
                            st.success(f"身分確認無誤 ({st.session_state.otp_email})")
                            new_pwd = st.text_input("設定新密碼", type="password", key="new_p_final")
                            confirm_pwd = st.text_input("再次輸入新密碼", type="password", key="cfm_p_final")
                            if st.button("💾 儲存新密碼"):
                                if new_pwd != confirm_pwd: st.error("兩次密碼不一致")
                                else:
                                    try:
                                        supabase.table("users").update({"password": new_pwd}).eq("email", st.session_state.otp_email).execute()
                                        st.balloons()
                                        st.success("🎉 密碼修改成功！請重新登入。")
                                        st.session_state.is_verified = False
                                        st.session_state.otp_code = None
                                        st.session_state.login_view = 'login' 
                                        time.sleep(2)
                                        st.rerun()
                                    except Exception as e: st.error(f"更新失敗: {e}")
            
            # --- Tab 2: 註冊新帳號 ---
            with tab2:
                if st.session_state.reg_phase == 'input':
                    st.write("")
                    new_u = st.text_input("設定帳號 (ID)", key="reg_u")
                    email = st.text_input("Email (限 Gmail)", placeholder="name@gmail.com", key="reg_e")
                    new_p = st.text_input("設定密碼", type="password", key="reg_p")
                    st.write("")
                    if st.button("📩 獲取驗證碼", use_container_width=True):
                        if not email.endswith("@gmail.com"): st.error("請使用 Gmail 信箱註冊")
                        elif not new_u or not new_p: st.error("請填寫完整資訊")
                        else:
                            exists, msg = check_user_exists(new_u, email)
                            if exists: st.error(msg)
                            else:
                                current_time = time.time()
                                if current_time - st.session_state.reg_last_send < 60: st.warning("⏳ 驗證碼剛寄出，請稍後再試。")
                                else:
                                    code = str(random.randint(100000, 999999))
                                    success, msg = send_verification_email(email, code, purpose="register")
                                    if success:
                                        st.session_state.reg_otp = code
                                        st.session_state.reg_data = {"u": new_u, "p": new_p, "e": email}
                                        st.session_state.reg_phase = 'verify'
                                        st.session_state.reg_last_send = current_time
                                        st.rerun()
                                    else: st.error(msg)
                elif st.session_state.reg_phase == 'verify':
                    st.info(f"驗證碼已發送至：{st.session_state.reg_data.get('e')}")
                    reg_code_input = st.text_input("請輸入 6 位數驗證碼", key="reg_code_in")
                    col_back, col_ok = st.columns(2)
                    with col_back:
                        if st.button("🔙 返回修改", use_container_width=True):
                            st.session_state.reg_phase = 'input'
                            st.rerun()
                    with col_ok:
                        if st.button("✅ 完成註冊", type="primary", use_container_width=True):
                            if reg_code_input == st.session_state.reg_otp:
                                u = st.session_state.reg_data['u']
                                p = st.session_state.reg_data['p']
                                e = st.session_state.reg_data['e']
                                success, msg = create_user_in_db(u, p, e)
                                if success:
                                    st.balloons()
                                    st.success("🎉 註冊成功！請切換到「登入」分頁進入系統。")
                                    st.session_state.reg_phase = 'input'
                                    st.session_state.reg_otp = None
                                    st.session_state.reg_data = {}
                                else: st.error(msg)
                            else: st.error("❌ 驗證碼錯誤")

def show_member_app():
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown(f"**Hi, {st.session_state.username}** 👋")
    with c2:
        if st.button("登出", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
            
    tab_pds, tab_card, tab_journal, tab_reader, tab_shop = st.tabs(["🧬 天賦運勢", "🔮 每日指引卡", "📔 日記", "📜 讀者專屬", "🛒 商城"])
    with tab_pds:
        with st.container(border=True):
            bd = st.date_input("出生年月日", value=datetime.date(1983, 9, 8), min_value=datetime.date(1900, 1, 1), max_value=datetime.date.today())
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
                if data['codes']['middle'][0] in PDS_CODES: st.success(f"🚩 **坐鎮碼**: {PDS_CODES[data['codes']['middle'][0]]}")
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
        st.markdown("#### 📔 此刻，與自己對話")
        with st.expander("⚙️ 進階設定：調整日期、時間或時區 (點擊展開)", expanded=False):
            timezone_options = {
                "🇹🇼 台灣/中國 (UTC+8)": 8,
                "🇯🇵 日本 (UTC+9)": 9,
                "🇺🇸 美國西部 (洛杉磯) (UTC-7)": -7,
                "🇺🇸 美國東部 (紐約) (UTC-4)": -4,
            }
            c_tz, c_date, c_time = st.columns([2, 1.5, 1.5])
            with c_tz:
                selected_zone = st.selectbox("🌍 時區", options=list(timezone_options.keys()), index=0)
            offset_hours = timezone_options[selected_zone]
            user_tz = datetime.timezone(datetime.timedelta(hours=offset_hours))
            now_local = datetime.datetime.now(user_tz)
            with c_date: pick_date = st.date_input("📅 日期", value=now_local.date())
            with c_time: pick_time = st.time_input("⏰ 時間", value=now_local.time())
        if 'pick_date' not in locals():
            pick_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date()
            pick_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).time()
        with st.form("j_form", clear_on_submit=True):
            txt = st.text_area("✍️", height=200, placeholder="親愛的，今天發生了什麼事？你的感覺如何？...\n(這裡是一個安全的空間，請放心書寫)")
            c_null, c_btn = st.columns([3, 1])
            with c_btn: submitted = st.form_submit_button("💾 收藏這份記憶", use_container_width=True)
            if submitted:
                if not txt: st.warning("⚠️ 內容是空的，試著寫下一個字也好。")
                else:
                    final_dt = datetime.datetime.combine(pick_date, pick_time)
                    date_str = final_dt.strftime("%Y-%m-%d %H:%M:%S")
                    data = {"username": st.session_state.username, "content": txt, "date_str": date_str}
                    try:
                        supabase.table("journals").insert(data).execute()
                        st.success(f"✅ 已保存！ ({date_str})")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e: st.error(f"儲存失敗: {e}")
        st.divider()
        st.markdown("##### 🕰️ 回憶長廊")
        history = get_journals(st.session_state.username)
        if history:
            for date_str, content in history:
                with st.expander(f"📅 {date_str} - {content[:10]}...", expanded=False):
                    st.markdown(content)
                    st.caption(f"記錄於: {date_str}")
        else: st.caption("這裡目前一片空白，等待你的第一筆紀錄...")

    with tab_reader:
        st.info("🚧 讀者專屬功能建置中... (這裡將連結你的書本內容)")
        st.image("https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c", use_container_width=True)

    with tab_shop:
        st.success("🚧 商城系統籌備中... (這裡將販售課程與周邊)")
        c1, c2 = st.columns(2)
        c1.metric("預計上架商品", "12 件")
        c2.metric("目前優惠", "早鳥 8 折")

if st.session_state.logged_in: show_member_app()
else: show_login_page()