from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests

app = Flask(__name__)

# --- ตั้งค่า ---
line_bot_api = LineBotApi('sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('ใส่_CHANNEL5a5f2ad36f44368e77a508f3421b5140')
MY_GROUP_ID = 'ใส่_GROUP_ID_ที่ดึงได้จากบอท'
FLOW_ACCESS_TOKEN='ใส่_AC...่นี่'

def get_ri_from_flowaccount():
    url = "https://mcp.flowaccount.com/mcp"
    headers = {"Authorization": f"Bearer {FLOW_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1, "sort_by": "publishedon:desc"}}
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        return data["result"]["content"][0]["data"]["list"]
    except Exception as e:
        print(f"Error: {e}")
        return []

def check_and_notify():
    today = datetime.datetime.now().date()
    items = get_ri_from_flowaccount()
    awa_items = [i for i in items if i['status'].lower().startswith('awa')]
    reminders = []
    for item in awa_items:
        due_date = datetime.datetime.strptime(item['dueDate'][:10], '%Y-%m-%d').date()
        delta = (due_date - today).days
        if delta in [7, 3, 1, 0]:
            reminders.append(f"• {item['documentSerial']} | {item['contactName']} | {item['total']} บ. (เหลือ {delta} วัน)")
    if reminders:

        line_bot_api.push_message(MY_GROUP_ID, TextSendMessage(text="⚠️ แจ้งเตือนจ่ายเงินซัพพลายเออร์:\n" + "\n".join(reminders)))

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="cron", hour=8, minute=0)
scheduler.start()

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
        today = datetime.datetime.now().date()
        items = get_ri_from_flowaccount()
        awa_items = [i for i in items if i['status'].lower().startswith('awa')]
        awa_items.sort(key=lambda x: x['dueDate'])
        
        if not awa_items:
            reply = "ไม่มีรายการที่ต้องจ่ายในระบบครับ"
        else:
            upcoming = [i for i in awa_items if (datetime.datetime.strptime(i['dueDate'][:10], '%Y-%m-%d').date() - today).days <= 30]
            if upcoming:
                reply = "ยอดค้างจ่าย (30 วันข้างหน้า):\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ. (ครบ {i['dueDate'][:10]})" for i in upcoming])
            else:
                next_item = awa_items[0]
                reply = f"ไม่มีรายการใน 30 วันนี้ครับ\nรายการถัดไป: {next_item['documentSerial']} ต้องจ่าย {next_item['dueDate'][:10]} ยอด {next_item['total']} บาท"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
