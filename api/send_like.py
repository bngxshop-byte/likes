from flask import Flask, request, Response
import requests
import re

app = Flask(__name__)

TARGET_URL = "http://fi10.bot-hosting.net:20160"  # الموقع الأصلي
MY_DOMAIN = "https://panel-bngx.vercel.app"       # دومينك على Vercel

def rewrite_links(content):
    # استبدال كل روابط الموقع الأصلي بدوميننا
    content = re.sub(r'http://fi10\.bot-hosting\.net:20160', MY_DOMAIN, content.decode('utf-8'))
    return content.encode('utf-8')

@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])
@app.route('/<path:path>', methods=["GET", "POST"])
def proxy(path):
    url = f"{TARGET_URL}/{path}"
    
    try:
        if request.method == "POST":
            resp = requests.post(url, data=request.form, headers=request.headers, allow_redirects=False)
        else:
            resp = requests.get(url, params=request.args, headers=request.headers, allow_redirects=False)
    except Exception as e:
        return f"Error connecting to target site: {e}", 500
    
    content = resp.content
    content_type = resp.headers.get('Content-Type', 'text/html')

    # إذا كانت الصفحة HTML، نقوم بإعادة كتابة الروابط
    if "text/html" in content_type:
        content = rewrite_links(content)

    return Response(content, status=resp.status_code, content_type=content_type)

if __name__ == "__main__":
    app.run(debug=True)
