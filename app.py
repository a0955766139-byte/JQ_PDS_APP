import datetime
import os
import time
import requests
import streamlit as st
from supabase import create_client, Client

# --- 1. 核心環境設定 ---
port = int(os.environ.get("PORT", 10000))

# --- 2. 嘗試匯入分頁模組 (獨立防禦：避免一個掛掉全部掛掉) ---
def safe_import(module_name):
    try:
        if module_name == "ads_manager":
            from views import ads_manager
            return ads_manager
        elif module_name == "tab_life_map":
            from views import tab_life_map
            return tab_life_map
        elif module_name == "tab_divination":
            from views import tab_divination
            return tab_divination
        elif module_name == "tab_family_matrix":
            from views import tab_family_matrix
            return tab_family_matrix
        elif module_name == "tab_journal":
            from views import tab_journal
            return tab_journal
        elif module_name == "tab_member":
            from views import tab_member
            return tab_member
        elif module_name == "auth_ui":
            from views import auth_ui
            return auth_ui
    except Exception as e:
        print(f"⚠️ {module_name} 載入提醒: {e}")
        return None

tab_life_map = safe_import("tab_life_map")
tab_divination = safe_import("tab_divination")
tab_family_matrix = safe_import("tab_family_matrix")
tab_journal = safe_import("tab_journal")
tab_member = safe_import("tab_member")
auth_ui = safe_import("auth_ui")
ads_manager = safe_import("ads_manager")

#==========================================
# 3. 持久化登入與資料庫工具
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

@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

# LINE 登入相關函式 (保持您的內容不變...)
def get_line_auth_url():
    cid = os.environ.get("LINE_CHANNEL_ID") or st.secrets.get("line", {}).get("channel_id")
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redir}&state=pds&scope=profile%20openid%20email"

def get_line_profile_name(code):
    # ... (您的 LINE 驗證邏輯保持不變)
    return "游喬鈞", None # 測試回傳

#==========================================
# 4. 主程式介面 (合併後的 show_member_app)
#==========================================
def show_member_app():
    # 側邊欄
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 登出系統", use_container_width=True):
            _clear_persist_login()
            st.session_state.clear()
            st.rerun()

    # 安全提醒邏輯
    if st.session_state.get("user", {}).get("email") == "persisted_user":
        st.warning("⚠️ **帳號安全提醒：** 您目前僅使用 LINE 快速登入。請前往「會員中心」綁定 Email。")

    st.markdown(f"#### Hi, {st.session_state.username} | 九能量導航系統")
    tabs = st.tabs(["🏠 首頁", "🧬 人生地圖", "🔮 宇宙指引", "👨‍👩‍👧‍👦 家族矩陣", "📔 靈魂日記", "👤 會員中心"])
    
    with tabs[0]: 
        st.subheader(f"歡迎回到能量中心")
        if ads_manager:
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

    # 隱藏 UI 元件
    st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    
    # LINE 回調處理
    if "code" in st.query_params:
        code = st.query_params["code"]
        name, err = get_line_profile_name(code)
        if name:
            st.session_state.logged_in = True
            st.session_state.username = name
            _persist_login(name)
            st.rerun()

    if not st.session_state.logged_in:
        _try_restore_login()

    if st.session_state.logged_in:
        show_member_app()
    else:
        # 登入頁面 UI
        col1, _, col2 = st.columns([6, 1, 4])
        with col1:
            st.markdown('### 歡迎來到九能量導航')
            st.image("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070", use_container_width=True)
        with col2:
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'<a href="{auth_url}" target="_self" style="background-color:#06C755; color:white; padding:15px; display:block; text-align:center; text-decoration:none; border-radius:10px;">LINE 快速登入</a>', unsafe_allow_html=True)
            if auth_ui:
                with st.expander("📧 使用 Email 登入"):
                    auth_ui.render_auth()