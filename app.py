from flask import Flask, request
import requests
from datetime import datetime
import json
import os
import re
import uuid

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
SHEETDB_URL = os.environ.get("SHEETDB_URL")

def interpretar_mensaje(mensaje):
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{
                "role": "user",
                "content": f"""Interpret this personal finance message and return ONLY a JSON with these fields:
- descripcion (string)
- monto (number)
- tipo (only "ingreso" or "gasto")
- categoria (one of: Sueldo, Freelance, Vivienda, Alimentacion, Transporte, Salud, Entretenimiento, Educacion, Ropa, Cuba, Otros)

Message: {mensaje}

Return ONLY the JSON, nothing else."""
            }],
            "max_tokens": 200
        }
    )
    texto = response.json()["choices"][0]["message"]["content"].strip()
    match = re.search(r'\{.*\}', texto, re.DOTALL)
    if match:
        texto = match.group(0)
    return json.loads(texto)

@app.route("/webhook", methods=["POST"])
def webhook():
    mensaje = request.form.get("Body", "")
    print(f"Webhook recibido: {mensaje}")

    try:
        datos = interpretar_mensaje(mensaje)
        fecha = datetime.now().strftime("%Y-%m-%d")
        id_unico = str(uuid.uuid4())[:8]

        r = requests.post(
            SHEETDB_URL,
            json={"data": [{
                "fecha": fecha,
                "descripcion": datos["descripcion"],
                "monto": datos["monto"],
                "tipo": datos["tipo"],
                "categoria": datos["categoria"],
                "id": id_unico
            }]}
        )
        print(f"SheetDB response: {r.status_code} - {r.text}")

        respuesta = f"✅ Registrado: {datos['descripcion']} - ${datos['monto']} ({datos['tipo']} en {datos['categoria']})"
    except Exception as e:
        print(f"ERROR: {str(e)}")
        respuesta = f"Error: {str(e)}"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{respuesta}</Message></Response>"""

@app.route("/")
def index():
    return "Bot de finanzas funcionando"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
