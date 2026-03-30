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
                "content": f"""Interpretá este mensaje de finanzas personales y devolvé SOLO un JSON con estos campos:
- descripcion (string)
- monto (número sin simbolos)
- tipo (solo "ingreso" o "gasto")
- categoria (una de estas: Sueldo, Freelance, Otros ingresos, Vivienda, Alimentacion, Transporte, Salud, Entretenimiento, Educacion, Otros gastos)

Mensaje: {mensaje}

IMPORTANTE: Respondé ÚNICAMENTE con el JSON, sin texto antes ni después, sin comillas, sin markdown."""
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

    try:
        datos = interpretar_mensaje(mensaje)
        fecha = datetime.now().strftime("%Y-%m-%d")

        requests.post(APPS_SCRIPT_URL, json={
            "fecha": fecha,
            "descripcion": datos["descripcion"],
            "monto": datos["monto"],
            "tipo": datos["tipo"],
            "categoria": datos["categoria"]
        })

        respuesta = f"Registrado: {datos['descripcion']} - ${datos['monto']} ({datos['tipo']} en {datos['categoria']})"
    except Exception as e:
        respuesta = f"Error: {str(e)}"

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{respuesta}</Message></Response>"""

@app.route("/")
def index():
    return "Bot de finanzas funcionando"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
