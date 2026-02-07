import datetime
import os
import time
import requests
import streamlit as st
from supabase import create_client, Client

#==========================================
# 1. 核心設定與模組匯入
#==========================================
try:
    # 這裡加入剛剛建立的 ads_manager
    from views import tab_life_map, tab_divination, tab_member, tab_family_matrix, tab_journal, auth_ui, ads_manager
except ImportError:
    tab_life_map = tab_divination = tab_member = tab_family_matrix = tab_journal = auth_ui = ads_manager = None
#==========================================
# 2. 持久化登入助手 (使用 Query Params)
#==========================================
def _persist_login(username):
    st.query_params["p_user"] = username

def _clear_persist_login():
    if "p_user" in st.query_params:
        del st.query_params["p_user"]

def _try_restore_login():
    p_user = st.query_params.get("p_user")
    if p_user and not st.session_state.get("logged_in"):
        st.session_state.logged_in = True
        st.session_state.username = p_user
        st.session_state.user = {"email": "persisted_user"}
        return True
    return False

# app.py 中的 show_member_app 函式內
def show_member_app():

    # 左側紫色欄位
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 登出系統", width="stretch"):
            _clear_persist_login()
            st.session_state.clear()
            st.rerun()

    # 檢查是否需要綁定 Email (延用 Composer 大規模改編中的邏輯)
    needs_bind = False
    if "user" in st.session_state and st.session_state.user.get("email") == "persisted_user":
        # 這裡檢查資料庫，若 email 欄位為空則 needs_bind = True
        needs_bind = True 

    if needs_bind:
        st.warning("⚠️ **帳號安全提醒：** 您目前僅使用 LINE 快速登入。請前往「會員中心」綁定 Email 信箱，確保您的親友檔案與日記數據永不遺失。")
        if st.button("立即前往綁定", width="stretch"):
            # 切換到會員中心分頁
            st.session_state.current_tab = 5 # 假設會員中心是第 5 個 Tab
            st.rerun()

#==========================================
# 3. 資料庫與 LINE 函式
#==========================================
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

def get_line_auth_url():
    cid = os.environ.get("LINE_CHANNEL_ID") or st.secrets.get("line", {}).get("channel_id")
    if not cid: return None
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redir}&state=pds&scope=profile%20openid%20email"

def get_line_profile_name(code):
    token_url = "https://api.line.me/oauth2/v2.1/token"
    cid = os.environ.get("LINE_CHANNEL_ID") or st.secrets.get("line", {}).get("channel_id")
    csecret = os.environ.get("LINE_CHANNEL_SECRET") or st.secrets.get("line", {}).get("channel_secret")
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")

    if not csecret or not cid: return None, "缺少 LINE 設定"

    try:
        res = requests.post(token_url, data={
            "grant_type": "authorization_code", "code": code, "redirect_uri": redir,
            "client_id": cid, "client_secret": csecret
        })
        if res.status_code != 200: return None, "Token 交換失敗"
        access_token = res.json().get("access_token")
        # ✅ 校正：修正 API 網址，移除多餘的 api.
        p_res = requests.get("https://api.line.me/v2/profile", headers={"Authorization": f"Bearer {access_token}"})
        if p_res.status_code != 200: return None, "取得資料失敗"
        return p_res.json().get("displayName"), None
    except Exception as e: return None, str(e)

#==========================================
# 4. 主程式介面
#==========================================
def show_member_app():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        # ✅ 校正：使用 2026 最新語法 width="stretch"
        if st.button("🚪 登出系統", width="stretch"):
            _clear_persist_login()
            st.session_state.clear()
            st.rerun()
            
    st.markdown(f"#### Hi, {st.session_state.username} | 九能量導航系統")
    tabs = st.tabs(["🏠 首頁", "🧬 人生地圖", "🔮 宇宙指引", "👨‍👩‍👧‍👦 家族矩陣", "📔 靈魂日記", "👤 會員中心"])
    
    with tabs[0]: 
        st.subheader(f"歡迎回到能量中心")
    # 呼叫廣告模組
    if 'ads_manager' in locals() or 'ads_manager' in globals():
        ads_manager.render_home_ads()    
    with tabs[1]: 
        if tab_life_map: tab_life_map.render()
    with tabs[2]: 
        if tab_divination: tab_divination.render_divination_view()
    with tabs[3]: 
        if tab_family_matrix: tab_family_matrix.render()
    with tabs[4]: 
        if tab_journal: tab_journal.render()
    with tabs[5]: 
        if tab_member: tab_member.render()

#==========================================
# 5. 程式入口 (守門員邏輯)
#==========================================
if __name__ == "__main__":
    st.set_page_config(page_title="九能量導航", page_icon="⚛️", layout="wide")

    # ✅ 校正：隱藏右上角紅框按鈕與工具列
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .welcome-title { font-size: 42px; font-weight: 900; color: #2c3e50; margin-top: 20px; }
        .line-btn { display: flex; align-items: center; justify-content: center; background-color: #06C755; color: white !important; text-decoration: none; font-weight: bold; padding: 15px; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

    # 注入 PWA 標籤
    from streamlit.components.v1 import html as components_html
    components_html("""
         <script>
          const link = document.createElement('link');
          link.rel = 'manifest'; link.href = 'manifest.json';
          document.head.appendChild(link);
          const appleIcon = document.createElement('link');
          appleIcon.rel = 'apple-touch-icon'; appleIcon.href = 'assets/logo.png';
          document.head.appendChild(appleIcon);
         </script>
    """, height=0)

    # A. 初始化狀態
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "username" not in st.session_state: st.session_state.username = ""

    # B. 校正順序：優先處理 LINE 回調驗證
    if "code" in st.query_params:
        code = st.query_params["code"]
        del st.query_params["code"] # 立即清除，防止無限重整
        with st.spinner("能量驗證中..."):
            name, err = get_line_profile_name(code)
            if name:
                st.session_state.logged_in = True
                st.session_state.username = name
                _persist_login(name)
                st.rerun()
            else:
                st.error(f"登入失敗: {err}")

    # C. 若無驗證代碼，嘗試還原持久化狀態
    if not st.session_state.logged_in:
        if _try_restore_login():
            st.rerun()

    # D. 介面分流
    if st.session_state.logged_in:
        show_member_app()
    else:
        # 顯示漂亮的首頁
        col1, _, col2 = st.columns([6, 1, 4])
        with col1:
            st.markdown('<div class="welcome-title">歡迎來到<br>九能量導航</div>', unsafe_allow_html=True)
            st.image("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop", width="stretch")
        
        with col2:
            st.write(""); st.write("")
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'<a href="{auth_url}" target="_self" class="line-btn">LINE 快速登入 / 註冊</a>', unsafe_allow_html=True)
            
            with st.expander("📧 使用 Email 登入/註冊"):
                if auth_ui: auth_ui.render_auth()