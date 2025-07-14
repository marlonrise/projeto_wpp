from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)

# Inicializa o banco
def init_db():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()

    # Cria a tabela se não existir
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT,
        mensagem TEXT,
        data_hora TEXT
    )
    """)

    # Adiciona coluna reference_id se ainda não existir
    cursor.execute("PRAGMA table_info(respostas)")
    colunas = [col[1] for col in cursor.fetchall()]
    if "reference_id" not in colunas:
        cursor.execute("ALTER TABLE respostas ADD COLUMN reference_id TEXT")

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
    cursor.execute("SELECT numero, mensagem, data_hora, reference_id FROM respostas ORDER BY id DESC")
    dados = cursor.fetchall()
    conn.close()

    html = """
    <html>
    <head>
        <title>Respostas Recebidas</title>
        <style>
            table { width: 90%; margin: 20px auto; border-collapse: collapse; }
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
                <th>Referência (ID da Mensagem)</th>
            </tr>
    """
    for numero, msg, dt, ref_id in dados:
        html += f"""
            <tr>
                <td>{numero}</td>
                <td>{msg}</td>
                <td>{dt}</td>
                <td>{ref_id or '-'}</td>
            </tr>
        """
    html += "</table></body></html>"
    return html

@app.route("/debug")
def debug():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM respostas")
    todos = cursor.fetchall()
    conn.close()
    return jsonify(todos)

@app.route("/verificar_banco")
def verificar_banco():
    existe = os.path.exists("dados.db")
    return f"Banco existe? {'✅ Sim' if existe else '❌ Não'}"

@app.route("/tabela_completa")
def tabela_completa():
    conn = sqlite3.connect("dados.db")
    cursor = conn.cursor()

    # Mostrar colunas
    cursor.execute("PRAGMA table_info(respostas)")
    colunas = cursor.fetchall()

    # Mostrar dados
    cursor.execute("SELECT * FROM respostas ORDER BY id DESC")
    dados = cursor.fetchall()
    conn.close()

    html = """
    <html>
    <head>
        <title>Tabela Completa</title>
        <style>
            table { width: 95%; margin: 20px auto; border-collapse: collapse; font-family: sans-serif; }
            th, td { border: 1px solid #aaa; padding: 6px; text-align: left; }
            th { background-color: #ddd; }
            h2 { text-align: center; }
        </style>
    </head>
    <body>
        <h2>📊 Estrutura da Tabela `respostas`</h2>
        <table>
            <tr><th>ID</th><th>Nome da Coluna</th><th>Tipo</th></tr>
    """
    for col in colunas:
        html += f"<tr><td>{col[0]}</td><td>{col[1]}</td><td>{col[2]}</td></tr>"
    html += "</table><h2>📋 Dados</h2><table><tr>"

    if colunas:
        for col in colunas:
            html += f"<th>{col[1]}</th>"
        html += "</tr>"
        for linha in dados:
            html += "<tr>" + "".join(f"<td>{valor}</td>" for valor in linha) + "</tr>"
    else:
        html += "<tr><td colspan='5'>Tabela vazia</td></tr>"

    html += "</table></body></html>"
    return html

if __name__ == "__main__":
    app.run(debug=True)
