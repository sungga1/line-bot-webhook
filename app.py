from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime
import requests

app = Flask(__name__)

# --- ใส่รหัสของคุณตรงนี้ ---
line_bot_api = LineBotApi('sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('5a5f2ad36f44368e77a508f3421b5140')
MY_GROUP_ID = 'C646395b06063544d6233261a86851493'
FLOW_ACCESS_TOKEN='eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGRjk2MDE2NjdFMDhCNjdGRTE4QjIxQ0FERjQzOTAyNDQ0N0E2NzQiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJiX2xnRm1mZ2kyZi1HTEljcmZRNUFrUkhwblEifQ.eyJuYmYiOjE3OTE4NTUxNDEsImV4cCI6MTc5MTg1ODc0MSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmZsb3dhY2NvdW50LmNvbSIsImF1ZCI6ImZsb3dhY2NvdW50LWFwaSIsImNsaWVudF9pZCI6Im1jcC1nYXRld2F5LXBrY2UiLCJzdWIiOiIxNTc5MzA4IiwiYXV0aF90aW1lIjoxNzkxMDgyNDUzLCJpZHAiOiJHb29nbGUiLCJjdXJyZW50Q29tcGFueUlkIjoiMjE0NzEwMyIsInN1cHBvcnRDb2RlIjoiTjE2MjI5NzAiLCJwZXJtaXNzaW9uIjoiNTQ5NzU1ODEzODg3Iiwic2NvcGUiOlsib3BlbmlkIiwicHJvZmlsZSIsImZsb3dhY2NvdW50LWFwaSIsIm9mZmxpbmVfYWNjZXNzIl0sImFtciI6WyJleHRlcm5hbCJdfQ.irefag82aNE3WSAm01MxzGtRO0QOjnbCdBwOwdKkavPEPtZMy1du9t-AehArZ1GAcmpPiZEeBhvM2Yx30UNw6tLXdRzZC0-Nywyy52sgnWAUajjP4mD8gu2bFiqRJhfzLf6y8oqPdoGHG0qD8ovz167xJW-gc9hB_ZcUuxBaQLgYN_cuudSwLbqj0HntCb1O8RJNKGUJAIxKezDJ7Th1qrprkFV6_n6f-0arVVS3onKdwMC8qLCXz2COe1x_0rIJfozoB4FAcxf8JyZY7VPSvdevq4ZgeX6ucoMbbld_AztlE1LJyMGRJXiuMv4a2U4-JL-MWEGt8QwNe5ipC-9Lfg' # เติม Access Token ให้เต็มนะครับ

def get_all_ri():
    url = "https://mcp.flowaccount.com/mcp"
    headers = {"Authorization": f"Bearer {FLOW_ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
        "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1, "sort_by": "publishedon:desc"}}
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        # --- เพิ่มบรรทัดนี้ ---
        print(f"DEBUG: ข้อมูลที่ได้รับจาก FlowAccount: {data}")
        # -------------------
        return data["result"]["content"][0]["data"]["list"]
    except Exception as e:
        print(f"DEBUG: Error in get_all_ri: {e}")
        return []

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    if 'ค้างจ่าย' in event.message.text:
        today = datetime.datetime.now().date()
        items = get_all_ri()
        # กรองรายการที่ยังไม่ได้จ่าย (ใช้ != 'paid' เพื่อความชัวร์)
        awa_items = sorted([i for i in items if i['status'].lower() != 'paid'], key=lambda x: x['dueDate'])
        
        if not awa_items:
            reply = "ไม่มีรายการที่ต้องจ่ายในระบบครับ"
        else:
            upcoming = [i for i in awa_items if (datetime.datetime.strptime(i['dueDate'][:10], '%Y-%m-%d').date() - today).days <= 30]
            if upcoming:
                reply = "ยอดค้างจ่าย (30 วันข้างหน้า):\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ. (ครบ {i['dueDate'][:10]})" for i in upcoming])
            else:
                next_item = awa_items[0]
                reply = f"ไม่มีรายการใน 30 วันนี้ครับ\nรายการถัดไปที่ต้องจ่ายเร็วสุด:\n{next_item['documentSerial']} จ่ายวันที่ {next_item['dueDate'][:10]} ยอด {next_item['total']} บาท"
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

@app.route("/line/webhook", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    try: handler.handle(body, signature)
    except InvalidSignatureError: abort(400)
    return 'OK'

if __name__ == "__main__":
    app.run(port=8080)
