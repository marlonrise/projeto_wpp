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

    # Ignorar grupos ou mensagens sem conteúdo útil
    if dados.get("isGroup") or dados.get("type") != "ReceivedCallback":
        return jsonify({"status": "ignorado"})

    numero = dados.get("phone")
    tipo = dados.get("type")
    is_group = dados.get("isGroup", False)
    from_me = dados.get("fromMe", False)
    reference_id = dados.get("referenceMessageId")

    # Extração da mensagem (pode estar em text["message"])
    mensagem_texto = None
    if isinstance(dados.get("text"), dict):
        mensagem_texto = dados["text"].get("message")
    elif isinstance(dados.get("message"), str):
        mensagem_texto = dados.get("message")

    if not mensagem_texto or from_me:
        return jsonify({"status": "ignorado"})

    # Registra no banco
    data_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO respostas (numero, mensagem, data_hora, reference_id) VALUES (?, ?, ?, ?)",
        (numero, mensagem_texto, data_hora, reference_id)
    )
    conn.commit()
    conn.close()

    print(f"✅ Recebido: {numero} | {mensagem_texto} | Ref: {reference_id}")
    return jsonify({"status": "ok"})


@app.route("/respostas")
def respostas():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()

    # Buscar todas as respostas
    cursor.execute("SELECT id, numero, mensagem, data_hora, reference_id FROM respostas ORDER BY id DESC")
    respostas = cursor.fetchall()

    # Criar um dicionário com mensagens por ID
    cursor.execute("SELECT id, reference_id, mensagem, data_hora FROM respostas")
    todas_msgs = cursor.fetchall()
    mapa_id_para_mensagem = {str(ref_id): msg for (_, ref_id, msg, _) in todas_msgs if ref_id}

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

    for id_, numero, mensagem, data_hora, ref_id in respostas:
        ref_id_display = ref_id or "-"
        resposta_referenciada = "-"

        if ref_id and ref_id in mapa_id_para_mensagem:
            resposta_referenciada = mapa_id_para_mensagem[ref_id]
        else:
            # Pegar a mensagem enviada anterior a esta (mesma pessoa)
            cursor.execute("""
                SELECT mensagem FROM respostas 
                WHERE numero = ? AND id < ? AND mensagem LIKE '*MENSAGEM DE TESTE%' 
                ORDER BY id DESC LIMIT 1
            """, (numero, id_))
            row = cursor.fetchone()
            if row:
                resposta_referenciada = row[0]

        html += f"""
            <tr>
                <td>{numero}</td>
                <td>{mensagem}</td>
                <td>{data_hora}</td>
                <td>{ref_id_display}</td>
                <td>{resposta_referenciada}</td>
            </tr>
        """

    html += "</table></body></html>"
    conn.close()
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

@app.route("/respostas_por_referencia/<ref_id>")
def respostas_por_referencia(ref_id):
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute("""
        SELECT numero, mensagem, data_hora 
        FROM respostas 
        WHERE reference_id = ? 
        ORDER BY id DESC
    """, (ref_id,))
    dados = cursor.fetchall()
    conn.close()

    if not dados:
        return f"<h3>❌ Nenhuma resposta encontrada com referência: {ref_id}</h3>"

    html = f"""
    <html>
    <head>
        <title>Respostas por Referência</title>
        <style>
            table {{ width: 90%; margin: 20px auto; border-collapse: collapse; }}
            th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            body {{ font-family: Arial, sans-serif; background: #f9f9f9; }}
            h2 {{ text-align: center; color: #333; }}
        </style>
    </head>
    <body>
        <h2>🔁 Respostas para a mensagem com ID: {ref_id}</h2>
        <table>
            <tr>
                <th>Número</th>
                <th>Mensagem</th>
                <th>Data/Hora</th>
            </tr>
    """
    for numero, msg, dt in dados:
        html += f"""
            <tr>
                <td>{numero}</td>
                <td>{msg}</td>
                <td>{dt}</td>
            </tr>
        """
    html += "</table></body></html>"
    return html


if __name__ == "__main__":
    app.run(debug=True)
