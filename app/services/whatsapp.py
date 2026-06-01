"""Envío de mensajes de WhatsApp vía Green API.

Tracy usa únicamente `send_whatsapp`. Si Green API no está configurado
(MODO DEMO), no falla: devuelve un dict con `error` y registra en consola.
"""
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

INSTANCE_ID = os.getenv("GREEN_API_INSTANCE_ID", "").strip()
API_TOKEN = os.getenv("GREEN_API_TOKEN", "").strip()


async def send_whatsapp(phone: str, message: str) -> dict:
    if not INSTANCE_ID or not API_TOKEN:
        print("[WhatsApp] Green API no configurado — revisa .env")
        return {"error": "Green API no configurado"}

    url = f"https://api.green-api.com/waInstance{INSTANCE_ID}/sendMessage/{API_TOKEN}"
    payload = {"chatId": f"{phone}@c.us", "message": message}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(url, json=payload)
            return r.json()
    except Exception as e:
        print(f"[WhatsApp] Error: {e}")
        return {"error": str(e)}
