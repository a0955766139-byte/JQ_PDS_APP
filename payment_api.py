import os
from fastapi import FastAPI, Request, Form
from fastapi.responses import PlainTextResponse
from supabase import create_client, Client

# 初始化 FastAPI 秘書
app = FastAPI(title="九能量金流接單秘書")

# 連線到您的 Supabase 資料庫
# (這裡會自動抓取您在 Zeabur 上設定的環境變數)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.get("/")
def read_root():
    return {"status": "金流秘書已上線，隨時準備接單！"}

# ==========================================
# ★ 核心任務：接收客樂得的 APN 主動通知
# ==========================================
@app.post("/webhook/ccat")
async def receive_payment_notification(request: Request):
    """
    接收統一客樂得付款成功後的背景通知 (Webhook/APN)
    """
    try:
        # 1. 取得客樂得傳來的表單資料 (通常包含訂單編號、金額、交易狀態等)
        form_data = await request.form()
        data_dict = dict(form_data)
        
        # ⚠️ 這裡請對照客樂得的 API 文件，通常他們會回傳類似以下的欄位：
        # OrderNo (您產生的訂單編號), Status (交易狀態), CheckMacValue (加密驗證碼) 等等
        # 假設客樂得傳來的訂單編號欄位叫做 'OrderNo'，狀態叫做 'Status'
        order_no = data_dict.get("OrderNo", "")
        status = data_dict.get("Status", "")
        
        print(f"🔔 收到金流通知！訂單編號: {order_no}, 狀態: {status}")
        
        # 2. 安全驗證 (確保通知真的是客樂得發的)
        # 這裡需要用您的 HashKey 和 HashIV 進行雜湊比對 (稍後我們可以根據文件寫這段)
        # if not verify_mac_value(data_dict):
        #     return PlainTextResponse("0|Error", status_code=400)

        # 3. 如果付款成功 (假設客樂得的成功代碼是 'S' 或 '1')
        if status == "S" or status == "1" or status == "SUCCESS":
            
            # 從訂單編號中，反查出這是哪個用戶買的 (這需要我們之後在資料庫建一個訂單表)
            # 這裡我們先示範「直接透過 line_user_id 或 username 升級」的邏輯
            # 假設我們將用戶的 line_user_id 藏在訂單編號的自訂欄位裡
            target_user_id = data_dict.get("CustomField1", "") 
            
            if target_user_id:
                # 🚀 執行資料庫升級動作！將用戶的 tier 改為 'pro'
                supabase.table("users").update({"tier": "pro"}).eq("line_user_id", target_user_id).execute()
                print(f"✅ 已成功將用戶 {target_user_id} 升級為專業會員！")

        # 4. 回報給客樂得主機：「我收到了，處理完畢！」
        # (通常金流公司要求回傳特定的字串，例如 "1|OK" 或 "SUCCESS")
        return PlainTextResponse("1|OK")

    except Exception as e:
        print(f"❌ 金流處理發生錯誤: {e}")
        return PlainTextResponse("0|Error", status_code=500)