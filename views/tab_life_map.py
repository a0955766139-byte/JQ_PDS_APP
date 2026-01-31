import streamlit as st
import datetime
import time
import textwrap
import os
from supabase import create_client, Client

# 嘗試匯入核心運算
try:
    import pds_core
except ImportError:
    st.error("⚠️ 找不到 pds_core 模組，請確保它位於專案根目錄。")

# --- 資料庫連線 ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except: return None

supabase = init_connection()

# --- 資料庫存取 (Private) ---
def _get_user_profile(username):
    if not supabase: return None
    try:
        res = supabase.table("users").select("full_name, english_name, birth_date").eq("username", username).execute()
        if res.data and res.data[0].get('birth_date'):
            data = res.data[0]
            return {
                "name": data.get('full_name', username),
                "english_name": data.get('english_name', ""),
                "birthdate": datetime.datetime.strptime(data['birth_date'], "%Y-%m-%d").date()
            }
        return None
    except: return None

def _save_user_profile(username, name, eng_name, birthdate):
    if not supabase: return
    try: 
        supabase.table("users").upsert({
            "username": username, 
            "full_name": name, 
            "english_name": eng_name,
            "birth_date": birthdate.isoformat()
        }, on_conflict="username").execute()
    except: pass

# --- 繪圖組件 (SVG) ---
def _draw_pyramid_svg(d):
    """繪製 PDS 金字塔 SVG"""
    p = d.get('params', d) 
    anchor = d.get('anchor', f"{p.get('M',0)}{p.get('N',0)}{p.get('O',0)}")
    
    for k in ['O','M','N','I','J','K','L']:
        if k not in p: p[k] = 0

    # 回傳單行字串，避免任何縮排問題
    return f"""<svg viewBox="0 0 500 380" style="width:100%; max-width:480px; margin: 0 auto; display: block; font-family: 'Helvetica Neue', sans-serif;"><defs><linearGradient id="grad1" x1="0%" y1="0%" x2="100%" y2="0%"><stop offset="0%" style="stop-color:#6a3093;stop-opacity:1" /><stop offset="100%" style="stop-color:#a044ff;stop-opacity:1" /></linearGradient><filter id="shadow" x="-20%" y="-20%" width="140%" height="140%"><feDropShadow dx="2" dy="2" stdDeviation="3" flood-color="#000000" flood-opacity="0.15"/></filter></defs><path d="M250,30 L50,230 L450,230 Z" fill="none" stroke="#6a3093" stroke-width="1.5" stroke-opacity="0.3"/><line x1="150" y1="130" x2="350" y2="130" stroke="#6a3093" stroke-width="1" stroke-dasharray="4,4" stroke-opacity="0.3"/><line x1="250" y1="30" x2="250" y2="130" stroke="#6a3093" stroke-width="1" stroke-opacity="0.2"/><circle cx="250" cy="70" r="28" fill="#FFD700" stroke="#fff" stroke-width="3" filter="url(#shadow)"/><text x="250" y="79" font-size="26" font-weight="900" fill="#333" text-anchor="middle">{p['O']}</text><text x="250" y="32" font-size="11" fill="#999" text-anchor="middle">主命數</text><circle cx="180" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="180" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['M']}</text><text x="180" y="210" font-size="11" fill="#999" text-anchor="middle">制約</text><circle cx="320" cy="170" r="24" fill="#fff" stroke="#6a3093" stroke-width="2"/><text x="320" y="179" font-size="22" font-weight="bold" fill="#333" text-anchor="middle">{p['N']}</text><text x="320" y="210" font-size="11" fill="#999" text-anchor="middle">外在</text><rect x="90" y="240" width="40" height="40" rx="8" fill="#f8f9fa" stroke="#e0e0e0" stroke-width="1"/><text x="110" y="267" font-size="18" font-weight="bold" fill="#666" text-anchor="middle">{p['I']}</text><rect x="140" y="240" width="40" height="40" rx="8" fill="#f8f9fa" stroke="#e0e0e0" stroke-width="1"/><text x="160" y="267" font-size="18" font-weight="bold" fill="#666" text-anchor="middle">{p['J']}</text><rect x="320" y="240" width="40" height="40" rx="8" fill="#f8f9fa" stroke="#e0e0e0" stroke-width="1"/><text x="340" y="267" font-size="18" font-weight="bold" fill="#666" text-anchor="middle">{p['K']}</text><rect x="370" y="240" width="40" height="40" rx="8" fill="#f8f9fa" stroke="#e0e0e0" stroke-width="1"/><text x="390" y="267" font-size="18" font-weight="bold" fill="#666" text-anchor="middle">{p['L']}</text><g transform="translate(0, 50)"><text x="250" y="270" font-size="12" fill="#999" text-anchor="middle" letter-spacing="3">坐鎮碼</text><text x="250" y="315" font-size="48" font-weight="900" fill="url(#grad1)" text-anchor="middle" style="text-shadow: 0px 4px 10px rgba(106, 48, 147, 0.2); letter-spacing: 2px;">{anchor}</text></g></svg>"""

# --- 核心：HTML 產生器 (獨立出來，防止縮排問題) ---
def _generate_report_html(p, chart, svg_code):
    # 這裡的字串全部頂格寫，不要有任何縮排，確保 Markdown 100% 解析正確
    return f"""
<style>
.v68-card {{ background: #fff; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); overflow: hidden; border: 1px solid #f0f0f0; margin-bottom: 20px; font-family: "Helvetica Neue", Arial, sans-serif; }}
.v68-header {{ background: linear-gradient(135deg, #512D6D 0%, #724892 100%); padding: 35px 20px; color: white; text-align: center; }}
.v68-name {{ font-size: 32px; font-weight: 700; margin-bottom: 5px; letter-spacing: 2px; }}
.v68-eng {{ font-size: 14px; text-transform: uppercase; letter-spacing: 1.5px; opacity: 0.8; margin-bottom: 10px; }}
.v68-meta {{ display: inline-block; background: rgba(255,255,255,0.15); padding: 4px 12px; border-radius: 20px; font-size: 12px; }}
.v68-grid {{ display: grid; grid-template-columns: 1fr 1fr; }}
.v68-cell {{ padding: 20px; border-bottom: 1px solid #f5f5f5; display: flex; justify-content: space-between; align-items: center; }}
.v68-cell:nth-child(odd) {{ border-right: 1px solid #f5f5f5; }}
.bg-special {{ background-color: #FFF8E1; }} 
.bg-career {{ background-color: #F1F8E9; }}
.v68-label {{ color: #888; font-size: 13px; font-weight: 500; }}
.v68-val {{ color: #333; font-size: 20px; font-weight: 800; font-family: "Georgia", serif; }}
.val-purple {{ color: #6a3093; }}
.val-orange {{ color: #F57C00; }}
.val-green {{ color: #388E3C; }}
</style>
<div class="v68-card">
<div class="v68-header">
<div class="v68-name">{p['name']}</div>
<div class="v68-eng">{p.get('english_name', 'Unknown')}</div>
<div class="v68-meta">{chart['age']} 歲 | {p['birthdate'].strftime('%Y/%m/%d')}</div>
</div>
<div class="v68-grid">
<div class="v68-cell"><span class="v68-label">生命道路 (Life Path)</span><span class="v68-val val-purple">{chart['lpn']}</span></div>
<div class="v68-cell"><span class="v68-label">姓名內驅 (Soul)</span><span class="v68-val val-purple">{chart['soul']}</span></div>
<div class="v68-cell bg-special"><span class="v68-label">個特數字 (Special)</span><span class="v68-val val-orange">{chart['special']}</span></div>
<div class="v68-cell"><span class="v68-label">坐鎮碼 (Anchor)</span><span class="v68-val val-purple">{chart['anchor']}</span></div>
<div class="v68-cell bg-career"><span class="v68-label">事業密碼 (Career)</span><span class="v68-val val-green">{chart['career']}</span></div>
<div class="v68-cell"><span class="v68-label">流年運勢 (Year)</span><span class="v68-val">{chart['py']}</span></div>
<div class="v68-cell"><span class="v68-label">成熟數字 (Maturity)</span><span class="v68-val">{chart['maturity']}</span></div>
<div class="v68-cell"><span class="v68-label">制約數字 (Restrict)</span><span class="v68-val">{chart['restrict']}</span></div>
</div>
<div style="padding: 40px 10px 20px 10px;">
{svg_code}
</div>
</div>
"""

# --- 介面邏輯 (UI) ---
def show_input_form():
    """顯示輸入表單"""
    db_profile = _get_user_profile(st.session_state.username)
    if db_profile:
        st.session_state.user_profile = db_profile
        st.session_state.username = db_profile['name']
        st.rerun()

    with st.container(border=True):
        st.markdown("##### 🧬 建立您的九能量檔案")
        st.caption("為了精準計算「姓名內驅數字」，請務必輸入護照上的英文姓名。")
        
        c1, c2 = st.columns(2)
        default_name = st.session_state.username if st.session_state.username != "LINE User" else ""
        with c1: name_input = st.text_input("中文姓名", value=default_name)
        with c2: eng_input = st.text_input("英文姓名 (拼音)", placeholder="請使用英文名威妥碼 (例: WANG HSIAO MING)")
        
        st.markdown("---")
        c_y, c_m, c_d = st.columns([2, 1, 1])
        with c_y: y = st.selectbox("出生年", range(1900, 2027), index=83)
        with c_m: m = st.selectbox("出生月", range(1, 13))
        with c_d: d = st.selectbox("出生日", range(1, 32))
        
        if st.button("🚀 啟動導航", type="primary", use_container_width=True):
            try:
                bd = datetime.date(y, m, d)
                _save_user_profile(st.session_state.username, name_input, eng_input, bd)
                st.session_state.user_profile = {"name": name_input, "english_name": eng_input, "birthdate": bd}
                st.session_state.username = name_input
                st.success("✅ 檔案建立成功！")
                time.sleep(1); st.rerun()
            except ValueError: st.error("日期無效")

def show_pds_report():
    """顯示報告 (呼叫獨立的 HTML 產生器)"""
    p = st.session_state.user_profile
    if st.session_state.username != p['name']:
        st.session_state.username = p['name']
        st.rerun()

    try:
        chart = pds_core.calculate_chart(p['birthdate'], p.get('english_name', ''))
        
        c_title, c_act = st.columns([3, 1])
        with c_act: 
            if st.button("🔄 修改資料", use_container_width=True):
                st.session_state.user_profile = None; st.rerun()

        # 生成 SVG
        svg_code = _draw_pyramid_svg({'params': chart['svg_params'], 'anchor': chart['anchor']})
        
        # 呼叫無縮排的 HTML 產生器
        html_code = _generate_report_html(p, chart, svg_code)
        
        st.markdown(html_code, unsafe_allow_html=True)
        
        st.info("💡 **覺察指引**：地圖已經展開，請對照《九能量》教材，結合您的生命經驗，探索這些數字背後對您的獨特意義。")

    except Exception as e:
        st.error(f"運算錯誤: {e}")

# --- 公開主介面 ---
def render():
    if st.session_state.user_profile is None:
        show_input_form()
    else:
        show_pds_report()