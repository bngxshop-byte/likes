import os
import hmac
import hashlib
import secrets
from flask import Flask, request, jsonify, session, redirect
import requests

app = Flask(__name__)
app.secret_key = secrets.token_hex(64)

# =================== إعدادات الأمان ====================
API_MASTER_KEY = "b1f4c9d6a7e2f3b8c0d5e6f7a1b2c3d4"
HMAC_SECRET = "f3a9b2c7d8e1f4a6b0c5d2e8f7a3b1c9d6e4f2a7b8c1d0e5f3a9b2c7d8e1f4a6"
CSRF_MASTER_KEY = "d4b2c7f3e1a6b8c0d5f2a9e7c1b3d4f6"

# =================== الموقع الأصلي ====================
TARGET_BASE_URL = "http://fi10.bot-hosting.net:20160"

# =================== حماية HMAC + API KEY ====================
def verify_hmac(body):
    signature = request.headers.get("X-Signature")
    if not signature:
        return False
    expected = hmac.new(HMAC_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)

def api_protected():
    key = request.headers.get("X-API-KEY")
    if not key or key != API_MASTER_KEY:
        return False
    if not verify_hmac(request.get_data()):
        return False
    return True

# =================== CSRF ====================
def generate_csrf():
    token = secrets.token_hex(16)
    session["csrf_token"] = token
    return token

def check_csrf():
    token_header = request.headers.get("X-CSRF-Token")
    if not token_header or token_header != session.get("csrf_token"):
        return False
    return True

# =================== proxy route ====================
@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
def proxy(path):
    # تحقق HMAC + API Key
    if not api_protected():
        return jsonify({"error": "Forbidden"}), 403

    # تحقق CSRF لكل POST/PUT/DELETE
    if request.method in ["POST", "PUT", "DELETE"]:
        if not check_csrf():
            return jsonify({"error": "CSRF verification failed"}), 403

    # تحويل "/" تلقائياً إلى "/login"
    if path == "":
        path = "login"

    url = f"{TARGET_BASE_URL}/{path}"

    try:
        # نسخ جميع الهيدرز ما عدا Host
        headers = {key: value for key, value in request.headers if key.lower() != "host"}
        data = request.get_data()
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=data,
            params=request.args,
            timeout=15
        )
        return (resp.content, resp.status_code, resp.headers.items())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =================== توليد CSRF عند GET على /login ====================
@app.route("/csrf-token", methods=["GET"])
def get_csrf_token():
    token = generate_csrf()
    return jsonify({"csrf_token": token})

# =================== تشغيل ====================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
