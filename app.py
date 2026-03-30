from flask import Flask, request
import requests
from datetime import datetime
import json
import os
import re

app = Flask(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
APPS_SCRIPT_URL = os.environ.get("APPS_SCRIPT_URL")

def interpretar_mensaje(mensaje):
    print(f"GROQ_API_KEY presente: {bool(GROQ_API_KEY)}")
    print(f"Mensaje recibido: {mensaje}")
    
    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama3-8b-8192",
            "messages": [{
                "role": "user",
                "content": f"""Interpret this personal finance message and return ONLY a JSON with these fields:
- descripcion (string)
- monto (number)
- tipo (only "ingreso" or "gasto")
- categoria (one of: Sueldo, Freelance, Vivienda, Alimentacion, Transporte, Salud, Entretenimiento, Educacion, Otros)

Message: {mensaje}

Return ONLY the JSON, nothing else."""
            }],
            "max_tokens": 200
        }
    )
    print(f"Groq status: {response.status_code}")
    print(f"Groq response: {response.text}")
    
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

        r = requests.post(APPS_SCRIPT_URL, json={
            "fecha": fecha,
            "descripcion": datos["descripcion"],
            "monto": datos["monto"],
            "tipo": datos["tipo"],
            "categoria": datos["categoria"]
        })
        print(f"Apps Script response: {r.status_code} - {r.text}")

        respuesta = f"Registrado: {datos['descripcion']} - ${datos['monto']} ({datos['tipo']} en {datos['categoria']})"
    except Exception as e:
        print(f"ERROR COMPLETO: {str(e)}")
        respuesta = f"Error: {str(e)}"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{respuesta}</Message></Response>"""

@app.route("/")
def index():
    return "Bot de finanzas funcionando"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
