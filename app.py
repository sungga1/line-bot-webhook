from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError

app = Flask(__name__)

# --- ค่าคงที่ ---
LINE_TOKEN='***'
LINE_SECRET='***'

handler = WebhookHandler('5a5f2ad36f44368e77a508f3421b5140')
line_bot_api = LineBotApi('sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU=')
@app.route("/", methods=['GET'])
def home():
    return "Bot is running clean."

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
    # เทสระบบตอบโต้
    if event.message.text == "ping":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="pong!"))

if __name__ == "__main__":
    app.run(port=8080)
