import streamlit as st
import time
import os
from supabase import create_client

# --- 連線設定 ---
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

def render_auth():
    """顯示登入/註冊頁面"""
    st.markdown("## 🔐 歡迎來到九能量導航")
    st.caption("請登入以存取您的專屬命盤與日記")

    tab1, tab2 = st.tabs(["登入 (Login)", "註冊 (Sign Up)"])

    # === 登入區塊 ===
    with tab1:
        with st.form("login_form"):
            email = st.text_input("電子信箱 (Email)")
            password = st.text_input("密碼", type="password")
            submit = st.form_submit_button("🚀 登入", type="primary", use_container_width=True)
        
        if submit:
            if not email or not password:
                st.warning("請輸入帳號與密碼")
            else:
                try:
                    # Supabase 登入指令
                    res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                    if res.user:
                        st.session_state["user"] = res.user
                        st.session_state["username"] = res.user.email # 綁定 Email 為識別碼
                        st.toast("✅ 登入成功！")
                        time.sleep(1)
                        st.rerun()
                except Exception as e:
                    st.error(f"登入失敗：{e}")

    # === 註冊區塊 ===
    with tab2:
        with st.form("signup_form"):
            new_email = st.text_input("設定電子信箱")
            new_password = st.text_input("設定密碼 (至少 6 碼)", type="password")
            confirm_password = st.text_input("確認密碼", type="password")
            submit_reg = st.form_submit_button("✨ 建立新帳號", use_container_width=True)

        if submit_reg:
            if new_password != confirm_password:
                st.error("❌ 兩次密碼輸入不一致")
            elif len(new_password) < 6:
                st.error("❌ 密碼長度需至少 6 碼")
            else:
                try:
                    # Supabase 註冊指令
                    res = supabase.auth.sign_up({"email": new_email, "password": new_password})
                    if res.user:
                        st.success("🎉 註冊成功！系統已自動為您登入。")
                        st.session_state["user"] = res.user
                        st.session_state["username"] = res.user.email
                        time.sleep(2)
                        st.rerun()
                except Exception as e:
                    st.error(f"註冊失敗：{e}")