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
        # 嘗試獲取資料，若無 birth_date 也不要報錯，回傳部分資料即可
        res = supabase.table("users").select("*").eq("username", username).execute()
        if res.data:
            d = res.data[0]
            # 處理日期字串轉物件
            bd = None
            if d.get('birth_date'):
                bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date()
            
            return {
                "id": "ME", 
                "name": d.get('full_name', username),
                "english_name": d.get('english_name', ""),
                "birthdate": bd # 可能為 None
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
            # 更新使用者資料
            supabase.table("users").update({
                "full_name": name, 
                "english_name": eng, 
                "birth_date": bd_str
            }).eq("username", username).execute()
        else:
            supabase.table("saved_charts").insert({
                "user_id": username, 
                "name": name, 
                "english_name": eng, 
                "birth_date": bd_str
            }).execute()
    except Exception as e: st.error(f"存檔失敗: {e}")

# --- 視覺元件渲染 ---
def _draw_pyramid_svg(d):
    p = d.get('params', d) 
    anchor = d.get('anchor', f"{p.get('M',0)}{p.get('N',0)}{p.get('O',0)}")
    return f"""<svg viewBox="0 0 500 380" style="width:100%; max-width:480px; margin: 0 auto; display: block; font-family: sans-serif;"><defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#6a3093;" /><stop offset="100%" style="stop-color:#a044ff;" /></linearGradient></defs><path d="M250,30 L50,230 L450,230 Z" fill="none" stroke="#6a3093" stroke-opacity="0.3"/><circle cx="250" cy="70" r="28" fill="#FFD700" stroke="#fff" stroke-width="3"/><text x="250" y="79" font-size="26" font-weight="900" fill="#333" text-anchor="middle">{p['O']}</text><text x="250" y="32" font-size="11" fill="#999" text-anchor="middle">主命數</text><circle cx="180" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="180" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['M']}</text><circle cx="320" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="320" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['N']}</text><g transform="translate(0, 50)"><text x="250" y="270" font-size="12" fill="#999" text-anchor="middle" letter-spacing="3">坐鎮碼</text><text x="250" y="315" font-size="48" font-weight="900" fill="url(#grad1)" text-anchor="middle">{anchor}</text></g></svg>"""

def _generate_report_html(name, eng, bd, chart, svg_code):
    # 解析性情字串 (身-心-靈-直)
    t = chart.get('temperament', "0-0-0-0").split('-')
    
    # 這裡把所有消失的數據都找回來！
    return f"""
<style>
.v68-card {{ background: #fff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #f0f0f0; margin-bottom: 20px; }}
.v68-header {{ background: linear-gradient(135deg, #512D6D 0%, #724892 100%); padding: 30px 20px; color: white; text-align: center; }}
.v68-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding: 15px; }}
.v68-cell {{ background: #fdfdfd; padding: 10px; border-radius: 8px; border: 1px solid #eee; display: flex; flex-direction: column; align-items: center; }}
.v68-label {{ color: #888; font-size: 12px; margin-bottom: 5px; }}
.v68-val {{ color: #333; font-size: 18px; font-weight: 800; }}
.temp-box {{ display: flex; justify-content: space-around; background: #f8f4fc; padding: 15px; margin: 10px; border-radius: 10px; }}
.temp-item {{ text-align: center; }}
.temp-num {{ font-size: 20px; font-weight: 900; color: #6a3093; }}
.temp-lbl {{ font-size: 11px; color: #888; }}
.section-title {{ padding: 15px 20px 5px 20px; font-size: 14px; font-weight: bold; color: #6a3093; border-bottom: 2px solid #f0f0f0; margin-bottom: 10px;}}
</style>

<div class="v68-card">
    <div class="v68-header">
        <div style="font-size: 28px; font-weight: 700;">{name}</div>
        <div style="font-size: 12px; opacity: 0.8;">{eng} | {bd.strftime('%Y/%m/%d')}</div>
    </div>
    
    <div class="section-title">📊 1. 性情能量 (身-心-靈-直)</div>
    <div class="temp-box">
        <div class="temp-item"><div class="temp-num">{t[0]}</div><div class="temp-lbl">身 (Phy)</div></div>
        <div class="temp-item"><div class="temp-num">{t[1]}</div><div class="temp-lbl">心 (Men)</div></div>
        <div class="temp-item"><div class="temp-num">{t[2]}</div><div class="temp-lbl">靈 (Emo)</div></div>
        <div class="temp-item"><div class="temp-num">{t[3]}</div><div class="temp-lbl">直 (Int)</div></div>
    </div>

    <div class="section-title">🗝️ 2. 核心命盤數據</div>
    <div class="v68-grid">
        <div class="v68-cell"><span class="v68-label">生命道路 (Life Path)</span><span class="v68-val">{chart['lpn']}</span></div>
        <div class="v68-cell"><span class="v68-label">內心數字 (Inner Self)</span><span class="v68-val" style="color:#e91e63;">{chart['inner']}</span></div>
        <div class="v68-cell"><span class="v68-label">姓名內驅 (Soul)</span><span class="v68-val">{chart['soul']}</span></div>
        <div class="v68-cell"><span class="v68-label">個特/外在 (Persona)</span><span class="v68-val">{chart['special']}</span></div>
        <div class="v68-cell"><span class="v68-label">制約數字 (Restrict)</span><span class="v68-val">{chart['restrict']}</span></div>
        <div class="v68-cell"><span class="v68-label">流年 (Flow Year)</span><span class="v68-val">{chart['py']}</span></div>
        <div class="v68-cell"><span class="v68-label">坐鎮碼 (Anchor)</span><span class="v68-val">{chart['anchor']}</span></div>
        <div class="v68-cell"><span class="v68-label">成熟數字 (Maturity)</span><span class="v68-val">{chart['maturity']}</span></div>
    </div>
    
    <div class="section-title">📐 3. PDS 全息金字塔</div>
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
            # 這裡加入了防呆機制：如果沒有設定生日，會回傳只有名字的資料
            selected_profile = _get_my_profile(username)
            if selected_profile and not selected_profile['birthdate']:
                st.warning("⚠️ 尚未設定出生日期，請在右側輸入")
                selected_profile = "NEW" # 強制顯示輸入框
                
        elif mode == "親友檔案庫":
            saved_list = _get_saved_charts(username)
            if saved_list:
                sel = st.selectbox("選擇親友", options=[f"{p['name']} ({p['birth_date']})" for p in saved_list])
                selected_profile = next(p for p in saved_list if f"{p['name']} ({p['birth_date']})" == sel)
            else:
                st.info("尚無存檔")
        else: selected_profile = "NEW"

    # 如果是新用戶，或者沒有資料，顯示輸入框 (也就是你說的「輸入個資」回來了)
    if selected_profile == "NEW" or selected_profile is None:
        st.subheader("📝 輸入導航資料")
        with st.container(border=True):
            # 預設值
            def_name = ""
            def_eng = ""
            def_bd = datetime.date(1990, 1, 1)
            
            # 如果是從"我的本命盤"過來但沒生日，嘗試帶入已知名字
            if mode == "我的本命盤" and isinstance(_get_my_profile(username), dict):
                 prof = _get_my_profile(username)
                 def_name = prof.get('name', '')
                 def_eng = prof.get('english_name', '')
            
            name = st.text_input("姓名", value=def_name)
            eng = st.text_input("英文名 (拼音)", value=def_eng)
            bd = st.date_input("出生日期", value=def_bd)
            
            if st.button("🚀 啟動導航", type="primary", use_container_width=True):
                _save_chart(username, name, eng, bd, is_me=(mode == "我的本命盤"))
                st.success("資料已保存！正在重啟...")
                time.sleep(1)
                st.rerun()
                
    elif selected_profile:
        # 正常顯示報表
        p = selected_profile
        # 確保有生日才能算
        if p.get('birthdate') or isinstance(p.get('birth_date'), str):
            bd = p['birthdate'] if 'birthdate' in p else datetime.datetime.strptime(p['birth_date'], "%Y-%m-%d").date()
            eng_name = p.get('english_name', '')
            
            # 呼叫核心運算
            chart = pds_core.calculate_chart(bd, eng_name)
            svg = _draw_pyramid_svg({'params': chart['svg_params'], 'anchor': chart['anchor']})
            
            # 渲染包含所有數據的 HTML
            st.markdown(_generate_report_html(p['name'], eng_name, bd, chart, svg), unsafe_allow_html=True)