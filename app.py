from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime, requests, json, os

app = Flask(__name__)

# --- ค่าคงที่ ---
LINE_TOKEN='sIpsVv...lFU='
LINE_SECRET='5a5f2a...5140'
GROUP_ID = 'C646395b06063544d6233261a86851493'
# ใส่ค่า Refresh Token และ Client ID ของคุณที่ได้มาจากไฟล์
REFRESH_TOKEN='NbYe3s...GE8M'
CLIENT_ID = 'claude-MHFByqsmm1J44ZOBX7lSbw'

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

def get_valid_token():
    # ระบบ Refresh Token อัตโนมัติ
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID
    }
    res = requests.post("https://mcp.flowaccount.com/oauth/token", data=payload)
    return res.json()['access_token']

def get_all_ri():
    try:
        access_token = get_valid_token()
        headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
        payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", 
                   "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1}}}
        res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
        return res.json()["result"]["content"][0]["data"]["list"]
    except Exception as e:
        print(f"DEBUG: Error = {e}")
        return []

# --- Scheduler และ Webhook เหมือนเดิม ---
# ... (ใส่ Scheduler และ @app.route ตามโค้ดเดิมได้เลยครับ) ...

# พิมพ์ "ค้างจ่าย" ใน LINE เพื่อเช็คผล
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        items = get_all_ri()
        if not items:

line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบรายการค้างจ่ายในระบบครับ"))
        else:
            # สรุปผล
            reply = "รายการที่พบ:\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in items[:5]])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
            
