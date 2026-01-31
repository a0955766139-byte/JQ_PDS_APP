import streamlit as st
from PIL import Image

# 1. 設定網頁標題與圖示
st.set_page_config(page_title="喬鈞 V19", page_icon="🐣")

# 2. 載入圖片函數 (加上快取，讓運作更順暢)
@st.cache_data
def load_image(image_name):
    return Image.open(f"assets/{image_name}")

# 3. 介面佈局
st.title("👾 喬鈞 V19：靈魂孵化器")
st.write("歡迎來到像素宇宙...")

# --- 測試顯示區域 ---

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🥚 靈魂之蛋")
    # 嘗試載入並顯示蛋
    try:
        egg_img = load_image("pixel_egg.png")
        st.image(egg_img, width=200, caption="等待孵化中...")
    except Exception as e:
        st.error(f"找不到圖片：pixel_egg.png，請確認檔案是否在 assets 資料夾中。")

with col2:
    st.markdown("### 👻 混沌幼體")
    # 嘗試載入並顯示小精靈 (如果你還沒修好這張，這區塊會顯示錯誤，沒關係)
    try:
        monster_img = load_image("pixel_monster.png")
        st.image(monster_img, width=200, caption="初生型態")
    except:
        st.info("幼體尚未誕生 (請放入 pixel_monster.png)")

# --- 懷舊風格 CSS 微調 ---
st.markdown("""
<style>
/* 讓圖片有點素顆粒感，不要被過度平滑化 */
img {
    image-rendering: pixelated; 
}
</style>
""", unsafe_allow_html=True)