# 檔案路徑: views/life_map_ui.py
import streamlit as st
import textwrap
import datetime

# --- 嘗試匯入核心計算模組 ---
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

# --- 輔助函式：顯示資訊列 ---
def _render_info_row(label, value, color="#333", is_header=False):
    fw = "800" if is_header else "600"
    fs = "18px" if is_header else "16px"
    st.markdown(f"""
    <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #eee; padding:8px 0;">
        <span style="color:#888; font-size:14px;">{label}</span>
        <span style="color:{color}; font-weight:{fw}; font-size:{fs};">{value}</span>
    </div>
    """, unsafe_allow_html=True)

# --- 核心函式：繪製 SVG 金字塔 ---
def draw_pyramid_svg(chart_data, bd):
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

# --- 主渲染入口：顯示 4 大分頁 ---
def render_energy_tabs(display_bd, display_name):
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
        chart_svg = draw_pyramid_svg(chart, display_bd)
        st.markdown(chart_svg, unsafe_allow_html=True)
        st.caption("聯合碼 (Joint Codes)")
        codes = chart.get('triangle_codes', [])
        if codes:
            g_cols = st.columns(6)
            for i, code in enumerate(codes[:6]):
                with g_cols[i]: st.markdown(f"`{code}`")

    with t4:
        st.markdown("##### 🏔️ 人生四大高峰與挑戰 (Diamond Chart)")
        try:
            engine = pds_core.NineEnergyNumerology()
            diamond_data = engine.calculate_diamond_chart(display_bd.year, display_bd.month, display_bd.day)
            
            # --- 定義 CSS 樣式 (讓程式碼更整潔) ---
            # 高峰樣式 (暖色系漸層 + 紅色左邊條)
            style_p = """
                background: linear-gradient(145deg, #fff8f8, #ffebeb);
                border-left: 6px solid #ff5252;
                border-radius: 12px;
                padding: 15px 20px;
                box-shadow: 0 4px 6px rgba(255, 82, 82, 0.1);
                height: 100%;
            """
            # 挑戰樣式 (冷色系漸層 + 藍紫色左邊條)
            style_c = """
                background: linear-gradient(145deg, #f8f9ff, #ebeeff);
                border-left: 6px solid #5c43b8;
                border-radius: 12px;
                padding: 15px 20px;
                box-shadow: 0 4px 6px rgba(92, 67, 184, 0.1);
                height: 100%;
            """
            # 數字大字體樣式
            style_num = "font-size: 48px; font-weight: 800; line-height: 1.2; margin: 10px 0;"
            # -------------------------------------

            for i, stage in enumerate(diamond_data.get('timeline', [])):
                # 階段標題
                st.markdown(f"""
                <div style="margin-top: 30px; margin-bottom: 15px; display: flex; align-items: baseline;">
                    <span style="font-size: 20px; font-weight: bold; margin-right: 10px;">📍 {stage['stage']}</span>
                    <span style="color: #666; font-weight: 500;">({stage['age_range']})</span>
                </div>
                """, unsafe_allow_html=True)
                
                # 使用 columns 將高峰與挑戰左右並排
                c1, c2 = st.columns(2, gap="medium")
                
                # --- 左側：高峰卡片 ---
                with c1:
                    st.markdown(f"""
                        <div style="{style_p}">
                            <div style="color: #d32f2f; font-weight: 700; display: flex; align-items: center;">
                                <span style="margin-right: 8px;">⭕</span> 高峰數 (機會)
                            </div>
                            <div style="{style_num} color: #c62828;">
                                {stage.get('p_val', '-')}
                            </div>
                            <div style="font-size: 13px; color: #9e5454;">
                                ✨ 能量紅利 / 開闢新局
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                # --- 右側：挑戰卡片 ---
                with c2:
                    st.markdown(f"""
                        <div style="{style_c}">
                            <div style="color: #4527a0; font-weight: 700; display: flex; align-items: center;">
                                <span style="margin-right: 8px;">⚠️</span> 挑戰數 (功課)
                            </div>
                            <div style="{style_num} color: #311b92;">
                                {stage.get('c_val', '-')}
                            </div>
                            <div style="font-size: 13px; color: #6f5e99;">
                                🔥 靈魂試煉 / 成長關卡
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # 階段之間的分隔線 (最後一個階段後不顯示)
                if i < len(diamond_data.get('timeline', [])) - 1:
                     st.markdown('<hr style="border-top: 1px dashed #ddd; margin: 30px 0;">', unsafe_allow_html=True)

        except Exception as e:
            st.error(f"運算模組載入失敗: {e}")