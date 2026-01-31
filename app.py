import os
import streamlit as st
import datetime
import time
import random
from supabase import create_client, Client

# --- 匯入 View 模組 ---
try:
    from views import tab_life_map
except ImportError as e:
    st.error(f"⚠️ 模組匯入失敗：{e}。請檢查 views 資料夾結構與 __init__.py 是否存在。")

# 匯入其他資源
try:
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    DIVINATION_CARDS = []

# --- 1. 基礎設定 ---
st.set_page_config(page_title="九能量導航", page_icon="❤️‍🔥", layout="wide")

# --- Session 初始化 ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'user_profile' not in st.session_state: st.session_state.user_profile = None

# --- 2. CSS 全局設定 ---
st.markdown("""
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        div[data-baseweb="tab-list"] {
            gap: 0px; background-color: #f8f9fa; padding: 8px; border-radius: 50px; 
            margin-bottom: 20px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.05);
        }
        button[data-baseweb="tab"] {
            border: none !important; border-radius: 40px; padding: 10px 25px; 
            font-size: 16px !important; color: #666; transition: all 0.3s;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, #6a3093 0%, #a044ff 100%) !important; 
            color: white !important; box-shadow: 0 4px 15px rgba(106, 48, 147, 0.3);
        }
        
        .line-btn {
            display: flex; align-items: center; justify-content: center;
            width: 100%; background-color: #06C755; color: white !important; 
            padding: 12px 0; border-radius: 8px; text-decoration: none; 
            font-weight: bold; font-family: sans-serif; margin-bottom: 15px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: background 0.3s;
        }
        .line-btn:hover { background-color: #05b34c; }
        .line-btn img { margin-right: 10px; height: 24px; width: 24px; filter: brightness(0) invert(1); }

        .divination-card { background: white; border-radius: 15px; padding: 25px; box-shadow: 0 8px 20px rgba(0,0,0,0.1); text-align: center; border: 1px solid #eee; margin-top: 10px; }
        .divination-img { width: 100%; max-height: 350px; object-fit: cover; border-radius: 12px; margin-bottom: 20px; }
        .divination-title { font-size: 26px; font-weight: bold; color: #2b3066; margin-bottom: 10px; }
        .divination-poem { font-style: italic; color: #555; margin-bottom: 20px; font-size: 18px; line-height: 1.6; }
        .divination-desc { color: #666; font-size: 16px; background: #f9f9f9; padding: 15px; border-radius: 10px; }
        .journal-entry { background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #6a3093; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# --- 3. 資料庫連線 (支援雲端環境變數) ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # 本地備援：如果環境變數沒抓到，嘗試讀取 secrets.toml
    if not url or not key:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        except: pass
        
    if url and key:
        return create_client(url, key)
    return None

supabase = init_connection()

# --- 4. 身份驗證邏輯 (修復 LINE 登入) ---
def get_line_auth_url():
    cid = os.environ.get("LINE_CHANNEL_ID")
    
    # 本地備援
    if not cid:
        try: cid = st.secrets["line"]["channel_id"]
        except: pass
    
    if not cid: return None

    # 取得 Redirect URI (優先讀取環境變數，否則使用預設)
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")
    
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redir}&state=pds&scope=profile%20openid%20email"

def handle_line_callback():
    if "code" in st.query_params:
        # 這裡為了展示，簡化處理
        st.session_state.logged_in = True
        st.session_state.username = "LINE User" 
        st.query_params.clear()
        st.rerun()

def login_user(u, p): return True if u and p else False

# --- 5. 舊有功能函式 ---
def check_db_today_draw(username):
    if not supabase: return None
    try:
        today = datetime.date.today().isoformat()
        res = supabase.table("daily_draws").select("*").eq("username", username).eq("draw_date", today).execute()
        return res.data[0] if res.data else None
    except: return None

def save_db_draw(username, card):
    if not supabase: return
    try:
        data = {"username": username, "draw_date": datetime.date.today().isoformat(), "title": card['title'], "poem": card['poem'], "desc": card['desc']}
        supabase.table("daily_draws").insert(data).execute()
    except: pass

def delete_db_today_draw(username):
    if not supabase: return
    try: supabase.table("daily_draws").delete().eq("username", username).eq("draw_date", datetime.date.today().isoformat()).execute()
    except: pass

def get_card_image(title):
    return "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=600&q=80"

def save_journal(username, content):
    if not supabase: return
    try: supabase.table("journals").insert({"username": username, "content": content, "date_str": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}).execute()
    except: pass

def get_journals(username):
    if not supabase: return []
    try:
        res = supabase.table("journals").select("content, date_str").eq("username", username).order("created_at", desc=True).limit(5).execute()
        return [(item['content'], item['date_str']) for item in res.data]
    except: return []

# --- 6. 登入頁面 ---
def show_login_page():
    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        st.markdown("# 👁️ 歡迎來到九能量導航")
        st.markdown("### 探索你到底是什麼模樣，解開生命的原始設定。")
        st.image("https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=2670&auto=format&fit=crop", use_container_width=True)
    with c2:
        with st.container(border=True):
            st.subheader("🔐 會員專區")
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'''<a href="{auth_url}" target="_self" class="line-btn"><img src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg">使用 LINE 一鍵登入</a>''', unsafe_allow_html=True)
            st.markdown("""<div style="text-align: center; color: #888; margin: 10px 0;">或是使用傳統帳號</div>""", unsafe_allow_html=True)
            tab1, tab2 = st.tabs(["登入", "找回帳號"])
            with tab1:
                u = st.text_input("帳號", key="u_log"); p = st.text_input("密碼", type="password")
                if st.button("登入系統", type="primary", use_container_width=True):
                    if login_user(u, p): st.session_state.logged_in = True; st.session_state.username = u; st.rerun()

# --- 7. 會員主程式 ---
def show_member_app():
    st.markdown(f"**Hi, {st.session_state.username}** | 九能量導航系統")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧬 人生地圖", "🔮 宇宙指引", "📔 靈魂日記", "📜 讀者專區", "🛒 能量商城"])
    
    with tab1:
        tab_life_map.render()

    with tab2:
        st.markdown("### 🔮 連結你的宇宙指引")
        saved_card = check_db_today_draw(st.session_state.username)
        if saved_card:
            st.success("✨ 今日指引已送達")
            img_url = get_card_image(saved_card['title'])
            st.markdown(f"""
            <div class="divination-card">
                <img src="{img_url}" class="divination-img">
                <div class="divination-content">
                    <div class="divination-title">{saved_card['title']}</div>
                    <div class="divination-poem">「{saved_card['poem']}」</div>
                    <div class="divination-desc">{saved_card['desc']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.checkbox("重置今日抽牌"): delete_db_today_draw(st.session_state.username); st.rerun()
        else:
            if st.button("🎴 抽取今日牌卡", type="primary", use_container_width=True):
                if DIVINATION_CARDS:
                    with st.spinner("連結宇宙中..."): time.sleep(1.5)
                    card = random.choice(DIVINATION_CARDS); save_db_draw(st.session_state.username, card); st.balloons(); st.rerun()
                else: st.warning("⚠️ 牌卡資料庫未載入")

    with tab3:
        st.markdown("### 📔 靈魂書寫")
        with st.form("journal_form"):
            j_content = st.text_area("寫下你的心情、覺察...", height=150)
            if st.form_submit_button("💾 保存日記"): 
                save_journal(st.session_state.username, j_content); st.success("日記已保存"); st.rerun()
        st.divider(); st.markdown("#### 📜 過去的篇章")
        journals = get_journals(st.session_state.username)
        if journals:
            for j in journals: st.markdown(f"""<div class='journal-entry'><div class='journal-date'>{j[1]}</div><div class='journal-content'>{j[0]}</div></div>""", unsafe_allow_html=True)
        else: st.info("目前還沒有日記...")

    with tab4: st.info("📖 這是《九能量》實體書讀者的專屬區域"); st.text_input("請輸入靈魂代碼"); st.button("🔓 解鎖內容")
    with tab5: st.success("🚧 商城系統籌備中")

# --- 8. 程式進入點 ---
if __name__ == "__main__":
    if not st.session_state.logged_in:
        handle_line_callback()
        if not st.session_state.logged_in:
            show_login_page()
    else:
        show_member_app()