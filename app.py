from flask import Flask, request
import anthropic
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import json
import os

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID")

def interpretar_mensaje(mensaje):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": f"""Interpretá este mensaje de finanzas personales y devolvé SOLO un JSON con estos campos:
- descripcion (string)
- monto (número sin simbolos)
- tipo (solo "ingreso" o "gasto")
- categoria (una de estas: Sueldo, Freelance, Otros ingresos, Vivienda, Alimentación, Transporte, Salud, Entretenimiento, Educación, Otros gastos)

Mensaje: {mensaje}

Respondé SOLO con el JSON, sin explicaciones."""
        }]
    )
    texto = response.content[0].text.strip()
    return json.loads(texto)

@app.route("/webhook", methods=["POST"])
def webhook():
    mensaje = request.form.get("Body", "")
    numero = request.form.get("From", "")
    
    try:
        datos = interpretar_mensaje(mensaje)
        fecha = datetime.now().strftime("%Y-%m-%d")
        
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds_json = json.loads(os.environ.get("GOOGLE_CREDENTIALS"))
        creds = Credentials.from_service_account_info(creds_json, scopes=scope)
        gc = gspread.authorize(creds)
        sh = gc.open_by_key(SPREADSHEET_ID)
        ws = sh.sheet1
        ws.append_row([fecha, datos["descripcion"], datos["monto"], datos["tipo"], datos["categoria"]])
        
        respuesta = f"✅ Registrado: {datos['descripcion']} - ${datos['monto']} ({datos['tipo']} en {datos['categoria']})"
    except Exception as e:
        respuesta = f"❌ No pude interpretar el mensaje. Intentá con algo como: 'gasté 5000 en el súper'"
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<Response><Message>{respuesta}</Message></Response>"""

@app.route("/")
def index():
    return "Bot de finanzas funcionando ✅"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
