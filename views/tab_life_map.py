import streamlit as st
import datetime
import os
import time
from supabase import create_client
from pypinyin import pinyin, Style  # 引入拼音套件

# 引入 UI 模組
from views import life_map_ui

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

# --- 輔助函式：自動生成威妥碼拼音 ---
def _auto_generate_english_name(chinese_name):
    """
    將中文姓名轉換為威妥碼拼音 (Wade-Giles)
    例如：游喬鈞 -> Yu Chiao Chun
    """
    if not chinese_name: return ""
    try:
        # 使用 pypinyin 套件進行轉換
        # heteronym=False: 不啟用多音字模式，避免回傳太多選項
        # style=Style.WADEGILES: 指定威妥碼拼音
        pinyin_list = pinyin(chinese_name, style=Style.WADEGILES, heteronym=False)
        
        # 處理結果：將 list of lists 轉為字串
        # pinyin 回傳格式為 [['yu'], ['chiao'], ['chun']]
        # 我們將其轉換為 "Yu Chiao Chun" (首字母大寫)
        english_parts = [item[0].capitalize() for item in pinyin_list]
        return " ".join(english_parts)
    except Exception as e:
        print(f"Translation Error: {e}")
        return ""

# --- 資料存取函式 ---
def _get_my_profile(username):
    if not supabase: return None
    try:
        res = supabase.table("users").select("*").eq("username", username).execute()
        if res.data:
            d = res.data[0]
            bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1990,1,1)
            return {"id": "ME", "name": d.get('full_name', username), "english_name": d.get('english_name', ""), "birthdate": bd, "type": "me", "category": "本人"}
        return None
    except: return None

def _get_saved_charts(username):
    if not supabase: return []
    try:
        res = supabase.table("saved_charts").select("*").eq("user_id", username).order("created_at", desc=True).execute()
        data = []
        for d in res.data:
            bd = datetime.datetime.strptime(d['birth_date'], "%Y-%m-%d").date() if d.get('birth_date') else datetime.date(1990,1,1)
            cat = d.get('category') if d.get('category') else "未分類"
            data.append({"id": d['id'], "name": d['name'], "english_name": d.get('english_name', ""), "birthdate": bd, "type": "friend", "category": cat})
        return data
    except: return []

def _save_chart(username, name, eng, bd, category, uid=None, is_me=False):
    if not supabase: 
        st.error("❌ 資料庫未連線")
        return

    try:
        bd_str = bd.isoformat()
        final_category = category if category else "未分類"

        # --- [關鍵功能] 自動補全英文名 ---
        # 如果使用者沒有輸入英文名 (eng 為空字串或 None)，則自動翻譯
        final_eng = eng
        if not final_eng or not final_eng.strip():
            final_eng = _auto_generate_english_name(name)
            # 可以在這裡加一個提示，告訴用戶系統幫他做了什麼
            if final_eng:
                st.toast(f"🪄 已自動為您生成英文名：{final_eng}")
        # --------------------------------

        data_payload = {
            "user_id": username, 
            "name": name, 
            "english_name": final_eng, 
            "birth_date": bd_str, 
            "category": final_category
        }

        if is_me:
            # 更新本人
            supabase.table("users").upsert({
                "username": username, 
                "full_name": name, 
                "english_name": final_eng, 
                "birth_date": bd_str
            }, on_conflict="username").execute()
            st.toast("✅ 本人資料已更新")
        
        else:
            # 更新/新增 親友
            if uid:
                supabase.table("saved_charts").update(data_payload).eq("id", uid).execute()
                st.toast("✅ 親友資料已更新")
            else:
                response = supabase.table("saved_charts").insert(data_payload).execute()
                if response.data:
                    st.toast("🎉 親友新增成功！")
                else:
                    st.warning("⚠️ 新增指令已送出，但沒有回傳確認，請刷新檢查。")

    except Exception as e:
        st.error(f"💀 存檔失敗，錯誤原因：{str(e)}")
        print(f"DEBUG ERROR: {e}")

def _delete_chart(chart_id):
    if not supabase: return
    try: supabase.table("saved_charts").delete().eq("id", chart_id).execute()
    except: pass

# --- 詳細資料區塊 (包含編輯功能) ---
def _render_chart_details_section(target, username, all_existing_categories):
    # 狀態管理：編輯模式
    edit_key = f"edit_mode_{target['id']}"
    if edit_key not in st.session_state: st.session_state[edit_key] = False
    is_editing = st.session_state[edit_key]

    # --- [關鍵修改] 標題區：加入英文名字顯示 ---
    c_title, c_btn = st.columns([4, 1])
    with c_title: 
        # 準備英文名字字串 (灰色小字)
        eng_display = ""
        if target.get('english_name'):
            eng_display = f" <span style='font-size:0.7em; color:#666; font-weight:normal'>({target['english_name']})</span>"
            
        # 渲染標題 (需開啟 unsafe_allow_html 才能吃 HTML 語法)
        st.markdown(f"#### 🧬 {target['name']}{eng_display} 的能量導航", unsafe_allow_html=True)
    # -----------------------------------------

    with c_btn:
        if is_editing:
            if st.button("取消", key=f"cancel_{target['id']}"):
                st.session_state[edit_key] = False
                st.rerun()
        else:
            if st.button("📝 編輯", key=f"edit_{target['id']}"):
                st.session_state[edit_key] = True
                st.rerun()

    # 編輯模式：顯示表單
    if is_editing:
        with st.container(border=True):
            with st.form(key=f"edit_form_{target['id']}"):
                e_name = st.text_input("姓名", value=target['name'])
                
                # 提示用戶可以留空
                e_eng = st.text_input(
                    "英文名 (可留空，系統將自動翻譯)", 
                    value=target['english_name'],
                    placeholder="例如: Yu Chiao Chun"
                )
                
                e_bd = st.date_input(
                    "出生日期", 
                    value=target['birthdate'], 
                    min_value=datetime.date(1900, 1, 1),
                    max_value=datetime.date.today()
                )
                
                st.caption("設定關係分類")
                c_cat_sel, c_cat_new = st.columns([1, 1])
                
                current_cat = target.get('category', '未分類')
                base_options = sorted(list(set(["家人", "朋友", "同事", "客戶", "未分類"] + all_existing_categories)))
                
                if current_cat not in base_options: base_options.insert(0, current_cat)
                try: cat_index = base_options.index(current_cat)
                except: cat_index = 0

                with c_cat_sel:
                    sel_cat = st.selectbox("選擇現有分類", base_options, index=cat_index)
                with c_cat_new:
                    new_cat_input = st.text_input("或建立新分類", placeholder="輸入名稱 (如: 球友)")

                if st.form_submit_button("✅ 儲存變更", type="primary", use_container_width=True):
                    final_cat = new_cat_input.strip() if new_cat_input.strip() else sel_cat
                    _save_chart(username, e_name, e_eng, e_bd, final_cat, uid=(None if target['type']=='me' else target['id']), is_me=(target['type']=='me'))
                    st.session_state[edit_key] = False
                    time.sleep(1)
                    st.rerun()

            if target['type'] == 'friend':
                if st.button("🗑️ 刪除此人", type="secondary", use_container_width=True, key=f"del_{target['id']}"):
                    _delete_chart(target['id'])
                    st.session_state.selected_profile_id = "ME"
                    st.rerun()
        
        life_map_ui.render_energy_tabs(target['birthdate'], target['english_name'])
        
    else:
        life_map_ui.render_energy_tabs(target['birthdate'], target['english_name'])

# --- 主渲染入口 ---
def render():
    username = st.session_state.username
    
    all_profiles = []
    me = _get_my_profile(username)
    if me: all_profiles.append(me)
    else: all_profiles.append({"id": "ME", "name": username, "english_name": "", "birthdate": datetime.date(1990,1,1), "type": "me", "category": "本人"})
    
    friends = _get_saved_charts(username)
    all_profiles.extend(friends)

    existing_cats = list(set([p.get('category', '未分類') for p in friends]))

    if "selected_profile_id" not in st.session_state: st.session_state.selected_profile_id = "ME"
    target = next((x for x in all_profiles if x['id'] == st.session_state.selected_profile_id), None)
    
    if not target and all_profiles:
        target = all_profiles[0]
        st.session_state.selected_profile_id = target['id']

    if target:
        _render_chart_details_section(target, username, existing_cats)
    
    st.divider()

    st.markdown("### 👨‍👩‍👧‍👦 家族矩陣：親友檔案庫")

    with st.expander("➕ 新增親友資料", expanded=False):
        with st.form("add_friend_form"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("姓名")
            # 提示用戶可以留空
            new_eng = c2.text_input("英文名 (留空則自動生成)", placeholder="系統將自動轉換為威妥碼拼音")
            
            new_bd = st.date_input(
                "出生日期", 
                min_value=datetime.date(1900,1,1),
                max_value=datetime.date.today()
            )
            
            st.caption("設定關係分類")
            c_cat_1, c_cat_2 = st.columns([1, 1])
            with c_cat_1:
                base_opts = sorted(list(set(["家人", "朋友", "同事", "客戶", "未分類"] + existing_cats)))
                sel_new_cat = st.selectbox("選擇現有分類", base_opts)
            with c_cat_2:
                manual_new_cat = st.text_input("或建立新分類", placeholder="例如: 大學同學")
            
            if st.form_submit_button("建立檔案", type="primary"):
                final_new_cat = manual_new_cat.strip() if manual_new_cat.strip() else sel_new_cat
                _save_chart(username, new_name, new_eng, new_bd, final_new_cat, is_me=False)
                st.toast(f"已新增 {new_name} 到 {final_new_cat}！")
                time.sleep(1)
                st.rerun()

    categories_map = {"全部": all_profiles}
    for p in all_profiles:
        cat = p.get('category', '未分類') or '未分類'
        if cat not in categories_map: categories_map[cat] = []
        categories_map[cat].append(p)
    
    fixed_order = ["全部", "本人", "家人", "朋友", "同事", "客戶"]
    dynamic_keys = sorted([k for k in categories_map.keys() if k not in fixed_order])
    final_tabs = [k for k in fixed_order if k in categories_map] + dynamic_keys
    
    tabs = st.tabs(final_tabs)
    for i, tab_name in enumerate(final_tabs):
        with tabs[i]:
            profiles = categories_map[tab_name]
            if not profiles: st.caption("此分類尚無資料")
            else:
                cols = st.columns(4)
                for idx, p in enumerate(profiles):
                    lpn = sum(int(d) for d in p['birthdate'].strftime("%Y%m%d"))
                    while lpn > 9: lpn = sum(int(d) for d in str(lpn))
                    
                    is_selected = (st.session_state.selected_profile_id == p['id'])
                    btn_type = "primary" if is_selected else "secondary"
                    
                    if cols[idx % 4].button(f"{p['name']}\n{lpn}號人", key=f"btn_{tab_name}_{p['id']}", use_container_width=True, type=btn_type):
                        st.session_state.selected_profile_id = p['id']
                        st.rerun()