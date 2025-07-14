from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os
import json

app = Flask(__name__)

# Inicializa o banco
def init_db():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        mensagem TEXT,
        data_hora TEXT,
        reference_id TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensagens_enviadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        mensagem TEXT,
        message_id TEXT,
        data_envio TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()

# Função para salvar envio
def salvar_envio(numero, mensagem, message_id):
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    data_envio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO mensagens_enviadas (numero, mensagem, message_id, data_envio) VALUES (?, ?, ?, ?)",
        (numero, mensagem, message_id, data_envio)
    )
    conn.commit()
    conn.close()

@app.route("/")
def home():
    return "✅ RPA Z-API online!"

@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.json

    # Salva log bruto
    with open("log.txt", "a", encoding="utf-8") as f:
        f.write(f"{json.dumps(dados, ensure_ascii=False)}\n")

    numero = dados.get("phone")
    mensagem_texto = dados.get("message")
    imagem = dados.get("image")
    legenda = imagem.get("caption") if imagem else None
    imagem_url = imagem.get("imageUrl") if imagem else None
    tipo = dados.get("type")
    is_group = dados.get("isGroup", False)
    reference_id = dados.get("referenceMessageId")

    if is_group or tipo == "sticker":
        return jsonify({"status": "ignorado"})

    if imagem_url:
        mensagem_final = f"[IMG] {imagem_url}\nLegenda: {legenda or '(sem legenda)'}"
    else:
        mensagem_final = mensagem_texto

    if not mensagem_final:
        return jsonify({"status": "ignorado"})

    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO respostas (numero, mensagem, data_hora, reference_id) VALUES (?, ?, ?, ?)",
        (numero, mensagem_final, data_hora, reference_id)
    )
    conn.commit()
    conn.close()

    print(f"✅ Registrado no banco: {numero} | {mensagem_final} | {reference_id}")
    return jsonify({"status": "ok"})

@app.route("/respostas")
def respostas():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.numero, r.mensagem, r.data_hora, r.reference_id, e.mensagem
        FROM respostas r
        LEFT JOIN mensagens_enviadas e ON r.reference_id = e.message_id
        ORDER BY r.id DESC
    """)
    dados = cursor.fetchall()
    conn.close()

    html = """
    <html>
    <head>
        <title>Respostas Recebidas</title>
        <style>
            table { width: 95%; margin: 20px auto; border-collapse: collapse; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            body { font-family: Arial, sans-serif; background: #f9f9f9; }
            h2 { text-align: center; color: #333; }
        </style>
    </head>
    <body>
        <h2>📨 Respostas Recebidas</h2>
        <table>
            <tr>
                <th>Número</th>
                <th>Mensagem</th>
                <th>Data/Hora</th>
                <th>ID Referência</th>
                <th>Mensagem Respondida</th>
            </tr>
    """
    for numero, msg, dt, ref_id, resposta_original in dados:
        html += f"""
            <tr>
                <td>{numero}</td>
                <td>{msg}</td>
                <td>{dt}</td>
                <td>{ref_id or '-'}</td>
                <td>{resposta_original or '-'}</td>
            </tr>
        """
    html += "</table></body></html>"
    return html

@app.route("/log")
def log():
    if os.path.exists("log.txt"):
        with open("log.txt", encoding="utf-8") as f:
            conteudo = f.read()
        return f"<pre>{conteudo}</pre>"
    return "Sem log ainda."

@app.route("/buscar_respostas")
def buscar_respostas():
    numero = request.args.get("numero")
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM respostas WHERE numero LIKE ?", (f"%{numero}%",))
    dados = cursor.fetchall()
    conn.close()
    return jsonify(dados)

if __name__ == "__main__":
    app.run(debug=True)
