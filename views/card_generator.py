import datetime
import io
import os
import random
import textwrap
from datetime import date
import qrcode
from PIL import Image, ImageDraw, ImageFont

from views import life_map_ui

FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "assets", "NotoSansTC-Bold.ttf")


def _safe_date(value):
    if isinstance(value, datetime.date):
        return value
    if isinstance(value, datetime.datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.date.fromisoformat(value)
        except ValueError:
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
    return datetime.date.today()


def _load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except (OSError, IOError):
        return ImageFont.load_default()


def _compose_chart(target):
    bd = _safe_date(target.get("birthdate", datetime.date.today()))
    name = target.get("name") or target.get("full_name") or "九能量會員"
    try:
        return life_map_ui.pds_core.calculate_chart(bd, name)
    except Exception:
        return {}


def _draw_gradient(draw, width, height):
    for y in range(height):
        ratio = y / max(height - 1, 1)
        r = int(6 + ratio * 25)
        g = int(12 + ratio * 18)
        b = int(40 + ratio * 55)
        draw.line([(0, y), (width, y)], fill=(r, g, b))


def calculate_age(birth_date):
    """計算精準年齡 (以生日到今天的歲數)"""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def _render_sections(draw, card, chart, user_data, birthdate, display_bd, current_age):
    width, height = card.size
    font_large = _load_font(70)
    font_title = _load_font(48)
    font_sub = _load_font(32)
    font_small = _load_font(28)
    font_label = _load_font(28)
    font_value = _load_font(48)

    user_name = (user_data.get("name") or "九能量會員").upper()
    draw.text((50, 60), user_name, font=font_large, fill=(255, 255, 255))
    info_text = f"出生日期：{display_bd}  |  年齡：{current_age} 歲"
    draw.text((50, 140), info_text, font=font_small, fill=(224, 224, 224))

    title_text = "九能量導航 • 個人能量圖卡"
    draw.text((width - 620, 60), title_text, font=font_title, fill=(255, 244, 222))

    subtitle = user_data.get("english_name") or ""
    if subtitle:
        draw.text((width - 620, 120), subtitle, font=font_sub, fill=(197, 194, 255))

    # 資料卡
    section_top = 360
    section_height = 200
    section_gap = 30
    colors = [(255, 255, 255, 20), (255, 255, 255, 15)]
    metrics = [
        ("生命道路", chart.get("lpn", "-")),
        ("姓名內驅", chart.get("soul", "-")),
        ("坐鎮碼", chart.get("anchor", "-")),
        ("性情數字", chart.get("temperament", "0-0-0-0")),
    ]
    for idx, (label, value) in enumerate(metrics):
        top = section_top + idx * (section_height + section_gap)
        draw.rounded_rectangle(
            [60, top, width - 60, top + section_height],
            radius=24,
            fill=(25, 28, 60) if idx % 2 == 0 else (22, 25, 54),
        )
        draw.text((90, top + 25), label, font=font_label, fill=(195, 187, 246))
        draw.text(
            (90, top + 80),
            str(value),
            font=font_value,
            fill=(255, 255, 255),
        )


def _render_triangle(draw, card, chart):
    width, height = card.size
    accent = (155, 134, 255)
    base_top = 930
    base = [
        (width // 2, base_top),
        (150, height - 260),
        (width - 150, height - 260),
    ]
    draw.polygon(base, outline=accent, width=6)

    nodes = chart.get("svg_params", {})
    positions = {
        "O": (width // 2, base_top + 30),
        "M": (width // 2 - 160, base_top + 160),
        "N": (width // 2 + 160, base_top + 160),
        "I": (width // 2 - 240, base_top + 310),
        "J": (width // 2 - 80, base_top + 310),
        "K": (width // 2 + 80, base_top + 310),
        "L": (width // 2 + 240, base_top + 310),
    }
    circle_radius = 48
    font_node = _load_font(36)
    for key, coord in positions.items():
        x, y = coord
        draw.ellipse(
            [x - circle_radius, y - circle_radius, x + circle_radius, y + circle_radius],
            outline=accent,
            width=5,
        )
        draw.text(
            (x, y - 20),
            key,
            font=_load_font(26),
            fill=(255, 255, 255),
            anchor="ma",
        )
        draw.text(
            (x, y + 20),
            str(nodes.get(key, "-")),
            font=font_node,
            fill=(255, 255, 255),
            anchor="ma",
        )

    code_text = chart.get("triangle_codes", [])[:3]
    code_str = " | ".join(code_text) if code_text else "尚未計算聯合碼"
    draw.text(
        (width // 2, height - 320),
        f"天賦三角形聯合碼：{code_str}",
        font=_load_font(32),
        fill=(217, 218, 255),
        anchor="ms",
    )


def _render_qrcode(card):
    qr = qrcode.QRCode(border=1, box_size=4)
    qr.add_data("https://jq-pds-app-1.onrender.com")
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="#1b1b1f", back_color="white").convert("RGB")
    qr_w = qr_img.size[0]
    qr_target_size = 220
    qr_resized = qr_img.resize((qr_target_size, qr_target_size))
    card.paste(qr_resized, (card.size[0] - qr_target_size - 90, card.size[1] - qr_target_size - 90))
    draw = ImageDraw.Draw(card)
    font = _load_font(24)
    draw.text(
        (card.size[0] - qr_target_size - 90, card.size[1] - qr_target_size - 120),
        "掃碼連到九能量導覽",
        font=font,
        fill=(255, 255, 255),
    )


def generate_energy_card(user_data):
    """
    產生專屬的九能量圖卡：包含核心指標、三角形與 QR。
    """
    width, height = 1080, 1680
    card = Image.new("RGB", (width, height), "#050714")
    draw = ImageDraw.Draw(card)
    _draw_gradient(draw, width, height)
    chart = _compose_chart(user_data)
    birthdate = _safe_date(user_data.get("birthdate"))
    display_bd = birthdate.strftime("%Y/%m/%d")
    current_age = calculate_age(birthdate)
    _render_sections(draw, card, chart, user_data, birthdate, display_bd, current_age)
    _render_triangle(draw, card, chart)
    _render_qrcode(card)
    return card


def calculate_age(birth_date):
    """計算精準年齡"""
    today = date.today()
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))


def generate_divination_card(username, core_word, message):
    """
    生成宇宙指引圖卡：帶有圓圈與指引文字
    """
    width, height = 1080, 1680
    bg_path = os.path.join(os.path.dirname(__file__), "..", "assets", "universe_bg.png")
    try:
        card = Image.open(bg_path).convert("RGB")
        if card.size != (width, height):
            card = card.resize((width, height))
    except (FileNotFoundError, OSError):
        card = Image.new("RGB", (width, height), "#03071b")
        draw = ImageDraw.Draw(card)
        _draw_gradient(draw, width, height)
        for _ in range(220):
            x = random.randint(0, width - 1)
            y = random.randint(0, height - 1)
            r = random.randint(1, 3)
            draw.ellipse(
                [x - r, y - r, x + r, y + r],
                fill=(255, 255, 255, random.randint(120, 220)),
            )
    draw = ImageDraw.Draw(card, "RGBA")

    circle_radius = 260
    center = (width // 2, height // 2 - 120)
    circle_box = [
        center[0] - circle_radius,
        center[1] - circle_radius,
        center[0] + circle_radius,
        center[1] + circle_radius,
    ]
    draw.ellipse(circle_box, fill=(255, 255, 255, 25), outline=(232, 178, 55), width=8)

    core_font = _load_font(220)
    draw.text(
        center,
        core_word,
        font=core_font,
        fill=(255, 255, 255, 230),
        anchor="mm",
    )

    textbox_top = int(height * 0.7)
    textbox_height = 220
    padding = 60
    textbox_box = [
        padding,
        textbox_top,
        width - padding,
        textbox_top + textbox_height,
    ]
    draw.rectangle(textbox_box, fill=(0, 0, 0, 180), outline=None)

    message_font = _load_font(48)
    wrapped_lines = textwrap.wrap(message, width=28)
    text_y = textbox_top + 40
    for line in wrapped_lines:
        draw.text(
            (width // 2, text_y),
            line,
            font=message_font,
            fill=(232, 232, 255, 240),
            anchor="ms",
        )
        text_y += 60

    brand_font = _load_font(24)
    draw.text(
        (width - 40, height - 30),
        "© 2026 Jow-Jiun Culture",
        font=brand_font,
        fill=(200, 200, 200),
        anchor="rd",
    )

    return card

def generate_divination_card(username, core_word, message):
    """
    生成宇宙指引專屬圖卡
    core_word: '道', '才', '覺', '華', '庫', '力'
    message: 占卜出的指引文字
    """
    # 這裡的邏輯會從 assets 中讀取星空底圖
    # 並利用 ImageDraw 在正中央寫上 core_word
    # 最後在下方寫上 message
    # 回傳 PIL Image 物件
    pass