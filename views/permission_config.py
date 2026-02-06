# views/permission_config.py

# === 🏅 會員權限設定表 ===
MEMBER_TIERS = {
    # 1. 一般用戶 (未登入或訪客，通常由 app.py 處理，這裡僅作參考)
    "guest": {
        "name": "訪客",
        "map_limit": 0,             # 無法存檔
        "journal_days": 0,          # 無法存檔
        "divination_days": 0,       # 無法使用
        "family_matrix": False,     # 無法使用
        "academy": False            # 無法進入
    },
    # 2. 註冊會員 (預設)
    "registered": {
        "name": "🌱 註冊會員",
        "map_limit": 5,             # 記錄 5 位
        "journal_days": 7,          # 記錄 7 日
        "divination_days": 7,       # 記錄 7 日
        "family_matrix": True,  # 可用 (但受限於 map_limit)
        "academy": False
    },
    # 3. 書友會會員
    "book_club": {
        "name": "📚 書友會會員",
        "map_limit": 5,             # 記錄 5 位
        "journal_days": 30,         # 記錄 30 日
        "divination_days": 7,
        "family_matrix": True,
        "academy": False
    },
    # 4. 付費基礎會員
    "basic": {
        "name": "💎 付費基礎會員",
        "map_limit": 20,           # 記錄 20 位
        "journal_days": 90,        # 記錄 90 日
        "divination_days": 30,
        "family_matrix": True,
        "academy": False
    },
    # 5. 付費專業階會員
    "pro": {
        "name": "👑 付費專業階會員",
        "map_limit": 100,          # 記錄 100 位
        "journal_days": 180,       # 記錄 180 日
        "divination_days": 90,
        "family_matrix": True,
        "academy": True            # ✅ 獨家開啟研究院
    }
}

def get_user_tier(role_name):
    """輸入身分代碼回傳設定，預設為 registered"""
    # 從資料庫 users 表格撈出的資料中，讀取 'role' 欄位
    role = str(role_name).lower().strip() if role_name else "registered"
    # 如果找不到對應的身分，就預設退回 registered
    return MEMBER_TIERS.get(role, MEMBER_TIERS["registered"])