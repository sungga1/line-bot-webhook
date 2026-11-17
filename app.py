import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import flow_api

app = Flask(__name__)

# อ่านค่า Token จาก Environment Variables ที่คุณเพิ่งใส่ไป
LINE_TOKEN = os.environ.get('LINE_TOKEN')
LINE_SECRET = os.environ.get('LINE_SECRET')

if not LINE_TOKEN or not LINE_SECRET:
    # แสดง Warning ถ้าไม่ได้ตั้งค่าอะไรไว้ (เพื่อความปลอดภัย)
    print("Warning: LINE_TOKEN or LINE_SECRET not set in Environment Variables")

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

@app.route("/line/webhook", methods=['POST'])
def callback():
    try:
        handler.handle(request.get_data(as_text=True), request.headers.get('X-Line-Signature'))
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        raw_data = flow_api.get_all_ri()
        # ตอบกลับข้อมูลดิบ (ตัดเหลือ 1000 ตัวอักษร)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(raw_data)[:1000]))

if __name__ == "__main__":
    app.run(port=8080)
