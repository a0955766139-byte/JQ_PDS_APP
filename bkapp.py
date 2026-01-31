import os
import streamlit as st
import datetime
import time
import random
import requests
import textwrap
import json
import sqlite3
from PIL import Image
from supabase import create_client, Client
from xpinyin import Pinyin 

# --- 1. 基礎設定 ---
st.set_page_config(page_title="喬鈞心學 PDS", page_icon="🔮", layout="wide")
IS_LOCAL_TESTING = True 

# --- 2. CSS 美化 (V45: 標題白字 + 高貴色調) ---
st.markdown("""
    <style>
        [data-testid="stToolbar"] {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        .stApp { font-family: "Helvetica Neue", "Helvetica", "Arial", sans-serif; background-color: #F9FAFB; }

        /* 標題樣式 */
        h1, h2, h3 { color: #1A237E !important; font-weight: 700 !important; }

        /* LINE 按鈕 */
        .line-btn {
            display: flex; align-items: center; justify-content: center;
            width: 100%; background-color: #06C755; color: white !important; 
            padding: 12px 0; border-radius: 8px; text-decoration: none; 
            font-weight: bold; font-size: 16px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); transition: all 0.3s;
        }
        .line-btn:hover { background-color: #05b34c; transform: translateY(-2px); }
        .line-icon { width: 24px; height: 24px; margin-right: 10px; filter: brightness(0) invert(1); }
        
        /* 按鈕優化 */
        div.stButton > button { 
            border-radius: 30px; font-weight: bold; padding: 10px 25px; 
            border: 1px solid #1A237E; color: #1A237E; background: transparent;
        }
        div.stButton > button:hover {
            background: #1A237E; color: white; border: 1px solid #1A237E;
        }
        div.stButton > button[kind="primary"] {
            background-color: #1A237E !important; color: white !important; border: none;
        }

        /* 數據卡片 */
        .stat-card {
            background-color: #FFFFFF; border-radius: 12px; padding: 15px 5px; text-align: center;
            border: 1px solid #E0E0E0; box-shadow: 0 4px 12px rgba(26, 35, 126, 0.05);
            height: 100%; transition: all 0.3s ease;
        }
        .stat-card:hover {
            transform: translateY(-3px); border-color: #B7950B; box-shadow: 0 8px 20px rgba(183, 149, 11, 0.15);
        }
        .stat-value {
            font-size: 1.4em; font-weight: 800; color: #1A237E; margin-bottom: 5px; white-space: nowrap;
        }
        .stat-label {
            font-size: 0.85em; color: #666; letter-spacing: 1px;
        }

        /* 報告頭部 (深藍漸層 + 白字) */
        .report-header-box {
            background: linear-gradient(135deg, #1A237E 0%, #1565C0 100%);
            padding: 25px; border-radius: 15px 15px 0 0;
            color: #FFFFFF !important; text-align: center; margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(26, 35, 126, 0.2);
        }
        .report-header-box h2 {
            color: #FFFFFF !important; text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        /* 抽牌卡片 */
        .divination-card { background: white; border-radius: 15px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto; text-align: center; border: 1px solid #eee; }
        .divination-img { width: 100%; height: 250px; object-fit: cover; }
        .divination-content { padding: 25px; }
        .divination-title { font-size: 1.6em; font-weight: bold; color: #1A237E; margin-bottom: 10px; }
        .divination-poem { font-family: "KaiTi", serif; font-size: 1.3em; color: #444; margin-bottom: 15px; font-style: italic; }
        .divination-desc { font-size: 0.95em; color: #555; line-height: 1.8; text-align: left; background: #F8F9FA; padding: 15px; border-radius: 8px; border-left: 3px solid #B7950B; }

        /* 日記 */
        .journal-entry {
            background: #FFFFFF; border-left: 4px solid #1A237E; padding: 15px;
            margin-bottom: 15px; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }
        .journal-date { font-size: 0.85em; color: #999; margin-bottom: 5px; font-weight: bold; }
        .journal-content { font-size: 1em; color: #333; white-space: pre-wrap; line-height: 1.6; }
    </style>
""", unsafe_allow_html=True)

# --- 3. 初始化 ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'username' not in st.session_state: st.session_state.username = ""
if 'user_profile' not in st.session_state: st.session_state.user_profile = None
if 'last_draw_date' not in st.session_state: st.session_state.last_draw_date = None
if 'todays_card' not in st.session_state: st.session_state.todays_card = None

# 資料庫連接
def init_local_db():
    conn = sqlite3.connect('pds_data.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS draw_history (username TEXT, draw_date TEXT, card_json TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS profiles (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_username TEXT, name TEXT, gender TEXT, eng_name TEXT, birth_date TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS journals (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, content TEXT, created_at TEXT)''')
    conn.commit()
    return conn
db_conn = init_local_db()

# 匯入規則
PDS_CODES = {}
DIVINATION_CARDS = []
try:
    from databases.pds_rules import PDS_CODES
    from databases.card_rules import DIVINATION_CARDS
except ImportError: pass

# --- 4. 輔助函式 ---
def get_base_url(): return "http://localhost:8501" if IS_LOCAL_TESTING else "https://jq-pds-app.onrender.com"

def get_line_auth_url():
    try: cid = st.secrets["line"]["channel_id"]
    except: return None
    redirect_uri = get_base_url(); state = str(random.randint(100000, 999999)); scope = "profile%20openid%20email"
    return f"https://access.line.me/oauth2/v2.1/authorize?response_type=code&client_id={cid}&redirect_uri={redirect_uri}&state={state}&scope={scope}"

def handle_line_callback():
    qp = st.query_params
    if "code" in qp:
        try:
            code = qp["code"]; cid = st.secrets["line"]["channel_id"]; csecret = st.secrets["line"]["channel_secret"]; redirect_uri = get_base_url()
            token_url = "https://api.line.me/oauth2/v2.1/token"; payload = {"grant_type": "authorization_code", "code": code, "redirect_uri": redirect_uri, "client_id": cid, "client_secret": csecret}
            headers = {"Content-Type": "application/x-www-form-urlencoded"}; res = requests.post(token_url, data=payload, headers=headers)
            if res.status_code == 200:
                id_token = res.json().get("id_token"); verify_url = "https://api.line.me/oauth2/v2.1/verify"; user_res = requests.post(verify_url, data={"id_token": id_token, "client_id": cid})
                if user_res.status_code == 200:
                    user_data = user_res.json(); st.session_state.logged_in = True; st.session_state.username = user_data.get("name", "LINE 用戶"); st.query_params.clear(); st.rerun()
        except Exception as e: st.error(f"登入錯誤: {e}")

if not st.session_state.logged_in: handle_line_callback()

# DB Helper
def get_card_image(title):
    default_img = "https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=600&q=80"
    if not title: return default_img
    if "甲子" in title or "天" in title: return "https://images.unsplash.com/photo-1596323605373-c464973347f7?w=600&q=80"
    if "火" in title or "日" in title: return "https://images.unsplash.com/photo-1523825036634-aab3cce05919?w=600&q=80"
    if "水" in title or "月" in title: return "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?w=600&q=80"
    if "金" in title or "財" in title: return "https://images.unsplash.com/photo-1621504450168-38c6814cc184?w=600&q=80"
    if "木" in title or "樹" in title: return "https://images.unsplash.com/photo-1542273917363-3b1817f69a2d?w=600&q=80"
    if "土" in title or "山" in title: return "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=600&q=80"
    if "天使" in title: return "https://images.unsplash.com/photo-1533577116850-9cc66cad8a9b?w=600&q=80"
    if "宇宙" in title: return "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?w=600&q=80"
    return default_img

def check_db_today_draw(username):
    today_str = datetime.date.today().isoformat()
    c = db_conn.cursor(); c.execute("SELECT card_json FROM draw_history WHERE username=? AND draw_date=?", (username, today_str)); result = c.fetchone()
    return json.loads(result[0]) if result else None
def save_db_draw(username, card):
    today_str = datetime.date.today().isoformat(); c = db_conn.cursor()
    c.execute("INSERT INTO draw_history (username, draw_date, card_json) VALUES (?, ?, ?)", (username, today_str, json.dumps(card, ensure_ascii=False))); db_conn.commit()
def delete_db_today_draw(username):
    today_str = datetime.date.today().isoformat(); c = db_conn.cursor(); c.execute("DELETE FROM draw_history WHERE username=? AND draw_date=?", (username, today_str)); db_conn.commit()
def save_profile_to_db(owner, name, gender, eng_name, birth_date):
    created_at = datetime.datetime.now().isoformat(); birth_str = birth_date.strftime("%Y-%m-%d"); c = db_conn.cursor()
    c.execute("SELECT id FROM profiles WHERE owner_username=? AND name=?", (owner, name))
    if c.fetchone(): c.execute("UPDATE profiles SET gender=?, eng_name=?, birth_date=? WHERE owner_username=? AND name=?", (gender, eng_name, birth_str, owner, name))
    else: c.execute("INSERT INTO profiles (owner_username, name, gender, eng_name, birth_date, created_at) VALUES (?, ?, ?, ?, ?, ?)", (owner, name, gender, eng_name, birth_str, created_at))
    db_conn.commit()
def get_user_profiles(owner):
    c = db_conn.cursor(); c.execute("SELECT name, gender, eng_name, birth_date FROM profiles WHERE owner_username=? ORDER BY created_at DESC", (owner,)); return c.fetchall()
def save_journal(username, content):
    if not content.strip(): return
    c = db_conn.cursor(); c.execute("INSERT INTO journals (username, content, created_at) VALUES (?, ?, ?)", (username, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))); db_conn.commit()
def get_journals(username):
    c = db_conn.cursor(); c.execute("SELECT content, created_at FROM journals WHERE username=? ORDER BY id DESC LIMIT 10", (username,)); return c.fetchall()

# --- 5. 核心運算 (V45: 全路徑 + 姓名全名運算修正) ---
def get_digit_sum(n): return sum(int(d) for d in str(n))
def get_single_digit(n):
    while n > 9: n = get_digit_sum(n)
    return n
def format_tradition(n):
    path = [str(n)]; curr = n
    while curr > 9: curr = get_digit_sum(curr); path.append(str(curr))
    if len(path) == 1: return path[0]
    return f"{''.join(path[:-1])}/{path[-1]}"

def calculate_name_module(name):
    if not name: return {"soul_str": "0", "soul_val": 0, "destiny_val": 0}
    name = name.upper().replace(" ", "")
    # Pythagorean table
    table = {'A':1,'J':1,'S':1,'B':2,'K':2,'T':2,'C':3,'L':3,'U':3,'D':4,'M':4,'V':4,'E':5,'N':5,'W':5,'F':6,'O':6,'X':6,'G':7,'P':7,'Y':7,'H':8,'Q':8,'Z':8}
    vowels = {'A','E','I','O','U'}
    
    sum_soul = 0
    sum_destiny = 0 
    
    for char in name:
        if char in table:
            val = table[char]
            sum_destiny += val
            if char in vowels: sum_soul += val
            
    return {"soul_str": format_tradition(sum_soul), "soul_val": get_single_digit(sum_soul), "destiny_val": get_single_digit(sum_destiny)}

def calculate_full_report(profile):
    bd = profile['birthdate']; y, m, d = bd.year, bd.month, bd.day
    str_y, str_m, str_d = f"{y:04d}", f"{m:02d}", f"{d:02d}"
    age = datetime.date.today().year - y
    
    # 1. 生命道路 (LPN) - 全數字直加
    all_digits_sum = sum(int(c) for c in (str_y + str_m + str_d))
    lpn_str = format_tradition(all_digits_sum)
    lpn_single = get_single_digit(all_digits_sum)
    
    # 2. 姓名內驅 (Soul Urge) - 使用全名拼音計算
    name_data = calculate_name_module(profile['eng_name'])
    
    # 3. 2026流年 (當年度)
    current_year = datetime.date.today().year
    py_num = get_single_digit(sum(int(c) for c in str(current_year)) + m + d)
    
    # 4. 坐鎮碼 (Anchor)
    anchor_m = get_single_digit(m + d)
    anchor_n = get_single_digit(sum(int(c) for c in str_y))
    anchor_o = get_single_digit(anchor_m + anchor_n)
    anchor_str = f"{anchor_m}{anchor_n}{anchor_o}"
    
    # 5. 個特數字 (Special Trait) - LPN總數 + 日
    st_val = all_digits_sum + d
    special_str = format_tradition(st_val)
    
    # 6. 事業密碼 (Career Code) - A + 1
    career_val = anchor_n + 1
    career_str = format_tradition(career_val)
    
    # 7. 成熟數字 (Maturity) - LPN單數 + 內驅單數
    mat_val = lpn_single + name_data['soul_val']
    maturity_str = format_tradition(mat_val)
    
    # 8. 制約數字 (Restriction) - 日的單數
    restrict_val = get_single_digit(d)
    
    return {
        "age": age, "lpn": lpn_str, "soul": name_data['soul_str'], "py": py_num, "anchor": anchor_str,
        "special": special_str, "career": career_str, "maturity": maturity_str, "restrict": restrict_val,
        "temp": {"body": 1, "mind": 3, "emotion": 5, "intuition": 2}
    }

# --- 6. 頁面顯示 ---
def display_stat(label, value):
    st.markdown(f"""<div class="stat-card"><div class="stat-value">{value}</div><div class="stat-label">{label}</div></div>""", unsafe_allow_html=True)

def show_login_page():
    c1, c2 = st.columns([1.5, 1], gap="large")
    with c1:
        st.markdown("# 👁️ 歡迎來到喬鈞心學")
        st.markdown("### 探索你到底是什麼模樣，解開生命的原始設定。")
        st.image("https://images.unsplash.com/photo-1517842645767-c639042777db?q=80&w=2670&auto=format&fit=crop", use_container_width=True)
    with c2:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("🔐 會員專區")
            auth_url = get_line_auth_url()
            if auth_url:
                st.markdown(f'''<a href="{auth_url}" target="_self" class="line-btn"><img src="https://upload.wikimedia.org/wikipedia/commons/4/41/LINE_logo.svg" class="line-icon">使用 LINE 帳號一鍵登入</a>''', unsafe_allow_html=True)
            else: st.warning("⚠️ 請檢查 secrets.toml 設定")
            st.markdown("<div style='text-align:center; color:#888; margin: 15px 0;'>或使用傳統帳號</div>", unsafe_allow_html=True)
            tab_login, tab_reg = st.tabs(["帳號登入", "註冊帳號"])
            with tab_login:
                u = st.text_input("帳號", key="u_login"); p = st.text_input("密碼", type="password", key="p_login")
                if st.button("登入", type="primary", use_container_width=True):
                    if u == "admin" or u == "user": st.session_state.logged_in = True; st.session_state.username = "游喬鈞 (Demo)" if u == "admin" else u; st.rerun()
                    else: st.error("帳號或密碼錯誤")
            with tab_reg: st.text_input("設定帳號"); st.text_input("設定密碼", type="password"); st.button("註冊並登入", use_container_width=True)

def show_input_form():
    with st.sidebar:
        st.markdown("### 📂 靈魂檔案室")
        saved_profiles = get_user_profiles(st.session_state.username)
        if saved_profiles:
            st.info(f"已建立 {len(saved_profiles)} 位個案")
            options = ["-- 選擇個案 --"] + [f"{p[0]}" for p in saved_profiles]
            selected = st.selectbox("快速載入", options)
            if selected != "-- 選擇個案 --":
                target = next(p for p in saved_profiles if p[0] == selected)
                bd_obj = datetime.datetime.strptime(target[3], "%Y-%m-%d").date()
                st.session_state.user_profile = {"name": target[0], "gender": target[1], "eng_name": target[2], "birthdate": bd_obj}
                st.rerun()
        else: st.markdown("_尚無儲存的檔案_")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.markdown("### 👋 PDS 全景地圖")
        with st.form("pds_input_form", clear_on_submit=False):
            name_input = st.text_input("📝 姓名/暱稱", value=st.session_state.username)
            gender = st.radio("⚥ 性別", ["男", "女"], horizontal=True)
            
            # ★★★ 預設拼音設為 YUCHIAOCHUN，確保用戶第一次就能看到正確的 22/4 ★★★
            eng_name_input = st.text_input("🔤 全名拼音 (命盤計算用，請確認)", value="YUCHIAOCHUN", help="請輸入完整護照拼音，確保內驅數正確")
            
            st.markdown("🎂 **出生年月日**")
            c1, c2, c3 = st.columns([1.2, 1, 1])
            with c1: years_list = list(range(1920, 2027))[::-1]; sel_year = st.selectbox("年 (Year)", years_list, index=42) # 預設 1983
            with c2: sel_month = st.selectbox("月 (Month)", list(range(1, 13)), index=8) # 預設 9月
            with c3: sel_day = st.selectbox("日 (Day)", list(range(1, 32)), index=7) # 預設 8日
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 生成全景報告", type="primary", use_container_width=True)
            if submitted:
                try: birth_date = datetime.date(sel_year, sel_month, sel_day)
                except: st.error("日期無效"); st.stop()
                
                final_eng_name = eng_name_input.strip().upper()
                if not final_eng_name and name_input:
                     try: p = Pinyin(); final_eng_name = p.get_pinyin(name_input, '').upper()
                     except: final_eng_name = name_input
                
                st.session_state.user_profile = {"name": name_input, "gender": gender, "eng_name": final_eng_name, "birthdate": birth_date}
                st.rerun()

def show_pds_report():
    profile = st.session_state.user_profile
    if not profile: return
    d = calculate_full_report(profile)
    name = profile['name']; ename = profile['eng_name']; age = d['age']; dob_str = profile['birthdate'].strftime("%Y/%m/%d")
    
    with st.container():
        st.markdown('<div class="report-header-box"><h2>人生全景圖</h2></div>', unsafe_allow_html=True)
        c1, c2 = st.columns([2, 1])
        with c1: st.markdown(f"### {name}\n**{ename}**"); 
        with c2: st.markdown(f"**{age}** 歲\n\n{dob_str}")
        st.markdown("---")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: display_stat("生命道路", d['lpn'])
        with col2: display_stat("姓名內驅", d['soul'])
        with col3: display_stat("2026流年", d['py'])
        with col4: display_stat("坐鎮碼", d['anchor'])
        st.markdown("<div style='height:15px'></div>", unsafe_allow_html=True)
        col5, col6, col7, col8 = st.columns(4)
        with col5: display_stat("個特數字", d['special'])
        with col6: display_stat("事業密碼", d['career'])
        with col7: display_stat("成熟數字", d['maturity'])
        with col8: display_stat("制約數字", d['restrict'])
        st.markdown("---")
        
        st.subheader("性情數字")
        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1: display_stat("身體", d['temp']['body'])
        with tc2: display_stat("頭腦", d['temp']['mind'])
        with tc3: display_stat("情緒", d['temp']['emotion'])
        with tc4: display_stat("直覺", d['temp']['intuition'])
        st.markdown("<br>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 儲存個案", use_container_width=True):
            save_profile_to_db(st.session_state.username, name, profile['gender'], ename, profile['birthdate'])
            st.success("已存檔！"); time.sleep(1); st.rerun()
    with c2:
        if st.button("🔄 重新輸入", use_container_width=True):
            st.session_state.user_profile = None; st.rerun()

# --- 主程式 ---
def main():
    if not st.session_state.logged_in: show_login_page(); return
    st.markdown(f"### Hi, {st.session_state.username}")
    tabs = st.tabs(["🧬 人生地圖", "🔮 宇宙指引", "📔 靈魂日記", "📜 讀者專屬", "🛒 靈魂商城"])
    
    with tabs[0]:
        if st.session_state.user_profile is None: show_input_form()
        else: show_pds_report()
            
    with tabs[1]:
        st.markdown("### 🔮 連結你的宇宙指引")
        saved_card = check_db_today_draw(st.session_state.username)
        if saved_card:
            st.success("✨ 今日指引已送達")
            img_url = get_card_image(saved_card['title'])
            st.markdown(f"""
            <div class="divination-card">
                <img src="{img_url}" class="divination-img" onerror="this.onerror=null; this.src='https://images.unsplash.com/photo-1534796636912-3b95b3ab5986?w=600&q=80';">
                <div class="divination-content">
                    <div class="divination-title">{saved_card['title']}</div>
                    <div class="divination-poem">「{saved_card['poem']}」</div>
                    <div class="divination-desc">{saved_card['desc']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.checkbox("重置今日抽牌"): delete_db_today_draw(st.session_state.username); st.rerun()
        else:
            if st.button("🎴 抽取今日牌卡", type="primary", use_container_width=True):
                if DIVINATION_CARDS:
                    with st.spinner("連結宇宙中..."): time.sleep(1.5)
                    card = random.choice(DIVINATION_CARDS); save_db_draw(st.session_state.username, card); st.balloons(); st.rerun()
                else: st.warning("牌卡資料載入中...")

    with tabs[2]:
        st.markdown("### 📔 靈魂書寫")
        with st.form("journal_form"):
            j_content = st.text_area("寫下你的心情、覺察...", height=150)
            if st.form_submit_button("💾 保存日記"): 
                save_journal(st.session_state.username, j_content)
                st.success("日記已保存")
                st.rerun()
        st.divider()
        st.markdown("#### 📜 過去的篇章")
        journals = get_journals(st.session_state.username)
        if journals:
            for j in journals:
                st.markdown(f"""<div class='journal-entry'><div class='journal-date'>{j[1]}</div><div class='journal-content'>{j[0]}</div></div>""", unsafe_allow_html=True)
        else: st.info("目前還沒有日記...")

    with tabs[3]: 
        st.info("📖 這是《九能量》實體書讀者的專屬區域")
        st.text_input("請輸入靈魂代碼")
        st.button("🔓 解鎖內容")

    with tabs[4]:
        st.markdown("### 🛒 能量補給站")
        col_shop1, col_shop2 = st.columns(2)
        with col_shop1:
            with st.container(border=True):
                st.image("https://images.unsplash.com/photo-1516975080664-ed2fc6a32937?q=80&w=800&auto=format&fit=crop", use_container_width=True)
                st.markdown("**【流年覺醒】2026 運勢詳解**")
                st.button("購買 NT$ 990", key="buy1", use_container_width=True)
        with col_shop2:
            with st.container(border=True):
                st.image("https://images.unsplash.com/photo-1528716321680-815a8cdb8cbe?q=80&w=800&auto=format&fit=crop", use_container_width=True)
                st.markdown("**【天賦原力】啟動你的主命數**")
                st.button("購買 NT$ 1,280", key="buy2", use_container_width=True)

if __name__ == "__main__":
    main()
