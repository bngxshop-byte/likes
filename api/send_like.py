from flask import Flask, redirect

app = Flask(__name__)

TARGET_LOGIN = "http://fi10.bot-hosting.net:20160/login"

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def redirect_to_login(path):
    return redirect(TARGET_LOGIN)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
