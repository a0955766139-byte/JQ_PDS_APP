import streamlit as st
import datetime
import random
import pandas as pd
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
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)

supabase = init_supabase()

def get_today_str():
    return datetime.datetime.now().strftime("%Y-%m-%d")

def check_today_draw(username):
    """檢查用戶今日是否已抽牌"""
    today = get_today_str()
    try:
        response = supabase.table("daily_draws")\
            .select("*")\
            .eq("username", username)\
            .eq("draw_date", today)\
            .execute()
        
        if response.data and len(response.data) > 0:
            return response.data[0] # 返回今日已抽的資料
        return None
    except Exception as e:
        st.error(f"資料庫連線錯誤: {e}")
        return None

def save_draw_result(username, card_data):
    """儲存抽牌結果"""
    today = get_today_str()
    payload = {
        "username": username,
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

def get_draw_history(username):
    """取得過去 7 天的歷史紀錄"""
    try:
        response = supabase.table("daily_draws")\
            .select("draw_date, title, poem")\
            .eq("username", username)\
            .order("draw_date", desc=True)\
            .limit(7)\
            .execute()
        return response.data
    except Exception as e:
        return []

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

def render_divination_view():
    inject_custom_css()
    
    # 確保有登入狀態 (若主程式已處理，這裡做雙重確認)
    if "username" not in st.session_state or not st.session_state.username:
        st.warning("請先登入以使用宇宙指引功能。")
        return

    user = st.session_state.username
    st.header("🔮 每日宇宙指引")
    
    # 1. 檢查今日狀態
    today_record = check_today_draw(user)

    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if today_record:
            # === 狀態 A: 今日已抽過 ===
            st.info(f"📅 {today_record['draw_date']} 的指引已送達")
            render_card_ui(today_record, is_new=False)
        
        else:
            # === 狀態 B: 今日尚未抽牌 ===
            st.markdown("""
            <div style="text-align: center; padding: 40px; border: 2px dashed #ccc; border-radius: 15px; margin-bottom: 20px;">
                <div style="font-size: 60px;">🃏</div>
                <p style="color: #666;">心誠則靈，連結宇宙能量...</p>
            </div>
            """, unsafe_allow_html=True)
            
            # 抽牌按鈕
            if st.button("🔮 連結宇宙・抽取指引", use_container_width=True):
                # 隨機邏輯
                picked_card = random.choice(DIVINATION_CARDS)
                
                # 寫入資料庫
                success = save_draw_result(user, picked_card)
                
                if success:
                    # 強制刷新頁面以顯示結果
                    st.rerun()

    st.markdown("---")

    # 2. 歷史紀錄區塊
    with st.expander("📜 查看過去 7 天的靈魂軌跡"):
        history = get_draw_history(user)
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