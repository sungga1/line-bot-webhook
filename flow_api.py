import json
import logging
import os

import requests

log = logging.getLogger("flow_api")

MCP_URL = "https://mcp.flowaccount.com/mcp"
TOKEN_URL = "https://mcp.flowaccount.com/oauth/token"
CLIENT_ID = os.environ.get("FLOW_CLIENT_ID", "claude-MHFByqsmm1J44ZOBX7lSbw")
TOKEN_FILE = os.environ.get("FLOW_TOKEN_FILE", "flow_token.json")

state = {"access_token": None, "session_id": None, "initialized": False}


# ---------- Refresh token (เก็บลงไฟล์ เพราะ OAuth มักออก refresh token ใหม่ทุกครั้ง) ----------
def _load_refresh_token():
    try:
        with open(TOKEN_FILE) as f:
            return json.load(f)["refresh_token"]
    except Exception:
        return os.environ.get("FLOW_REFRESH_TOKEN")


def _save_refresh_token(token):
    with open(TOKEN_FILE, "w") as f:
        json.dump({"refresh_token": token}, f)


def refresh_access_token():
    rt = _load_refresh_token()
    if not rt:
        raise RuntimeError("ไม่มี refresh token (ตั้ง FLOW_REFRESH_TOKEN)")
    res = requests.post(
        TOKEN_URL,
        data={"grant_type": "refresh_token", "refresh_token": rt, "client_id": CLIENT_ID},
        timeout=20,
    )
    if res.status_code != 200:
        raise RuntimeError(f"refresh token ไม่สำเร็จ HTTP {res.status_code}: {res.text[:300]}")
    body = res.json()
    state["access_token"] = body["access_token"]
    state["session_id"] = None
    state["initialized"] = False
    if body.get("refresh_token"):
        _save_refresh_token(body["refresh_token"])
    return state["access_token"]


# ---------- MCP over HTTP ----------
def _parse_response(res):
    """รองรับทั้ง JSON ปกติและ SSE (text/event-stream)"""
    ctype = res.headers.get("Content-Type", "")
    if "text/event-stream" in ctype:
        for line in res.text.splitlines():
            if line.startswith("data:"):
                data = line[5:].strip()
                if data:
                    return json.loads(data)
        raise RuntimeError("SSE ไม่มี data")
    return res.json()


def _post(payload, retry=True):
    if not state["access_token"]:
        refresh_access_token()
    headers = {
        "Authorization": f"Bearer {state['access_token']}",
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if state["session_id"]:
        headers["Mcp-Session-Id"] = state["session_id"]
    res = requests.post(MCP_URL, json=payload, headers=headers, timeout=30)
    if res.status_code == 401 and retry:
        refresh_access_token()
        return _post(payload, retry=False)
    if res.status_code >= 400:
        raise RuntimeError(f"MCP HTTP {res.status_code}: {res.text[:300]}")
    return res


def _ensure_initialized():
    if state["initialized"]:
        return
    res = _post({
        "jsonrpc": "2.0", "id": 0, "method": "initialize",
        "params": {"protocolVersion": "2025-03-26", "capabilities": {},
                   "clientInfo": {"name": "line-bot", "version": "1.0"}},
    })
    state["session_id"] = res.headers.get("Mcp-Session-Id")
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    state["initialized"] = True


def call_tool(name, arguments):
    _ensure_initialized()
    res = _post({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                 "params": {"name": name, "arguments": arguments}})
    data = _parse_response(res)
    if "error" in data:
        raise RuntimeError(f"MCP error: {data['error']}")
    result = data["result"]
    if result.get("isError"):
        raise RuntimeError(f"tool error: {result['content'][0].get('text', '')[:300]}")
    text = result["content"][0]["text"]
    try:
        return json.loads(text)  # ส่วนใหญ่ tool คืน JSON ในรูปข้อความ
    except ValueError:
        return text


def _extract_items(parsed):
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("data", "items", "list", "results", "documents"):
            v = parsed.get(key)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                inner = _extract_items(v)
                if inner:
                    return inner
    return []


# ---------- ฟังก์ชันที่ app.py เรียก ----------
def get_raw():
    """ไว้ debug: ดูข้อมูลดิบที่ FlowAccount ส่งกลับมา"""
    return call_tool("expense__list_receiving_inventory", {"page": 1, "pageSize": 50})


def is_unpaid(item):
    # TODO: หลังพิมพ์ "debug" ใน LINE แล้วเห็นชื่อ field สถานะจริง ให้แก้ตรงนี้
    # เช่น return item.get("statusString") == "รออนุมัติจ่าย"
    return True


def get_unpaid_ri():
    items = _extract_items(get_raw())
    return [i for i in items if isinstance(i, dict) and is_unpaid(i)]
