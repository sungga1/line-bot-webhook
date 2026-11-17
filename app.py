from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests

app = Flask(__name__)

# --- ค่าคงที่ ---
LINE_TOKEN='sIpsVv...lFU='
LINE_SECRET='5a5f2a...5140'
MY_GROUP_ID = 'C646395b06063544d6233261a86851493'
REFRESH_TOKEN='NbYe3s...GE8M'
CLIENT_ID = 'claude-MHFByqsmm1J44ZOBX7lSbw'

# --- ตัวจัดการ Token ---
cache = {"access_token": None}

def refresh_token():
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID
    }
    try:
        res = requests.post("https://mcp.flowaccount.com/oauth/token", data=payload)
        if res.status_code == 200:
            cache["access_token"] = res.json()['access_token']
            return cache["access_token"]
    except Exception:
        return None
    return None

def get_all_ri():
    if not cache["access_token"]:
        cache["access_token"] = refresh_token()
    
    headers = {
        "Authorization": f"Bearer {cache['access_token']}",
        "Content-Type": "application/json"
    }
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "expense__list_receiving_inventory",
            "arguments": {"page": 1}
        }
    }
    
    res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)

if res.status_code == 401 or "session_expired" in res.text:
        new_token = refresh_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
            res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
    
    try:
        return res.json()["result"]["content"][0]["data"]["list"]
    except Exception:
        return []

# --- ระบบ Webhook ---
handler = WebhookHandler(LINE_SECRET)
line_bot_api = LineBotApi(LINE_TOKEN)

@app.route("/line/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        items = get_all_ri()
        if not items:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบรายการค้างจ่ายในระบบครับ"))
        else:
            reply = "รายการค้างจ่าย:\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in items[:5]])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
    
