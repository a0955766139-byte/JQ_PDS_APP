import streamlit as st
import datetime
import os
import textwrap
import time
from supabase import create_client

# --- 核心模組匯入 ---
try:
    import pds_core
except ImportError:
    # 模擬 pds_core (避免報錯用)
    class MockPDS:
        def calculate_chart(self, bd, name):
            total = sum(int(d) for d in bd.strftime("%Y%m%d"))
            while total > 9: total = sum(int(d) for d in str(total))
            return {
                'lpn': total, 'soul': 1, 'career': 8, 'restrict': 5, 'anchor': 4,
                'inner': 3, 'special': 9, 'maturity': 6, 'py': (datetime.date.today().year - bd.year + 1) % 9 or 9,
                'temperament': '2-3-1-4', 
                'svg_params': {'O':6,'M':3,'N':3,'I':1,'J':2,'K':2,'L':1},
                'triangle_codes': ['12-3', '45-9'] * 6
            }
        class NineEnergyNumerology:
            def calculate_diamond_chart(self, y, m, d):
                return {'timeline': []}
    pds_core = MockPDS()

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
            bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1990,1,1)
            # 自己預設分類為 "本人"
            return {"id": "ME", "name": d.get('full_name', username), "english_name": d.get('english_name', ""), "birthdate": bd, "type": "me", "category": "本人"}
        return None
    except: return None

def _get_saved_charts(username):
    if not supabase: return []
    try:
        # 抓取 category 欄位
        res = supabase.table("saved_charts").select("*").eq("user_id", username).order("created_at", desc=True).execute()
        data = []
        for d in res.data:
            bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1990,1,1)
            cat = d.get('category') if d.get('category') else "未分類" # 防呆
            data.append({"id": d['id'], "name": d['name'], "english_name": d.get('english_name', ""), "birthdate": bd, "type": "friend", "category": cat})
        return data
    except: return []

def _save_chart(username, name, eng, bd, category, uid=None, is_me=False):
    if not supabase: return
    try:
        bd_str = bd.isoformat()
        if is_me:
            supabase.table("users").upsert({"username": username, "full_name": name, "english_name": eng, "birth_date": bd_str}, on_conflict="username").execute()
        else:
            if uid:
                supabase.table("saved_charts").update({
                    "name": name, 
                    "english_name": eng, 
                    "birth_date": bd_str,
                    "category": category # 儲存分類
                }).eq("id", uid).execute()
            else:
                supabase.table("saved_charts").insert({
                    "user_id": username, 
                    "name": name, 
                    "english_name": eng, 
                    "birth_date": bd_str,
                    "category": category # 儲存分類
                }).execute()
    except Exception as e: st.error(f"存檔失敗: {e}")

def _delete_chart(chart_id):
    if not supabase: return
    try: supabase.table("saved_charts").delete().eq("id", chart_id).execute()
    except: pass

# --- UI 輔助元件 ---
def _render_info_row(label, value, color="#333", is_header=False):
    fw = "800" if is_header else "600"
    fs = "18px" if is_header else "16px"
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding:8px 0;">
        <span style="color:#888; font-size:14px;">{label}</span>
        <span style="color:{color}; font-weight:{fw}; font-size:{fs};">{value}</span>
    </div>
    """, unsafe_allow_html=True)

# --- SVG 繪圖 ---
def _draw_pyramid_svg(chart_data, bd):
    p = chart_data.get('svg_params', {})
    s_d, s_m, s_y = f"{bd.day:02d}", f"{bd.month:02d}", f"{bd.year:04d}"
    color_main, color_fill = "#6a3093", "#ffffff"
    stroke_width, font_style = 3, f'font-family: sans-serif; font-weight: bold; fill: {color_main};'
    box_style = f'fill="{color_fill}" stroke="{color_main}" stroke-width="{stroke_width}" rx="15"'

    svg_content = textwrap.dedent(f"""
    <defs>
        <symbol id="star" viewBox="0 0 24 24">
            <path fill="{color_main}" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
        </symbol>
    </defs>
    <use href="#star" x="288" y="-17" width="24" height="24" />
    <use href="#star" x="18" y="283" width="24" height="24" />
    <use href="#star" x="558" y="283" width="24" height="24" />
    <line x1="300" y1="20" x2="50" y2="280" stroke="{color_main}" stroke-width="{stroke_width}" stroke-linecap="round" />
    <line x1="50" y1="280" x2="550" y2="280" stroke="{color_main}" stroke-width="{stroke_width}" stroke-linecap="round" />
    <line x1="300" y1="20" x2="550" y2="280" stroke="{color_main}" stroke-width="{stroke_width}" stroke-linecap="round" />
    <line x1="300" y1="120" x2="300" y2="280" stroke="{color_main}" stroke-width="{stroke_width}" />
    <line x1="175" y1="190" x2="425" y2="190" stroke="{color_main}" stroke-width="{stroke_width}" />
    <g transform="translate(300, 80)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('O','?')}</text></g>
    <g transform="translate(210, 150)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('M','?')}</text></g>
    <g transform="translate(390, 150)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('N','?')}</text></g>
    <g transform="translate(150, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('I','?')}</text></g>
    <g transform="translate(250, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('J','?')}</text></g>
    <g transform="translate(350, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('K','?')}</text></g>
    <g transform="translate(450, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('L','?')}</text></g>
    <g transform="translate(150, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_d}</text></g>
    <g transform="translate(250, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_m}</text></g>
    <g transform="translate(350, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_y[:2]}</text></g>
    <g transform="translate(450, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_y[2:]}</text></g>
    """)
    return f'<svg viewBox="0 -40 600 450" style="width:100%; max-width:500px; margin: 0 auto; display: block;">{svg_content}</svg>'

# --- 詳細圖表渲染 ---
def _render_chart_details(target, username, all_existing_categories):
    # 狀態管理：編輯模式
    edit_key = f"edit_mode_{target['id']}"
    if edit_key not in st.session_state: st.session_state[edit_key] = False
    is_editing = st.session_state[edit_key]

    # 標題區
    c_title, c_btn = st.columns([4, 1])
    with c_title: st.markdown(f"#### 🧬 {target['name']} 的能量導航")
    with c_btn:
        if is_editing:
            if st.button("取消", key=f"cancel_{target['id']}"):
                st.session_state[edit_key] = False
                st.rerun()
        else:
            if st.button("📝 編輯", key=f"edit_{target['id']}"):
                st.session_state[edit_key] = True
                st.rerun()

    # 編輯區塊 (含分類功能)
    if is_editing:
        with st.container(border=True):
            e_name = st.text_input("姓名", value=target['name'])
            e_eng = st.text_input("英文名", value=target['english_name'])
            e_bd = st.date_input("出生日期", value=target['birthdate'])
            
            # --- 分類選擇邏輯 ---
            current_cat = target.get('category', '未分類')
            # 預設選項 + 目前的分類 (若有) + 新增選項
            base_options = sorted(list(set(["家人", "朋友", "同事", "客戶", "未分類"] + all_existing_categories)))
            options = base_options + ["➕ 新增分類..."]
            
            # 確保目前的分類在選項中
            if current_cat not in options: options.insert(0, current_cat)
            
            try:
                cat_index = options.index(current_cat)
            except:
                cat_index = 0
                
            sel_cat = st.selectbox("關係分類", options, index=cat_index)
            
            final_cat = sel_cat
            if sel_cat == "➕ 新增分類...":
                final_cat = st.text_input("請輸入新分類名稱", placeholder="例如：大學同學")
                if not final_cat: final_cat = "未分類" # 防呆
            # -------------------

            c_save, c_del = st.columns([1, 1])
            with c_save:
                if st.button("✅ 儲存變更", type="primary", use_container_width=True):
                    _save_chart(username, e_name, e_eng, e_bd, final_cat, uid=(None if target['type']=='me' else target['id']), is_me=(target['type']=='me'))
                    st.session_state[edit_key] = False
                    st.toast("資料已更新！")
                    time.sleep(1)
                    st.rerun()
            with c_del:
                if target['type'] == 'friend' and st.button("🗑️ 刪除此人", type="secondary", use_container_width=True):
                    _delete_chart(target['id'])
                    st.session_state.selected_profile_id = "ME"
                    st.rerun()
        display_bd, display_name = e_bd, e_eng
    else:
        display_bd, display_name = target['birthdate'], target['english_name']

    # 計算數據
    chart = pds_core.calculate_chart(display_bd, display_name)
    
    # 分頁展示
    t1, t2, t3, t4 = st.tabs(["本命盤 (核心)", "性情數字", "天賦三角形", "高峰與挑戰"])
    
    with t1:
        st.markdown("##### 💎 核心能量指標")
        c1, c2, c3, c4 = st.columns(4)
        with c1: _render_info_row("生命道路", chart.get('lpn'), "#6a3093", True)
        with c2: _render_info_row("姓名內驅", chart.get('soul'), "#e91e63")
        with c3: _render_info_row("事業密碼", chart.get('career'))
        with c4: _render_info_row("制約數字", chart.get('restrict'))
        c5, c6, c7, c8 = st.columns(4)
        with c5: _render_info_row("坐鎮碼", chart.get('anchor'))
        with c6: _render_info_row("內心數字", chart.get('inner'))
        with c7: _render_info_row("個人特質", chart.get('special'))
        with c8: _render_info_row("成熟數字", chart.get('maturity'))
        st.markdown("---")
        st.markdown(f"**🌊 當前流年運勢：第 {chart.get('py')} 數年**")
        st.progress(chart.get('py') / 9)

    with t2:
        st.markdown("##### 🧘 四大性情維度")
        temp = chart.get('temperament', '0-0-0-0').split('-')
        tc1, tc2, tc3, tc4 = st.columns(4)
        tc1.metric("身體", temp[0]); tc2.metric("頭腦", temp[1])
        tc3.metric("情緒", temp[2]); tc4.metric("直覺", temp[3])

    with t3:
        st.markdown("##### 📐 能量幾何視圖")
        chart_svg = _draw_pyramid_svg(chart, display_bd)
        st.markdown(chart_svg, unsafe_allow_html=True)
        st.caption("聯合碼 (Joint Codes)")
        codes = chart.get('triangle_codes', [])
        if codes:
            g_cols = st.columns(6)
            for i, code in enumerate(codes[:6]):
                with g_cols[i]: st.markdown(f"`{code}`")

    with t4:
        st.markdown("##### 🏔️ 人生四大高峰與挑戰")
        try:
            engine = pds_core.NineEnergyNumerology()
            diamond_data = engine.calculate_diamond_chart(display_bd.year, display_bd.month, display_bd.day)
            for stage in diamond_data.get('timeline', []):
                with st.container(border=True):
                    st.markdown(f"**{stage['stage']}** <small>({stage['age_range']})</small>", unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    col1.metric("⭕ 高峰 (機會)", stage.get('p_val', '-'))
                    col2.metric("⚠️ 挑戰 (功課)", stage.get('c_val', '-'))
        except Exception as e:
            st.error(f"運算模組載入失敗: {e}")

# --- 主渲染函式 ---
def render():
    username = st.session_state.username
    
    # 準備資料
    all_profiles = []
    me = _get_my_profile(username)
    if me: all_profiles.append(me)
    else: all_profiles.append({"id": "ME", "name": username, "english_name": "", "birthdate": datetime.date(1990,1,1), "type": "me", "category": "本人"})
    
    friends = _get_saved_charts(username)
    all_profiles.extend(friends)

    # 提取所有已存在的分類 (用於選單選項)
    existing_cats = list(set([p.get('category', '未分類') for p in friends]))

    # --- 1. 上半部：詳細資料 (紅色區塊) ---
    # 確保有選擇
    if "selected_profile_id" not in st.session_state: st.session_state.selected_profile_id = "ME"
    
    # 找出目前選中的人
    target = next((x for x in all_profiles if x['id'] == st.session_state.selected_profile_id), None)
    
    # 如果找不到(可能被刪了)，就預設回自己
    if not target and all_profiles:
        target = all_profiles[0]
        st.session_state.selected_profile_id = target['id']

    if target:
        _render_chart_details(target, username, existing_cats)
    
    st.divider()

    # --- 2. 下半部：家族矩陣列表 (綠色區塊 - 含分類分頁) ---
    st.markdown("### 👨‍👩‍👧‍👦 家族矩陣：親友檔案庫")

    # 新增按鈕區 (放在列表上方)
    with st.expander("➕ 新增親友資料", expanded=False):
        with st.form("add_friend_form"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("姓名"); new_eng = c2.text_input("英文名")
            new_bd = st.date_input("出生日期", min_value=datetime.date(1900,1,1))
            
            # 新增時的分類選擇
            base_opts = sorted(list(set(["家人", "朋友", "同事", "客戶", "未分類"] + existing_cats)))
            new_opts = base_opts + ["➕ 新增分類..."]
            sel_new_cat = st.selectbox("關係分類", new_opts)
            
            if st.form_submit_button("建立檔案", type="primary"):
                final_new_cat = sel_new_cat
                if sel_new_cat == "➕ 新增分類...":
                    # 這裡比較尷尬，因為 form 裡面的 input 如果條件顯示會比較難拿值
                    # 簡化處理：如果選新增，預設存成 "未分類"，讓用戶去編輯改名，或者存一個預設值
                    # 為了 UX，我們假設用戶選這個就是要打字，但因為 streamlit form 限制，我們先存 "未分類"
                    # *更進階做法*：將 text_input 移出 form 或使用 session state。
                    # *這裡採用的折衷方案*：存檔後提示去編輯分類。
                    final_new_cat = "未分類" 
                    st.toast("已建立！若需自訂分類請點擊編輯修改", icon="ℹ️")
                
                _save_chart(username, new_name, new_eng, new_bd, final_new_cat, is_me=False)
                st.rerun()

    # === 分類分頁邏輯 ===
    # 整理分類與對應的人
    # 固定順序：全部 -> 家人 -> 朋友 -> 同事 -> 其他...
    categories_map = {"全部": all_profiles}
    
    # 自動分群
    for p in all_profiles:
        cat = p.get('category', '未分類')
        if not cat: cat = '未分類'
        if cat not in categories_map: categories_map[cat] = []
        categories_map[cat].append(p)
    
    # 決定分頁標籤順序
    fixed_order = ["全部", "本人", "家人", "朋友", "同事", "客戶"]
    dynamic_keys = sorted([k for k in categories_map.keys() if k not in fixed_order])
    # 過濾出實際存在的標籤
    final_tabs = [k for k in fixed_order if k in categories_map] + dynamic_keys
    
    # 渲染 Tabs
    tabs = st.tabs(final_tabs)
    
    for i, tab_name in enumerate(final_tabs):
        with tabs[i]:
            profiles_in_cat = categories_map[tab_name]
            if not profiles_in_cat:
                st.caption("此分類尚無資料")
            else:
                # 渲染該分類下的按鈕
                cols = st.columns(4)
                for idx, p in enumerate(profiles_in_cat):
                    lpn = sum(int(d) for d in p['birthdate'].strftime("%Y%m%d"))
                    while lpn > 9: lpn = sum(int(d) for d in str(lpn))
                    
                    is_selected = (st.session_state.selected_profile_id == p['id'])
                    # 按鈕樣式 (選中的人會有視覺回饋)
                    btn_type = "primary" if is_selected else "secondary"
                    
                    if cols[idx % 4].button(
                        f"{p['name']}\n{lpn}號人", 
                        key=f"btn_{tab_name}_{p['id']}", # key 加上 tab 名稱避免重複
                        use_container_width=True,
                        type=btn_type
                    ):
                        st.session_state.selected_profile_id = p['id']
                        st.rerun()