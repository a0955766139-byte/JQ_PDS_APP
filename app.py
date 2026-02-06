import streamlit as st
import datetime
import time
import os
import requests #  LINE 溝通必要模組
from supabase import create_client, Client

#==========================================
# 1. 核心設定與模組匯入--- 嘗試匯入各個模組 (加上防呆機制) ---
#==========================================
try:
    from views import tab_life_map
except ImportError:
    tab_life_map = None

try:
    from views import tab_divination
except ImportError:
    tab_divination = None

try:
    from views import tab_member
except ImportError:
    tab_member = None

try:
    from views import tab_family_matrix
except ImportError:
    tab_family_matrix = None

try:
    from views import tab_journal
except ImportError:
    tab_journal = None

try:
    from views import auth_ui
except ImportError:
    auth_ui = None


#==========================================
# 2. 資料庫與輔助函式--- 資料庫連線 ---
#==========================================
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        except: pass
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

#==========================================
# --- [A] LINE 授權網址生成器 (出發) ---
def get_line_auth_url():
    cid = os.environ.get("LINE_CHANNEL_ID")
    if not cid:
        try: cid = st.secrets["line"]["channel_id"]
        except: pass
    if not cid: return None
    
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redir}&state=pds&scope=profile%20openid%20email"

# --- [B] LINE 回調處理器 (回來)  ---
def get_line_profile_name(code):
    token_url = "https://api.line.me/oauth2/v2.1/token"
    cid = os.environ.get("LINE_CHANNEL_ID")
    csecret = os.environ.get("LINE_CHANNEL_SECRET")
    
    # 嘗試從 secrets 讀取
    if not cid:
        try: cid = st.secrets["line"]["channel_id"]
        except: pass
    if not csecret:
        try: csecret = st.secrets["line"]["channel_secret"]
        except: pass
        
    redir = os.environ.get("LINE_REDIRECT_URI", "https://jq-pds-app.onrender.com")

    if not csecret or not cid: return None, "缺少 LINE Channel ID 或 Secret 設定"

    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redir,
        "client_id": cid,
        "client_secret": csecret
    }
    
    try:
        # 1. 用 code 換 token
        res = requests.post(token_url, data=payload)
        if res.status_code != 200:
            return None, f"Token 交換失敗: {res.text}"
            
        access_token = res.json().get("access_token")
        
        # 2. 用 token 換個人資料
        p_res = requests.get("https://api.line.me/v2/profile", headers={"Authorization": f"Bearer {access_token}"})
        if p_res.status_code != 200:
            return None, "無法取得個人資料"
            
        return p_res.json().get("displayName"), None
    except Exception as e:
        return None, str(e)

#==========================================
# --- 3. 日記功能函式 ---
#==========================================
def save_journal(username, content):
    if not supabase: return False
    try:
        supabase.table("journals").insert({
            "user_id": username,
            "content": content,
            "created_at": datetime.datetime.now().isoformat()
        }).execute()
        return True
    except: return False

def get_journals(username):
    if not supabase: return []
    try:
        res = supabase.table("journals").select("*").eq("user_id", username).order("created_at", desc=True).execute()
        return [(r['content'], r['created_at'][:10]) for r in res.data]
    except: return []

#==========================================
# 4. 主程式介面 (登入後的首頁)
#==========================================
def show_member_app():
    #==========================================
    # 登入後的側邊欄
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
            
    #==========================================
    # 頂部標題
    st.markdown(f"#### Hi, {st.session_state.username} | 九能量導航系統")
    #==========================================
    # 頂部標題
    t_home, t_map, t_uni, t_fam, t_diary, t_mem = st.tabs([
        "🏠 首頁",
         "🧬 人生地圖", 
         "🔮 宇宙指引", 
         "👨‍👩‍👧‍👦 家族矩陣",
          "📔 靈魂日記",
           "👤 會員中心"
    ])
    
    
    #==========================================
    # === Tab 0: 首頁 ===
    with t_home:
        st.subheader(f"歡迎回到能量中心，{st.session_state.username}")
        #==========================================
        # 中富科技白金質感廣告
        st.markdown("""
        <style>
            .partner-card {
                background: #ffffff; border: 1px solid #f5f5f5; border-radius: 16px; padding: 30px;
                margin-bottom: 25px; box-shadow: 0 15px 40px rgba(0,0,0,0.05); position: relative; overflow: hidden;
                transition: transform 0.3s ease;
            }
            .partner-card:hover { transform: translateY(-5px); }
            .partner-card::before { 
                content: ""; position: absolute; top: 0; left: 0; right: 0; height: 6px;
                background: linear-gradient(90deg, #D4AF37, #F7E98D, #D4AF37);
            }
            .partner-badge {
                background: linear-gradient(135deg, #D4AF37 0%, #C5A028 100%); color: white;
                padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: bold;
                display: inline-block; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(212, 175, 55, 0.3);
            }
            .partner-title { color: #2c3e50; font-size: 24px; font-weight: 800; margin-bottom: 8px; }
            .award-text { color: #D4AF37; font-size: 14px; font-weight: bold; margin-bottom: 15px; }
            a { text-decoration: none; }
        </style>
        <div class="partner-card">
            <div class="partner-badge">🏆 OFFICIAL PARTNER</div>
            <div class="partner-title">🌿 台灣中富生物科技</div>
            <div class="award-text">★ 榮獲 2025 Monde Selection 世界品質評鑑大賞 金獎</div>
            <p style="color:#555; font-size:15px; line-height:1.8; margin-bottom: 20px;">
                <b>「美，源自於健康的修護。」</b><br>
                九能量為您導航人生，中富生技為您守護青春。<br>
                嚴選台灣珍寶<b>「山芙蓉」</b>，打造醫療級的極致修護力。<br>
                <span style="color:#888; font-size:13px;">(魔立奇肌 x G.U治优 系列)</span>
            </p>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                 <a href="https://www.zhongfu-bcl.com.tw/" target="_blank" style="flex: 1; background: #2c3e50; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 14px;">✨ 探索獲獎商品 (官網)</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
# === Tab 1: 人生地圖 (個人專屬) ===
    with t_map:
        if tab_life_map: tab_life_map.render()
        else: st.error("模組載入失敗")

# === Tab 2: 宇宙指引 ===
    with t_uni:
        if tab_divination: tab_divination.render_divination_view()
        else: st.info("🔮 宇宙連線中...")

# === Tab 3: 家族矩陣 (親友庫管理 ) ===
    with t_fam: 
        if tab_family_matrix:
            try: tab_family_matrix.render() 
            except Exception as e: st.error(f"家族矩陣渲染錯誤: {e}")
        else: st.info("👨‍👩‍👧‍👦 家族模組載入中...")

# === Tab 4: 靈魂日記 ===
    with t_diary:
        if tab_journal:
            try:
                tab_journal.render()
            except Exception as e:
                st.error(f"靈魂日記模組錯誤：{e}")
        else:
            st.markdown("### 📔 靈魂書寫")
            with st.form("journal_form"):
                j_content = st.text_area("寫下你的心情...", height=150)
                if st.form_submit_button("💾 保存日記"):
                    if save_journal(st.session_state.username, j_content):
                        st.success("日記已保存")
                        time.sleep(1)
                        st.rerun()
            for j in get_journals(st.session_state.username):
                st.markdown(f"<div class='journal-entry'><small>{j[1]}</small><br>{j[0]}</div>", unsafe_allow_html=True)

# === Tab 5: 會員中心 ===
    with t_mem:
        if tab_member: tab_member.render()
        else: st.error("會員模組載入失敗")

#==========================================
# 4. 程式入口 (Landing Page & Callback Handler)
#==========================================
if __name__ == "__main__":
    st.set_page_config(page_title="九能量導航", page_icon="⚛️", layout="wide")

    # --- [A] 初始化 Session State ---
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "username" not in st.session_state:
        st.session_state.username = ""

    # --- [B] 優先處理 LINE 回調邏輯 (LINE 登入通道) ---
    if "code" in st.query_params:
        with st.spinner("正在驗證 LINE 授權..."):
            code = st.query_params["code"]
            line_name, error_msg = get_line_profile_name(code)
            
            if line_name:
                st.session_state.logged_in = True
                st.session_state.user = {"email": "line_user"} # 模擬一個 user 物件
                st.session_state.username = line_name
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"LINE 登入失敗：{error_msg}")

    # --- [C] 核心守門員：判斷是否進入 App ---
    # 邏輯：如果有 'user' (Email登入) 或 'logged_in' (LINE登入) 則顯示會員內容
    if st.session_state.user or st.session_state.logged_in:
        show_member_app()
    
    else:
        # 尚未登入：顯示 Auth UI (包含 Email 登入/註冊 + LINE 按鈕)
        if auth_ui:
            # 這裡呼叫我們上一用 views/auth_ui.py 做的介面
            auth_ui.render_auth() 
            
            # [選用] 如果您希望在 Email 登入下方保留 LINE 按鈕，可以加在這裡
            st.divider()
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'''
                <div style="text-align: center;">
                    <p style="color:#666; font-size:0.9em;">或是使用社群帳號快速登入</p>
                    <a href="{auth_url}" target="_self" style="
                        display: inline-flex; align-items: center; justify-content: center;
                        background-color: #06C755; color: white; text-decoration: none;
                        font-weight: bold; padding: 10px 20px; border-radius: 8px;
                        box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
                        <img src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg" 
                        style="width: 20px; height: 20px; margin-right: 8px; filter: brightness(0) invert(1);">
                        LINE 登入
                    </a>
                </div>
                ''', unsafe_allow_html=True)
        else:
            st.error("找不到 views/auth_ui.py，請確認檔案是否存在。")