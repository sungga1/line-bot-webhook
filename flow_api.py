import os
import requests
import json

cache = {"access_token": None}
# อ่านค่า Token จากระบบ Environment ของ Render
REFRESH_TOKEN = os.environ.get('REFRESH_TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID', 'claude-MHFByqsmm1J44ZOBX7lSbw')

def refresh_token():
    payload = {"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN, "client_id": CLIENT_ID}
    try:
        res = requests.post("https://mcp.flowaccount.com/oauth/token", data=payload)
        if res.status_code == 200:
            cache["access_token"] = res.json().get('access_token')
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
        if "result" in data and data["result"].get("content"):
            return data["result"]["content"][0]["text"] # ส่งข้อมูลดิบออกมา
        return "ไม่พบข้อมูลจาก API"
    except Exception as e:
        return f"Error: {str(e)}"
