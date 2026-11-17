from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
# (สมมติว่าคุณมีฟังก์ชันดึงยอดค้างจ่ายจาก FlowAccount อยู่แล้ว)
# ผมจะเพิ่มส่วน Scheduler ให้รันเช้า 8 โมงทุกวัน

app = Flask(__name__)
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

def check_and_notify():
    # 1. ดึงรายการ RI สถานะ 'awa' จาก FlowAccount
    # 2. คำนวณวันครบกำหนด (Due Date)
    # 3. ถ้าเหลือ 7, 3, 1 วัน หรือวันนี้ คือวันครบกำหนด ให้ส่งแจ้งเตือน:
    message = "⚠️ เตือนจ่ายเงินซัพพลายเออร์: [เลขเอกสาร] ยอด [จำนวนเงิน] ครบกำหนด [วันที่]"
    line_bot_api.push_message('YOUR_GROUP_ID', TextSendMessage(text=message))

# ตั้งเวลาให้ทำงานทุกวัน 08:00
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="cron", hour=8, minute=0)
scheduler.start()

@app.route("/line/webhook", methods=['POST'])
def callback():
    # (โค้ด Webhook เดิมของคุณที่ใช้ตอบโต้)
    return 'OK'

if __name__ == "__main__":
    app.run(port=8080)
