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

# ==========================================
# ★ 新增：中文轉威妥瑪拼音的魔法函式
# ==========================================
def get_wade_giles(text):
    """將中文姓名轉換為威妥瑪拼音 (大寫)"""
    if not text: return ""
    try:
        from pypinyin import pinyin, Style
        # 轉換為威妥瑪拼音 (會帶有數字聲調，例如 CHUN1)
        raw_pinyin = pinyin(text, style=Style.WADEGILES)
        result = []
        for item in raw_pinyin:
            # 移除非英文字母的字元 (過濾掉數字)，並轉成大寫
            clean_text = ''.join([c for c in item[0] if c.isalpha()]).upper()
            result.append(clean_text)
        return " ".join(result) # 以空格分隔，例如：YU CHIAO CHUN
    except ImportError:
        print("尚未安裝 pypinyin 套件")
        return ""
    except Exception:
        return ""


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
                supabase.table("saved_charts").insert({"line_user_id": line_id, "name": name, "english_name": eng, "birth_date": bd_str}).execute()
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
    # ==========================================
    # 1. 🛡️ 防護機制：確認登入狀態與身分對位
    # ==========================================
    line_id = st.session_state.get("line_user_id") 
    if not line_id:
        st.warning("請先透過 LINE 登入")
        return

    # 🎒 取得使用者資料 (合併重複宣告，統一使用 c_name)
    user_profile = st.session_state.get("user_profile") or {}
    c_name = user_profile.get("full_name") or st.session_state.get("username", "未知姓名")
    
    # ★ 關鍵修復：取得自己的真實生日，若無則預設 1990-01-01 (避免算錯命數)
    my_bd_str = user_profile.get("birth_date")
    if my_bd_str:
        my_bd = datetime.datetime.strptime(my_bd_str, "%Y-%m-%d").date()
    else:
        my_bd = datetime.date(1990, 1, 1)

    # ==========================================
    # 2. ★ 乾淨俐落的單一標題
    # ==========================================
    st.markdown(f"### 👨‍👩‍👧‍👦 {c_name} 的家族矩陣：親友檔案庫")
    st.write("") 
       
    # ==========================================
    # 3. 準備親友資料清單
    # ==========================================
    # 確保 friends_raw 有資料，若無則預設為空列表 [] (避免報錯)
    friends_list = friends_raw if friends_raw is not None else []

    all_profiles = []
    
    # 把「自己」加進列表 (使用動態抓取的真實姓名與生日)
    all_profiles.append({
        "id": "ME", 
        "name": c_name, 
        "english_name": user_profile.get("english_name", ""), 
        "birthdate": my_bd, 
        "type": "me"
    })

    # 把「親友」加進列表
    for d in friends_list:
        bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1990,1,1)
        all_profiles.append({
            "id": d.get('id'), 
            "name": d.get('name', '未命名'), 
            "english_name": d.get('english_name', ""), 
            "birthdate": bd, 
            "category": d.get('category', "未分類"), # ★ 新增這行：抓取分類
            "type": "friend"
        })


    # ==========================================
    # ★ 新增：動態生成分類選單 (記憶用戶的自訂分類)
    # ==========================================
    default_cats = ["家人", "朋友", "同事", "客戶", "未分類"]
    # 抓取用戶所有親友目前使用的分類
    existing_cats = [p.get("category", "未分類") for p in all_profiles if p.get("type") == "friend"]
    # 合併清單、去除重複項，並保留預設選項在最前面
    cat_options = list(dict.fromkeys(default_cats + existing_cats))

    
    # ==========================================
    # 4. 介面展示 (新增表單與卡片列表)
    # ==========================================
    with st.expander("➕ 新增親友資料", expanded=False):
        with st.form("family_matrix_add_form"):
            # 第一排：姓名與英文名
            c1, c2 = st.columns(2)
            new_name = c1.text_input("姓名")
            new_eng = c2.text_input("英文名", placeholder="留空白，系統自動生成威妥瑪拼音")
            
            # 第二排：生日、下拉分類、自訂分類 (切成 3 欄)
            c3, c4, c5 = st.columns(3)
            new_bd = c3.date_input("出生日期", min_value=datetime.date(1900,1,1))
            new_cat_select = c4.selectbox("📂 選擇現有分類", cat_options, index=cat_options.index("未分類"))
            new_cat_custom = c5.text_input("✏️ 或自訂新分類", placeholder="若填寫將優先使用")

            if st.form_submit_button("建立檔案", type="primary"):
                # 1. 處理英文名與分類
                final_eng = new_eng.strip() if new_eng.strip() else get_wade_giles(new_name)
                final_cat = new_cat_custom.strip() if new_cat_custom.strip() else new_cat_select
                
                # 2. ★ 終極修復：直接將資料寫入 Supabase，不再依賴舊的 _save_chart
                from app import supabase
                if supabase:
                    try:
                        # ★ 從系統記憶中抓取目前登入者的 LINE 名稱
                        current_username = st.session_state.get("username", "未知用戶")

                        # 執行資料庫的新增指令 (Insert)
                        supabase.table("saved_charts").insert({
                            "line_user_id": line_id,
                            "username": current_username, # ★ 核心修復：強制把您的名字寫進資料庫
                            "name": new_name,
                            "english_name": final_eng,
                            "birth_date": str(new_bd),
                            "category": final_cat
                        }).execute()
                        
                        # 成功提示與畫面刷新
                        st.success(f"✅ 已成功新增親友檔案：{new_name}")
                        import time; time.sleep(1); st.rerun()
                        
                    except Exception as e:
                        st.error(f"⚠️ 寫入資料庫失敗: {e}")
                else:
                    st.error("⚠️ 無法連線至資料庫，請稍後再試。")

    st.divider()

    # 使用 session_state 紀錄目前選中的 profile_id
    if "selected_profile_id" not in st.session_state:
        st.session_state.selected_profile_id = "ME"

    # 渲染頭像列表
    # ==========================================
    # ★ 新增：動態分類分頁標籤 (Tabs)
    # ==========================================
    # 1. 抓取目前所有親友的「不重複分類」清單
    unique_cats = []
    for p in all_profiles:
        cat = p.get("category")
        # 排除掉自己(ME)，只收集親友的分類
        if cat and cat not in unique_cats and p["id"] != "ME":
            unique_cats.append(cat)
            
    # 2. 建立分頁標籤 (把 "全部" 永遠放第一位，其餘自動排列)
    tab_titles = ["🌟 全部"] + [f"📂 {c}" for c in unique_cats]
    tabs = st.tabs(tab_titles)

    # 3. 根據選中的分頁，過濾並顯示對應的按鈕
    for i, tab in enumerate(tabs):
        with tab:
            current_title = tab_titles[i]
            
            # 過濾邏輯：如果是「全部」，就顯示所有人；否則只抓對應分類的人
            if "全部" in current_title:
                display_profiles = all_profiles
            else:
                target_cat = current_title.replace("📂 ", "")
                display_profiles = [p for p in all_profiles if p.get('category') == target_cat]

            # 渲染該分頁的頭像列表
            if not display_profiles:
                st.info("此分類目前沒有親友資料。")
            else:
                cols = st.columns(4)
                for idx, p in enumerate(display_profiles):
                    # 計算主命數
                    lpn = sum(int(d) for d in p['birthdate'].strftime("%Y%m%d"))
                    while lpn > 9: lpn = sum(int(d) for d in str(lpn))
                    
                    is_selected = (st.session_state.selected_profile_id == p['id'])
                    btn_type = "primary" if is_selected else "secondary"
                    
                    with cols[idx % 4]:
                        # ⚠️ 關鍵防呆：按鈕的 key 必須加上分頁編號 (i)，防止 Streamlit 報錯重複的 ID
                        if st.button(
                            f"{p['name']}\n{lpn}號人", 
                            key=f"btn_tab{i}_{p['id']}", 
                            use_container_width=True,
                            type=btn_type,
                            help=f"點擊查看 {p['name']} 的詳細盤"
                        ):
                            st.session_state.selected_profile_id = p['id']
                            st.rerun()

    st.divider()

    # ==========================================
    # ★ 新增：選定親友的專屬「修改/刪除」面板
    # ==========================================
    target_id = st.session_state.selected_profile_id
    target_profile = next((p for p in all_profiles if p['id'] == target_id), None)

    if target_profile:
        # 1. 判斷如果是「自己 (ME)」，提示去會員中心改
        if target_profile['id'] == "ME":
            st.info("💡 這是您本人的本命盤。如需修改姓名或生日，請至「👤 會員中心」進行更新。")
        
        # 2. 如果是「親友」，就顯示最新的修改與刪除表單
        else:
            with st.expander(f"⚙️ 管理【{target_profile['name']}】的檔案 (修改 / 刪除)", expanded=False):
                with st.form(f"edit_form_{target_id}"):
                    c1, c2 = st.columns(2)
                    edit_name = c1.text_input("📝 修改姓名", value=target_profile['name'])
                    edit_eng = c2.text_input("📝 修改英文名", value=target_profile['english_name'], placeholder="留空白，系統自動生成威妥瑪拼音")
                    
                    c3, c4, c5 = st.columns(3)
                    edit_bd = c3.date_input("📅 修改出生日期", value=target_profile['birthdate'], min_value=datetime.date(1900,1,1))
                    
                    default_cats = ["家人", "朋友", "同事", "客戶", "未分類"]
                    existing_cats = [p.get("category", "未分類") for p in all_profiles if p.get("type") == "friend"]
                    dynamic_cat_options = list(dict.fromkeys(default_cats + existing_cats))
                    
                    current_cat = target_profile.get("category", "未分類")
                    if current_cat not in dynamic_cat_options:
                        dynamic_cat_options.append(current_cat)
                    cat_index = dynamic_cat_options.index(current_cat)
                    
                    edit_cat_select = c4.selectbox("📂 修改現有分類", dynamic_cat_options, index=cat_index)
                    edit_cat_custom = c5.text_input("✏️ 或變更為新分類", placeholder="若填寫將優先使用")

                    st.write("") 
                    col_submit, col_delete = st.columns([1, 1])
                    
                    with col_submit:
                        if st.form_submit_button("💾 儲存修改", type="primary", use_container_width=True):
                            final_edit_eng = edit_eng.strip() if edit_eng.strip() else get_wade_giles(edit_name)
                            final_edit_cat = edit_cat_custom.strip() if edit_cat_custom.strip() else edit_cat_select
                            
                            from app import supabase
                            if supabase:
                                try:
                                    supabase.table("saved_charts").update({
                                        "name": edit_name,
                                        "english_name": final_edit_eng,
                                        "birth_date": str(edit_bd),
                                        "category": final_edit_cat 
                                    }).eq("id", target_id).execute()
                                    st.success(f"✅ 已成功更新 {edit_name} 的資料！")
                                    import time; time.sleep(1); st.rerun()
                                except Exception as e:
                                    st.error(f"修改失敗: {e}")
                    
                    with col_delete:
                        delete_confirm = st.checkbox("⚠️ 確認刪除此檔案 (打勾後再按刪除)")
                        if st.form_submit_button("🗑️ 刪除檔案", use_container_width=True):
                            if delete_confirm:
                                from app import supabase
                                if supabase:
                                    try:
                                        supabase.table("saved_charts").delete().eq("id", target_id).execute()
                                        st.session_state.selected_profile_id = "ME"
                                        st.success("✅ 檔案已徹底刪除！")
                                        import time; time.sleep(1); st.rerun()
                                    except Exception as e:
                                        st.error(f"刪除失敗: {e}")
                            else:
                                st.warning("請先勾選上方的「確認刪除此檔案」再執行刪除動作。")

        # ==========================================
        # ★ 升級：動態生成專屬能量導航精美卡片
        # ==========================================
        t_name = target_profile.get("name", "未知")
        t_eng = target_profile.get("english_name", "")
        t_bd = target_profile.get("birthdate", "未知")
    
        display_eng = f" <span style='font-size: 16px; color: #888;'>({t_eng})</span>" if t_eng else ""

        st.markdown(f"""
        <div style="background: linear-gradient(to right, #ffffff, #f9fbfd); padding: 20px 25px; border-radius: 15px; border-left: 6px solid #6a3093; box-shadow: 0 4px 15px rgba(0,0,0,0.04); margin-bottom: 25px; margin-top: 10px;">
            <div style="font-size: 24px; font-weight: 800; color: #2c3e50; margin-bottom: 8px; letter-spacing: 0.5px;">
                🧬 {t_name}{display_eng} 的專屬能量導航
            </div>
            <div style="font-size: 15px; color: #555;">
                📅 <b>西元出生日期：</b> <span style="color: #6a3093; font-weight: bold;">{t_bd}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    

    # --- 3. 詳細資料展示區 ---
    st.write("")
    target = next((x for x in all_profiles if x['id'] == st.session_state.selected_profile_id), None)
    
    if target:
        # 狀態管理：編輯模式
        edit_key = f"edit_mode_{target['id']}"
        if edit_key not in st.session_state: st.session_state[edit_key] = False
        
        is_editing = st.session_state[edit_key]

    
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
            st.markdown("##### 🏔️ 人生四大高峰與挑戰 (Diamond Chart)")
            engine = pds_core.NineEnergyNumerology()
            diamond_data = engine.calculate_diamond_chart(display_bd.year, display_bd.month, display_bd.day)

            for stage in diamond_data.get('timeline', []):
                stage_name = stage.get("stage", "階段")
                age_range = stage.get("age_range", "")
                pinnacle = stage.get("p_val", "-")
                challenge = stage.get("c_val", "-")

                with st.container(border=True):
                    st.markdown(f"""
                    <div style="display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:12px;">
                        <div style="font-size:20px; font-weight:700;">{stage_name}</div>
                        <div style="color:#5c43b8; font-weight:600;">{age_range}</div>
                    </div>
                    <div style="height:2px; background:#efeef9; margin:10px 0 16px;"></div>
                    """, unsafe_allow_html=True)
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div style="border-radius:12px; padding:14px; background:linear-gradient(145deg,#ffe7e6,#ffd0cb); text-align:center; box-shadow:0 6px 14px rgba(198, 0, 0, 0.08);">
                            <div style="font-size:14px; letter-spacing:0.4px;">⭕ 高峰數</div>
                            <div style="font-size:28px; font-weight:700; color:#c62828;">{pinnacle}</div>
                            <div style="font-size:12px; color:#992828;">開闢機會 / 能量紅利</div>
                        </div>
                        """, unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"""
                        <div style="border-radius:12px; padding:14px; background:linear-gradient(145deg,#e6e1ff,#d0c1ff); text-align:center; box-shadow:0 6px 14px rgba(76, 0, 153, 0.08);">
                            <div style="font-size:14px; letter-spacing:0.4px;">⚠️ 挑戰數</div>
                            <div style="font-size:28px; font-weight:700; color:#4b0082;">{challenge}</div>
                            <div style="font-size:12px; color:#4b0082;">功課 / 能量試煉</div>
                        </div>
                        """, unsafe_allow_html=True)
    else:
        st.info("請先建立或選擇一筆檔案，以顯示能量導航資訊。")

    st.divider()