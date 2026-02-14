import streamlit as st
import datetime
import os
import time
from supabase import create_client

# --- 資料庫連線 ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    if url and key: return create_client(url, key)
    return None

supabase = init_connection()

# --- 資料存取函式 ---
def fetch_journals():
    """取得該使用者的所有日記 (認 ID)"""
    if not supabase: return []
    # 💡 修正 1：直接從 session_state 抓取永久 ID
    line_id = st.session_state.get("line_user_id")
    if not line_id: return []
    
    try:
        res = supabase.table("journal_entries")\
            .select("*")\
            .eq("line_user_id", line_id)\
            .order("created_at", desc=True)\
            .execute()
        return res.data
    except Exception as e:
        st.warning(f"讀取失敗: {e}")
        return []

def save_journal(content, mood, emoji, entry_id=None):
    """新增或更新日記 (同時儲存 ID 與 姓名)"""
    if not supabase: return
    
    line_id = st.session_state.get("line_user_id")
    username = st.session_state.get("username") # 儲存當下的名字作為備份
    
    tz_tw = datetime.timezone(datetime.timedelta(hours=8))
    now = datetime.datetime.now(tz_tw).isoformat()
    
    try:
        data = {
            "line_user_id": line_id,   # 💡 關鍵：永久門牌
            "user_id": username,        # 💡 視覺：當時姓名
            "content": content,
            "mood": mood,
            "emoji": emoji,
            "updated_at": now
        }
        if entry_id: # 更新模式
            # 更新時也要確保是本人 (雙重鎖定：id + line_user_id)
            supabase.table("journal_entries").update(data)\
                .eq("id", entry_id).eq("line_user_id", line_id).execute()
            st.toast("✅ 日記已更新！")
        else: # 新增模式
            supabase.table("journal_entries").insert(data).execute()
            st.toast("🎉 新日記已儲存！")
    except Exception as e:
        st.error(f"儲存失敗: {e}")

def delete_journal(entry_id):
    """刪除日記 (增加 ID 安全檢查)"""
    if not supabase: return
    line_id = st.session_state.get("line_user_id")
    try:
        supabase.table("journal_entries").delete()\
            .eq("id", entry_id).eq("line_user_id", line_id).execute()
        st.toast("🗑️ 日記已刪除")
    except Exception as e:
        st.error(f"刪除失敗: {e}")

# --- 主渲染函式 ---
def render():
    # 💡 修正 2：身分對位
    line_id = st.session_state.get("line_user_id")
    display_name = st.session_state.get("username", "未知用戶")

    if not line_id:
        st.warning("請先透過 LINE 登入以開啟靈魂書寫空間")
        return

    st.markdown(f"### 📔 {display_name} 的靈魂書寫：與內在對話")

    emoji_options = ["😀", "😃", "😄", "😆", "🥹", "😅", "😂", "🤣", "🥲", "☺️", "😊", "🥰", "😍", "😘", "😙", "😎", "😕", "🙁", "🙃", "🤩", "🥳", "😩", "😥", "🥶", "🥵", "😶‍🌫️", "🤕", "🤑"]
    tz_tw = datetime.timezone(datetime.timedelta(hours=8))

    if "journal_edit_id" not in st.session_state: st.session_state.journal_edit_id = None
    if "journal_content" not in st.session_state: st.session_state.journal_content = ""
    if "journal_mood" not in st.session_state: st.session_state.journal_mood = "good"
    if "journal_emoji" not in st.session_state: st.session_state.journal_emoji = emoji_options[0]

    mode_title = "📝 撰寫新篇章" if not st.session_state.journal_edit_id else "✏️ 編輯日記"
    st.markdown(f"##### {mode_title}")

    if st.session_state.journal_edit_id:
        if st.button("🔄 放棄編輯，寫新日記"):
            st.session_state.journal_edit_id = None
            st.session_state.journal_content = ""
            st.rerun()

    with st.form("journal_form"):
        col1, col2 = st.columns([1, 1])
        with col1:
            mood_opts = ["好心情 (🔴)", "壞心情 (🔵)"]
            default_mood_idx = 0 if st.session_state.journal_mood == "good" else 1
            sel_mood = st.radio("今日基調", mood_opts, index=default_mood_idx, horizontal=True)
            mood_val = "good" if "好心情" in sel_mood else "bad"
        with col2:
            try: curr_emoji_idx = emoji_options.index(st.session_state.journal_emoji)
            except: curr_emoji_idx = 0
            selected_emoji = st.selectbox("選擇今日表情", emoji_options, index=curr_emoji_idx)

        content = st.text_area("寫下你的心情...", value=st.session_state.journal_content, height=250)
        
        c_save, _ = st.columns([4, 1])
        with c_save:
            submitted = st.form_submit_button("💾 儲存紀錄", type="primary", use_container_width=True)
        
    if submitted:
        if not content.strip():
            st.warning("內容不能為空喔！")
        else:
            # 💡 修正 3：呼叫不帶 username (函式內會自取)
            save_journal(content, mood_val, selected_emoji, st.session_state.journal_edit_id)
            time.sleep(1)
            st.session_state.journal_edit_id = None
            st.session_state.journal_content = ""
            st.rerun()

    if st.session_state.journal_edit_id:
        if st.button("🗑️ 刪除此篇日記", type="secondary"):
            delete_journal(st.session_state.journal_edit_id)
            st.session_state.journal_edit_id = None
            st.session_state.journal_content = ""
            st.rerun()

    st.divider()
    st.markdown("##### 🗂️ 歷史紀錄")
    
    # 💡 修正 4：讀取函式簡化
    journals = fetch_journals()
    
    if not journals:
        st.caption("目前沒有日記，開始寫第一篇吧！")
    else:
        for j in journals:
            dt = datetime.datetime.fromisoformat(j['created_at'].replace('Z', '+00:00'))
            dt_tw = dt.astimezone(tz_tw)
            date_str = dt_tw.strftime("%Y/%m/%d %H:%M")
            preview = j['content'][:50].replace("\n", " ") + ("..." if len(j['content']) > 50 else "")
            saved_mood = j.get('mood', 'neutral')
            saved_emoji = j.get('emoji', '📝')

            # 視覺化色塊渲染
            if saved_mood == 'good': box = st.error(" ") # 紅色
            elif saved_mood == 'bad': box = st.info(" ") # 藍色
            else: box = st.container(border=True)
            
            with box:
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f"**{saved_emoji} {date_str}**")
                    st.caption(preview)
                with c2:
                    if st.button("✏️", key=f"edit_{j['id']}"):
                        st.session_state.journal_edit_id = j['id']
                        st.session_state.journal_content = j['content']
                        st.session_state.journal_mood = saved_mood
                        st.session_state.journal_emoji = saved_emoji
                        st.rerun()