import os
import streamlit as st
import datetime
import time
import random
from supabase import create_client, Client

# --- 1. 基礎設定與導入 ---
st.set_page_config(page_title="喬鈞心學", page_icon="❤️‍🔥", layout="wide")

# 隱藏 Streamlit 選單
hide_st_style = """
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        #MainMenu {visibility: hidden !important; display: none !important;}
        header {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
    </style>
"""
# --- 介面優化：隱藏選單 + 強化分頁按鈕樣式 ---
st.markdown("""
    <style>
        /* 1. 隱藏 Streamlit 預設選單 (漢堡與浮水印) */
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        #MainMenu {visibility: hidden !important; display: none !important;}
        header {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
        
        /* 2. 針對分頁按鈕 (Tab) 進行整形 */
        button[data-baseweb="tab"] {
            font-size: 24px !important;    /* 🔥 字體放大 (原本約 16px) */
            font-weight: 700 !important;   /* 🔥 字體加粗 */
            background-color: #f0f2f6;     /* 沒選中時的背景色：淺灰 */
            border-radius: 10px 10px 0px 0px; /* 圓角設計，像文件夾 */
            border: 1px solid #E0E0E0;     /* 淡淡的邊框 */
            margin-right: 8px;             /* 按鈕之間的間距 */
            padding: 10px 20px;            /* 按鈕留白，讓它胖一點 */
            transition: all 0.3s;          /* 點擊時的動畫效果 */
        }
        
        /* 3. 當分頁「被選中」時的樣子 */
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: #FF4B4B !important; /* 🔥 選中變成紅色 (配合你的主題) */
            color: white !important;              /* 字變成白色 */
            border: none;                         /* 拿掉邊框 */
            box-shadow: 0px 4px 10px rgba(0,0,0,0.1); /* 加一點陰影，浮起來的感覺 */
        }
        
        /* 強制修正選中時內層文字顏色 (確保是白色) */
        button[data-baseweb="tab"][aria-selected="true"] p {
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

# 匯入規則
try:
    from databases.pds_rules import PDS_CODES, LIFE_PATH_MEANINGS, PERSONAL_YEAR_MEANINGS
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    st.error("⚠️ 找不到 databases 資料夾！請檢查 GitHub 檔案結構。")
    st.stop()

# --- 2. 資料庫連線 (Supabase) ---
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

supabase = init_connection()

# --- 3. 會員系統功能 (新功能!) ---

def register_user(username, password, email):
    """註冊新用戶"""
    # 1. 先檢查帳號是否已存在
    try:
        check = supabase.table("users").select("username").eq("username", username).execute()
        if check.data:
            return False, "❌ 這個帳號已經有人用了，請換一個！"
    except Exception as e:
        return False, f"連線檢查失敗: {e}"

    # 2. 建立新帳號
    data = {"username": username, "password": password, "email": email}
    try:
        supabase.table("users").insert(data).execute()
        return True, "✅ 註冊成功！請切換到「登入」頁籤登入。"
    except Exception as e:
        return False, f"註冊失敗: {e}"

def login_user(username, password):
    """驗證登入"""
    try:
        # 去資料庫找：有沒有這個帳號 且 密碼也對 的人？
        response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        if response.data:
            return True # 找到了！登入成功
        else:
            return False # 沒找到，帳密錯誤
    except Exception:
        return False

# --- 4. 業務功能 (日記與抽牌) ---

def save_journal(username, content):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"username": username, "content": content, "date_str": date_str}
    try:
        supabase.table("journals").insert(data).execute()
    except Exception as e:
        st.error(f"儲存失敗: {e}")

def get_journals(username):
    try:
        response = supabase.table("journals").select("*").eq("username", username).order("created_at", desc=True).execute()
        return [(item["date_str"], item["content"]) for item in response.data]
    except:
        return []

def get_today_draw(username):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    try:
        response = supabase.table("daily_draws").select("*").eq("username", username).eq("draw_date", today_str).execute()
        if response.data:
            item = response.data[0]
            return (item["title"], item["poem"], item["desc"])
        return None
    except:
        return None

def save_today_draw(username, card):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    data = {"username": username, "draw_date": today_str, "title": card['title'], "poem": card['poem'], "desc": card['desc']}
    try:
        supabase.table("daily_draws").insert(data).execute()
    except:
        pass

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

# --- Session 初始化 ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'show_register_hint' not in st.session_state: st.session_state.show_register_hint = False

# --- 頁面視圖 ---

def show_login_page():
    col1, col2 = st.columns([1.5, 1], gap="large")
    with col1:
        st.markdown("# ❤️‍🔥 歡迎來到喬鈞心學")
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
            st.header("🔐 會員專區")
            tab1, tab2 = st.tabs(["登入", "註冊新帳號"])
            
            # --- 登入區塊 ---
            with tab1:
                st.write("")
                u = st.text_input("帳號", key="u_login")
                p = st.text_input("密碼", type="password", key="p_login")
                st.write("") 
                if st.button("登入系統", type="primary", use_container_width=True):
                    # 這裡呼叫新的 login_user 函式去查資料庫
                    if login_user(u, p):
                        st.session_state.logged_in = True
                        st.session_state.username = u
                        st.session_state.show_register_hint = False
                        st.success(f"歡迎回來，{u}！")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("帳號不存在或密碼錯誤")
            
            # --- 註冊區塊 ---
            with tab2:
                st.write("")
                new_u = st.text_input("設定帳號 (ID)")
                email = st.text_input("Email (限 Gmail)", placeholder="name@gmail.com")
                new_p = st.text_input("設定密碼", type="password")
                st.write("")
                if st.button("立即註冊", use_container_width=True):
                    if not email.endswith("@gmail.com"):
                        st.error("請使用 Gmail 信箱註冊")
                    elif not new_u or not new_p:
                        st.error("請填寫完整資訊")
                    else:
                        # 呼叫新的 register_user 函式寫入資料庫
                        success, msg = register_user(new_u, new_p, email)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

def show_member_app():
    c1, c2 = st.columns([3, 1])
    with c1: st.markdown(f"**Hi, {st.session_state.username}** 👋")
    with c2:
        if st.button("登出", key="logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.rerun()
            
    tab_pds, tab_card, tab_journal, tab_reader, tab_shop = st.tabs(["🧬 天賦運勢", "🔮 抽卡", "📔 日記", "📜 讀者專屬", "🛒 商城"])
    
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

    with tab_reader:
        st.info("🚧 讀者專屬功能建置中... (這裡將連結你的書本內容)")
        st.image("https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c", use_container_width=True)

    with tab_shop:
        st.success("🚧 商城系統籌備中... (這裡將販售課程與周邊)")
        c1, c2 = st.columns(2)
        c1.metric("預計上架商品", "12 件")
        c2.metric("目前優惠", "早鳥 8 折")

if st.session_state.logged_in:
    show_member_app()
else:
    show_login_page()