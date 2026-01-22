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
# --- 介面優化：V3 現代 AI 科技風格 (流體導航列) ---
st.markdown("""
    <style>
        /* 1. 隱藏 Streamlit 預設選單 (漢堡與浮水印) */
        [data-testid="stToolbar"] {visibility: hidden !important; display: none !important;}
        #MainMenu {visibility: hidden !important; display: none !important;}
        header {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
        
        /* 2. 導航列容器：創造「一體成型」的底座 */
        div[data-baseweb="tab-list"] {
            gap: 0px; /* 🔥 關鍵：移除分頁之間的間隙 */
            background-color: #f8f9fa; /* 淺灰底色，像一個凹槽 */
            padding: 8px; /* 內縮一點，讓按鈕懸浮在裡面 */
            border-radius: 50px; /* 極度圓潤的膠囊形狀 */
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.05); /* 內陰影，增加立體感 */
            margin-bottom: 20px; /* 跟下方內容保持距離 */
        }
        
        /* 3. 分頁按鈕本體 */
        button[data-baseweb="tab"] {
            background-color: transparent; /* 預設透明 */
            border: none !important; /* 移除邊框 */
            margin: 0 !important; /* 移除外距 */
            border-radius: 40px; /* 按鈕也是圓的 */
            padding: 10px 25px; /* 增加寬度 */
            font-size: 18px !important;
            font-weight: 600 !important;
            color: #666; /* 未選中時是深灰色 */
            transition: all 0.3s ease; /* 0.3秒絲滑過渡動畫 */
        }
        
        /* 4. 滑鼠懸停效果 (Hover) */
        button[data-baseweb="tab"]:hover {
            background-color: rgba(0,0,0,0.05); /* 微微變深 */
            color: #333;
        }
        
        /* 5. 選中狀態 (Active) - 重頭戲！AI 感的核心 */
        button[data-baseweb="tab"][aria-selected="true"] {
            /* 🔥 現代 AI 常用的流體漸層 (配合你的紅色主題) */
            background: linear-gradient(135deg, #FF4B4B 0%, #FF9068 100%) !important; 
            color: white !important; /* 白字 */
            box-shadow: 0 4px 15px rgba(255, 75, 75, 0.35); /* 🔥 發光暈影 (Glow) */
            transform: scale(1.02); /* 微微放大，強調選中感 */
        }
        
        /* 強制修正選中時內層文字顏色 */
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

# --- 修正版：強制使用台灣時間 (UTC+8) 並顯示秒數 ---
def save_journal(username, content):
    # 1. 定義台灣時區 (UTC+8)
    tz_taiwan = datetime.timezone(datetime.timedelta(hours=8))
    
    # 2. 取得「現在」的台灣時間
    current_time = datetime.datetime.now(tz_taiwan)
    
    # 3. 格式化成字串 (年-月-日 時:分:秒)
    # 注意：原本只有 %H:%M，這裡加上 :%S 顯示秒數，這樣就不會看起來都一樣了
    date_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
    
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
        st.markdown("### 什麼是現代數字心理學？")
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
            
    tab_pds, tab_card, tab_journal, tab_reader, tab_shop = st.tabs(["🧬 天賦運勢", "🔮 每日指引卡", "📔 日記", "📜 讀者專屬", "🛒 商城"])
    
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
        # --- V5 優化：沈浸式日記體驗 ---
        
        # 1. 標題區：給予一點儀式感
        st.markdown("#### 📔 此刻，與自己對話")
        
        # 2. 將「技術性設定」藏起來 (Expander)
        # 只有當使用者想「補寫」或「人在國外」時，才需要點開這裡
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
            
            # 計算時間
            offset_hours = timezone_options[selected_zone]
            user_tz = datetime.timezone(datetime.timedelta(hours=offset_hours))
            now_local = datetime.datetime.now(user_tz)
            
            with c_date:
                pick_date = st.date_input("📅 日期", value=now_local.date())
            with c_time:
                pick_time = st.time_input("⏰ 時間", value=now_local.time())

        # 3. 核心書寫區 (乾淨、無干擾)
        # 如果使用者沒展開上面的設定，這裡預設就是當下的台灣時間
        if 'pick_date' not in locals(): # 防呆
            pick_date = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date()
            pick_time = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).time()
            selected_zone = "🇹🇼 台灣/中國 (UTC+8)"

        with st.form("j_form", clear_on_submit=True): # clear_on_submit=True 讓寫完後自動清空
            txt = st.text_area("✍️", height=200, placeholder="親愛的，今天發生了什麼事？你的感覺如何？...\n(這裡是一個安全的空間，請放心書寫)")
            
            # 透過 columns 讓按鈕縮小一點，靠右一點
            c_null, c_btn = st.columns([3, 1])
            with c_btn:
                submitted = st.form_submit_button("💾 收藏這份記憶", use_container_width=True)
            
            if submitted:
                if not txt:
                    st.warning("⚠️ 內容是空的，試著寫下一個字也好。")
                else:
                    final_dt = datetime.datetime.combine(pick_date, pick_time)
                    date_str = final_dt.strftime("%Y-%m-%d %H:%M:%S")
                    
                    data = {"username": st.session_state.username, "content": txt, "date_str": date_str}
                    try:
                        supabase.table("journals").insert(data).execute()
                        st.success(f"✅ 已保存！ ({date_str})")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"儲存失敗: {e}")
        
        # 4. 歷史紀錄 (優化顯示)
        st.divider()
        st.markdown("##### 🕰️ 回憶長廊")
        history = get_journals(st.session_state.username)
        if history:
            for date_str, content in history:
                # 使用 expander 讓長篇日記預設收合，畫面更清爽
                with st.expander(f"📅 {date_str} - {content[:10]}...", expanded=False):
                    st.markdown(content)
                    st.caption(f"記錄於: {date_str}")
        else:
            st.caption("這裡目前一片空白，等待你的第一筆紀錄...")

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