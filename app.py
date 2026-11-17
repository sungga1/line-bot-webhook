import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
import flow_data  # <--- เรียกใช้ฟังก์ชันใหม่

app = Flask(__name__)

# อ่านค่าจาก Environment Variables ที่ Render
LINE_TOKEN = os.environ.get('LINE_TOKEN')
LINE_SECRET = os.environ.get('LINE_SECRET')

line_bot_api = LineBotApi(LINE_TOKEN)
handler = WebhookHandler(LINE_SECRET)

# ลิงก์สำหรับ Login ใหม่
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
        result = flow_data.get_all_ri() # ใช้ฟังก์ชันใหม่ดึงข้อมูล
        
        # ตรวจสอบว่า Token หมดหรือยัง
        if result == "SESSION_EXPIRED_MARKER":
            # ส่งลิงก์ Login ให้คุณในกลุ่ม LINE
            message = TextSendMessage(text="⚠️ สำคัญ: Session ของ FlowAccount หมดอายุครับ\n"
                                          "กรุณาแทบที่นี่เพื่อ Login ใหม่:\n" + LOGIN_URL)
            line_bot_api.reply_message(event.reply_token, message)
            return

        # แสดงผลข้อมูล
        if not result:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่มีรายการค้างจ่ายในระบบครับ"))
        else:
            # ตัดข้อความให้สั้นลงหน่อย
            reply = "รายการค้างจ่าย:\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in result[:3]])

line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
