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

# ==========================================
# 新手註冊彈跳視窗 (Onboarding Dialog)
# ==========================================
@st.dialog("✨ 歡迎來到九能量！請完成新手註冊")
def onboarding_popup():
    st.markdown("這是您第一次登入，請填寫基本資料來解鎖您的 **專屬能量藍圖**。")
    
    with st.form("onboarding_form"):
        # 預設帶入 LINE 的名字，但允許用戶修改為真實姓名
        real_name = st.text_input("真實姓名", value=st.session_state.username)
        eng_name = st.text_input("英文名字 / 暱稱 (選填)")
        
        # 這裡非常關鍵，因為人生地圖需要生日來計算
        birth_date = st.date_input("出生日期", min_value=datetime.date(1900, 1, 1), value=datetime.date(1990, 1, 1))
        email = st.text_input("聯絡信箱")
        
        submitted = st.form_submit_button("🚀 完成註冊，進入戰情室", use_container_width=True)

        if submitted:
            # 1. 防呆：確保重要資料有填寫
            if not real_name or not email:
                st.error("⚠️ 請填寫真實姓名與聯絡信箱")
                return
            
            # 2. 賦予會員初始階級 (Tiering)
            default_tier = "🌱 一般會員 (Free)"
            
            # 3. 準備寫入系統的資料袋 (這就解決了之前的 NoneType 當機問題！)
            st.session_state.user_profile = {
                "full_name": real_name,
                "english_name": eng_name,
                "birth_date": str(birth_date),
                "email": email,
                "tier": default_tier
            }
            
            # ★ 這裡未來可以加上寫入 Supabase 資料庫的程式碼
            # supabase.table("users").insert({...}).execute()
            
            # 4. 標記為已完成註冊，並刷新頁面關閉視窗
            st.session_state.is_new_user = False
            st.success("註冊成功！正在為您生成能量藍圖...")
            time.sleep(1)
            st.rerun()
            
# --- 資料庫連線 (保持穩定) ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

# 🛠️ 修正 1：更新邏輯改用 line_user_id 鎖定
def update_profile(line_user_id, full_name, eng_name, birth_date, email=None, phone=None):
    if not supabase: return False
    try:
        data = {
            "username": full_name, # 同步更新顯示姓名
            "full_name": full_name,
            "english_name": eng_name,
            "birth_date": birth_date.isoformat(),
            "last_updated": datetime.datetime.now().isoformat()
        }
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone
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
    user = st.session_state.get('user_profile') or {}
    username = user.get("username") or st.session_state.get("username", "未知用戶")
    role = user.get("role", "user")
    # 動態計算當前權限等級
    tier_info = get_user_tier(display_name) 

    # --- 上半部：個人檔案卡 ---
    col1, col2 = st.columns([1, 2])
    with col1:
        # 顯示視覺上的尊榮標籤
        st.info(f"當前身分：{display_name}")
    st.success(f"權限：{tier_info.get('name', '會員')}")
    if role == 'admin':
            st.warning("🛡️ 管理員模式已開啟")
    
    with col2:
        with st.form("profile_form"):
            st.subheader("📝 編輯我的能量原始設定")
            # 這裡顯示 LINE 抓到的名字作為預設
            new_name = st.text_input("顯示暱稱", value=user.get('full_name', display_name))
            new_eng = st.text_input("英文名 (用於性情計算)", value=user.get('english_name', ''))
            new_email = st.text_input("Gmail 信箱 (綁定通知)", value=user.get('email', ''))
            new_phone = st.text_input("聯絡電話", value=user.get('phone', ''))
            
            # 處理日期
            bd_val = user.get('birth_date')
            if isinstance(bd_val, str):
                bd_val = datetime.datetime.strptime(bd_val, "%Y-%m-%d").date()
            new_bd = st.date_input(
                "出生日期",
                value=bd_val if bd_val else datetime.date(2000, 1, 1),
                min_value=datetime.date(1800, 1, 1),
                max_value=datetime.date(2050, 12, 31),
            )
            
            if st.form_submit_button("💾 保存並同步 ID 能量"):
                # 💡 關鍵：傳入 joe1369 進行物理存檔
                if update_profile(line_id, new_name, new_eng, new_bd, email=new_email, phone=new_phone):
                    st.toast("✅ 資料已與 LINE ID 成功對位！", icon="🎉")

                    # ★ 新增這兩行防呆：如果 user_profile 是空的，就給它一個空字典
                    if st.session_state.get('user_profile') is None:
                        st.session_state['user_profile'] = {}
                    # 更新 Session 避免重複抓取
                    st.session_state.user_profile['full_name'] = new_name
                    st.session_state.user_profile['english_name'] = new_eng
                    st.session_state.user_profile['birth_date'] = new_bd.isoformat()
                    st.session_state.user_profile['email'] = new_email
                    st.session_state.user_profile['phone'] = new_phone
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