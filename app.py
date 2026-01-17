import streamlit as st
import datetime
import time
import random
from supabase import create_client, Client

# 匯入規則
try:
    from databases.pds_rules import PDS_CODES, LIFE_PATH_MEANINGS, PERSONAL_YEAR_MEANINGS
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    st.error("⚠️ 找不到 databases 資料夾！請檢查 GitHub 檔案結構。")
    st.stop()

# --- 資料庫管家 (Supabase 版) ---

# 1. 建立連線 (從 Secrets 拿鑰匙)
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"連線失敗，請檢查 Secrets 設定: {e}")
        st.stop()

supabase = init_connection()

# 2. 存日記
def save_journal(username, content):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    data = {"username": username, "content": content, "date_str": date_str}
    try:
        supabase.table("journals").insert(data).execute()
    except Exception as e:
        st.error(f"儲存失敗: {e}")

# 3. 讀日記
def get_journals(username):
    try:
        response = supabase.table("journals").select("*").eq("username", username).order("created_at", desc=True).execute()
        return [(item["date_str"], item["content"]) for item in response.data]
    except Exception as e:
        st.error(f"讀取失敗: {e}")
        return []

# 4. 檢查今日抽牌
def get_today_draw(username):
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    try:
        response = supabase.table("daily_draws").select("*").eq("username", username).eq("draw_date", today_str).execute()
        if response.data:
            item = response.data[0]
            return (item["title"], item["poem"], item["desc"])
        return None
    except Exception:
        return None # 如果表格還沒建，先略過錯誤

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
    try:
        supabase.table("daily_draws").insert(data).execute()
    except Exception as e:
        pass # 暫時忽略錯誤

# --- PDS 計算核心 (保持不變) ---
def get_digit_sum(n):
    while n > 9: n = sum(int(d) for d in str(n))
    return n

def calculate_pds_full_codes(birthdate):
    y, m, d = birthdate.year, birthdate.month, birthdate.day
    sy, sm, sd = f"{y:04d}", f"{
