from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import os

app = Flask(__name__)

# แก้ไขที่นี่ให้เป็นรหัสของคุณ
line_bot_api = LineBotApi('ใส่_CHANNEL_ACCESS_TOKEN_ที่นี่')
handler = WebhookHandler('ใส่_CHANNEL_SECRET_ที่นี่')

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
        group_id = event.source.group_id
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=f"Group ID คือ: {group_id}"))

if __name__ == "__main__":
    app.run(port=8080)
