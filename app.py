import os
from flask import Flask, request, abort
from linebot import WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent

app = Flask(__name__)
# ใช้ LINE_SECRET จาก environment variable ของ Render
handler = WebhookHandler(os.environ.get('LINE_SECRET'))

@app.route("/line/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent)
def handle_message(event):
    # นี่คือจุดที่จะ Print UserId ออกมาใน Log ของ Render
    print(f"!!! USER_ID DETECTED: {event.source.user_id} !!!")

if __name__ == "__main__":
    app.run(port=int(os.environ.get("PORT", 10000)))
