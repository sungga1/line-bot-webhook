import base64
import hashlib
import secrets

# --- ฟังก์ชันช่วยเหลือ ---
def base64url_encode(data: bytes) -> str:
    """
    เข้ารหัสเป็น Base64 URL-safe
    ใช้สำหรับสร้าง Code Verifier/Challenge
    """
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

# --- ฟังก์ชันสำคัญ: สร้าง PKCE Pair ---
def generate_pkce_pair() -> tuple:
    """
    สร้างคู่ของรหัสความปลอดภัย (Code Verifier และ Challenge)
    FlowAccount จะตรวจสอบค่านี้ทุกครั้งที่ login
    คืนค่า: (code_verifier, code_challenge)
    """
    code_verifier = base64url_encode(secrets.token_bytes(32))
    digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64url_encode(digest)
    return code_verifier, code_challenge

import os
import requests

# ดึงข้อมูลจาก Render Environment (เราจะไม่ใส่ Token ลงใน code ตรงๆ)
REFRESH_TOKEN = os.environ.get('REFRESH_TOKEN')
CLIENT_ID = os.environ.get('CLIENT_ID', 'claude-MHFByqsmm1J44ZOBX7lSbw')
TOKEN_ENDPOINT = "https://mcp.flowaccount.com/oauth/token"

cache = {"access_token": None}

def refresh_token():
    """
    ฟังก์ชันสำหรับรีเฟรช Access Token ใหม่
    """
    if not REFRESH_TOKEN:
        return None
        
    payload = {
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
        "client_id": CLIENT_ID
    }
    try:
        res = requests.post(TOKEN_ENDPOINT, data=payload, timeout=15)
        if res.status_code == 200:
            data = res.json()
            cache["access_token"] = data.get('access_token')
            return cache["access_token"]
    except Exception as e:
        print(f"DEBUG: Refresh Token Error: {e}")
    return None

def get_valid_token():
    """
    ด่านหน้า: เรียกใช้ฟังก์ชันนี้เพื่อขอ Token ที่ใช้งานได้เสมอ
    """
    if not cache["access_token"]:
        cache["access_token"] = refresh_token()
    return cache["access_token"]
