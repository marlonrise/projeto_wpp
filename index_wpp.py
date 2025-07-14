import requests
import time
import csv
from datetime import datetime

# CONFIGURAÇÕES Z-API
INSTANCE_ID = "3E426D8FEC09A0BA8B615E3E11E99CA6"
INSTANCE_TOKEN = "C05BB81117DF0B3472BB162D"
CLIENT_TOKEN = "F98beb30ba3b34fbc9a3ce7609296cb48S"
URL_ENVIO = f"https://api.z-api.io/instances/{INSTANCE_ID}/token/{INSTANCE_TOKEN}/send-text"
ENVIO_CSV = "envios.csv"
DESTINATARIOS = [ "5541992274941"]

HEADERS = {
    "Client-Token": CLIENT_TOKEN,
    "Content-Type": "application/json"
}

def enviar_mensagens():
    with open(ENVIO_CSV, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["numero", "mensagem", "status_code", "resposta", "data_envio"])

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

                writer.writerow([
                    numero,
                    mensagem,
                    response.status_code,
                    response.text,
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ])

                print(f"📤 Enviada para {numero}: {response.status_code}")
                time.sleep(30)

if __name__ == "__main__":
    enviar_mensagens()
