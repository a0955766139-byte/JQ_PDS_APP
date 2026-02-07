import streamlit as st

def render_home_ads():
    """
    渲染首頁的所有廣告與問卷區塊
    """
    # --- 1. 廣告區塊：台灣中富生物科技 ---
    with st.container(border=True):
        st.markdown("""
        <div style="background: linear-gradient(135deg, #fdfbfb 0%, #ebedee 100%); padding: 20px; border-radius: 15px;">
            <h3 style="color: #2c3e50; margin-bottom: 5px;">🏆 台灣中富生物科技</h3>
            <p style="color: #7f8c8d; font-size: 14px;">白金質感・獲獎能量商品</p>
            <a href="https://www.zfbiotech.com" target="_blank" style="display: inline-block; background: #6a3093; color: white; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: bold;">✨ 探索獲獎商品 (官網)</a>
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