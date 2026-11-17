from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import os

app = Flask(__name__)
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
    if 'ดึง ID กลุ่ม' in msg:
        # บรรทัดนี้จะตอบกลับ ID กลุ่มให้คุณ
        group_id = event.source.group_id
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"Group ID คือ: {group_id}"))

def check_and_notify():
    # ในอนาคตใส่ Group ID ที่ได้จากข้อบนนี้ลงใน push_message
    line_bot_api.push_message('ใส่_Group_ID_ที่ได้_ตรงนี้', TextSendMessage(text="⚠️ เตือน: มีรายการครบกำหนดจ่ายเงิน!"))

if __name__ == "__main__":
    app.run(port=8080)
