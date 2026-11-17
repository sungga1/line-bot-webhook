import requests
import json

cache = {"access_token": None}
# ใส่ Refresh Token ใหม่ที่นี่
REFRESH_TOKEN='EYy-oB6L1gZ-M9tJ0y7n-K3lVfN4j5i9Yq2tZ_vB_Ww.z3Xm_pQ8u_V1wT6eR0qA9w'
CLIENT_ID = 'claude-MHFByqsmm1J44ZOBX7lSbw'

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
        # แปลงข้อความดิบออกมาดู
        raw_text = data["result"]["content"][0]["text"]
        return raw_text # คืนค่าข้อความดิบไปให้ LINE เลย
    except Exception as e:
        return f"Error: {str(e)}"
