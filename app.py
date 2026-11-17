from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import datetime, requests

app = Flask(__name__)

# --- ค่าคงที่ ---
LINE_TOKEN='sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU='
LINE_SECRET='5a5f2ad36f44368e77a508f3421b5140'
REFRESH_TOKEN='NbYe3sbPrvGk8EaV1UYNcexhdKGoxsTVPpxFwEAGE8M' # ใส่ Refresh Token ของคุณ
CLIENT_ID = 'claude-MHFByqsmm1J44ZOBX7lSbw'

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)
cache = {"access_token": None}

def refresh_token():
    payload = {"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN, "client_id": CLIENT_ID}
    try:
        res = requests.post("https://mcp.flowaccount.com/oauth/token", data=payload)
        if res.status_code == 200:
            cache["access_token"] = res.json()['access_token']
            return cache["access_token"]
    except: pass
    return None

def get_all_ri():
    if not cache["access_token"]: cache["access_token"] = refresh_token()
    headers = {"Authorization": f"Bearer {cache['access_token']}", "Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", 
               "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1}}}
    res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
    
    if res.status_code == 401 or "session_expired" in res.text:
        new_token = refresh_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"

res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
    try:
        return res.json()["result"]["content"][0]["data"]["list"]
    except: return []

@app.route("/line/webhook", methods=['POST'])
def callback():
    try:
        handler.handle(request.get_data(as_text=True), request.headers.get('X-Line-Signature'))
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        items = get_all_ri()
        if not items:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่มีรายการค้างจ่ายในระบบครับ"))
        else:
            items.sort(key=lambda x: x['dueDate'])
            reply = "รายการค้างจ่าย:\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in items[:3]])
            reply += f"\n\nถัดไป: {items[0]['documentSerial']} ครบ {items[0]['dueDate'][:10]}"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
