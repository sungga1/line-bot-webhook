from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import flow_api

app = Flask(__name__)

LINE_TOKEN='sIpsVv...lFU='
LINE_SECRET='5a5f2a...5140'

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

@app.route("/line/webhook", methods=['POST'])
def callback():
    try:
        handler.handle(request.get_data(as_text=True), request.headers.get('X-Line-Signature'))
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        items = flow_api.get_all_ri()
        if not items:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่มีรายการค้างจ่ายในระบบครับ"))
        else:
            items.sort(key=lambda x: x['dueDate'])
            reply = "รายการค้างจ่าย:\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in items[:3]])
            reply += f"\n\nถัดไป: {items[0]['documentSerial']} ครบ {items[0]['dueDate'][:10]}"
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
