import requests
import json

cache = {"access_token": None}
REFRESH_TOKEN=*** # จะดึงจาก Environment Variables ของ Render
CLIENT_ID = 'claude-MHFByqsmm1J44ZOBX7lSbw'

def refresh_token():
    if not REFRESH_TOKEN: return None # ถ้ายังไม่ได้ตั้งค่า
    payload = {"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN, "client_id": CLIENT_ID}
    try:
        res = requests.post("https://mcp.flowaccount.com/oauth/token", data=payload)
        data = res.json()
        if data.get("error") == "session_expired":
            return "EXPIRED" # ส่งสัญญาณเตือนว่าหมดอายุ
        if res.status_code == 200:
            cache["access_token"] = data.get('access_token')
            return cache["access_token"]
    except: pass
    return None

def get_all_ri():
    if not cache["access_token"]: cache["access_token"] = refresh_token()
    headers = {"Authorization": f"Bearer {cache['access_token']}", "Content-Type": "application/json"}
    payload = {"jsonrpc": "2.0", "id": 1, "method": "tools/call", 
               "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1, "pageSize": 50}}}
    
    try:
        res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
        data = res.json()
        
        # ตรวจสอบ Error ก่อนจะไปดึงข้อมูล
        if "error" in data and data["error"] == "session_expired":
            return "SESSION_EXPIRED_MARKER" # <--- สัญญาณเตือนพิเศษ
            
        if "result" in data and data["result"].get("content"):
            return data["result"]["content"][0]["text"]
        return "ไม่พบข้อมูลจาก API"
    except Exception as e:
        return f"Error: {str(e)}"
