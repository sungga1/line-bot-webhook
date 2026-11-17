import requests
import json

cache = {"access_token": None}
REFRESH_TOKEN='NbYe3s...GE8M'
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
               "params": {"name": "expense__list_receiving_inventory", "arguments": {"page": 1}}}
    res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
    
    if res.status_code == 401 or "session_expired" in res.text:
        new_token = refresh_token()
        if new_token:
            headers["Authorization"] = f"Bearer {new_token}"
            res = requests.post("https://mcp.flowaccount.com/mcp", json=payload, headers=headers)
    try:
        return res.json()["result"]["content"][0]["data"]["list"]
    except: return []
