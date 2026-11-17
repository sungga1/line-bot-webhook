from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests

app = Flask(__name__)

# --- ค่าที่สรุปให้แล้ว ---
line_bot_api = LineBotApi('sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('5a5f2ad36f44368e77a508f3421b5140')
MY_GROUP_ID = 'C646395b06063544d6233261a86851493'
FLOW_ACCESS_TOKEN='eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGRjk2MDE2NjdFMDhCNjdGRTE4QjIxQ0FERjQzOTAyNDQ0N0E2NzQiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJiX2xnRm1mZ2kyZi1HTEljcmZRNUFrUkhwblEifQ.eyJuYmYiOjE3OTQ4OTY3MDMsImV4cCI6MTc5NDkwMDMwMywiaXNzIjoiaHR0cHM6Ly9hdXRoLmZsb3dhY2NvdW50LmNvbSIsImF1ZCI6ImZsb3dhY2NvdW50LWFwaSIsImNsaWVudF9pZCI6Im1jcC1nYXRld2F5LXBrY2UiLCJzdWIiOiIxNjg5MTgxIiwiYXV0aF90aW1lIjoxNzk0ODk2NzAzLCJpZHAiOiJsb2NhbCIsImN1cnJlbnRDb21wYW55SWQiOiIyMTQ3MTAzIiwic3VwcG9ydENvZGUiOiJOMTYyMjk3MCIsInBlcm1pc3Npb24iOiI1MTc1NDM1NTkxNjciLCJzY29wZSI6WyJvcGVuaWQiLCJwcm9maWxlIiwiZmxvd2FjY291bnQtYXBpIiwib2ZmbGluZV9hY2Nlc3MiXSwiYW1yIjpbInB3ZCJdfQ.LKyFkhPfkNQkCy4eiJxgJHG6R5B7Jgyeu48MIRqDLVEvdYzIkOUvLwEGcguJ4KH32VJ7n4CsQJMBjm6aY-0oyW-LqkyBZNuAiJ_gucueDzmh2onpIkR-1dgH8uMlM3zre2mxnztSsK-QbLv1vu_yMVHoxEst-ZGNIT7i6hGrJNwxp7nOcCo9Or45LUsXsQKp5xs8MSQrqD5PuUXNz6QSlfdjE8vddevffs1MqLC7ftgb4YX8nUYWtKtp0fKzKMpZvWpig3GpgvLXRWEjl_aMpZ1SOZra44QGMBPDkMhP2HjDB1FEdEYulB_IXjgyV5wzxnIDBcl2DpKhLLi4uVXqmA' # (อย่าลืมเติม Token เต็มๆ ของคุณตรงนี้)

def get_ri_from_flowaccount():
    url = "https://mcp.flowaccount.com/mcp"
    headers = {"Authorization": f"Bearer {FLOW_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", 
               "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1, "sort_by": "publishedon:desc"}}}
    try:
        response = requests.post(url, json=payload, headers=headers)
        return [i for i in response.json()["result"]["content"][0]["data"]["list"] if i['status'].lower().startswith('awa')]
    except: return []

def check_and_notify():
    today = datetime.datetime.now().date()
    awa_items = get_ri_from_flowaccount()
    reminders = [f"• {i['documentSerial']} | {i['contactName']} | {i['total']} บ. (เหลือ {(datetime.datetime.strptime(i['dueDate'][:10], '%Y-%m-%d').date() - today).days} วัน)" 
                 for i in awa_items if (datetime.datetime.strptime(i['dueDate'][:10], '%Y-%m-%d').date() - today).days in [7, 3, 1, 0]]
    if reminders:

        line_bot_api.push_message(MY_GROUP_ID, TextSendMessage(text="⚠️ แจ้งเตือนจ่ายเงินซัพพลายเออร์:\n" + "\n".join(reminders)))

scheduler = BackgroundScheduler()
scheduler.add_job(func=check_and_notify, trigger="cron", hour=8, minute=0)
scheduler.start()

@app.route("/line/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        items = get_ri_from_flowaccount()
        reply = "ยอดค้างจ่าย RI:\n" + ("\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in items]) if items else "ไม่มีรายการที่ต้องจ่าย")
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
