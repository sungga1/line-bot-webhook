from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests # อย่าลืมเพิ่ม requests ใน requirements.txt

app = Flask(__name__)
line_bot_api = LineBotApi('ใส่_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('ใส่_CHANNEL_SECRET')
MY_GROUP_ID = 'ใส่_GROUP_ID'

# ฟังก์ชันดึงข้อมูล RI จาก FlowAccount
def get_ri_from_flowaccount():
    # ใช้ token เดียวกับที่คุณใช้ดึงข้อมูลก่อนหน้านี้
    # คืนค่า list ของรายการที่มี {'documentSerial': '...', 'contactName': '...', 'total': ..., 'dueDate': '2026-...' }
    return [] # ใส่ตรรกะดึงข้อมูลของคุณที่นี่

def check_and_notify():
    today = datetime.datetime.now().date()
    items = get_ri_from_flowaccount()
    reminders = []
    
    for item in items:
        due_date = datetime.datetime.strptime(item['dueDate'][:10], '%Y-%m-%d').date()
        delta = (due_date - today).days
        if delta in [7, 3, 1, 0]:
            reminders.append(f"• {item['documentSerial']} | {item['contactName']} | {item['total']} บ. (เหลือ {delta} วัน)")
            
    if reminders:
        msg = "⚠️ แจ้งเตือนจ่ายเงินซัพพลายเออร์:\n" + "\n".join(reminders)
        line_bot_api.push_message(MY_GROUP_ID, TextSendMessage(text=msg))

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
        items = get_ri_from_flowaccount()
        # กรองเฉพาะที่ยังไม่จ่าย (status awaiting) และสรุปให้ดู
        reply = "ยอด RI ที่ต้องจ่าย:\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in items])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
