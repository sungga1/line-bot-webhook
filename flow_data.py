import os
import requests
import time
import auth_manager

MCP_ENDPOINT = "https://mcp.flowaccount.com/mcp"

def _post_with_retry(url, headers, json_data, max_attempts=3, retry_delay=3):
    """
    ระบบ Retry Logic เลียนแบบโปรแกรม PC
    ถ้าเน็ตขัดข้อง จะลองใหม่ 3 ครั้งก่อนยอมแพ้
    """
    for attempt in range(1, max_attempts + 1):
        try:
            res = requests.post(url, headers=headers, json=json_data, timeout=30)
            return res
        except requests.exceptions.RequestException as e:
            if attempt < max_attempts:
                print(f"⚠️ เน็ตแกว่ง ลองใหม่รอบที่ {attempt}... ({e})")
                time.sleep(retry_delay)
            else:
                print(f"❌ เชื่อมต่อ FlowAccount ไม่สำเร็จ: {e}")
                raise e

          def get_all_ri():
    """
    ดึงรายการรับสินค้า (RI) โดยเรียกผ่านฟังก์ชัน Retry
    """
    token = auth_manager.get_valid_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "expense__list_receiving_inventory",
            "arguments": {"page": 1, "pageSize": 50}
        }
    }
    
    try:
        res = _post_with_retry(MCP_ENDPOINT, headers=headers, json_data=payload)
        data = res.json()
        
        # ตรวจสอบสัญญาณ Session หมดอายุ (ถอดแบบจากโปรแกรม PC)
        if "result" in data and data["result"].get("content"):
            content_text = str(data["result"]["content"][0].get("text", ""))
            if "session_expired" in content_text or "unauthorized" in content_text:
                return "SESSION_EXPIRED_MARKER"
        
        # ดึงข้อมูลรายการ
        if "result" in data and data["result"].get("content"):
            import json
            content = data["result"]["content"][0]
            inner = json.loads(content.get("text", "{}"))
            return inner.get("data", {}).get("list", [])
        return []
    except Exception as e:
        print(f"DEBUG: get_all_ri error: {e}")
        return []

  CLIENT_ID = os.environ.get('CLIENT_ID', 'claude-MHFByqsmm1J44ZOBX7lSbw')
