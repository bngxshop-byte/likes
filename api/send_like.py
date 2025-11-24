import os
import hmac
import hashlib
from flask import Flask, request, jsonify, Response
import requests
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# ================= إعدادات الأمان =================
API_MASTER_KEY = os.environ.get("API_MASTER_KEY", "b1f4c9d6a7e2f3b8c0d5e6f7a1b2c3d4")
HMAC_SECRET = os.environ.get("HMAC_SECRET", "f3a9b2c7d8e1f4a6b0c5d2e8f7a3b1c9d6e4f2a7b8c1d0e5f3a9b2c7d8e1f4a6")
CSRF_MASTER_KEY = os.environ.get("CSRF_MASTER_KEY", "d4b2c7f3e1a6b8c0d5f2a9e7c1b3d4f6")

TARGET_BASE_URL = "http://fi10.bot-hosting.net:20160"

# ================= حماية HMAC + API =================
def verify_hmac(body):
    signature = request.headers.get("X-Signature")
    if not signature:
        return False
    expected = hmac.new(HMAC_SECRET.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)

def api_protected(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get("X-API-KEY")
        if not key or key != API_MASTER_KEY:
            return jsonify({"error": "Forbidden"}), 403
        if not verify_hmac(request.get_data()):
            return jsonify({"error": "Invalid HMAC"}), 403
        return f(*args, **kwargs)
    return decorated

# ================= CSRF Protection =================
def generate_csrf():
    import secrets
    return hmac.new(CSRF_MASTER_KEY.encode(), secrets.token_bytes(32), hashlib.sha256).hexdigest()

def check_csrf():
    token_header = request.headers.get("X-CSRF-Token") or request.headers.get("X-CSRF")
    if not token_header:
        return False
    return True

# ================= Proxy Route =================
@app.route("/", defaults={"path": "login"}, methods=["GET", "POST", "PUT", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "DELETE"])
@api_protected
def proxy(path):
    url = f"{TARGET_BASE_URL}/{path}"

    try:
        # تمرير جميع الهيدرز باستثناء host
        headers = {k: v for k, v in request.headers.items() if k.lower() != "host"}
        # تمرير البيانات
        data = request.get_data() or None
        resp = requests.request(
            method=request.method,
            url=url,
            headers=headers,
            data=data,
            params=request.args,
            timeout=15,
            allow_redirects=True
        )
        # إعادة المحتوى مع الهيدرز
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers_resp = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
        return Response(resp.content, resp.status_code, headers_resp)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= Run Server =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
