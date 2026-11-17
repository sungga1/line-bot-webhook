from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests # อย่าลืมเพิ่ม requests ใน requirements.txt

app = Flask(__name__)
line_bot_api = LineBotApi('sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('5a5f2ad36f44368e77a508f3421b5140')
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
    msg = event.message.text
    if 'ค้างจ่าย' in msg:
        today = datetime.datetime.now().date()
        items = get_ri_from_flowaccount()
        awa_items = [i for i in items if i['status'].lower().startswith('awa')]
        
        if not awa_items:
            reply = "ไม่มีรายการที่ต้องจ่ายในระบบครับ"
        else:
            # เรียงลำดับรายการตามวันครบกำหนด
            awa_items.sort(key=lambda x: x['dueDate'])
            
            # สรุปรายการในรอบ 30 วัน
            upcoming = [i for i in awa_items if (datetime.datetime.strptime(i['dueDate'][:10], '%Y-%m-%d').date() - today).days <= 30]
            
            if upcoming:
                reply = "ยอดค้างจ่าย (30 วันข้างหน้า):\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ. (ครบ {i['dueDate'][:10]})" for i in upcoming])
            else:
                next_item = awa_items[0] # รายการที่เร็วที่สุดที่เหลืออยู่
                reply = f"ไม่มีรายการใน 30 วันนี้ครับ\nรายการถัดไป: {next_item['documentSerial']} ต้องจ่าย {next_item['dueDate'][:10]} ยอด {next_item['total']} บาท"
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
