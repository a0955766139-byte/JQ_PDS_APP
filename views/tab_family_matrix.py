import streamlit as st
import datetime
import time
import os
from supabase import create_client, Client

# --- 核心模組匯入 (保持 PDS 核心不變) ---
try:
    import pds_core
except ImportError:
    # 模擬 pds_core 供測試，防止報錯
    class MockPDS:
        def calculate_chart(self, bd, name):
            # 簡易模擬數據
            total = sum(int(d) for d in bd.strftime("%Y%m%d"))
            while total > 9: total = sum(int(d) for d in str(total))
            return {
                'lpn': total, 'soul': 1, 'career': 8, 'restrict': 5, 'anchor': 4,
                'inner': 3, 'special': 9, 'maturity': 6, 'py': (datetime.date.today().year - bd.year + 1) % 9 or 9,
                'temperament': '2-3-1-4', 
                'svg_params': {'O':6,'M':3,'N':3,'I':1,'J':2,'K':2,'L':1},
                'triangle_codes': ['12-3', '45-9'] * 6
            }
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
            return {"id": "ME", "name": d.get('full_name', username), "english_name": d.get('english_name', ""), "birthdate": bd, "type": "me"}
        return None
    except: return None

# --- 資料存取函式 ---
def get_user_charts():
    """核心：使用真實 ID (joe1369) 抓取資料庫 22 筆資料"""
    # 💡 從 Session 抓取不變的 ID 標籤
    line_id = st.session_state.get("line_user_id") 
    
    if not line_id:
        st.warning("⚠️ 尚未取得 LINE ID，無法讀取數據")
        return []
    try:
        # 💡 查詢語法：eq("user_id", "joe1369")
        response = supabase.table("saved_charts") \
            .select("*") \
            .eq("line_user_id", line_id) \
            .execute()
        return response.data
    except Exception as e:
        st.error(f"讀取資料庫失敗: {e}")
        return []

def _save_chart(line_id, name, eng, bd, uid=None, is_me=False):
    """存檔：確保門牌號碼是唯一 LINE ID"""
    if not supabase: return
    try:
        bd_str = bd.isoformat()
        if is_me:
            # users 表格使用 line_user_id 作為 Unique Key
            supabase.table("users").upsert({
                "line_user_id": line_id, 
                "full_name": name, 
                "english_name": eng, 
                "birth_date": bd_str
            }, on_conflict="line_user_id").execute()
        else:
            if uid: # 更新
                supabase.table("saved_charts").update({"name": name, "english_name": eng, "birth_date": bd_str}).eq("id", uid).execute()
            else: # 新增：這裡 user_id 必須填入真實 ID
                supabase.table("saved_charts").insert({"user_id": line_id, "name": name, "english_name": eng, "birth_date": bd_str}).execute()
    except Exception as e: 
        st.error(f"存檔失敗: {e}")

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
    s_d = f"{bd.day:02d}"
    s_m = f"{bd.month:02d}"
    s_y = f"{bd.year:04d}"
    color_main, color_fill = "#6a3093", "#ffffff"
    stroke_width, font_style = 2, 'font-family: sans-serif; font-weight: bold; fill: #6a3093;'
    box_style = f'fill="{color_fill}" stroke="{color_main}" stroke-width="{stroke_width}" rx="5"'

    svg = f"""
<svg viewBox="0 0 600 420" style="width:100%; max-width:500px; margin: 0 auto; display: block;">
<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto"><path d="M0,0 L0,10 L10,5 z" fill="{color_main}" /></marker></defs>
<path d="M300,20 L50,280 L550,280 Z" fill="none" stroke="{color_main}" stroke-width="3" />
<line x1="300" y1="120" x2="300" y2="280" stroke="{color_main}" stroke-width="2" />
<line x1="175" y1="190" x2="425" y2="190" stroke="{color_main}" stroke-width="2" />
<g transform="translate(300, 80)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('O','?')}</text></g>
<g transform="translate(210, 150)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('M','?')}</text></g>
<g transform="translate(390, 150)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('N','?')}</text></g>
<g transform="translate(150, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('I','?')}</text></g>
<g transform="translate(250, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('J','?')}</text></g>
<g transform="translate(350, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('K','?')}</text></g>
<g transform="translate(450, 240)"><rect x="-25" y="-25" width="50" height="50" {box_style} /><text x="0" y="8" text-anchor="middle" font-size="24" {font_style}>{p.get('L','?')}</text></g>
<line x1="50" y1="280" x2="550" y2="280" stroke="{color_main}" stroke-width="2" />
<g transform="translate(150, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_d}</text></g>
<g transform="translate(250, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_m}</text></g>
<g transform="translate(350, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_y[:2]}</text></g>
<g transform="translate(450, 340)"><text x="0" y="8" text-anchor="middle" font-size="28" {font_style}>{s_y[2:]}</text></g>
</svg>
"""
    return svg

# --- 主渲染邏輯 ---
def render(friends_raw=None):
    # 1. 💡 身分對位：後台用的門牌 (joe1369)
    line_id = st.session_state.get("line_user_id") 
    
    # 2. 💡 視覺對位：前台顯現的稱呼 (喬鈞老師)
    display_name = st.session_state.get("username", "未知用戶")
    
    # 3. 顯示歡迎語
    st.markdown(f"### 👨‍👩‍👧‍👦 {display_name} 的家族矩陣") # 這裡顯示姓名
    
    # 4. 取得親友資料
    friends_raw = friends_raw if friends_raw is not None else get_user_charts()
    
    st.markdown("### 👨‍👩‍👧‍👦 家族矩陣：親友檔案庫")
    
    # --- 1. 資料準備 ---
    all_profiles = []
    
    # 取得自己 (模擬或從 users 表抓)
    all_profiles.append({"id": "ME", "name": display_name, "english_name": "", "birthdate": datetime.date(2000,1,1), "type": "me"})

    for d in friends_raw:
        bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(2000,1,1)
        all_profiles.append({"id": d['id'], "name": d['name'], "english_name": d.get('english_name', ""), "birthdate": bd, "type": "friend"})

    # 💡 修正：新增按鈕傳入 line_id 而非 username
    with st.expander("➕ 新增親友資料", expanded=False):
        with st.form("family_matrix_add_form"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("姓名")
            new_eng = c2.text_input("英文名")
            new_bd = st.date_input("出生日期", min_value=datetime.date(1900,1,1))
            if st.form_submit_button("建立檔案", type="primary"):
                _save_chart(line_id, new_name, new_eng, new_bd, is_me=False)
                st.rerun()

    st.divider()

    # --- 2. 列表展示 (Card View) ---
    # 使用 session_state 紀錄目前選中的 profile_id
    if "selected_profile_id" not in st.session_state:
        st.session_state.selected_profile_id = "ME"

    # 渲染頭像列表
    cols = st.columns(4)
    for idx, p in enumerate(all_profiles):
        # 計算主命數作為 Icon
        lpn = sum(int(d) for d in p['birthdate'].strftime("%Y%m%d"))
        while lpn > 9: lpn = sum(int(d) for d in str(lpn))
        
        is_selected = (st.session_state.selected_profile_id == p['id'])
        
        # 卡片樣式
        card_bg = "#f0f2f6" if not is_selected else "#e3d5f2"
        border_color = "transparent" if not is_selected else "#6a3093"
        
        with cols[idx % 4]:
            if st.button(
                f"{p['name']}\n{lpn}號人", 
                key=f"btn_{p['id']}", 
                use_container_width=True,
                help=f"點擊查看 {p['name']} 的詳細盤"
            ):
                st.session_state.selected_profile_id = p['id']
                st.rerun()

    # --- 3. 詳細資料展示區 ---
    st.write("")
    target = next((x for x in all_profiles if x['id'] == st.session_state.selected_profile_id), None)
    
    if target:
        # 狀態管理：編輯模式
        edit_key = f"edit_mode_{target['id']}"
        if edit_key not in st.session_state: st.session_state[edit_key] = False
        
        is_editing = st.session_state[edit_key]

        # 標題區 + 編輯按鈕
        c_title, c_btn = st.columns([4, 1])
        with c_title:
            st.markdown(f"#### 🧬 {target['name']} 的能量導航")
        with c_btn:
            if is_editing:
                if st.button("取消", key=f"fam_cancel_{target['id']}"):
                    st.session_state[edit_key] = False
                    st.rerun()
            else:
                if st.button("📝 編輯", key=f"fam_edit_{target['id']}"):
                    st.session_state[edit_key] = True
                    st.rerun()

        # 編輯模式與檢視模式切換
        if is_editing:
            with st.container(border=True):
                e_name = st.text_input("姓名", value=target['name'])
                e_eng = st.text_input("英文名", value=target['english_name'])
                e_bd = st.date_input(
                    "出生日期",
                    value=target['birthdate'],
                    min_value=datetime.date(1900, 1, 1),
                    max_value=datetime.date(2026, 12, 31)
                )
                
                c_save, c_del = st.columns([1, 1])
                with c_save:
                    if st.button("✅ 儲存變更", type="primary", use_container_width=True):
                        _save_chart(line_id, e_name, e_eng, e_bd, uid=(None if target['type']=='me' else target['id']), is_me=(target['type']=='me'))
                        st.session_state[edit_key] = False
                        st.toast("資料已更新！")
                        time.sleep(1)
                        st.rerun()
                with c_del:
                    if target['type'] == 'friend':
                        if st.button("🗑️ 刪除此人", type="secondary", use_container_width=True):
                            _delete_chart(target['id'])
                            st.session_state.selected_profile_id = "ME"
                            st.rerun()
            
            # 編輯時暫時使用新輸入的資料來預覽 (或暫停顯示盤)
            display_bd = e_bd
            display_name = e_eng
        else:
            display_bd = target['birthdate']
            display_name = target['english_name']

        # --- 計算能量數據 ---
        chart = pds_core.calculate_chart(display_bd, display_name)
        
        # --- 4 大分頁展示 ---
        t1, t2, t3, t4 = st.tabs(["本命盤 (核心)", "性情數字", "天賦三角形", "高峰與挑戰"])
        
        # [Tab 1] 本命盤
        with t1:
            st.markdown("##### 💎 核心能量指標")
            
            # 第一排
            c1, c2, c3, c4 = st.columns(4)
            with c1: _render_info_row("生命道路", chart.get('lpn'), "#6a3093", True)
            with c2: _render_info_row("姓名內驅", chart.get('soul'), "#e91e63")
            with c3: _render_info_row("事業密碼", chart.get('career'))
            with c4: _render_info_row("制約數字", chart.get('restrict'))
            
            # 第二排
            c5, c6, c7, c8 = st.columns(4)
            with c5: _render_info_row("坐鎮碼", chart.get('anchor'))
            with c6: _render_info_row("內心數字", chart.get('inner'))
            with c7: _render_info_row("個人特質", chart.get('special'))
            with c8: _render_info_row("成熟數字", chart.get('maturity'))
            
            # 流年特別強調
            st.markdown("---")
            st.markdown(f"**🌊 當前流年運勢：第 {chart.get('py')} 數年**")
            st.progress(chart.get('py') / 9)

        # [Tab 2] 性情數字
        with t2:
            st.markdown("##### 🧘 四大性情維度")
            temp = chart.get('temperament', '0-0-0-0').split('-')
            
            tc1, tc2, tc3, tc4 = st.columns(4)
            with tc1: 
                st.metric("身體 (Body)", temp[0])
                st.caption("行動力、執行力")
            with tc2: 
                st.metric("頭腦 (Mind)", temp[1])
                st.caption("邏輯、思考")
            with tc3: 
                st.metric("情緒 (Emotion)", temp[2])
                st.caption("感受、表達")
            with tc4: 
                st.metric("直覺 (Intuition)", temp[3])
                st.caption("靈感、潛意識")

        # [Tab 3] 天賦三角形
        with t3:
            st.markdown("##### 📐 能量幾何視圖")
            svg_html = _draw_pyramid_svg(chart, display_bd)
            st.markdown(svg_html, unsafe_allow_html=True)
            
            st.write("")
            st.markdown("**🔗 聯合碼 (Joint Codes)**")
            # 模擬 12 組聯合碼展示 (兩兩一組)
            codes = chart.get('triangle_codes', [])
            if codes:
                g_cols = st.columns(6)
                for i, code in enumerate(codes[:6]): # 展示前6組
                    with g_cols[i]: st.markdown(f"`{code}`")

        # [Tab 4] 高峰與挑戰
        with t4:
            st.warning("🚧 曼格拉系統運算法則開發中...")
            st.info("此區塊將展示人生四大高峰與挑戰數字，敬請期待 V2.1 更新。")