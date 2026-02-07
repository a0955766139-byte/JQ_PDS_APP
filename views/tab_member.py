import streamlit as st
import datetime
import os
import time  
from supabase import create_client
from views.permission_config import get_user_tier  #「喬鈞心學研究院」 (專區權限)


try:
    from views import auth_ui
except ImportError:
    auth_ui = None

try:
    from views import auth_ui
except ImportError:
    auth_ui = None

# --- 資料庫連線 (標準化) ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    # 兼容本地與雲端
    if not url or not key:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        except: pass
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

def update_profile(username, full_name, eng_name, birth_date):
    if not supabase: return False
    try:
        data = {
            "full_name": full_name,
            "english_name": eng_name,
            "birth_date": birth_date.isoformat()
        }
        supabase.table("users").update(data).eq("username", username).execute()
        return True
    except Exception as e:
        st.error(f"更新失敗: {e}")
        return False

def get_all_users():
    """管理員專用：獲取所有用戶"""
    if not supabase: return []
    try:
        res = supabase.table("users").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

def render():
    st.markdown("## 👤 會員指揮中心")
    
    if "user_profile" not in st.session_state or not st.session_state.user_profile:
        st.warning("請先登入以存取會員功能")
        return

    # 1. 獲取當前用戶資料
    user = st.session_state.user_profile
    username = st.session_state.username
    role = user.get('role', 'user')
    plan = user.get('plan', 'free')

    # --- 上半部：個人檔案卡 ---
    col1, col2 = st.columns([1, 2])
    with col1:
        st.info(f"當前身份：{role.upper()} | 方案：{plan.upper()}")
        if role == 'admin':
            st.success("🛡️ 您擁有最高指揮權限")
    
    with col2:
        with st.form("profile_form"):
            st.subheader("📝 編輯我的原始設定")
            new_name = st.text_input("中文暱稱", value=user.get('full_name', ''))
            new_eng = st.text_input("英文名 (用於性情計算)", value=user.get('english_name', ''))
            
            # 處理日期格式
            bd_val = user.get('birth_date')
            if isinstance(bd_val, str):
                bd_val = datetime.datetime.strptime(bd_val, "%Y-%m-%d").date()
            
            new_bd = st.date_input("出生日期", value=bd_val if bd_val else datetime.date(1990,1,1))
            
            if st.form_submit_button("💾 保存設定"):
                if update_profile(username, new_name, new_eng, new_bd):
                    st.toast("✅ 資料已更新！", icon="🎉")
                    # 更新 Session 狀態
                    st.session_state.user_profile['full_name'] = new_name
                    st.session_state.user_profile['english_name'] = new_eng
                    st.session_state.user_profile['birth_date'] = new_bd.isoformat()
                    time.sleep(1) # <--- 這裡需要 import time
                    st.rerun()

    st.divider()

    # --- 下半部：管理員上帝視角 (Admin Only) ---
    if role == 'admin':
        st.markdown("### 👁️ 喬鈞文化流量監控 (Admin Area)")
        st.markdown("這裡只有你能看見，掌握所有註冊會員的狀態。")
        
        all_users = get_all_users()
        if all_users:
            st.dataframe(
                all_users, 
                column_config={
                    "created_at": "註冊時間",
                    "full_name": "暱稱",
                    "username": "LINE ID",
                    "role": "權限"
                },
                use_container_width=True
            )
            st.metric("目前總會員數", len(all_users))
        else:
            st.info("目前尚無其他會員資料")