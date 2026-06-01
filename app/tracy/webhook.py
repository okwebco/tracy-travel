"""Webhook entrante de Green API: opt-in (activación por código) y CANCELAR.

Configura la URL de este endpoint en el panel de Green API (ver notas de despliegue).
"""
from datetime import date
import json
import re

from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.tracy.models import Consulta
from app.tracy import services, modos as modos_mod
from app.services.whatsapp import send_whatsapp

router = APIRouter(prefix="/api/webhook", tags=["tracy-webhook"])


def _extraer(payload: dict) -> tuple[str | None, str | None]:
    """Extrae (remitente, texto) del payload de Green API (incomingMessageReceived).

    Tolerante a variaciones del formato; ante dudas devuelve (None, None).
    """
    try:
        sender = payload.get("senderData", {}).get("sender", "")
        # sender suele venir como '573001112233@c.us'
        numero = re.sub(r"\D", "", sender) if sender else None

        md = payload.get("messageData", {}) or {}
        texto = None
        if "textMessageData" in md:
            texto = md["textMessageData"].get("textMessage")
        elif "extendedTextMessageData" in md:
            texto = md["extendedTextMessageData"].get("text")
        return numero, (texto or "").strip()
    except Exception:
        return None, None


def _activar(db: Session, consulta: Consulta) -> None:
    """Activa una consulta tras el opt-in: fija estado, checkpoints y totales.

    La primera entrega es SIEMPRE inmediata (hoy) en los tres modos; el cron
    `revisar` la procesa de inmediato (la llamamos justo después en el webhook).
    """
    hoy = date.today()
    fechas = modos_mod.calcular_checkpoints(
        consulta.modo,
        desde=hoy,
        rastreo_dias=consulta.rastreo_dias,
        seguimiento_cantidad=consulta.seguimiento_cantidad,
        seguimiento_frecuencia=consulta.seguimiento_frecuencia,
    )
    consulta.estado = "activa"
    consulta.ejecuciones_hechas = 0
    consulta.ejecuciones_totales = len(fechas)
    consulta.checkpoints = json.dumps([f.isoformat() for f in fechas])
    consulta.proxima_ejecucion = fechas[0]  # hoy = entrega inmediata #1


@router.post("/whatsapp")
async def webhook_whatsapp(request: Request):
    try:
        payload = await request.json()
    except Exception:
        return {"ok": True}  # nunca crashear ante payloads raros

    numero, texto = _extraer(payload)
    if not numero or not texto:
        return {"ok": True, "ignorado": True}

    db = SessionLocal()
    try:
        texto_upper = texto.upper()

        # CANCELAR: detiene todas las consultas activas del número
        if "CANCELAR" in texto_upper:
            activas = db.query(Consulta).filter(
                Consulta.whatsapp == numero,
                Consulta.estado == "activa",
            ).all()
            for c in activas:
                c.estado = "cancelada"
            db.commit()
            await send_whatsapp(numero, "🛑 Listo, detuve tu(s) rastreo(s). Escríbeme cuando quieras volver a buscar.")
            return {"ok": True, "canceladas": len(activas)}

        # Opt-in por código: buscar código en el texto
        consulta = None
        for token in re.findall(r"[A-Za-z0-9]{4,12}", texto_upper):
            c = db.query(Consulta).filter(
                Consulta.codigo_optin == token,
                Consulta.estado == "pendiente_optin",
            ).first()
            if c:
                consulta = c
                break

        if consulta:
            _activar(db, consulta)
            db.commit()
            await send_whatsapp(numero, services.mensaje_bienvenida(consulta))

            # Resultado inmediato (#1) en los tres modos: busca, genera el
            # reporte y lo envía YA. Luego siguen los checkpoints programados.
            from app.tracy import cron
            await cron.procesar_consulta(db, consulta)
            await cron.notificar(db)

            return {"ok": True, "activada": consulta.id}

        return {"ok": True, "sin_coincidencia": True}
    finally:
        db.close()
