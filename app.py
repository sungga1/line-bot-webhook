from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

# ===== ต้องใส่ให้ตรงครับ (จาก LINE Developers) =====
line_bot_api = LineBotApi('sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('5a5f2ad36f44368e77a508f3421b5140')

@app.route("/line/webhook", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    # 1. คำสั่งดึง ID กลุ่ม (สำคัญสำหรับการแจ้งเตือนอัตโนมัติ)
    if 'ดึง ID กลุ่ม' in msg:
        try:
            group_id = event.source.group_id
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"Group ID คือ: {group_id}"))
        except LineBotApiError as e:
            # แจ้งเตือนใน Log แต่ไม่ให้บอทค้าง
            print(f"LineBotApiError: {e.message}")
    
    # 2. ตัวอย่างคำสั่งอื่นๆ (ขยายได้ครับ)
    # if 'สถานะ' in msg:
    #    ... ดึงข้อมูลจาก FlowAccount ...

# ===== ระบบแจ้งเตือนทุกเช้าที่ 8:00 =====
def check_and_notify():
    # ตรงนี้จะเรียกใช้งานดึงยอดค้างจ่ายจาก FlowAccount จริงๆ ได้
    # สำหรับทดสอบให้ส่งข้อความแจ้งเตือนตรงไปที่ Group
    line_bot_api.push_message('ใส่_Group_ID_ที่ดึงได้จากคำสั่งข้างบน', 
                              TextSendMessage(text="⚠️ เตือน: ตรวจพบรายการครบกำหนดจ่ายเงินซัพพลายเออร์"))

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="cron", hour=8, minute=0)
scheduler.start()

@app.route("/line/webhook", methods=['POST'])
def callback():

    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

if __name__ == "__main__":
    app.run(port=8080)
