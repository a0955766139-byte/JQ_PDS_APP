import streamlit as st
import datetime
import time
import os
from supabase import create_client, Client

# 嘗試匯入核心運算 V4.5
try:
    import pds_core
except ImportError:
    st.error("⚠️ 找不到 pds_core 模組，請檢查檔案是否存在")

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

# --- 資料存取邏輯 ---
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

# --- 視覺元件渲染 ---
def _draw_pyramid_svg(d):
    p = d.get('params', d) 
    anchor = d.get('anchor', f"{p.get('M',0)}{p.get('N',0)}{p.get('O',0)}")
    return f"""<svg viewBox="0 0 500 380" style="width:100%; max-width:480px; margin: 0 auto; display: block; font-family: sans-serif;"><defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#6a3093;" /><stop offset="100%" style="stop-color:#a044ff;" /></linearGradient></defs><path d="M250,30 L50,230 L450,230 Z" fill="none" stroke="#6a3093" stroke-opacity="0.3"/><circle cx="250" cy="70" r="28" fill="#FFD700" stroke="#fff" stroke-width="3"/><text x="250" y="79" font-size="26" font-weight="900" fill="#333" text-anchor="middle">{p['O']}</text><text x="250" y="32" font-size="11" fill="#999" text-anchor="middle">主命數</text><circle cx="180" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="180" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['M']}</text><circle cx="320" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="320" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['N']}</text><g transform="translate(0, 50)"><text x="250" y="270" font-size="12" fill="#999" text-anchor="middle" letter-spacing="3">坐鎮碼</text><text x="250" y="315" font-size="48" font-weight="900" fill="url(#grad1)" text-anchor="middle">{anchor}</text></g></svg>"""

def _generate_report_html(name, eng, bd, chart, svg_code):
    t = chart['temperament'].split('-')
    return f"""
<style>
.v68-card {{ background: #fff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #f0f0f0; margin-bottom: 20px; }}
.v68-header {{ background: linear-gradient(135deg, #512D6D 0%, #724892 100%); padding: 30px 20px; color: white; text-align: center; }}
.v68-grid {{ display: grid; grid-template-columns: 1fr 1fr; }}
.v68-cell {{ padding: 15px; border-bottom: 1px solid #f5f5f5; display: flex; justify-content: space-between; align-items: center; }}
.v68-label {{ color: #888; font-size: 13px; }}
.v68-val {{ color: #333; font-size: 18px; font-weight: 800; }}
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
        <div class="v68-cell"><span class="v68-label">生命道路</span><span class="v68-val">{chart['lpn']}</span></div>
        <div class="v68-cell"><span class="v68-label">內心數字</span><span class="v68-val" style="color:#e91e63;">{chart['inner']}</span></div>
        <div class="v68-cell"><span class="v68-label">事業密碼</span><span class="v68-val">{chart['career']}</span></div>
        <div class="v68-cell"><span class="v68-label">成熟數字</span><span class="v68-val">{chart['maturity']}</span></div>
    </div>
    <div style="padding: 20px 0;">{svg_code}</div>
</div>
"""

# --- 介面主邏輯 ---
def render():
    username = st.session_state.username
    with st.sidebar:
        st.header("🗂️ 檔案管理")
        mode = st.radio("選擇模式", ["我的本命盤", "親友檔案庫", "➕ 新增查詢"])
        selected_profile = None
        if mode == "我的本命盤":
            selected_profile = _get_my_profile(username)
        elif mode == "親友檔案庫":
            saved_list = _get_saved_charts(username)
            if saved_list:
                sel = st.selectbox("選擇親友", options=[f"{p['name']} ({p['birth_date']})" for p in saved_list])
                selected_profile = next(p for p in saved_list if f"{p['name']} ({p['birth_date']})" == sel)
                if selected_profile:
                    with st.popover("🗑️ 刪除此檔案"):
                        if st.button("確認刪除", type="primary"):
                            _delete_chart(selected_profile['id']); st.rerun()
        else: selected_profile = "NEW"

    if selected_profile == "NEW" or (mode == "我的本命盤" and selected_profile is None):
        st.subheader("📝 輸入導航資料")
        with st.container(border=True):
            name = st.text_input("姓名", value=username if mode=="我的本命盤" else "")
            eng = st.text_input("英文名 (拼音)")
            bd_input = st.date_input("出生日期", datetime.date(1983, 9, 8))
            if st.button("🚀 啟動導航", type="primary", use_container_width=True):
                _save_chart(username, name, eng, bd_input, is_me=(mode == "我的本命盤"))
                st.rerun()
    elif selected_profile:
        p = selected_profile
        
        # ✅ 【關鍵修復】智慧判斷日期欄位
        if 'birth_date' in p:
            # 來自 saved_charts (字串格式)
            bd = datetime.datetime.strptime(p['birth_date'], "%Y-%m-%d").date()
        elif 'birthdate' in p:
            # 來自 _get_my_profile (日期物件)
            bd = p['birthdate']
        else:
            bd = datetime.date.today() # 防呆預設值

        chart = pds_core.calculate_chart(bd, p.get('english_name', ''))
        svg = _draw_pyramid_svg({'params': chart['svg_params'], 'anchor': chart['anchor']})
        st.markdown(_generate_report_html(p['name'], p.get('english_name',''), bd, chart, svg), unsafe_allow_html=True)