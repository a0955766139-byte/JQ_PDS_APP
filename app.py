import os
import streamlit as st
import datetime
import time
import random
from supabase import create_client, Client
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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

# --- 3. 會員系統功能 (含救援機制) ---

def register_user(username, password, email):
    """註冊新用戶"""
    try:
        # 檢查帳號
        check = supabase.table("users").select("username").eq("username", username).execute()
        if check.data:
            return False, "❌ 這個帳號已經有人用了，請換一個！"
        # 檢查 Email (避免重複註冊)
        check_email = supabase.table("users").select("email").eq("email", email).execute()
        if check_email.data:
            return False, "❌ 這個 Email 已經註冊過了，請直接登入或找回帳號。"
    except Exception as e:
        return False, f"連線檢查失敗: {e}"

    data = {"username": username, "password": password, "email": email}
    try:
        supabase.table("users").insert(data).execute()
        return True, "✅ 註冊成功！請切換到「登入」頁籤登入。"
    except Exception as e:
        return False, f"註冊失敗: {e}"

def login_user(username, password):
    """驗證登入"""
    try:
        response = supabase.table("users").select("*").eq("username", username).eq("password", password).execute()
        if response.data:
            return True
        else:
            return False
    except Exception:
        return False

def find_username(email):
    """忘記帳號：用 Email 找回"""
    try:
        response = supabase.table("users").select("username").eq("email", email).execute()
        if response.data:
            return True, response.data[0]["username"]
        else:
            return False, "找不到這個 Email 的註冊資料。"
    except Exception as e:
        return False, str(e)

def reset_password(username, email, new_password):
    """忘記密碼：驗證帳號+Email後重設"""
    try:
        # 1. 先驗證身分 (帳號 + Email 是否匹配)
        check = supabase.table("users").select("*").eq("username", username).eq("email", email).execute()
        if not check.data:
            return False, "❌ 帳號與 Email 不匹配，無法重設。"
        
        # 2. 更新密碼
        # 注意：Supabase 更新資料需要指定條件 (eq)
        supabase.table("users").update({"password": new_password}).eq("username", username).execute()
        return True, "✅ 密碼重設成功！請使用新密碼登入。"
    except Exception as e:
        return False, f"重設失敗: {e}"

def send_email_otp(to_email, otp_code):
    """發送驗證碼到使用者的 Gmail"""
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    # 從 secrets 讀取帳密
    sender_email = st.secrets["email"]["sender"]
    sender_password = st.secrets["email"]["password"]

    subject = "【喬鈞心學】密碼重設驗證碼"
    body = f"""
    親愛的會員您好：
    
    我們收到了您的密碼重設請求。
    您的驗證碼是：【 {otp_code} 】
    
    此驗證碼有效期限為 5 分鐘，請勿將此代碼告訴任何人。
    
    若您未申請重設密碼，請忽略此信。
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, to_email, msg.as_string())
        server.quit()
        return True, "📧 驗證信已發送！請去信箱收信。"
    except Exception as e:
        return False, f"寄信失敗: {e}"

# --- 頁面視圖 ---

def show_login_page():
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
            st.header("🔐 會員專區")
            # 🔥 新增第三個分頁：救援 (SOS) 🔥
            tab1, tab2, tab3 = st.tabs(["登入", "註冊新帳號", "🆘 忘記帳密"])
            
            # --- 1. 登入 ---
            with tab1:
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
                    else:
                        st.error("帳號不存在或密碼錯誤")
            
            # --- 2. 註冊 ---
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
                        success, msg = register_user(new_u, new_p, email)
                        if success:
                            st.success(msg)
                        else:
                            st.error(msg)

            # --- 3. 救援 (找回帳密) ---
            with tab3:
                st.write("")
                mode = st.radio("協助項目", ["找回帳號", "重設密碼 (Email驗證)"])
                st.divider()
                
                if mode == "找回帳號":
                    # (這部分保持原本的邏輯，或你要改成寄信也可以)
                    email = st.text_input("輸入註冊 Email", key="find_u")
                    if st.button("🔍 查詢"):
                        found, res = find_username(email) # 假設你還有保留這個函式
                        if found: st.info(f"您的帳號是：{res}") # 比較安全的做法其實也是寄信告知
                        else: st.error(res)

                elif mode == "重設密碼 (Email驗證)":
                    # 初始化 Session State 來存驗證碼和時間
                    if 'otp_code' not in st.session_state: st.session_state.otp_code = None
                    if 'otp_email' not in st.session_state: st.session_state.otp_email = None
                    if 'last_send_time' not in st.session_state: st.session_state.last_send_time = 0
                    if 'is_verified' not in st.session_state: st.session_state.is_verified = False

                    # 步驟 1: 發送驗證碼
                    if not st.session_state.is_verified:
                        email_input = st.text_input("請輸入您的註冊 Email", key="rst_email")
                        
                        if st.button("📩 發送驗證碼"):
                            # 1. 檢查冷卻時間 (5分鐘 = 300秒)
                            current_time = time.time()
                            if current_time - st.session_state.last_send_time < 300:
                                wait_time = 300 - int(current_time - st.session_state.last_send_time)
                                st.warning(f"⏳ 請勿頻繁發送，請再等待 {wait_time} 秒。")
                            else:
                                # 2. 檢查 Email 是否存在於資料庫
                                check = supabase.table("users").select("username").eq("email", email_input).execute()
                                if not check.data:
                                    st.error("❌ 找不到這個 Email，請確認是否已註冊。")
                                else:
                                    # 3. 生成 6 位數驗證碼
                                    code = str(random.randint(100000, 999999))
                                    
                                    # 4. 寄信
                                    success, msg = send_email_otp(email_input, code)
                                    if success:
                                        st.session_state.otp_code = code # 暫存在 Session
                                        st.session_state.otp_email = email_input
                                        st.session_state.last_send_time = current_time # 更新發送時間
                                        st.success(msg)
                                    else:
                                        st.error(msg)
                        
                        # 步驟 2: 輸入驗證碼
                        if st.session_state.otp_code:
                            st.info("驗證碼已寄出，請檢查您的 Gmail (包含垃圾郵件匣)")
                            user_code = st.text_input("輸入 6 位數驗證碼", key="u_code")
                            if st.button("✅ 驗證身分"):
                                if user_code == st.session_state.otp_code:
                                    st.success("驗證成功！請設定新密碼。")
                                    st.session_state.is_verified = True
                                    st.rerun()
                                else:
                                    st.error("❌ 驗證碼錯誤")
                    
                    # 步驟 3: 重設密碼 (只有驗證通過才會顯示)
                    else:
                        st.success(f"身分確認無誤 ({st.session_state.otp_email})")
                        new_pwd = st.text_input("設定新密碼", type="password", key="new_p_final")
                        confirm_pwd = st.text_input("再次輸入新密碼", type="password", key="cfm_p_final")
                        
                        if st.button("💾 儲存新密碼"):
                            if new_pwd != confirm_pwd:
                                st.error("兩次密碼不一致")
                            else:
                                # 更新資料庫
                                try:
                                    supabase.table("users").update({"password": new_pwd}).eq("email", st.session_state.otp_email).execute()
                                    st.balloons()
                                    st.success("🎉 密碼修改成功！請重新登入。")
                                    # 清除狀態
                                    st.session_state.is_verified = False
                                    st.session_state.otp_code = None
                                    time.sleep(2)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"更新失敗: {e}")
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