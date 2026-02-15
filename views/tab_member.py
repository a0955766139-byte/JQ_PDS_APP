import streamlit as st
import datetime
import os
import time  
from supabase import create_client

# --- 核心權限對接 ---
try:
    from views.permission_config import get_user_tier
    from views import auth_ui, ads_manager
except ImportError:
    auth_ui = None
    ads_manager = None

# --- 資料庫連線 (保持穩定) ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

# 🛠️ 修正 1：更新邏輯改用 line_user_id 鎖定
def update_profile(line_user_id, full_name, eng_name, birth_date):
    if not supabase: return False
    try:
        data = {
            "username": full_name, # 同步更新顯示姓名
            "full_name": full_name,
            "english_name": eng_name,
            "birth_date": birth_date.isoformat(),
            "last_updated": datetime.datetime.now().isoformat()
        }
        # 💡 關鍵：使用永久不變的 ID 作為過濾條件
        supabase.table("users").update(data).eq("line_user_id", line_user_id).execute()
        return True
    except Exception as e:
        st.error(f"更新失敗: {e}")
        return False

def get_all_users():
    """管理員專用：讀取所有具備 ID 的真實用戶"""
    if not supabase: return []
    try:
        res = supabase.table("users").select("*").order("created_at", desc=True).execute()
        return res.data
    except: return []

def render():
    st.markdown("## 👤 會員指揮中心")
    
    # 💡 修正 2：改讀取的關鍵變數 (ID 與 顯示姓名)
    line_id = st.session_state.get("line_user_id")
    display_name = st.session_state.get("username", "未知用戶")
    
    if not line_id:
        st.warning("⚠️ 請先透過 LINE 快速登入以啟動會員功能")
        return

    # 💡 修正 2：優先讀取資料庫存好的 username
    user = st.session_state.get('user_profile', {})
    username = user.get("username") or st.session_state.get("username", "未知用戶")
    # 動態計算當前權限等級
    tier_info = get_user_tier(display_name) 

    # --- 上半部：個人檔案卡 ---
    col1, col2 = st.columns([1, 2])
    with col1:
        # 顯示視覺上的尊榮標籤
        st.info(f"當前身分：{display_name}")
        st.success(f"權限：{tier_info['label']}")
        if role == 'admin':
            st.warning("🛡️ 管理員模式已開啟")
    
    with col2:
        with st.form("profile_form"):
            st.subheader("📝 編輯我的能量原始設定")
            # 這裡顯示 LINE 抓到的名字作為預設
            new_name = st.text_input("顯示暱稱", value=user.get('full_name', display_name))
            new_eng = st.text_input("英文名 (用於性情計算)", value=user.get('english_name', ''))
            
            # 處理日期
            bd_val = user.get('birth_date')
            if isinstance(bd_val, str):
                bd_val = datetime.datetime.strptime(bd_val, "%Y-%m-%d").date()
            new_bd = st.date_input("出生日期", value=bd_val if bd_val else datetime.date(1990,9,8))
            
            if st.form_submit_button("💾 保存並同步 ID 能量"):
                # 💡 關鍵：傳入 joe1369 進行物理存檔
                if update_profile(line_id, new_name, new_eng, new_bd):
                    st.toast("✅ 資料已與 LINE ID 成功對位！", icon="🎉")
                    # 更新 Session 避免重複抓取
                    st.session_state.user_profile['full_name'] = new_name
                    st.session_state.user_profile['english_name'] = new_eng
                    st.session_state.user_profile['birth_date'] = new_bd.isoformat()
                    time.sleep(1)
                    st.rerun()

    st.divider()

    # --- 下半部：管理員上帝視角 (Admin Only) ---
    if role == 'admin':
        st.markdown("### 👁️ 全域會員數據監控 (ID 導向)")
        all_users = get_all_users()
        if all_users:
            st.dataframe(
                all_users, 
                column_config={
                    "line_user_id": "永久 ID (sub)",
                    "full_name": "當前暱稱",
                    "birth_date": "生日",
                    "role": "權限等級"
                },
                use_container_width=True
            )
            st.metric("總註冊靈魂數", len(all_users))

# --- tab_member.py 優化 ---

def show_member_center():
    profile = st.session_state.get("user_profile", {})
    
    st.info("### 👤 個人檔案設定")
    col1, col2 = st.columns(2)
    
    with col1:
        # 顯示資料庫中的 username
        st.write(f"**🌟 顯示姓名：** {profile.get('username')}")
        st.write(f"**📧 電子郵件：** {profile.get('email', '未設定')}")
        
    with col2:
        # 顯示您的唯一靈魂門牌
        st.write(f"**🆔 系統 ID：** `{profile.get('line_user_id')}`")
        st.write(f"**👑 會員等級：** {profile.get('role', 'user').upper()}")
