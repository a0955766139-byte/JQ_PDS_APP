import streamlit as st
import datetime
import os
import time  
from supabase import create_client

# --- 1. 資料庫連線初始化 ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

# --- 2. 核心更新邏輯：支援 Gmail 綁定與帳密設置 ---
def update_user_settings(line_user_id, updates):
    """
    精準對位更新：鎖定 line_user_id 進行多欄位寫入
    """
    if not supabase: return False
    try:
        # 增加最後更新時間戳記
        updates["last_login"] = datetime.datetime.now().isoformat()
        supabase.table("users").update(updates).eq("line_user_id", line_user_id).execute()
        return True
    except Exception as e:
        st.error(f"❌ 數據同步失敗：{e}")
        return False

# --- 3. 會員中心主渲染函數 ---
def render():
    st.markdown("## 👤 會員指揮中心")
    
    # 從 Session 抓取核心 Profile
    profile = st.session_state.get("user_profile", {})
    line_id = st.session_state.get("line_user_id")
    
    if not line_id:
        st.warning("⚠️ 請先透過 LINE 快速登入以啟動會員功能")
        return

    # --- 第一區：個人尊榮狀態 (Read-only) ---
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("當前身分", profile.get("tier_label") or "基礎學員") #
    with col_b:
        st.metric("每日積分", profile.get("daily_points") or 0)
    with col_c:
        st.metric("付費狀態", (profile.get("plan") or "free").upper())

    # --- 第二區：自我設置中心 (Editable) ---
    st.markdown("### 🛠️ 用戶自我設置")
    with st.form("member_setting_form"):
        c1, c2 = st.columns(2)
        with c1:
            # 登入用戶名與密碼設置 (為未來對接研究院做準備)
            new_nickname = st.text_input("設置登入用戶名", value=profile.get("user_nickname") or "")
            new_password = st.text_input("設定帳戶密碼", value=profile.get("password") or "", type="password", help="用於未來電腦端登入")
            new_phone = st.text_input("聯繫電話", value=profile.get("phone") or "")
        
        with c2:
            # Gmail 唯一驗證綁定
            new_email = st.text_input("登記 Gmail (唯一驗證)", value=profile.get("email") or "", help="連動研究院上課通知與 Zoom 系統")
            
            # 出生年月日校準
            bd_val = profile.get('birth_date')
            if isinstance(bd_val, str) and bd_val:
                bd_val = datetime.datetime.strptime(bd_val, "%Y-%m-%d").date()
            new_bd = st.date_input("出生年月日", value=bd_val if bd_val else datetime.date(1990,1,1))
        
        if st.form_submit_button("💾 保存並同步設置"):
            updates = {
                "user_nickname": new_nickname,
                "password": new_password,
                "email": new_email,
                "phone": new_phone,
                "birth_date": new_bd.isoformat()
            }
            if update_user_settings(line_id, updates):
                st.toast("✅ 設置已顯化成功！", icon="🎉")
                # 同步更新 Session 狀態防止畫面延遲
                st.session_state.user_profile.update(updates)
                time.sleep(1)
                st.rerun()

    st.divider()

    # --- 第三區：學習項目與進階查看 ---
    tab_course, tab_mentor = st.tabs(["📚 已購課程項目", "🤝 專屬輔導員"])
    
    with tab_course:
        st.markdown("#### 您的智慧資產清單")
        courses = profile.get("purchased_courses") or [] #
        if courses:
            for course in courses:
                st.info(f"📖 {course}")
        else:
            st.write("目前尚無購買課程，前往「喬鈞研究院」探索更多？")

    with tab_mentor:
        st.markdown("#### 專屬能量管家")
        mentor = profile.get("mentor_contact") or "未分配"
        st.success(f"您的專屬輔導員：{mentor}")
        st.caption("如有系統使用或課程問題，請直接聯繫您的輔導員。")

    # --- 底部：靈魂門牌 (唯讀) ---
    st.caption(f"唯一的靈魂門牌 (LINE ID): {line_id}")
