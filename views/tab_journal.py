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

def save_journal(username, content, entry_id=None):
    """新增或更新日記"""
    if not supabase: return
    now = datetime.datetime.now().isoformat()
    try:
        data = {
            "user_id": username,
            "content": content,
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

    # 初始化 Session State (紀錄目前正在編輯哪一篇)
    if "journal_edit_id" not in st.session_state:
        st.session_state.journal_edit_id = None
    if "journal_content" not in st.session_state:
        st.session_state.journal_content = ""

    # --- 介面佈局：左側列表(3) | 右側編輯區(7) ---
    col_list, col_editor = st.columns([3, 7])

    # === 左側：歷史日記列表 ===
    with col_list:
        st.markdown("##### 🗂️ 歷史紀錄")
        if st.button("➕ 寫新日記", use_container_width=True, type="primary"):
            st.session_state.journal_edit_id = None
            st.session_state.journal_content = ""
            st.rerun()
        
        st.divider()
        
        # 讀取資料
        journals = fetch_journals(username)
        if not journals:
            st.caption("目前沒有日記，開始寫第一篇吧！")
        
        # 顯示列表 (Scrollable container)
        with st.container(height=500):
            for j in journals:
                # 解析時間
                dt = datetime.datetime.fromisoformat(j['created_at'].replace('Z', '+00:00'))
                date_str = dt.strftime("%Y/%m/%d")
                time_str = dt.strftime("%H:%M")
                preview = j['content'][:20] + "..." if len(j['content']) > 20 else j['content']
                
                # 判斷是否為當前選中
                is_active = (st.session_state.journal_edit_id == j['id'])
                btn_type = "secondary" if not is_active else "primary"
                
                # 日記卡片按鈕
                if st.button(
                    f"📅 {date_str}\n{preview}", 
                    key=f"j_{j['id']}", 
                    use_container_width=True, 
                    type=btn_type,
                    help=f"建立於 {time_str}"
                ):
                    st.session_state.journal_edit_id = j['id']
                    st.session_state.journal_content = j['content']
                    st.rerun()

    # === 右側：編輯器 ===
    with col_editor:
        # 標題變化
        mode_title = "📝 撰寫新篇章" if not st.session_state.journal_edit_id else "✏️ 編輯日記"
        st.markdown(f"##### {mode_title}")

        with st.form("journal_form"):
            # 文字輸入區
            content = st.text_area(
                "寫下你的心情...", 
                value=st.session_state.journal_content, 
                height=400,
                placeholder="今天發生了什麼？你的內在有什麼聲音？"
            )
            
            # 按鈕區
            c_save, c_del = st.columns([1, 1])
            with c_save:
                submitted = st.form_submit_button("💾 儲存紀錄", type="primary", use_container_width=True)
            
            # 只有在編輯模式才顯示刪除按鈕 (這裡用 form_submit 會觸發 form，所以刪除通常建議拉出 form 或用特別處理)
            # 為了簡化，我們把刪除按鈕放在 Form 外面，或者使用 Checkbox 確認
            
        if submitted:
            if not content.strip():
                st.warning("內容不能為空喔！")
            else:
                save_journal(username, content, st.session_state.journal_edit_id)
                # 儲存後重置狀態或保留，這裡選擇保留以便繼續編輯
                st.session_state.journal_content = content 
                time.sleep(1)
                st.rerun()

        # 刪除功能 (獨立於 Form 之外，避免誤觸)
        if st.session_state.journal_edit_id:
            st.write("") # Spacer
            with st.expander("🗑️ 刪除此篇日記"):
                st.warning("刪除後無法復原，確定嗎？")
                if st.button("確認刪除", type="primary"):
                    delete_journal(st.session_state.journal_edit_id)
                    st.session_state.journal_edit_id = None
                    st.session_state.journal_content = ""
                    st.rerun()