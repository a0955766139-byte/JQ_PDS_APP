import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import pds_core
import datetime

# --- 五世的視覺魔法區 (維持不變) ---
def render_radar_chart(family_data):
    """繪製家族能量雷達圖"""
    categories = ['1 創始', '2 連結', '3 表達', '4 穩定', '5 自由', '6 關懷', '7 真理', '8 權力', '9 智慧']
    fig = go.Figure()
    colors = ['#FFD700', '#FF69B4', '#00BFFF', '#32CD32', '#9370DB'] 
    
    for idx, member in enumerate(family_data):
        p = member['chart']['svg_params']
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
            radialaxis=dict(visible=True, range=[0, 6], showticklabels=False, linecolor='rgba(0,0,0,0.1)'),
            angularaxis=dict(tickfont=dict(size=14, color='#6a3093'))
        ),
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig, use_container_width=True)

def render_stats_table(family_data):
    """架構師的數據儀表板"""
    st.subheader("📋 家族能量參數表")
    table_data = []
    for m in family_data:
        c = m['chart']
        temp = c.get('temperament', '0-0-0-0')
        table_data.append({
            "姓名": m['name'],
            "主命數": c['svg_params']['O'],
            "坐鎮碼 (Anchor)": c['anchor'],
            "內心 (Inner)": c['inner'],
            "制約 (Restrict)": c['restrict'],
            "流年 (Flow Year)": c['py'],
            "性情 (Temp)": temp
        })
    df = pd.DataFrame(table_data)
    st.dataframe(
        df, use_container_width=True, hide_index=True,
        column_config={
            "主命數": st.column_config.NumberColumn(format="%d 號人"),
            "流年 (Flow Year)": st.column_config.NumberColumn(format="流年 %d"),
        }
    )

# --- 主渲染區 ---
def render():
    st.markdown("## 👨‍👩‍👧‍👦 家族矩陣能量場")
    
    # 延遲載入避免迴圈
    from . import tab_life_map

    username = st.session_state.username
    my_profile = tab_life_map._get_my_profile(username)
    saved_charts = tab_life_map._get_saved_charts(username)
    
    # --- 判斷是否有資料 ---
    if not my_profile and not saved_charts:
        st.info("👋 歡迎來到家族矩陣！")
        st.warning("這裡目前空空如也。請先到 **「🧬 地圖人生」** 幫家人建立檔案。")
        st.markdown("👉 **請點擊左側選單的「🧬 地圖人生」開始輸入**")
        return

    # --- 設定矩陣成員 ---
    with st.container(border=True):
        st.subheader("⚙️ 點名時刻：誰要加入能量場？")
        
        all_options = {}
        if my_profile:
            all_options[f"{my_profile['name']} (我)"] = my_profile
        for p in saved_charts:
            all_options[f"{p['name']}"] = p
            
        selected_keys = st.multiselect(
            "請勾選家人：", 
            list(all_options.keys()), 
            default=[list(all_options.keys())[0]] if all_options else None
        )
        
        # 這裡不放輸入框，只放提示
        st.caption("💡 找不到家人？請先去 **「🧬 地圖人生 > ➕ 新增親友」** 建立檔案。")

        matrix_members = []
        for key in selected_keys:
            p = all_options[key]
            if 'birth_date' in p: bd = datetime.datetime.strptime(p['birth_date'], "%Y-%m-%d").date()
            elif 'birthdate' in p: bd = p['birthdate']
            else: bd = datetime.date.today()
            
            full_chart = pds_core.calculate_chart(bd, p.get('english_name', ''))
            matrix_members.append({
                "name": p['name'], 
                "chart": full_chart,
                "params": full_chart['svg_params'] | {'O': int(full_chart['svg_params']['O'])}
            })

    # --- 呈現結果 ---
    if len(matrix_members) > 0:
        st.divider()
        render_radar_chart(matrix_members)
        render_stats_table(matrix_members)
        st.divider()
        st.subheader("💫 家族動力轉化 (和解語法)")
        dynamics = pds_core.calculate_family_dynamics(matrix_members)
        
        if dynamics['tips']:
            for tip in dynamics['tips']:
                st.markdown(f"""
                <div style="background:#fff; padding:15px; border-radius:12px; border:1px solid #eee; box-shadow:0 4px 6px rgba(0,0,0,0.05); margin-bottom:12px;">
                    <div style="font-size:12px; color:#888; margin-bottom:4px;">
                        🔄 <b>{tip['from']}</b> 對 <b>{tip['to']}</b> 的覺察：
                    </div>
                    <div style="font-size:16px; font-weight:600; color:#4a4a4a; line-height:1.5;">
                        {tip['script']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("目前的組合非常和諧。")
    else:
        st.info("👈 請在上方勾選成員")