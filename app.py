from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "RPA Z-API online!"

@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.json
    print("📥 Webhook recebido:", dados)
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)
