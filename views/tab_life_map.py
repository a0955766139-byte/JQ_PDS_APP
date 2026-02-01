import streamlit as st
import datetime
import time
import os
from supabase import create_client, Client

# --- 核心模組匯入 ---
try:
    import pds_core
except ImportError:
    st.error("⚠️ 找不到 pds_core 模組")

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
def _get_my_profile(username):
    if not supabase: return None
    try:
        res = supabase.table("users").select("*").eq("username", username).execute()
        if res.data:
            d = res.data[0]
            if d.get('birth_date'):
                return {
                    "id": "ME", "name": d.get('full_name', username),
                    "english_name": d.get('english_name', ""),
                    "birthdate": datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date()
                }
        return None
    except: return None

def _get_saved_charts(username):
    if not supabase: return []
    try:
        res = supabase.table("saved_charts").select("*").eq("user_id", username).order("created_at", desc=True).execute()
        return res.data
    except: return []

def _save_chart(username, name, eng, bd, is_me=False):
    if not supabase: return
    try:
        bd_str = bd.isoformat()
        if is_me:
            supabase.table("users").upsert({"username": username, "full_name": name, "english_name": eng, "birth_date": bd_str}, on_conflict="username").execute()
        else:
            supabase.table("saved_charts").insert({"user_id": username, "name": name, "english_name": eng, "birth_date": bd_str}).execute()
    except Exception as e: st.error(f"存檔失敗: {e}")

def _delete_chart(chart_id):
    if not supabase: return
    try: supabase.table("saved_charts").delete().eq("id", chart_id).execute()
    except: pass

# --- SVG 繪圖 ---
def _draw_pyramid_svg(d):
    p = d.get('params', d) 
    anchor = d.get('anchor', f"{p.get('M',0)}{p.get('N',0)}{p.get('O',0)}")
    return f"""<svg viewBox="0 0 500 380" style="width:100%; max-width:480px; margin: 0 auto; display: block; font-family: sans-serif;"><defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#6a3093;" /><stop offset="100%" style="stop-color:#a044ff;" /></linearGradient></defs><path d="M250,30 L50,230 L450,230 Z" fill="none" stroke="#6a3093" stroke-opacity="0.3"/><circle cx="250" cy="70" r="28" fill="#FFD700" stroke="#fff" stroke-width="3"/><text x="250" y="79" font-size="26" font-weight="900" fill="#333" text-anchor="middle">{p['O']}</text><text x="250" y="32" font-size="11" fill="#999" text-anchor="middle">主命數</text><circle cx="180" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="180" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['M']}</text><circle cx="320" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="320" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['N']}</text><g transform="translate(0, 50)"><text x="250" y="270" font-size="12" fill="#999" text-anchor="middle" letter-spacing="3">坐鎮碼</text><text x="250" y="315" font-size="48" font-weight="900" fill="url(#grad1)" text-anchor="middle">{anchor}</text></g></svg>"""

# --- HTML 報告產生器 (修正版：補回所有數據) ---
def _generate_report_html(name, eng, bd, chart, svg_code):
    temp_str = chart.get('temperament', '0-0-0-0')
    t = temp_str.split('-')
    
    return f"""
<style>
.v68-card {{ background: #fff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #f0f0f0; margin-bottom: 20px; }}
.v68-header {{ background: linear-gradient(135deg, #512D6D 0%, #724892 100%); padding: 30px 20px; color: white; text-align: center; }}
.v68-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0; }}
.v68-cell {{ padding: 12px 15px; border-bottom: 1px solid #f5f5f5; display: flex; justify-content: space-between; align-items: center; }}
.v68-label {{ color: #888; font-size: 13px; }}
.v68-val {{ color: #333; font-size: 16px; font-weight: 800; }}
.temp-box {{ display: flex; justify-content: space-around; background: #f8f4fc; padding: 15px; margin: 10px; border-radius: 10px; }}
.temp-item {{ text-align: center; }}
.temp-num {{ font-size: 20px; font-weight: 900; color: #6a3093; }}
.temp-lbl {{ font-size: 11px; color: #888; }}
</style>
<div class="v68-card">
    <div class="v68-header">
        <div style="font-size: 28px; font-weight: 700;">{name}</div>
        <div style="font-size: 12px; opacity: 0.8;">{eng} | {bd.strftime('%Y/%m/%d')}</div>
    </div>
    <div style="padding: 10px 20px 0 20px; font-size: 14px; font-weight: bold; color: #6a3093;">📊 性情能量分佈</div>
    <div class="temp-box">
        <div class="temp-item"><div class="temp-num">{t[0]}</div><div class="temp-lbl">身 (Phy)</div></div>
        <div class="temp-item"><div class="temp-num">{t[1]}</div><div class="temp-lbl">心 (Men)</div></div>
        <div class="temp-item"><div class="temp-num">{t[2]}</div><div class="temp-lbl">靈 (Emo)</div></div>
        <div class="temp-item"><div class="temp-num">{t[3]}</div><div class="temp-lbl">直 (Int)</div></div>
    </div>
    
    <div class="v68-grid">
        <div class="v68-cell"><span class="v68-label">生命道路 (Life Path)</span><span class="v68-val">{chart['lpn']}</span></div>
        <div class="v68-cell"><span class="v68-label">內心數字 (Inner)</span><span class="v68-val" style="color:#e91e63;">{chart['inner']}</span></div>
        
        <div class="v68-cell"><span class="v68-label">姓名內驅 (Soul)</span><span class="v68-val">{chart['soul']}</span></div>
        <div class="v68-cell"><span class="v68-label">個人特質 (Persona)</span><span class="v68-val">{chart['special']}</span></div>
        
        <div class="v68-cell"><span class="v68-label">事業密碼 (Career)</span><span class="v68-val">{chart['career']}</span></div>
        <div class="v68-cell"><span class="v68-label">成熟數字 (Maturity)</span><span class="v68-val">{chart['maturity']}</span></div>
        
        <div class="v68-cell"><span class="v68-label">制約數字 (Restrict)</span><span class="v68-val">{chart['restrict']}</span></div>
        <div class="v68-cell"><span class="v68-label">流年運勢 (Flow Year)</span><span class="v68-val" style="color:#6a3093;">{chart['py']}</span></div>
        
        <div class="v68-cell" style="grid-column: span 2;"><span class="v68-label">坐鎮碼 (Anchor)</span><span class="v68-val">{chart['anchor']}</span></div>
    </div>
    
    <div style="padding: 20px 0;">{svg_code}</div>
</div>
"""

# --- 主渲染函式 ---
def render():
    username = st.session_state.username
    with st.sidebar:
        st.header("🗂️ 檔案管理")
        mode = st.radio("選擇模式", ["我的本命盤", "📂 親友檔案庫", "➕ 新增親友"], index=0)

    # --- 邏輯：準備要顯示或編輯的資料 ---
    target_data = None
    is_me = (mode == "我的本命盤")
    
    if mode == "我的本命盤":
        target_data = _get_my_profile(username)
    elif mode == "📂 親友檔案庫":
        saved_list = _get_saved_charts(username)
        if saved_list:
            sel = st.selectbox("選擇親友", options=[f"{p['name']} ({p['birth_date']})" for p in saved_list])
            target_data = next((p for p in saved_list if f"{p['name']} ({p['birth_date']})" == sel), None)
            
            if target_data:
                 with st.popover("🗑️ 刪除此檔案"):
                    if st.button("確認刪除", type="primary"):
                        _delete_chart(target_data['id']); st.rerun()
        else:
            st.info("目前沒有存檔，請選擇「➕ 新增親友」。")
            
    # --- 關鍵修正：輸入表格永遠置頂 (Always Show Input) ---
    # 這裡的邏輯是：如果是「新增模式」，顯示空表單
    # 如果是「我的本命盤」或「親友檔案」，顯示「帶有資料的表單」供修改
    
    # 預設值設定
    def_name = ""
    def_eng = ""
    def_bd = datetime.date(1983, 9, 8)
    
    if target_data:
        def_name = target_data['name']
        def_eng = target_data.get('english_name', '')
        if 'birth_date' in target_data:
            if isinstance(target_data['birth_date'], str):
                def_bd = datetime.datetime.strptime(target_data['birth_date'], "%Y-%m-%d").date()
            else:
                def_bd = target_data['birth_date']
        elif 'birthdate' in target_data:
            def_bd = target_data['birthdate']
    elif mode == "我的本命盤": # 第一次登入
         def_name = username

    # 渲染輸入區塊 (放在最上面！)
    with st.container(border=True):
        col_t1, col_t2 = st.columns([3, 1])
        with col_t1:
            if mode == "➕ 新增親友":
                st.subheader("📝 輸入新成員資料")
            else:
                st.subheader(f"📝 編輯資料：{def_name}")
        
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: name = st.text_input("姓名", value=def_name)
        with c2: eng = st.text_input("英文名 (拼音)", value=def_eng)
        with c3: bd_input = st.date_input("出生日期", value=def_bd)
        
        btn_label = "🚀 啟動導航 / 更新資料" if mode == "我的本命盤" else "💾 存檔並計算"
        
        if st.button(btn_label, type="primary", use_container_width=True):
            _save_chart(username, name, eng, bd_input, is_me=is_me)
            st.toast("✅ 資料已更新！", icon="🎉")
            time.sleep(0.5)
            st.rerun()

    # --- 渲染報告卡片 (如果有資料的話) ---
    if target_data or (mode == "我的本命盤" and target_data): 
        # 即使剛按了更新，target_data 可能還是舊的，所以我們直接用上面的輸入值來即時運算
        # 但為了保險，我們通常重新讀取。這裡為了簡單，我們如果有 target_data 就顯示
        # 若是剛存檔，rerun 後會進到這裡
        
        p = target_data
        if not p: # 防呆，如果是第一次輸入完還沒存
            return

        # 確保日期格式正確
        if 'birth_date' in p:
             if isinstance(p['birth_date'], str):
                bd = datetime.datetime.strptime(p['birth_date'], "%Y-%m-%d").date()
             else: bd = p['birth_date']
        elif 'birthdate' in p: bd = p['birthdate']
        else: bd = datetime.date.today()

        chart = pds_core.calculate_chart(bd, p.get('english_name', ''))
        svg = _draw_pyramid_svg({'params': chart['svg_params'], 'anchor': chart['anchor']})
        
        st.markdown(_generate_report_html(p['name'], p.get('english_name',''), bd, chart, svg), unsafe_allow_html=True)
        