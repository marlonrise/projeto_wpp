from flask import Flask, request, jsonify, render_template
import sqlite3
from datetime import datetime

app = Flask(__name__)

# Cria banco e tabela se não existir
def init_db():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        mensagem TEXT,
        data_hora TEXT
    )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def home():
    return "✅ RPA Z-API online!"

@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.json
    numero = dados.get("phone")
    mensagem = dados.get("message")
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if numero and mensagem:
        conn = sqlite3.connect("dados.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO respostas (numero, mensagem, data_hora) VALUES (?, ?, ?)",
                       (numero, mensagem, data_hora))
        conn.commit()
        conn.close()

        print(f"📥 Mensagem recebida de {numero}: {mensagem}")

    return jsonify({"status": "ok"})

@app.route("/respostas")
def respostas():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute("SELECT numero, mensagem, data_hora FROM respostas ORDER BY id DESC")
    dados = cursor.fetchall()
    conn.close()

    html = "<h2>📨 Respostas recebidas</h2><ul>"
    for numero, msg, dt in dados:
        html += f"<li><b>{numero}</b> às <i>{dt}</i>: {msg}</li>"
    html += "</ul>"
    return html

if __name__ == "__main__":
    app.run(debug=True)
