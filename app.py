from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

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
    # ไม่ต้องมี if แล้ว ตอบทุกอย่างที่พิมพ์เข้ามา!
    reply_text = f"บอทได้รับข้อความแล้ว: {event.message.text}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    app.run(port=8080)
