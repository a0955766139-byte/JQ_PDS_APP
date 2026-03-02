import streamlit as st
import datetime
import os
import time
from supabase import create_client
from pypinyin import pinyin, Style
from views.permission_config import get_user_tier
from views import life_map_ui

# --- 1. 資料庫與輔助函式 ---
@st.cache_resource
def init_connection():
    url = os.environ.get("SUPABASE_URL") or st.secrets.get("supabase", {}).get("url")
    key = os.environ.get("SUPABASE_KEY") or st.secrets.get("supabase", {}).get("key")
    return create_client(url, key) if url and key else None

supabase = init_connection()

def _auto_generate_english_name(chinese_name):
    if not chinese_name: return ""
    try:
        pinyin_list = pinyin(chinese_name, style=Style.WADEGILES, heteronym=False)
        return " ".join([item[0].capitalize() for item in pinyin_list])
    except: return ""

# --- 2. 資料存取函式 (核心：對準 line_user_id) ---
def _get_my_profile(line_user_id): # ✅ 統一使用 line_user_id
    if not supabase: return None
    try:
        res = supabase.table("users").select("*").eq("line_user_id", line_user_id).execute()
        if res.data:
            d = res.data[0]
            bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1983,9,8)
            return {"id": "ME", "name": d.get('full_name', "本人"), "english_name": d.get('english_name', ""), "birthdate": bd, "type": "me", "category": "本人"}
        return None
    except: return None

def _get_saved_charts(line_user_id):
    if not supabase: return []
    try:
        res = supabase.table("saved_charts").select("*").eq("line_user_id", line_user_id).order("created_at", desc=True).execute()
        data = []
        for d in res.data:
            bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1990,1,1)
            data.append({"id": d['id'], "name": d['name'], "english_name": d.get('english_name', ""), "birthdate": bd, "type": "friend", "category": d.get('category', "未分類")})
        return data
    except: return []

def _save_chart(line_user_id, name, eng, bd, category, uid=None, is_me=False):
    if not supabase: return
    try:
        bd_str = bd.isoformat()
        final_eng = eng if eng and eng.strip() else _auto_generate_english_name(name)
        if is_me:
            # ✅ 修正：這裡要用參數傳進來的 line_user_id
            supabase.table("users").upsert({"line_user_id": line_user_id, "full_name": name, "english_name": final_eng, "birth_date": bd_str}, on_conflict="line_user_id").execute()
        else:
            data_payload = {"line_user_id": line_user_id, "name": name, "english_name": final_eng, "birth_date": bd_str, "category": category or "未分類"}
            if uid: supabase.table("saved_charts").update(data_payload).eq("id", uid).execute()
            else: supabase.table("saved_charts").insert(data_payload).execute()
        st.toast("✅ 能量存檔成功")
    except Exception as e: st.error(f"💀 存檔失敗: {e}")

# --- 3. 主渲染入口 ---
def render(friends_raw=None): # ✅ 必須接收這個參數
    
    # ==========================================
    # 1. 🛡️ 防護機制優先：確認登入狀態
    # ==========================================
    line_id = st.session_state.get("line_user_id")
    if not line_id:
        st.warning("請先透過 LINE 登入")
        return
        
    # 🎒 統一取得資料袋 (合併重複宣告)
    user_profile = st.session_state.get("user_profile") or {}
    
    # ==========================================
    # 2. ★ 頂部個人資料確認區塊 (身分名牌)
    # ==========================================
    # 從資料袋中抓出使用者的資料
    c_name = user_profile.get("full_name") or st.session_state.get("username", "未知姓名")
    e_name = user_profile.get("english_name") or ""
    b_date = user_profile.get("birth_date") or "未設定出生日期"
    
    # 格式化顯示：如果有英文名字，才加上括號
    display_eng = f" <span style='font-size: 16px; color: #888;'>({e_name})</span>" if e_name else ""

    # 繪製精美的身分名牌卡片
    st.markdown(f"""
    <div style="background: linear-gradient(to right, #ffffff, #f9fbfd); padding: 20px 25px; border-radius: 15px; border-left: 6px solid #6a3093; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-bottom: 25px; margin-top: 10px;">
        <div style="font-size: 24px; font-weight: 800; color: #2c3e50; margin-bottom: 8px; letter-spacing: 0.5px;">
            🧬 {c_name}{display_eng} 的專屬能量導航
        </div>
        <div style="font-size: 15px; color: #555;">
            📅 <b>西元出生日期：</b> <span style="color: #6a3093; font-weight: bold;">{b_date}</span>
            <span style="font-size: 13px; color: #aaa; margin-left: 15px;">(若需更正，請至「會員中心」修改)</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    # ==========================================

    # ==========================================
    # 3. ⚙️ 會員階級與數據處理邏輯
    # ==========================================
    user_role = user_profile.get("role", "registered")
    tier_config = get_user_tier(user_role)
    
    all_profiles = []
    me = _get_my_profile(line_id)
    if me: all_profiles.append(me)
    
    # 💡 數據顯化邏輯
    friends_list = friends_raw if friends_raw is not None else _get_saved_charts(line_id)
    processed_friends = []
    for d in friends_list:
        bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1990,1,1)
        processed_friends.append({"id": d.get('id'), "name": d.get('name'), "english_name": d.get('english_name', ""), "birthdate": bd, "type": "friend", "category": d.get('category', "未分類")})
    
    all_profiles.extend(processed_friends)
    current_used = len(processed_friends)

    # 渲染目前選中的檔案
    if "selected_profile_id" not in st.session_state: st.session_state.selected_profile_id = "ME"
    target = next((x for x in all_profiles if x['id'] == st.session_state.selected_profile_id), all_profiles[0])
    
    if target:
        # 直接呼叫 UI 模組顯示 1983-09-08 等能量圖
        life_map_ui.render_energy_tabs(target['birthdate'], target['english_name'])

    st.divider()
    st.markdown(f"### 👨‍👩‍👧‍👦 家族矩陣：親友檔案庫")
    st.caption(f"目前等級：{tier_config['name']} | 額度：{current_used} / {tier_config['map_limit']}")

    if current_used < tier_config['map_limit']:
        with st.expander("➕ 新增親友資料"):
            with st.form("life_map_add_form"):
                n_name = st.text_input("姓名")
                n_eng = st.text_input("英文名 (留空自動生成)")
                n_bd = st.date_input("出生日期", value=datetime.date(1990,1,1))
                n_cat = st.selectbox("分類", ["家人", "朋友", "同事", "客戶", "未分類"])
                if st.form_submit_button("建立檔案"):
                    _save_chart(line_id, n_name, n_eng, n_bd, n_cat) # ✅ 使用 line_id 存檔
                    time.sleep(1)
                    st.rerun()