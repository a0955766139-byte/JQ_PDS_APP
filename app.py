import os
import streamlit as st
import datetime
import time
import requests
from supabase import create_client, Client

# ==============================================================================
# 0. 模組化匯入區 (Module Imports)
# ==============================================================================
try:
    from views import tab_life_map
    from views import tab_family_matrix  # ✅ 新增：家族矩陣模組
    from views import tab_member         # 會員中心
    # from views import tab_home         # (註解：如果你還沒建立 tab_home.py，先不要打開這行，以免報錯)
    from views import tab_divination     # 宇宙指引
except ImportError as e:
    st.error(f"⚠️ 核心模組匯入失敗：{e}")

# ==============================================================================
# 1. 基礎設定與 Session 初始化
# ==============================================================================
st.set_page_config(page_title="九能量導航", page_icon="❤️‍🔥", layout="wide")

if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = "" 
if 'display_name' not in st.session_state: st.session_state.display_name = "" 
if 'user_profile' not in st.session_state: st.session_state.user_profile = None

# ==============================================================================
# 2. Global CSS 全局樣式 (視覺防護罩)
# ==============================================================================
st.markdown("""
    <style>
        /* 隱藏預設工具欄與頁尾 */
        [data-testid="stToolbar"] {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        
        /* Tab 分頁美化 */
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
        
        /* LINE 按鈕樣式 (綠色) */
        .line-btn {
            display: flex; align-items: center; justify-content: center;
            width: 100%; background-color: #06C755; color: white !important; 
            padding: 12px 0; border-radius: 8px; text-decoration: none; 
            font-weight: bold; font-family: sans-serif; margin-bottom: 15px; 
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: background 0.3s;
        }
        .line-btn:hover { background-color: #05b34c; color: white !important; text-decoration: none; }
        .line-btn img { margin-right: 10px; height: 24px; width: 24px; filter: brightness(0) invert(1); }

        /* 日記樣式 */
        .journal-entry { background: white; padding: 15px; border-radius: 10px; border-left: 4px solid #6a3093; margin-bottom: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    </style>
""", unsafe_allow_html=True)

# ==============================================================================
# 3. 資料庫連線與驗證邏輯
# ==============================================================================
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        except: pass
    if url and key:
        try: return create_client(url, key)
        except Exception: return None
    return None

supabase = init_connection()

def get_line_auth_url():
    cid = os.environ.get("LINE_CHANNEL_ID")
    if not cid:
        try: cid = st.secrets["line"]["channel_id"]
        except: pass
    if not cid: return None
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redir}&state=pds&scope=profile%20openid%20email"

def get_line_profile_name(code):
    token_url = "https://api.line.me/oauth2/v2.1/token"
    cid = os.environ.get("LINE_CHANNEL_ID")
    csecret = os.environ.get("LINE_CHANNEL_SECRET")
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")

    if not csecret:
        try: csecret = st.secrets["line"]["channel_secret"]
        except: pass
    if not csecret: return None, "缺少 Secret"

    payload = {"grant_type": "authorization_code", "code": code, "redirect_uri": redir, "client_id": cid, "client_secret": csecret}
    try:
        res = requests.post(token_url, data=payload)
        access_token = res.json().get("access_token")
        p_res = requests.get("https://api.line.me/v2/profile", headers={"Authorization": f"Bearer {access_token}"})
        return p_res.json().get("displayName"), None
    except Exception as e: return None, str(e)

def handle_line_callback():
    if "code" in st.query_params:
        code = st.query_params["code"]
        line_name, error = get_line_profile_name(code)
        if line_name:
            st.session_state.logged_in = True
            st.session_state.username = line_name 
            st.query_params.clear()
            st.rerun()

def save_journal(username, content):
    if not supabase: return False
    try:
        supabase.table("journals").insert({"username": username, "content": content, "date_str": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}).execute()
        return True
    except Exception: return False

def get_journals(username):
    if not supabase: return []
    try:
        res = supabase.table("journals").select("content, date_str").eq("username", username).order("created_at", desc=True).limit(5).execute()
        return [(item['content'], item['date_str']) for item in res.data]
    except Exception: return []

# ==============================================================================
# 4. 介面渲染 (Login & App)
# ==============================================================================
def show_login_page():
    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        st.markdown("# 👁️ 歡迎來到九能量導航")
        st.markdown("### 探索你到底是什麼模樣，解開生命的原始設定。")
        st.image("https://images.unsplash.com/photo-1531306728370-e2ebd9d7bb99?q=80&w=2400&auto=format&fit=crop", use_container_width=True)
    with c2:
        with st.container(border=True):
            st.subheader("🔐 會員專區")
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'''<a href="{auth_url}" target="_self" class="line-btn"><img src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg">使用 LINE 一鍵登入</a>''', unsafe_allow_html=True)
            st.text_input("帳號 (傳統登入功能籌備中)", disabled=True)

def show_member_app():
    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # Main Area
    st.markdown(f"**Hi, {st.session_state.username}** | 九能量導航系統")
    
    # 定義六大分頁 (這裡修正了重複定義的問題，只保留這一組)
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏠 首頁",          # 原本是 "人聲地圖" 重複，我建議 Tab1 當作 Dashboard 或首頁
        "🧬 人生地圖", 
        "🔮 宇宙指引", 
        "👨‍👩‍👧‍👦 家族矩陣",     # 這裡換上新功能
        "📔 靈魂日記", 
        "👤 會員中心"
    ])
    
    # === Tab 1: 首頁 (Dashboard) ===
    with tab1: 
        # 如果你有 tab_home.py 可以用 tab_home.render()
        # 目前先顯示簡單歡迎
        st.subheader(f"歡迎回到能量中心，{st.session_state.username}")
        st.info("請從上方分頁選擇您要進行的探索。")

    # === Tab 2: 人生地圖 ===
    with tab2: tab_life_map.render()

    # === Tab 3: 宇宙指引 ===
    with tab3: tab_divination.render_divination_view()

    # === Tab 4: 家族矩陣 (✅ 這裡呼叫五世的新傑作) ===
    with tab4: 
        # 呼叫 views/tab_family_matrix.py 裡的 render 函式
        try:
            tab_family_matrix.render() 
        except Exception as e:
            st.error(f"家族矩陣渲染錯誤: {e}")

    # === Tab 5: 靈魂日記 ===
    with tab5:
        st.markdown("### 📔 靈魂書寫")
        with st.form("journal_form"):
            j_content = st.text_area("寫下你的心情、覺察...", height=150)
            if st.form_submit_button("💾 保存日記"): 
                if save_journal(st.session_state.username, j_content):
                    st.success("日記已保存"); time.sleep(1); st.rerun()
        journals = get_journals(st.session_state.username)
        for j in journals: 
            st.markdown(f"<div class='journal-entry'><small>{j[1]}</small><br>{j[0]}</div>", unsafe_allow_html=True)
    
    # === Tab 6: 會員中心 ===
    with tab6: 
        tab_member.render()

# ==============================================================================
# 5. 程式進入點
# ==============================================================================
if __name__ == "__main__":
    if not st.session_state.logged_in:
        handle_line_callback()
        if not st.session_state.logged_in: show_login_page()
    else: show_member_app()