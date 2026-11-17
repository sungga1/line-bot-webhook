import os
from flask import Flask, request, abort, redirect
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, URIAction
from linebot.exceptions import InvalidSignatureError
import flow_api

app = Flask(__name__)

LINE_TOKEN = os.environ.get('LINE_TOKEN')
LINE_SECRET = os.environ.get('LINE_SECRET')

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# ลิงก์สำหรับ Login ใหม่ (ใช้ Client ID เดิม)
LOGIN_URL = "https://mcp.flowaccount.com/oauth/authorize?response_type=code&client_id=claude-MHFByqsmm1J44ZOBX7lSbw&redirect_uri=http://localhost:8089/callback&scope=openid+profile+flowaccount-api+offline_access"

@app.route("/line/webhook", methods=['POST'])
def callback():
    try:
        handler.handle(request.get_data(as_text=True), request.headers.get('X-Line-Signature'))
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        result = flow_api.get_all_ri()
        
        # ตรวจสอบสัญญาณเตือน "Token หมดอายุ"
        if result == "SESSION_EXPIRED_MARKER":
            # ส่งลิงก์ Login ให้คุณในกลุ่ม LINE
            message = TextSendMessage(text="⚠️ สำคัญ: Session ของ FlowAccount หมดอายุครับ\n"
                                          "กรุณาแทบที่นี่เพื่อ Login ใหม่:\n" + LOGIN_URL)
            line_bot_api.reply_message(event.reply_token, message)
            return

        # แสดงผลข้อมูลตามปกติ
        if not result or result == "ไม่พบข้อมูลจาก API":
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่มีรายการค้างจ่ายในระบบครับ"))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=str(result)[:1000]))

if __name__ == "__main__":
    app.run(port=8080)
