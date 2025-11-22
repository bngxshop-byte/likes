from flask import Flask, request, Response
import requests

app = Flask(__name__)

TARGET_URL = "http://fi10.bot-hosting.net:20160/login"   # الرابط الأصلي

@app.route("/login", methods=["GET", "POST"])
def proxy_login():
    try:
        if request.method == "GET":
            # إرسال طلب GET للرابط الأصلي
            r = requests.get(TARGET_URL, timeout=10)
            return Response(r.content, status=r.status_code, content_type=r.headers.get("content-type"))

        elif request.method == "POST":
            # إرسال البيانات بنفس البوست الأصلي
            r = requests.post(TARGET_URL, data=request.form, timeout=10)
            return Response(r.content, status=r.status_code, content_type=r.headers.get("content-type"))

    except Exception as e:
        return {"error": str(e)}, 500


# لكي يعمل على Vercel
def handler(event, context):
    return app(event, context)
