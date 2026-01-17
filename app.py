import streamlit as st
# ... (其他 import 保持不變)
from supabase import create_client, Client # 匯入 Supabase 工具

# --- 資料庫管家 (Supabase 版) ---

# 1. 建立連線 (從 Secrets 拿鑰匙)
@st.cache_resource
def init_connection():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_connection()

# 2. 存日記
def save_journal(username, content):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    # 寫入 Supabase (看起來很像 Python 的字典操作)
    data = {"username": username, "content": content, "date_str": date_str}
    supabase.table("journals").insert(data).execute()

# 3. 讀日記
def get_journals(username):
    # 從 journals 表格選取所有欄位，條件是 username，並依照時間倒序
    response = supabase.table("journals").select("*").eq("username", username).order("created_at", desc=True).execute()
    # Supabase 回傳的資料在 response.data 裡，它是個列表
    # 我們要把格式轉換一下，讓 App 看得懂 (轉成 list of tuples)
    # 假設之前格式是 (date, content)
    return [(item["date_str"], item["content"]) for item in response.data]

# 4. 檢查今日抽牌
def get_today_draw(username):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    response = supabase.table("daily_draws").select("*").eq("username", username).eq("draw_date", today_str).execute()
    if response.data:
        item = response.data[0]
        return (item["title"], item["poem"], item["desc"])
    return None

# 5. 存今日抽牌
def save_today_draw(username, card):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    data = {
        "username": username, 
        "draw_date": today_str, 
        "title": card['title'], 
        "poem": card['poem'], 
        "desc": card['desc']
    }
    supabase.table("daily_draws").insert(data).execute()

# 注意：init_db() 不再需要了，因為 Supabase 表格是你手動在網頁上建好的
