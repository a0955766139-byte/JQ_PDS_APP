import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import pds_core
import datetime

# ❌ 移除這裡的 from views import ... (這是導致迴圈的元兇)

def render_radar_chart(family_data):
    """
    五世 (The Artist) 的傑作：繪製家族能量雷達圖
    """
    categories = ['1 創始', '2 連結', '3 表達', '4 穩定', '5 自由', '6 關懷', '7 真理', '8 權力', '9 智慧']
    
    fig = go.Figure()
    colors = ['#FFD700', '#FF69B4', '#00BFFF', '#32CD32'] # 金、粉、藍、綠
    
    for idx, member in enumerate(family_data):
        p = member['params']
        counts = [0] * 9
        counts[p['O']-1] += 3
        for k in ['M', 'N', 'I', 'J', 'K', 'L']:
            val = p.get(k, 0)
            if 1 <= val <= 9: counts[val-1] += 1
            
        r_data = counts + [counts[0]]
        theta_data = categories + [categories[0]]
        
        fig.add_trace(go.Scatterpolar(
            r=r_data,
            theta=theta_data,
            fill='toself',
            name=f"{member['name']} ({p['O']}號人)",
            line=dict(color=colors[idx % len(colors)], width=2),
            opacity=0.4
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 5], showticklabels=False, linecolor='rgba(0,0,0,0.1)'),
            angularaxis=dict(tickfont=dict(size=14, color='#6a3093'))
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

def render():
    st.markdown("## 👨‍👩‍👧‍👦 家族矩陣能量場")
    st.markdown("在這裡，我們看見的不是衝突，而是能量的交織與共振。")

    # ✅ 關鍵修正：延遲載入 (Lazy Import)
    # 只有當函式執行時，才去呼叫隔壁鄰居，避開啟動時的相撞
    from . import tab_life_map 

    username = st.session_state.username
    my_profile = tab_life_map._get_my_profile(username)
    saved_charts = tab_life_map._get_saved_charts(username)
    
    if not my_profile:
        st.warning("請先在「人生地圖」建立您的個人檔案。")
        return

    with st.expander("⚙️ 設定矩陣成員", expanded=True):
        st.write("請選擇要與您進行能量共振的家人/夥伴（最多選 3 位）：")
        
        options = {f"{p['name']}": p for p in saved_charts}
        selected_names = st.multiselect("選擇親友", list(options.keys()), max_selections=3)
        
        matrix_members = []
        
        # 加入自己
        my_chart = pds_core.calculate_chart(my_profile['birthdate'], my_profile['english_name'])
        matrix_members.append({
            "name": my_profile['name'], 
            "params": my_chart['svg_params'] | {'O': int(my_chart['svg_params']['O'])}
        })
        
        # 加入親友
        for name in selected_names:
            p = options[name]
            if 'birth_date' in p: bd = datetime.datetime.strptime(p['birth_date'], "%Y-%m-%d").date()
            elif 'birthdate' in p: bd = p['birthdate']
            else: bd = datetime.date.today()
            
            c = pds_core.calculate_chart(bd, p.get('english_name', ''))
            matrix_members.append({"name": p['name'], "params": c['svg_params']})

    if len(matrix_members) > 0:
        st.divider()
        st.subheader("📊 能量共振雷達")
        render_radar_chart(matrix_members)
        
        st.divider()
        st.subheader("💫 家族動力核心 (M+O)")
        
        dynamics = pds_core.calculate_family_dynamics(matrix_members)
        
        for tip in dynamics['tips']:
            st.markdown(f"""
            <div style="background:#f8f9fa; padding:15px; border-radius:10px; border-left:5px solid #6a3093; margin-bottom:10px;">
                <small style="color:#666;">💌 給 <b>{tip['to']}</b> 的利他話語：</small><br>
                <div style="font-size:16px; font-weight:bold; color:#333; margin-top:5px;">{tip['script']}</div>
            </div>
            """, unsafe_allow_html=True)