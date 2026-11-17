from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import flow_api

app = Flask(__name__)

LINE_TOKEN='sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU='
LINE_SECRET='5a5f2ad36f44368e77a508f3421b5140'

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
        # ตอบกลับข้อมูลดิบ (ตัดให้เหลือ 1000 ตัวอักษรเพื่อไม่ให้ LINE บล็อก)
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(raw_data)[:1000]))

if __name__ == "__main__":
    app.run(port=8080)
