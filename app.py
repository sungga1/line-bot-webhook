from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.exceptions import InvalidSignatureError
from apscheduler.schedulers.background import BackgroundScheduler
import datetime, requests

app = Flask(__name__)

# --- ค่าคงที่ ---
LINE_TOKEN='sIpsVvwuaSiSHk5SyZgMhLzI6bXtNVInBR7Wpgv241cgbPi9QkeukSXrJGGWCpBGnH5OSZym9oI7wEEeptiZ2Mi4ackRhFbejdlLpnjO+TYst9hRSSyYTkA6fJOHAyZxH2/xXVAxJBzDXjtBnN8uAQdB04t89/1O/w1cDnyilFU='
LINE_SECRET='5a5f2ad36f44368e77a508f3421b5140'
MY_GROUP_ID = 'C646395b06063544d6233261a86851493'
REFRESH_TOKEN='eyJhbGciOiJSUzI1NiIsImtpZCI6IjZGRjk2MDE2NjdFMDhCNjdGRTE4QjIxQ0FERjQzOTAyNDQ0N0E2NzQiLCJ0eXAiOiJhdCtqd3QiLCJ4NXQiOiJiX2xnRm1mZ2kyZi1HTEljcmZRNUFrUkhwblEifQ.eyJuYmYiOjE3OTE4NTUxNDEsImV4cCI6MTc5MTg1ODc0MSwiaXNzIjoiaHR0cHM6Ly9hdXRoLmZsb3dhY2NvdW50LmNvbSIsImF1ZCI6ImZsb3dhY2NvdW50LWFwaSIsImNsaWVudF9pZCI6Im1jcC1nYXRld2F5LXBrY2UiLCJzdWIiOiIxNTc5MzA4IiwiYXV0aF90aW1lIjoxNzkxMDgyNDUzLCJpZHAiOiJHb29nbGUiLCJjdXJyZW50Q29tcGFueUlkIjoiMjE0NzEwMyIsInN1cHBvcnRDb2RlIjoiTjE2MjI5NzAiLCJwZXJtaXNzaW9uIjoiNTQ5NzU1ODEzODg3Iiwic2NvcGUiOlsib3BlbmlkIiwicHJvZmlsZSIsImZsb3dhY2NvdW50LWFwaSIsIm9mZmxpbmVfYWNjZXNzIl0sImFtciI6WyJleHRlcm5hbCJdfQ.irefag82aNE3WSAm01MxzGtRO0QOjnbCdBwOwdKkavPEPtZMy1du9t-AehArZ1GAcmpPiZEeBhvM2Yx30UNw6tLXdRzZC0-Nywyy52sgnWAUajjP4mD8gu2bFiqRJhfzLf6y8oqPdoGHG0qD8ovz167xJW-gc9hB_ZcUuxBaQLgYN_cuudSwLbqj0HntCb1O8RJNKGUJAIxKezDJ7Th1qrprkFV6_n6f-0arVVS3onKdwMC8qLCXz2COe1x_0rIJfozoB4FAcxf8JyZY7VPSvdevq4ZgeX6ucoMbbld_AztlE1LJyMGRJXiuMv4a2U4-JL-MWEGt8QwNe5ipC-9Lfg'
CLIENT_ID = 'claude-MHFByqsmm1J44ZOBX7lSbw'

# --- ระบบ Token ---
cache = {"access_token": None}

def refresh_token():
    payload = {"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN, "client_id": CLIENT_ID}
    try:
        res = requests.post("https://mcp.flowaccount.com/oauth/token", data=payload)
        if res.status_code == 200:
            cache["access_token"] = res.json()['access_token']
            return cache["access_token"]
    except Exception:
        pass
    return None

def get_all_ri():
    if not cache["access_token"]:
        cache["access_token"] = refresh_token()
    headers = {"Authorization": f"Bearer {cache['access_token']}", "Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", 
               "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1}}}
    res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
    
    if res.status_code == 401 or "session_expired" in res.text:
        new_token = refresh_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
            res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)

try:
        return res.json()["result"]["content"][0]["data"]["list"]
    except Exception:
        return []

# --- Webhook ---
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
        items = get_all_ri()
        if not items:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="ไม่พบรายการค้างจ่ายในระบบครับ"))
        else:
            reply = "รายการค้างจ่าย:\n" + "\n".join([f"• {i['documentSerial']} | {i['total']} บ." for i in items[:5]])
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    app.run(port=8080)
