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
        st.error(f"❌ {module_name} 載入失敗: {e}")
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
    if value:
        return value
    return st.secrets.get(section, {}).get(key, default)

#==========================================
# 3. 持久化登入與資料庫工具
#==========================================
def _persist_login(user_id):
    # 💡 改為只使用 st.query_params：建立 copy 再 assign
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
            # 💡 修改：精準抓取所有 Profile 資料
            res = supabase.table("users").select("*").eq("line_user_id", p_user_id).execute()
            
            if res.data:
                user_profile = res.data[0]
                st.session_state.logged_in = True
                st.session_state.line_user_id = p_user_id 
                # 💡 防止名字為 NULL 導致崩潰
                st.session_state.username = user_profile.get('username') or "能量導航員"
                st.session_state.user_profile = user_profile
                return True
            else:
                # 如果查無此人，清除網址參數防止死循環
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
    if url and key:
        return create_client(url, key)
    return None

supabase = init_connection()

# LINE 登入相關函式 (保持您的內容不變...)
def get_line_auth_url():
    cid = get_secret_value("line", "channel_id")
    redir = get_secret_value("line", "redirect_uri")
    if not cid or not redir:
        st.error(f"⚠️ 系統配置缺失：CID={bool(cid)}, REDIR={bool(redir)}")
        return None
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redir}&state=pds&scope=profile%20openid%20email"

def get_line_profile_name(code):
    """真實 LINE API 對接：獲取唯一 User ID 與 顯示姓名"""
    try:
        # 1. 向 LINE 請求 Access Token
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
        
        # 2. 解析 ID Token (包含唯一 User ID)
        id_token = res.get("id_token")
        if not id_token:
            return None, f"Token 獲取失敗: {res.get('error_description')}"
            
        # 3. 請求 Profile 資訊
        profile_url = "https://api.line.me/v2/profile"
        auth_headers = {"Authorization": f"Bearer {res.get('access_token')}"}
        user_info = requests.get(profile_url, headers=auth_headers).json()
        
        # 💡 重大變更：同時回傳唯一 ID (userId) 與 顯示姓名 (displayName)
        line_user_id = user_info.get("userId") # 這串亂碼是永久不變的門牌
        display_name = user_info.get("displayName") # 這是會變的名字
        
        return {"id": line_user_id, "name": display_name}, None
    except Exception as e:
        return None, str(e)

def sync_legacy_records(line_id, display_name):
    """登入時自動把舊 username 的紀錄補上 line_user_id"""
    if not supabase: return
    try:
        supabase.table("users") \
            .update({"line_user_id": line_id}) \
            .eq("username", display_name) \
            .is_("line_user_id", None) \
            .execute()
        supabase.table("saved_charts") \
            .update({"line_user_id": line_id}) \
            .eq("username", display_name) \
            .is_("line_user_id", None) \
            .execute()
    except Exception:
        pass

#==========================================
# 4. 主程式介面 (合併後的 show_member_app)
#==========================================
def show_member_app():
    # 💡 1. 關鍵救援：先從資料庫抓取所有「親友檔案」
    # 使用新命名的 line_user_id 欄位
    friends_raw = []
    if supabase and "line_user_id" in st.session_state:
        try:
            res = supabase.table("saved_charts") \
                .select("*") \
                .eq("line_user_id", st.session_state.line_user_id) \
                .execute()
            friends_raw = res.data or []
        except Exception as e:
            st.error(f"⚠️ 無法讀取測算檔案：{e}")

    # 側邊欄與登出邏輯 (保持不變)
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        if st.button("🚪 登出系統", use_container_width=True):
            _clear_persist_login()
            st.session_state.clear()
            st.rerun()

    # 安全提醒邏輯：引領用戶綁定 Gmail
    user_profile = st.session_state.get("user_profile") or {}
    if user_profile.get("role") == "registered":
        st.warning("⚠️ **帳號安全提醒：** 建議前往「會員中心」確認您的聯繫資訊。")

    st.markdown(f"#### Hi, {st.session_state.username} | 九能量導航系統")
    tabs = st.tabs(["🏠 首頁", "🧬 人生地圖", "🔮 宇宙指引", "👨‍👩‍👧‍👦 家族矩陣", "📔 靈魂日記", "👤 會員中心"])
    
    with tabs[0]: 
        st.subheader(f"歡迎回到能量中心")
        if ads_manager: ads_manager.render_home_ads()
            
    # 💡 2. 關鍵救援：將 friends_raw 傳入各個分頁 (讓紅字消失)
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

#==========================================
# 5. 程式入口 (守門員邏輯)
#==========================================
if __name__ == "__main__":
    st.set_page_config(page_title="九能量導航", page_icon="⚛️", layout="wide")

    # 隱藏 UI 元件
    st.markdown("<style>#MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}</style>", unsafe_allow_html=True)

    if "logged_in" not in st.session_state: st.session_state.logged_in = False
    if "username" not in st.session_state: st.session_state.username = ""
    if "user_profile" not in st.session_state: st.session_state.user_profile = None
    
    # 當頁面重新整理或帶著 p_user 時嘗試還原登入狀態
    _try_restore_login()
    
    # LINE 回調處理
    if "code" in st.query_params and not st.session_state.logged_in:
        code = st.query_params["code"]
        user_data, err = get_line_profile_name(code)
        
        # 💡 修正 A：先清理 URL 參數，切斷死迴圈連結
        st.query_params.clear() 
        
        if user_data:
            line_id = user_data["id"]     # 真實 ID: joe1369
            line_name = user_data["name"] # 顯示姓名: 喬鈞老師

            # 💡 修正 B：執行資料庫同步 (防禦性寫法)
            if supabase:
                try:
                    supabase.table("users").upsert({
                        "line_user_id": line_id,
                        "username": line_name,
                        "last_login": datetime.datetime.now().isoformat()
                    }, on_conflict="line_user_id").execute()
                except Exception as e:
                    # 如果資料庫欄位缺失會報錯，但我們不讓它卡死登入流程
                    st.warning(f"⚠️ 帳號同步延遲 (請確認資料庫欄位): {e}")
                finally:
                    sync_legacy_records(line_id, line_name)

            # 💡 修正 C：正確設定 Session 狀態並執行轉場
            st.session_state.line_user_id = line_id
            st.session_state.username = line_name
            st.session_state.logged_in = True
            
            # 持久化登入 (存入 p_user=joe1369)
            _persist_login(line_id) 
            
            # 成功後重啟頁面，進入主介面
            st.rerun()
        else:
            st.error(f"LINE 登入失敗：{err}")

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
