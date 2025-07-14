import requests
import time
import csv
from datetime import datetime
import os


# CONFIGURAÇÕES Z-API
INSTANCE_ID = "3E426D8FEC09A0BA8B615E3E11E99CA6"
INSTANCE_TOKEN = "C05BB81117DF0B3472BB162D"
CLIENT_TOKEN = "F98beb30ba3b34fbc9a3ce7609296cb48S"
URL_ENVIO = f"https://api.z-api.io/instances/{INSTANCE_ID}/token/{INSTANCE_TOKEN}/send-text"
ENVIO_CSV = "envios.csv"
DESTINATARIOS = ["5541992274941"]

HEADERS = {
    "Client-Token": CLIENT_TOKEN,
    "Content-Type": "application/json"
}

def enviar_mensagens():
    escrever_cabecalho = not os.path.exists(ENVIO_CSV) or os.stat(ENVIO_CSV).st_size == 0

    with open(ENVIO_CSV, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        if escrever_cabecalho:
            writer.writerow(["numero", "mensagem", "status_code", "message_id", "resposta_raw", "data_envio"])

        for numero in DESTINATARIOS:
            for i in range(2):
                mensagem = f"Olá! Esta é a mensagem {i+1} para {numero[-4:]} 🎯"
                payload = {
                    "phone": numero,
                    "message": mensagem,
                    "delayTyping": 2,
                    "delayMessage": 1
                }

                response = requests.post(URL_ENVIO, headers=HEADERS, json=payload)

                message_id = None
                try:
                    if response.status_code == 200:
                        response_json = response.json()
                        message_id = response_json.get("messageId")
                except Exception as e:
                    print(f"❌ Erro ao extrair messageId: {e}")

                writer.writerow([
                    numero,
                    mensagem,
                    response.status_code,
                    message_id,
                    response.text,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])

                print(f"📤 Enviada para {numero}: {response.status_code} | ID: {message_id}")
                time.sleep(30)

if __name__ == "__main__":
    enviar_mensagens()
