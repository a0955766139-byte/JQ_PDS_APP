import streamlit as st
import datetime
import random
import pandas as pd
import os
from supabase import create_client, Client

# ==============================================================================
# 0. 資源與設定 (Configuration & Assets)
# ==============================================================================

# 嘗試從外部模組匯入牌卡資料，若無則使用測試資料 (方便開發測試)
try:
    from databases.card_rules import DIVINATION_CARDS
except ImportError:
    # 預設測試資料 (Fallback Data)
    DIVINATION_CARDS = [
        {
            "title": "創始之光",
            "poem": "混沌初開見真章，一念清靜萬法揚。",
            "desc": "現在是開啟新計畫的最佳時機，相信你的直覺，勇敢踏出第一步。",
            "image_url": "https://images.unsplash.com/photo-1532968961962-8a0cb3a2d4f5?q=80&w=1000&auto=format&fit=crop"
        },
        {
            "title": "靜謐之海",
            "poem": "波瀾不驚心自閒，深海藏珍待有緣。",
            "desc": "先暫緩行動，向內探索。答案不在外面的喧囂，而在你內心的平靜裡。",
            "image_url": "https://images.unsplash.com/photo-1468581264429-2548ef9eb732?q=80&w=1000&auto=format&fit=crop"
        },
        {
            "title": "豐盛之樹",
            "poem": "根深葉茂果自成，春風化雨潤無聲。",
            "desc": "你過去的努力正在發酵。保持耐心，持續灌溉，豐盛的成果即將顯化。",
            "image_url": "https://images.unsplash.com/photo-1518173946687-a4c8892bbd9f?q=80&w=1000&auto=format&fit=crop"
        }
    ]

# 注入 CSS (Card UI 與 按鈕風格)
def inject_custom_css():
    st.markdown("""
    <style>
        /* 紫色主按鈕風格 */
        div.stButton > button {
            background-color: #6a3093;
            color: white;
            border-radius: 8px;
            font-weight: bold;
            border: none;
            padding: 10px 24px;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #55257a;
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(106, 48, 147, 0.4);
        }

        /* 卡片容器風格 */
        .divination-card {
            background-color: #ffffff;
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            border: 1px solid #e0e0e0;
            text-align: center;
            margin-bottom: 20px;
            color: #333333;
        }
        .card-title {
            color: #6a3093;
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
            font-family: "Microsoft JhengHei", sans-serif;
        }
        .card-poem {
            font-size: 18px;
            color: #555;
            font-style: italic;
            margin-bottom: 16px;
            border-left: 4px solid #6a3093;
            padding-left: 12px;
            display: inline-block;
            text-align: left;
        }
        .card-desc {
            font-size: 16px;
            line-height: 1.6;
            color: #444;
            background-color: #f8f4fc;
            padding: 15px;
            border-radius: 8px;
        }
        .card-img {
            border-radius: 12px;
            max-width: 100%;
            height: auto;
            margin-bottom: 16px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        }
        
        /* 歷史紀錄列表 */
        .history-item {
            padding: 10px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 1. Supabase 資料庫邏輯 (Backend Logic)
# ==============================================================================

@st.cache_resource
def init_supabase():
    # 優先從環境變數讀取 (Render 模式)
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    # 如果環境變數不存在，才嘗試讀取 st.secrets (本地模式)
    if not url or not key:
        try:
            url = st.secrets["supabase"]["url"]
            key = st.secrets["supabase"]["key"]
        except:
            st.error("🚫 找不到 Supabase 金鑰配置")
            return None
    return create_client(url, key)

supabase = init_supabase()

def get_today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def check_today_draw():
    """使用永久 ID 檢查今日是否已抽牌"""
    today = get_today_str()
    line_id = st.session_state.get("line_user_id") # 💡 改讀 ID
    if not line_id: return None
    
    try:
        response = supabase.table("daily_draws")\
            .select("*")\
            .eq("line_user_id", line_id)\
            .eq("draw_date", today)\
            .execute()
        
        if response.data: return response.data[0]
        return None
    except Exception as e:
        st.error(f"資料庫連線錯誤: {e}")
        return None

def save_draw_result(card_data):
    """儲存結果：同時鎖定 ID 與 儲存當時姓名"""
    today = get_today_str()
    line_id = st.session_state.get("line_user_id")
    display_name = st.session_state.get("username")
    
    payload = {
        "line_user_id": line_id,   # 💡 永久門牌
        "username": display_name,   # 💡 當時稱呼
        "draw_date": today,
        "title": card_data["title"],
        "poem": card_data["poem"],
        "desc": card_data["desc"],
        "image_url": card_data.get("image_url", ""),
        "created_at": datetime.datetime.now().isoformat()
    }
    
    try:
        supabase.table("daily_draws").insert(payload).execute()
        return True
    except Exception as e:
        st.error(f"儲存失敗: {e}")
        return False

def get_draw_history():
    """取得過去 7 天的靈魂軌跡 (認 ID)"""
    line_id = st.session_state.get("line_user_id")
    try:
        response = supabase.table("daily_draws")\
            .select("draw_date, title, poem")\
            .eq("line_user_id", line_id)\
            .order("draw_date", desc=True)\
            .limit(7)\
            .execute()
        return response.data
    except: return []

# ==============================================================================
# 2. UI 渲染邏輯 (Frontend Views)
# ==============================================================================

def render_card_ui(card_data, is_new=False):
    """渲染精美的卡片 UI"""
    if is_new:
        st.balloons()
        st.success("✨ 宇宙訊息已下載完畢")

    st.markdown(f"""
    <div class="divination-card">
        <img src="{card_data.get('image_url', 'https://via.placeholder.com/400x300?text=Card+Image')}" class="card-img">
        <div class="card-title">{card_data['title']}</div>
        <div class="card-poem">{card_data['poem']}</div>
        <div class="card-desc">
            <strong>💡 宇宙指引：</strong><br>
            {card_data['desc']}
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_divination_view(friends_raw=None):
    inject_custom_css()
    
    line_id = st.session_state.get("line_user_id")
    display_name = st.session_state.get("username", "導航員")
    
    if not line_id:
        st.warning("請先透過 LINE 快速登入，宇宙能量才能精準鎖定您的 ID。")
        return

    st.header(f"🔮 {display_name} 的每日宇宙指引") # 💡 顯示姓名
    
    # 1. 檢查今日狀態
    today_record = check_today_draw()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if today_record:
            st.info(f"📅 今日指引已送達")
            render_card_ui(today_record, is_new=False)
        else:
            st.markdown('<div style="text-align: center; padding: 40px;">🃏<p>連結宇宙能量...</p></div>', unsafe_allow_html=True)
            if st.button("🔮 連結宇宙・抽取指引", use_container_width=True):
                picked_card = random.choice(DIVINATION_CARDS)
                if save_draw_result(picked_card):
                    st.rerun()

    st.markdown("---")
    with st.expander("📜 查看過去 7 天的靈魂軌跡"):
        history = get_draw_history()
        if history:
            for item in history:
                st.markdown(f"""
                <div class='history-item'>
                    <span style='color: #6a3093; font-weight: bold;'>{item['draw_date']}</span>
                    <span>{item['title']} - {item['poem']}</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.caption("尚無歷史紀錄，今天是你開始的第一天！")

# ==============================================================================
# 主程式進入點 (Main Entry)
# ==============================================================================
if __name__ == "__main__":
    # 用於單獨測試此檔案的 Mock 登入
    if "username" not in st.session_state:
        st.session_state.username = "test_user_jow_jiun"
    
    render_divination_view()