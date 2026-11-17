from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime

app = Flask(__name__)

# --- ตั้งค่าของคุณ ---
line_bot_api = LineBotApi('ใส่_CHANNEL_ACCESS_TOKEN_ที่นี่')
handler = WebhookHandler('ใส่_CHANNEL_SECRET_ที่นี่')
MY_GROUP_ID = 'ใส่_GROUP_ID_ที่ได้จากบอท'

# --- ระบบแจ้งเตือนอัตโนมัติ (Scheduler) ---
def check_and_notify():
    # ในนี้คือตรรกะดึงข้อมูลจาก FlowAccount (เชื่อมต่อกับฟังก์ชันดึง RI เดิม)
    # และตรวจสอบเงื่อนไข 7, 3, 1 วัน
    message = "⚠️ เตือน: ตรวจพบรายการครบกำหนดจ่ายเงินซัพพลายเออร์"
    line_bot_api.push_message(MY_GROUP_ID, TextSendMessage(text=message))

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="cron", hour=8, minute=0)
scheduler.start()

# --- ระบบ Webhook ตอบโต้ ---
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
    if 'ค้างจ่าย' in msg:
        # แทนที่ด้วยตรรกะดึงยอด RI ของคุณ
        reply = 'ยอดค้างจ่าย RI ปี 2026:\n1. RI202609230001 | 422,000 บาท\n2. RI202607110002 | 196,000 บาท'
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))
    elif 'ดึง ID กลุ่ม' in msg:
        
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"Group ID คือ: {event.source.group_id}"))

if __name__ == "__main__":
    app.run(port=8080)
