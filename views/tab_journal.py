import streamlit as st
import datetime
import os
import time
from supabase import create_client

# --- 資料庫連線 ---
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

# --- 資料存取函式 ---
def fetch_journals(username):
    """取得該使用者的所有日記，按時間倒序排列"""
    if not supabase: return []
    try:
        res = supabase.table("journal_entries")\
            .select("*")\
            .eq("user_id", username)\
            .order("created_at", desc=True)\
            .execute()
        return res.data
    except Exception as e:
        st.error(f"讀取失敗: {e}")
        return []

def save_journal(username, content, mood, entry_id=None):
    """新增或更新日記 (包含心情)"""
    if not supabase: return
    now = datetime.datetime.now().isoformat()
    try:
        data = {
            "user_id": username,
            "content": content,
            "mood": mood,  # 新增：儲存心情顏色
            "updated_at": now
        }
        if entry_id: # 更新模式
            supabase.table("journal_entries").update(data).eq("id", entry_id).execute()
            st.toast("✅ 日記已更新！")
        else: # 新增模式
            supabase.table("journal_entries").insert(data).execute()
            st.toast("🎉 新日記已儲存！")
    except Exception as e:
        st.error(f"儲存失敗: {e}")

def delete_journal(entry_id):
    """刪除日記"""
    if not supabase: return
    try:
        supabase.table("journal_entries").delete().eq("id", entry_id).execute()
        st.toast("🗑️ 日記已刪除")
    except Exception as e:
        st.error(f"刪除失敗: {e}")

# --- 主渲染函式 ---
def render():
    # 確保有登入
    if "username" not in st.session_state:
        st.warning("請先登入")
        return

    username = st.session_state.username
    st.markdown("### 📔 靈魂書寫：與內在對話")

    # 初始化 Session State
    if "journal_edit_id" not in st.session_state:
        st.session_state.journal_edit_id = None
    if "journal_content" not in st.session_state:
        st.session_state.journal_content = ""
    if "journal_mood" not in st.session_state:
        st.session_state.journal_mood = "good" # 預設好心情

    # === 上半部：編輯器區塊 ===
    mode_title = "📝 撰寫新篇章" if not st.session_state.journal_edit_id else "✏️ 編輯日記"
    st.markdown(f"##### {mode_title}")

    # 放棄編輯按鈕
    if st.session_state.journal_edit_id:
        if st.button("🔄 放棄編輯，寫新日記"):
            st.session_state.journal_edit_id = None
            st.session_state.journal_content = ""
            st.session_state.journal_mood = "good"
            st.rerun()

    with st.form("journal_form"):
        # 1. 心情選擇器 (Radio Button)
        # 對應值: "good" -> 紅色框, "bad" -> 藍色框
        c_mood, c_spacer = st.columns([1, 1])
        with c_mood:
            # 根據 Session State 設定預設選項索引
            mood_options = ["好心情 (🔴 紅色)", "壞心情 (🔵 藍色)"]
            default_index = 0 if st.session_state.journal_mood == "good" else 1
            
            selected_mood_label = st.radio(
                "今日心情色調", 
                mood_options, 
                index=default_index,
                horizontal=True
            )
            # 將標籤轉回代碼
            mood_val = "good" if "好心情" in selected_mood_label else "bad"

        # 2. 文字輸入區
        content = st.text_area(
            "寫下你的心情...", 
            value=st.session_state.journal_content, 
            height=300,
            placeholder="今天發生了什麼？你的內在有什麼聲音？"
        )
        
        # 3. 按鈕區
        c_save, c_del = st.columns([4, 1])
        with c_save:
            submitted = st.form_submit_button("💾 儲存紀錄", type="primary", use_container_width=True)
        
    if submitted:
        if not content.strip():
            st.warning("內容不能為空喔！")
        else:
            save_journal(username, content, mood_val, st.session_state.journal_edit_id)
            st.session_state.journal_content = content 
            st.session_state.journal_mood = mood_val
            time.sleep(1)
            st.rerun()

    # 刪除功能
    if st.session_state.journal_edit_id:
        with st.expander("🗑️ 刪除此篇日記"):
            st.warning("刪除後無法復原，確定嗎？")
            if st.button("確認刪除", type="primary"):
                delete_journal(st.session_state.journal_edit_id)
                st.session_state.journal_edit_id = None
                st.session_state.journal_content = ""
                st.session_state.journal_mood = "good"
                st.rerun()

    st.divider()

    # === 下半部：歷史紀錄區塊 ===
    st.markdown("##### 🗂️ 歷史紀錄")
    
    journals = fetch_journals(username)
    
    if not journals:
        st.caption("目前沒有日記，開始寫第一篇吧！")
    else:
        for j in journals:
            dt = datetime.datetime.fromisoformat(j['created_at'].replace('Z', '+00:00'))
            date_str = dt.strftime("%Y/%m/%d %H:%M")
            preview = j['content'][:50].replace("\n", " ") + ("..." if len(j['content']) > 50 else "")
            
            # 判斷心情顏色
            # 使用 Streamlit 內建的 colored box: error=紅, info=藍
            saved_mood = j.get('mood', 'neutral')
            
            # 定義容器類型 (利用 error/info 來達成紅/藍框效果)
            if saved_mood == 'good':
                container_type = st.error # 紅色 (雖然叫 error，但在這裡是代表好心情的紅)
                icon = "🔴"
            elif saved_mood == 'bad':
                container_type = st.info  # 藍色
                icon = "🔵"
            else:
                container_type = st.container # 預設灰色
                icon = "⚪"

            # 渲染卡片
            # 如果是預設灰色，需要加 border=True；如果是紅/藍，內建就有底色
            if saved_mood in ['good', 'bad']:
                with container_type():
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{icon} {date_str}**")
                        st.caption(preview)
                    with c2:
                        if st.button("✏️", key=f"load_{j['id']}", help="編輯此篇日記"):
                            st.session_state.journal_edit_id = j['id']
                            st.session_state.journal_content = j['content']
                            st.session_state.journal_mood = saved_mood
                            st.rerun()
            else:
                # 舊資料或無心情的顯示方式
                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"**{date_str}**")
                        st.caption(preview)
                    with c2:
                        if st.button("✏️", key=f"load_{j['id']}"):
                            st.session_state.journal_edit_id = j['id']
                            st.session_state.journal_content = j['content']
                            st.session_state.journal_mood = "good"
                            st.rerun()