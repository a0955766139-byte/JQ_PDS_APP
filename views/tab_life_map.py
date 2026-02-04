# 檔案路徑: views/tab_life_map.py
import streamlit as st
import datetime
import os
import time
from supabase import create_client

# 引入剛剛建立的 UI 模組
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
    if not supabase: return
    try:
        bd_str = bd.isoformat()
        if is_me:
            supabase.table("users").upsert({"username": username, "full_name": name, "english_name": eng, "birth_date": bd_str}, on_conflict="username").execute()
        else:
            if uid:
                supabase.table("saved_charts").update({
                    "name": name, "english_name": eng, "birth_date": bd_str, "category": category
                }).eq("id", uid).execute()
            else:
                supabase.table("saved_charts").insert({
                    "user_id": username, "name": name, "english_name": eng, "birth_date": bd_str, "category": category
                }).execute()
    except Exception as e: st.error(f"存檔失敗: {e}")

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

    # 編輯模式：顯示表單
    if is_editing:
        with st.container(border=True):
            e_name = st.text_input("姓名", value=target['name'])
            e_eng = st.text_input("英文名", value=target['english_name'])
            e_bd = st.date_input("出生日期", value=target['birthdate'])
            
            # 分類選擇
            current_cat = target.get('category', '未分類')
            base_options = sorted(list(set(["家人", "朋友", "同事", "客戶", "未分類"] + all_existing_categories)))
            options = base_options + ["➕ 新增分類..."]
            
            if current_cat not in options: options.insert(0, current_cat)
            try: cat_index = options.index(current_cat)
            except: cat_index = 0
                
            sel_cat = st.selectbox("關係分類", options, index=cat_index)
            final_cat = sel_cat
            if sel_cat == "➕ 新增分類...":
                final_cat = st.text_input("請輸入新分類名稱", placeholder="例如：大學同學")
                if not final_cat: final_cat = "未分類"

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
        
        # 編輯時用新資料預覽
        life_map_ui.render_energy_tabs(e_bd, e_eng)
        
    else:
        # 顯示模式：直接呼叫 UI 模組渲染圖表
        life_map_ui.render_energy_tabs(target['birthdate'], target['english_name'])

# --- 主渲染入口 ---
def render():
    username = st.session_state.username
    
    # 準備資料
    all_profiles = []
    me = _get_my_profile(username)
    if me: all_profiles.append(me)
    else: all_profiles.append({"id": "ME", "name": username, "english_name": "", "birthdate": datetime.date(1990,1,1), "type": "me", "category": "本人"})
    
    friends = _get_saved_charts(username)
    all_profiles.extend(friends)

    # 提取現有分類
    existing_cats = list(set([p.get('category', '未分類') for p in friends]))

    # --- 1. 上半部：詳細資料 ---
    if "selected_profile_id" not in st.session_state: st.session_state.selected_profile_id = "ME"
    target = next((x for x in all_profiles if x['id'] == st.session_state.selected_profile_id), None)
    
    if not target and all_profiles:
        target = all_profiles[0]
        st.session_state.selected_profile_id = target['id']

    if target:
        _render_chart_details_section(target, username, existing_cats)
    
    st.divider()

    # --- 2. 下半部：家族矩陣列表 ---
    st.markdown("### 👨‍👩‍👧‍👦 家族矩陣：親友檔案庫")

    # 新增按鈕
    with st.expander("➕ 新增親友資料", expanded=False):
        with st.form("add_friend_form"):
            c1, c2 = st.columns(2)
            new_name = c1.text_input("姓名"); new_eng = c2.text_input("英文名")
            new_bd = st.date_input("出生日期", min_value=datetime.date(1900,1,1))
            
            base_opts = sorted(list(set(["家人", "朋友", "同事", "客戶", "未分類"] + existing_cats)))
            new_opts = base_opts + ["➕ 新增分類..."]
            sel_new_cat = st.selectbox("關係分類", new_opts)
            
            if st.form_submit_button("建立檔案", type="primary"):
                final_new_cat = sel_new_cat
                if sel_new_cat == "➕ 新增分類...":
                    final_new_cat = "未分類" 
                    st.toast("已建立！若需自訂分類請點擊編輯修改", icon="ℹ️")
                
                _save_chart(username, new_name, new_eng, new_bd, final_new_cat, is_me=False)
                st.rerun()

    # 分類分頁渲染
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
                    btn_type = "primary" if st.session_state.selected_profile_id == p['id'] else "secondary"
                    if cols[idx % 4].button(f"{p['name']}\n{lpn}號人", key=f"btn_{tab_name}_{p['id']}", use_container_width=True, type=btn_type):
                        st.session_state.selected_profile_id = p['id']
                        st.rerun()