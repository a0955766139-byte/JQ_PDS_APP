import streamlit as st
import plotly.graph_objects as go
import pds_core  # 引用核心算力
from views import tab_life_map # 借用這裡的資料庫存取函式

def render_radar_chart(family_data):
    """
    五世 (The Artist) 的傑作：繪製家族能量雷達圖
    """
    categories = ['1 創始', '2 連結', '3 表達', '4 穩定', '5 自由', '6 關懷', '7 真理', '8 權力', '9 智慧']
    
    fig = go.Figure()

    # 為每位家人畫出一層能量網
    colors = ['#FFD700', '#FF69B4', '#00BFFF', '#32CD32'] # 金、粉、藍、綠
    
    for idx, member in enumerate(family_data):
        # 取得該成員的 PDS 參數
        p = member['params']
        # 計算該成員在 1-9 號的能量分佈 (簡單權重：主命x3, 其他x1)
        counts = [0] * 9
        counts[p['O']-1] += 3
        for k in ['M', 'N', 'I', 'J', 'K', 'L']:
            val = p.get(k, 0)
            if 1 <= val <= 9: counts[val-1] += 1
            
        # 封閉圖形 (最後一點要連回第一點)
        r_data = counts + [counts[0]]
        theta_data = categories + [categories[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=r_data,
            theta=theta_data,
            fill='toself',
            name=f"{member['name']} ({p['O']}號人)",
            line=dict(color=colors[idx % len(colors)], width=2),
            opacity=0.4  # 半透明，讓能量看起來在交融
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], showticklabels=False, linecolor='rgba(0,0,0,0.1)'),
            angularaxis=dict(tickfont=dict(size=14, color='#6a3093', family="Microsoft JhengHei"))
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)', # 透明背景
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)

def render():
    st.markdown("## 👨‍👩‍👧‍👦 家族矩陣能量場")
    st.markdown("在這裡，我們看見的不是衝突，而是能量的交織與共振。")

    # 1. 載入資料 (這部分還是要借用架構師的邏輯)
    if 'username' not in st.session_state:
        st.warning("請先登入")
        return

    username = st.session_state.username
    # 注意：這裡假設 tab_life_map 有這兩個函式。如果沒有，可能需要調整 import 來源或直接查詢 DB
    try:
        my_profile = tab_life_map._get_my_profile(username)
        saved_charts = tab_life_map._get_saved_charts(username)
    except AttributeError:
        st.error("系統連結錯誤：無法讀取個人檔案。請先確認 tab_life_map 模組是否完整。")
        return
    
    if not my_profile:
        st.warning("請先在「人生地圖」建立您的個人檔案。")
        return

    # 2. 選擇要加入矩陣的成員
    with st.expander("⚙️ 設定矩陣成員", expanded=True):
        st.write("請選擇要與您進行能量共振的家人/夥伴（最多選 3 位）：")
        
        # 預設選中自己
        options = {f"{p['name']}": p for p in saved_charts}
        selected_names = st.multiselect("選擇親友", list(options.keys()), max_selections=3)
        
        # 建立運算清單
        matrix_members = []
        
        # 加入自己 (先算好 PDS)
        # 修正：確保日期格式正確
        import datetime
        my_bd = my_profile['birthdate']
        if isinstance(my_bd, str):
            my_bd = datetime.datetime.strptime(my_bd, "%Y-%m-%d").date()

        my_chart = pds_core.calculate_chart(my_bd, my_profile['english_name'])
        matrix_members.append({
            "name": my_profile['name'], 
            "params": my_chart['svg_params'] | {'O': int(my_chart['svg_params']['O'])} 
        })
        
        # 加入選中的親友
        for name in selected_names:
            p = options[name]
            # 日期相容性處理
            if 'birth_date' in p: bd_raw = p['birth_date']
            elif 'birthdate' in p: bd_raw = p['birthdate']
            else: bd_raw = str(datetime.date.today())
            
            if isinstance(bd_raw, str):
                try:
                    bd = datetime.datetime.strptime(bd_raw, "%Y-%m-%d").date()
                except:
                    bd = datetime.date.today() # Fallback
            else:
                bd = bd_raw
            
            c = pds_core.calculate_chart(bd, p.get('english_name', ''))
            matrix_members.append({"name": p['name'], "params": c['svg_params']})

    # 3. 呼叫五世進行視覺渲染
    if len(matrix_members) > 0:
        st.divider()
        st.subheader("📊 能量共振雷達")
        render_radar_chart(matrix_members)
        
        st.divider()
        st.subheader("💫 家族動力核心 (M+O)")
        
        # 呼叫架構師寫好的核心運算
        try:
            dynamics = pds_core.calculate_family_dynamics(matrix_members)
            
            # 顯示和解語法
            for tip in dynamics['tips']:
                st.markdown(f"""
                <div style="background:#f8f9fa; padding:15px; border-radius:10px; border-left:5px solid #6a3093; margin-bottom:10px;">
                    <small style="color:#666;">💌 給 <b>{tip['to']}</b> 的利他話語：</small><br>
                    <div style="font-size:16px; font-weight:bold; color:#333; margin-top:5px;">{tip['script']}</div>
                </div>
                """, unsafe_allow_html=True)
        except AttributeError:
             st.warning("⚠️ 視覺官提示：架構師似乎忘了在 pds_core 實作 calculate_family_dynamics。請檢查後端代碼。")

    else:
        st.info("請選擇至少一位親友來啟動矩陣。")