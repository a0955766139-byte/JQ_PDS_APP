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
        # 這裡改成 warning 以免干擾版面，但通常不會出錯
        st.warning(f"讀取失敗: {e}")
        return []

def save_journal(username, content, mood, emoji, entry_id=None):
    """新增或更新日記 (包含心情與表情) - 強制使用台灣時間"""
    if not supabase: return
    
    # 設定台灣時區 (UTC+8)
    tz_tw = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz_tw).isoformat()
    
    try:
        data = {
            "user_id": username,
            "content": content,
            "mood": mood,
            "emoji": emoji,
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

    # 定義表情包清單
    emoji_options = [
        "😀", "😃", "😄", "😆", "🥹", "😅", "😂", "🤣", "🥲", "☺️", 
        "😊", "🥰", "😍", "😘", "😙", "😎", "😕", "🙁", "🙃", "🤩", 
        "🥳", "😩", "😥", "🥶", "🥵", "😶‍🌫️", "🤕", "🤑"
    ]
    
    # 定義時區物件 (用於顯示)
    tz_tw = datetime.timezone(datetime.timedelta(hours=8))

    # 初始化 Session State
    if "journal_edit_id" not in st.session_state:
        st.session_state.journal_edit_id = None
    if "journal_content" not in st.session_state:
        st.session_state.journal_content = ""
    if "journal_mood" not in st.session_state:
        st.session_state.journal_mood = "good"
    if "journal_emoji" not in st.session_state:
        st.session_state.journal_emoji = emoji_options[0]

    # === 上半部：編輯器區塊 ===
    mode_title = "📝 撰寫新篇章" if not st.session_state.journal_edit_id else "✏️ 編輯日記"
    st.markdown(f"##### {mode_title}")

    # 放棄編輯按鈕
    if st.session_state.journal_edit_id:
        if st.button("🔄 放棄編輯，寫新日記"):
            st.session_state.journal_edit_id = None
            st.session_state.journal_content = ""
            st.session_state.journal_mood = "good"
            st.session_state.journal_emoji = emoji_options[0]
            st.rerun()

    with st.form("journal_form"):
        col1, col2 = st.columns([1, 1])
        
        # 1. 心情色調
        with col1:
            mood_opts = ["好心情 (🔴)", "壞心情 (🔵)"]
            default_mood_idx = 0 if st.session_state.journal_mood == "good" else 1
            sel_mood = st.radio("今日基調", mood_opts, index=default_mood_idx, horizontal=True)
            mood_val = "good" if "好心情" in sel_mood else "bad"

        # 2. 表情包選擇
        with col2:
            try:
                curr_emoji_idx = emoji_options.index(st.session_state.journal_emoji)
            except:
                curr_emoji_idx = 0
            selected_emoji = st.selectbox("選擇今日表情", emoji_options, index=curr_emoji_idx)

        # 3. 文字輸入區
        content = st.text_area(
            "寫下你的心情...", 
            value=st.session_state.journal_content, 
            height=300,
            placeholder="今天發生了什麼？你的內在有什麼聲音？"
        )
        
        # 4. 按鈕區
        c_save, c_del = st.columns([4, 1])
        with c_save:
            submitted = st.form_submit_button("💾 儲存紀錄", type="primary", use_container_width=True)
        
    if submitted:
        if not content.strip():
            st.warning("內容不能為空喔！")
        else:
            save_journal(username, content, mood_val, selected_emoji, st.session_state.journal_edit_id)
            st.session_state.journal_content = content 
            st.session_state.journal_mood = mood_val
            st.session_state.journal_emoji = selected_emoji
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
                st.session_state.journal_emoji = emoji_options[0]
                st.rerun()

    st.divider()

    # === 下半部：歷史紀錄區塊 ===
    st.markdown("##### 🗂️ 歷史紀錄")
    
    try:
        journals = fetch_journals(username)
    except Exception as e:
        st.error(f"讀取錯誤: {e}")
        journals = []
    
    if not journals:
        st.caption("目前沒有日記，開始寫第一篇吧！")
    else:
        for j in journals:
            # 時間處理
            dt = datetime.datetime.fromisoformat(j['created_at'].replace('Z', '+00:00'))
            dt_tw = dt.astimezone(tz_tw)
            date_str = dt_tw.strftime("%Y/%m/%d %H:%M")

            preview = j['content'][:50].replace("\n", " ") + ("..." if len(j['content']) > 50 else "")
            saved_mood = j.get('mood', 'neutral')
            saved_emoji = j.get('emoji') 
            if not saved_emoji: saved_emoji = "📝"

            # 決定容器類型與初始化
            # 關鍵修正：對於 st.error 和 st.info，我們必須傳入一個參數 " " (空白字串)
            # 這樣才不會報 'missing argument' 錯誤，同時能顯示背景色
            
            box_context = None # 用來存放 context manager
            
            if saved_mood == 'good':
                box_context = st.error(" ") # 紅色背景，標題放空
            elif saved_mood == 'bad':
                box_context = st.info(" ")  # 藍色背景，標題放空
            else:
                box_context = st.container(border=True) # 預設灰色框
            
            # 使用我們設定好的 Context Manager
            with box_context:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"### {saved_emoji}  <span style='font-size:0.8em; color:#666'>{date_str}</span>", unsafe_allow_html=True)
                    st.caption(preview)
                with c2:
                    if st.button("✏️", key=f"load_{j['id']}", help="編輯"):
                        st.session_state.journal_edit_id = j['id']
                        st.session_state.journal_content = j['content']
                        st.session_state.journal_mood = saved_mood
                        st.session_state.journal_emoji = saved_emoji
                        st.rerun()