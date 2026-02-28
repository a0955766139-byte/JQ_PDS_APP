import datetime
import os
import time
import requests
import streamlit as st
from supabase import create_client, Client

# ==========================================
# 0. 頁面設定 (必須是全站第一個執行的 Streamlit 指令)
# ==========================================
st.set_page_config(page_title="九能量導航", page_icon="logo.jpg", layout="wide", initial_sidebar_state="expanded")

# 隱藏 UI 浮水印元件
st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

# ==========================================
# 1. 核心環境設定 & 模組安全匯入
# ==========================================
port = int(os.environ.get("PORT", 10000))

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
        # 這裡改成 warning，避免 error 區塊太大影響視覺
        st.warning(f"⚠️ {module_name} 載入延遲: {e}")
    return None

tab_life_map = safe_import("tab_life_map")
tab_divination = safe_import("tab_divination")
tab_family_matrix = safe_import("tab_family_matrix")
tab_journal = safe_import("tab_journal")
tab_member = safe_import("tab_member")
auth_ui = safe_import("auth_ui")
ads_manager = safe_import("ads_manager")

def get_secret_value(section: str, key: str, default=None):
    env_key = f"{section}_{key}".upper()
    value = os.environ.get(env_key)
    if value: return value
    return st.secrets.get(section, {}).get(key, default)

# ==========================================
# 2. 持久化登入與資料庫工具
# ==========================================
def _persist_login(user_id):
    params = dict(st.query_params)
    params["p_user"] = str(user_id)
    st.query_params = params

def _clear_persist_login():
    params = dict(st.query_params)
    params.pop("p_user", None)
    st.query_params = params

def _try_restore_login():
    p_user_id = st.query_params.get("p_user") 
    if p_user_id and not st.session_state.get("logged_in"):
        try:
            res = supabase.table("users").select("*").eq("line_user_id", p_user_id).execute()
            if res.data:
                user_profile = res.data[0]
                st.session_state.logged_in = True
                st.session_state.line_user_id = p_user_id 
                st.session_state.username = user_profile.get('username') or "能量導航員"
                st.session_state.user_profile = user_profile
                return True
            else:
                _clear_persist_login()
                return False
        except Exception as e:
            print(f"登入還原失敗: {e}")
            return False
    return False

@st.cache_resource
def init_connection():
    url = get_secret_value("supabase", "url")
    key = get_secret_value("supabase", "key")
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

# --- LINE 登入相關函式 ---
def get_line_auth_url():
    cid = get_secret_value("line", "channel_id")
    redir = get_secret_value("line", "redirect_uri")
    if not cid or not redir: return None
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redir}&state=pds&scope=profile%20openid%20email"

def get_line_profile_name(code):
    try:
        token_url = "https://api.line.me/oauth2/v2.1/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": get_secret_value("line", "redirect_uri"),
            "client_id": get_secret_value("line", "channel_id"),
            "client_secret": get_secret_value("line", "channel_secret")
        }
        res = requests.post(token_url, headers=headers, data=data).json()
        
        id_token = res.get("id_token")
        if not id_token: return None, f"Token 獲取失敗: {res.get('error_description')}"
            
        profile_url = "https://api.line.me/v2/profile"
        auth_headers = {"Authorization": f"Bearer {res.get('access_token')}"}
        user_info = requests.get(profile_url, headers=auth_headers).json()
        
        return {"id": user_info.get("userId"), "name": user_info.get("displayName")}, None
    except Exception as e:
        return None, str(e)

def sync_legacy_records(line_id, display_name):
    if not supabase: return
    try:
        supabase.table("users").update({"line_user_id": line_id}).eq("username", display_name).is_("line_user_id", None).execute()
        supabase.table("saved_charts").update({"line_user_id": line_id}).eq("username", display_name).is_("line_user_id", None).execute()
    except Exception: pass

# ==========================================
# 3. 新手註冊彈跳視窗 (Onboarding)
# ==========================================
@st.dialog("✨ 歡迎來到九能量！請完成新手註冊")
def onboarding_popup():
    st.markdown("這是您第一次登入，請填寫基本資料來解鎖您的 **專屬能量藍圖**。")
    
    with st.form("onboarding_form"):
        real_name = st.text_input("真實姓名", value=st.session_state.get("username", ""))
        eng_name = st.text_input("英文名字 / 暱稱 (選填)")
        birth_date = st.date_input("出生日期", min_value=datetime.date(1900, 1, 1), value=datetime.date(1983, 9, 8))
        email = st.text_input("聯絡信箱")
        
        submitted = st.form_submit_button("🚀 完成註冊，進入戰情室", use_container_width=True)

        if submitted:
            if not real_name or not email:
                st.error("⚠️ 請填寫真實姓名與聯絡信箱")
                return
            
            # 建立完整的 user_profile 字典
            profile_data = {
                "full_name": real_name,
                "english_name": eng_name,
                "birth_date": str(birth_date),
                "email": email,
                "tier": "🌱 一般會員 (Free)"
            }
            st.session_state.user_profile = profile_data
            
            # 同步更新至 Supabase (確保下次登入資料還在)
            if supabase and st.session_state.get("line_user_id"):
                try:
                    supabase.table("users").update({
                        "full_name": real_name,
                        "english_name": eng_name,
                        "birth_date": str(birth_date),
                        "email": email,
                        "role": "registered"
                    }).eq("line_user_id", st.session_state.line_user_id).execute()
                except Exception as e:
                    print(f"資料庫更新失敗: {e}")
            
            st.session_state.is_new_user = False
            st.success("✅ 註冊成功！正在為您生成能量藍圖...")
            time.sleep(1)
            st.rerun()

# ==========================================
# 4. 主程式介面 (戰情室)
# ==========================================
def show_member_app():
    friends_raw = []
    if supabase and "line_user_id" in st.session_state:
        try:
            res = supabase.table("saved_charts").select("*").eq("line_user_id", st.session_state.line_user_id).execute()
            friends_raw = res.data or []
        except Exception as e:
            st.error(f"⚠️ 無法讀取測算檔案：{e}")

    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        # 顯示會員階級 (如果有填寫的話)
        if st.session_state.get("user_profile") and "tier" in st.session_state.user_profile:
            st.caption(f"🎖️ {st.session_state.user_profile['tier']}")
        st.divider()
        if st.button("🚪 登出系統", use_container_width=True):
            _clear_persist_login()
            st.session_state.clear()
            st.rerun()

    user_profile = st.session_state.get("user_profile") or {}
    # 如果資料不齊全，給予溫馨提示
    if not user_profile.get("birth_date"):
        st.warning("⚠️ **導航提醒：** 您的個人資料尚未完善，請前往「會員中心」更新出生日期，以獲取精準星盤。")

    st.markdown(f"#### Hi, {st.session_state.username} | 九能量導航系統")
    tabs = st.tabs(["🏠 首頁", "🧬 人生地圖", "🔮 宇宙指引", "👨‍👩‍👧‍👦 家族矩陣", "📔 靈魂日記", "👤 會員中心"])
    
    with tabs[0]: 
        st.subheader(f"歡迎回到能量中心")
        if ads_manager: ads_manager.render_home_ads()
    with tabs[1]: 
        if tab_life_map: tab_life_map.render(friends_raw)
    with tabs[2]: 
        if tab_divination: tab_divination.render_divination_view(friends_raw)
    with tabs[3]: 
        if tab_family_matrix: tab_family_matrix.render(friends_raw)
    with tabs[4]: 
        if tab_journal: tab_journal.render()
    with tabs[5]: 
        if tab_member: tab_member.render()

# ==========================================
# 5. 程式入口 (狀態與路由控制)
# ==========================================
if __name__ == "__main__":
    # 初始化 Session 狀態
    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "username" not in st.session_state: st.session_state.username = ""
    if "user_profile" not in st.session_state: st.session_state.user_profile = None
    
    # 嘗試還原登入狀態
    _try_restore_login()
    
    # LINE 回調處理 (攔截通行證)
    if "code" in st.query_params and not st.session_state.logged_in:
        code = st.query_params["code"]
        user_data, err = get_line_profile_name(code)
        
        st.query_params.clear() # 清理網址參數，切斷死循環
        
        if user_data:
            line_id = user_data["id"]
            line_name = user_data["name"]

            if supabase:
                try:
                    supabase.table("users").upsert({
                        "line_user_id": line_id,
                        "username": line_name,
                        "last_login": datetime.datetime.now().isoformat()
                    }, on_conflict="line_user_id").execute()
                except Exception as e:
                    pass # 不干擾登入流程
                finally:
                    sync_legacy_records(line_id, line_name)

            st.session_state.line_user_id = line_id
            st.session_state.username = line_name
            st.session_state.logged_in = True
            
            _persist_login(line_id) 
            st.rerun()
        else:
            st.error(f"LINE 登入失敗：{err}")

    # --- 最終畫面渲染判斷 ---
    if st.session_state.logged_in:
        # ★ 防呆優化：如果 user_profile 是 None，或是空字典，就代表是新用戶
        if not st.session_state.get("user_profile") or st.session_state.get("is_new_user", False):
            st.session_state.is_new_user = True
            onboarding_popup() 
        else:
            show_member_app() 
            
    else:
        # 🛑 乾淨的 V20.35 登入頁面 UI (絕對沒有 Email)
        col1, _, col2 = st.columns([6, 1, 4])
        with col1:
            st.markdown('### 歡迎來到九能量導航')
            # 修正警告：使用 width="stretch"
            st.image("https://images.unsplash.com/photo-1519681393784-d120267933ba?q=80&w=2070&auto=format&fit=crop", width="stretch")
        with col2:
            st.write(""); st.write(""); st.write(""); st.write("")
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'''
                    <a href="{auth_url}" target="_self" style="background-color:#06C755; color:white; padding:15px; display:block; text-align:center; text-decoration:none; border-radius:10px; font-weight:bold; font-size:16px;">
                        LINE 帳號登錄 / 註冊
                    </a>
                ''', unsafe_allow_html=True)
            else:
                st.error("⚠️ 系統錯誤：未檢測到 LINE Channel ID")
            st.write("")
            st.caption("© 2026 Jow-Jiun Culture | 喬鈞心學")