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
    from views import tab_life_map, tab_divination, tab_member, tab_family_matrix, tab_journal, auth_ui
except ImportError:
    tab_life_map = tab_divination = tab_member = tab_family_matrix = tab_journal = auth_ui = None

#==========================================
# 2. 持久化登入助手 (使用 Query Params)
#==========================================
def _persist_login(username):
    # 將用戶名存入網址，下次打開時可識別
    st.query_params["p_user"] = username

def _clear_persist_login():
    if "p_user" in st.query_params:
        del st.query_params["p_user"]

def _try_restore_login():
    # 檢查網址是否有持久化參數
    p_user = st.query_params.get("p_user")
    if p_user and not st.session_state.get("logged_in"):
        st.session_state.logged_in = True
        st.session_state.username = p_user
        st.session_state.user = {"email": "persisted_user"}
        return True
    return False

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
        p_res = requests.get("https://api.api.line.me/v2/profile", headers={"Authorization": f"Bearer {access_token}"})
        return p_res.json().get("displayName"), None
    except Exception as e: return None, str(e)

#==========================================
# 4. 主程式介面
#==========================================
def show_member_app():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 登出系統", use_container_width=True):
            _clear_persist_login()
            st.session_state.clear()
            st.rerun()
            
    st.markdown(f"#### Hi, {st.session_state.username} | 九能量導航系統")
    tabs = st.tabs(["🏠 首頁", "🧬 人生地圖", "🔮 宇宙指引", "👨‍👩‍👧‍👦 家族矩陣", "📔 靈魂日記", "👤 會員中心"])
    
    with tabs[0]: st.subheader(f"歡迎回到能量中心")
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


    # 在 st.set_page_config 之後加入
    from streamlit.components.v1 import html as components_html

    components_html("""
         <script>
           // 1. 插入 Web Manifest 連結
          const link = document.createElement('link');
         link.rel = 'manifest';
           link.href = 'manifest.json';
           document.head.appendChild(link);

          // 2. 插入 Apple Touch Icon (針對 iPhone 優化)
          const appleIcon = document.createElement('link');
          appleIcon.rel = 'apple-touch-icon';
          appleIcon.href = 'assets/logo.png';
         document.head.appendChild(appleIcon);
     </script>
    """, height=0)

    # A. 初始化狀態
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "username" not in st.session_state: st.session_state.username = ""

    # B. 嘗試自動登入
    _try_restore_login()

    # C. 處理 LINE 回調
    if "code" in st.query_params:
        code = st.query_params["code"]
        # 先清除 code 避免重複驗證
        del st.query_params["code"]
        with st.spinner("驗證中..."):
            name, err = get_line_profile_name(code)
            if name:
                st.session_state.logged_in = True
                st.session_state.username = name
                _persist_login(name)
                st.rerun()

    # D. 判斷顯示畫面
    if st.session_state.logged_in:
        show_member_app()
    else:
        # Landing Page 渲染
        st.markdown("""
        <style>
        .welcome-title { font-size: 42px; font-weight: 900; color: #2c3e50; margin-top: 20px; }
        .line-btn { display: flex; align-items: center; justify-content: center; background-color: #06C755; color: white !important; text-decoration: none; font-weight: bold; padding: 15px; border-radius: 10px; }
        /* 隱藏右上角的 Streamlit 選單按鈕 */
        #MainMenu {visibility: hidden;}
    
        /* 隱藏底部的 Streamlit 頁尾 (Made with Streamlit) */
        footer {visibility: hidden;}
    
        /* 隱藏頂部的裝飾線，讓畫面更乾淨 */
        header {visibility: hidden;}
        </style>
        """, unsafe_allow_html=True)

        col1, _, col2 = st.columns([6, 1, 4])
        with col1:
            st.markdown('<div class="welcome-title">歡迎來到<br>九能量導航</div>', unsafe_allow_html=True)
            st.image("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop", use_container_width=True)
        
        with col2:
            st.write(""); st.write("")
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'<a href="{auth_url}" target="_self" class="line-btn">LINE 快速登入 / 註冊</a>', unsafe_allow_html=True)
            
            with st.expander("📧 使用 Email 登入/註冊"):
                if auth_ui: auth_ui.render_auth()