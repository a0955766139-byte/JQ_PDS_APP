import streamlit as st

def render_home_ads():
    """
    渲染首頁的所有廣告與問卷區塊
    """
    # --- 1. 廣告區塊：台灣中富生物科技 ---
    with st.container(border=True):
       st.markdown("""
        <style>
            .partner-card {
                background: #ffffff; border: 1px solid #f5f5f5; border-radius: 16px; padding: 30px;
                margin-bottom: 25px; box-shadow: 0 15px 40px rgba(0,0,0,0.05); position: relative; overflow: hidden;
                transition: transform 0.3s ease;
            }
            .partner-card:hover { transform: translateY(-5px); }
            .partner-card::before { 
                content: ""; position: absolute; top: 0; left: 0; right: 0; height: 6px;
                background: linear-gradient(90deg, #D4AF37, #F7E98D, #D4AF37);
            }
            .partner-badge {
                background: linear-gradient(135deg, #D4AF37 0%, #C5A028 100%); color: white;
                padding: 6px 16px; border-radius: 20px; font-size: 12px; font-weight: bold;
                display: inline-block; margin-bottom: 15px; box-shadow: 0 4px 10px rgba(212, 175, 55, 0.3);
            }
            .partner-title { color: #2c3e50; font-size: 24px; font-weight: 800; margin-bottom: 8px; }
            .award-text { color: #D4AF37; font-size: 14px; font-weight: bold; margin-bottom: 15px; }
            a { text-decoration: none; }
        </style>
        <div class="partner-card">
            <div class="partner-badge">🏆 OFFICIAL PARTNER</div>
            <div class="partner-title">🌿 台灣中富生物科技</div>
            <div class="award-text">★ 榮獲 2025 Monde Selection 世界品質評鑑大賞 金獎</div>
            <p style="color:#555; font-size:15px; line-height:1.8; margin-bottom: 20px;">
                <b>「美，源自於健康的修護。」</b><br>
                九能量為您導航人生，中富生技為您守護青春。<br>
                嚴選台灣珍寶<b>「山芙蓉」</b>，打造醫療級的極致修護力。<br>
                <span style="color:#888; font-size:13px;">(魔立奇肌 x G.U治优 系列)</span>
            </p>
            <div style="display: flex; gap: 10px; margin-top: 20px;">
                 <a href="https://www.zhongfu-bcl.com.tw/" target="_blank" style="flex: 1; background: #2c3e50; color: white; padding: 12px; border-radius: 8px; text-align: center; font-weight: bold; font-size: 14px;">✨ 探索獲獎商品 (官網)</a>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("") # 間隔
    
    # --- 2. 雙欄位區塊：喬鈞心學研究院 & 問卷收集 ---
    c1, c2 = st.columns(2)
    
    with c1:
        with st.container(border=True):
            st.markdown("#### 🎓 喬鈞心學研究院")
            st.caption("探索心靈深度，掌握生命藍圖")
            # 使用 Link Button 避免 Key 衝突
            st.link_button("進入研究院", "https://your-academy-link.com", width="stretch")
            
    with c2:
        with st.container(border=True):
            st.markdown("#### 📚 九能量新書問卷")
            st.caption("您的寶貴意見，是新書最美的能量")
            st.link_button("填寫問卷", "https://your-survey-link.com", width="stretch")