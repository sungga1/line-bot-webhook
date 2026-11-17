import json
import logging
import os

from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

import flow_api

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("app")

app = Flask(__name__)

# อ่านค่าลับจาก environment variable ไม่ฝังในโค้ด
line_bot_api = LineBotApi(os.environ["LINE_TOKEN"])
handler = WebhookHandler(os.environ["LINE_SECRET"])


@app.route("/line/webhook", methods=["POST"])
def callback():
    try:
        handler.handle(request.get_data(as_text=True), request.headers.get("X-Line-Signature"))
    except InvalidSignatureError:
        abort(400)
    return "OK"


def _fmt_money(v):
    try:
        return f"{float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def _reply(event, text):
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=text[:4900]))


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text = event.message.text.strip()

    # พิมพ์ "debug" ใน LINE เพื่อดูข้อมูลดิบที่ FlowAccount ส่งกลับมา
    if text.lower() == "debug":
        try:
            raw = flow_api.get_raw()
            _reply(event, json.dumps(raw, ensure_ascii=False, indent=1) if not isinstance(raw, str) else raw)
        except Exception as e:
            log.exception("debug failed")
            _reply(event, f"Error: {e}")
        return

    if "ค้างจ่าย" not in text:
        return

    try:
        items = flow_api.get_unpaid_ri()
    except Exception as e:
        # แยกกรณี "ดึงข้อมูลไม่ได้" ออกจาก "ไม่มีรายการ" ไม่ให้สับสนกัน
        log.exception("get_unpaid_ri failed")
        _reply(event, f"ดึงข้อมูลจาก FlowAccount ไม่สำเร็จ: {e}")
        return

    if not items:
        _reply(event, "ไม่มีรายการค้างจ่ายในระบบครับ")
        return

    items.sort(key=lambda x: x.get("dueDate") or "9999")
    lines = [f"• {i.get('documentSerial', '-')} | {_fmt_money(i.get('total'))} บ."
             for i in items[:10]]
    first = items[0]
    reply = f"รายการค้างจ่าย ({len(items)} รายการ):\n" + "\n".join(lines)
    reply += f"\n\nถัดไป: {first.get('documentSerial', '-')} ครบ {(first.get('dueDate') or '-')[:10]}"
    _reply(event, reply)


if __name__ == "__main__":
    app.run(port=8080)
