"""Crons internos de Tracy: revisar, notificar, purga.

Protegidos por header X-Cron-Token == CRON_TOKEN. Las mismas funciones se usan
desde el scheduler local (APScheduler) y desde Cloud Scheduler en producción.
"""
import json
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from fastapi import Depends
from app.tracy import config, services
from app.tracy.models import Consulta, Reporte
from app.tracy.providers import aggregator
from app.services.whatsapp import send_whatsapp

router = APIRouter(prefix="/api/internal/cron", tags=["tracy-cron"])


def _verificar_token(token: str | None):
    if not config.CRON_TOKEN:
        # En MODO DEMO sin token configurado, se permite (degradación elegante).
        return
    if token != config.CRON_TOKEN:
        raise HTTPException(status_code=401, detail="Token de cron inválido")


def _mejor_precio_previo(db: Session, consulta: Consulta) -> float | None:
    """Mínimo precio_referencia visto en reportes previos de la consulta."""
    previos = db.query(Reporte).filter(Reporte.consulta_id == consulta.id).all()
    precios = []
    for r in previos:
        try:
            p = json.loads(r.payload_json).get("precio_referencia")
            if p is not None:
                precios.append(p)
        except Exception:
            pass
    return min(precios) if precios else None


def _siguiente_checkpoint(consulta: Consulta) -> date | None:
    """Devuelve la fecha del próximo checkpoint pendiente según los hechos.

    Lee la lista `checkpoints` (CSV ISO) y toma la entrada en el índice
    `ejecuciones_hechas`. Si no hay lista (consulta antigua) cae al modelo
    legado (+1 día). Devuelve None si ya no quedan checkpoints.
    """
    if consulta.checkpoints:
        try:
            fechas = [date.fromisoformat(x) for x in json.loads(consulta.checkpoints)]
        except Exception:
            fechas = []
        idx = consulta.ejecuciones_hechas or 0
        if idx < len(fechas):
            return fechas[idx]
        return None
    return None


async def _generar_reporte(db: Session, c: Consulta) -> None:
    """Ejecuta el aggregator para una consulta y crea su Reporte (no envía).

    `aggregator.buscar_vuelos` devuelve un dict por tramos:
    {"vuelos_ida": [...], "vuelos_vuelta": [...] | None}.
    """
    resultado = await aggregator.buscar_vuelos(c)

    mejor_previo = _mejor_precio_previo(db, c)
    payload = services.construir_payload(c, resultado, mejor_previo)

    reporte = Reporte(
        consulta_id=c.id,
        numero=c.whatsapp,
        payload_json=json.dumps(payload, ensure_ascii=False),
        enviado=False,
        expires_at=datetime.utcnow() + timedelta(hours=config.REPORTE_TTL_HORAS),
    )
    db.add(reporte)

    c.ejecuciones_hechas = (c.ejecuciones_hechas or 0) + 1
    if c.ejecuciones_hechas >= c.ejecuciones_totales:
        c.estado = "finalizada"
        c.proxima_ejecucion = None
    else:
        # Programar el siguiente checkpoint real (offsets no uniformes en rastreo).
        siguiente = _siguiente_checkpoint(c)
        c.proxima_ejecucion = siguiente or (date.today() + timedelta(days=1))


async def procesar_consulta(db: Session, c: Consulta) -> None:
    """Genera el reporte del checkpoint actual de UNA consulta y persiste.

    Se usa en la entrega inmediata #1 tras el opt-in.
    """
    await _generar_reporte(db, c)
    db.commit()


async def revisar(db: Session) -> int:
    """Genera reportes para las consultas activas cuyo checkpoint cae hoy o antes."""
    hoy = date.today()
    consultas = db.query(Consulta).filter(
        Consulta.estado == "activa",
        Consulta.proxima_ejecucion != None,  # noqa: E711
        Consulta.proxima_ejecucion <= hoy,
    ).all()

    generados = 0
    for c in consultas:
        await _generar_reporte(db, c)
        generados += 1

    db.commit()
    return generados


async def notificar(db: Session) -> int:
    """Envía por WhatsApp los reportes no enviados aún; marca enviado=True."""
    reportes = db.query(Reporte).filter(
        Reporte.enviado == False,  # noqa: E712
    ).all()

    enviados = 0
    for r in reportes:
        try:
            payload = json.loads(r.payload_json)
        except Exception:
            payload = {}
        consulta = db.query(Consulta).filter(Consulta.id == r.consulta_id).first()
        cierre = bool(consulta and consulta.estado == "finalizada")
        mejor_visto = _mejor_precio_previo(db, consulta) if consulta else None
        mensaje = services.mensaje_whatsapp_resumen(payload, r.numero, cierre=cierre,
                                                    mejor_precio_visto=mejor_visto)
        resultado = await send_whatsapp(r.numero, mensaje)
        if resultado.get("error"):
            print(f"[Tracy/Cron] WhatsApp no enviado a {r.numero} (modo demo o error). Mensaje:\n{mensaje}")
        r.enviado = True
        enviados += 1

    db.commit()
    return enviados


def purga(db: Session) -> int:
    """Borra reportes expirados (expires_at < ahora)."""
    ahora = datetime.utcnow()
    expirados = db.query(Reporte).filter(Reporte.expires_at < ahora).all()
    n = len(expirados)
    for r in expirados:
        db.delete(r)
    db.commit()
    return n


# --- Endpoints HTTP ---

@router.post("/revisar")
async def endpoint_revisar(x_cron_token: str | None = Header(None), db: Session = Depends(get_db)):
    _verificar_token(x_cron_token)
    n = await revisar(db)
    return {"reportes_generados": n}


@router.post("/notificar")
async def endpoint_notificar(x_cron_token: str | None = Header(None), db: Session = Depends(get_db)):
    _verificar_token(x_cron_token)
    n = await notificar(db)
    return {"notificaciones_enviadas": n}


@router.post("/purga")
async def endpoint_purga(x_cron_token: str | None = Header(None), db: Session = Depends(get_db)):
    _verificar_token(x_cron_token)
    n = purga(db)
    return {"reportes_purgados": n}


# --- Envoltorios para el scheduler local (manejan su propia sesión) ---

async def job_revisar():
    db = SessionLocal()
    try:
        n = await revisar(db)
        if n:
            print(f"[Tracy/Scheduler] {n} reporte(s) generado(s)")
    finally:
        db.close()


async def job_notificar():
    db = SessionLocal()
    try:
        n = await notificar(db)
        if n:
            print(f"[Tracy/Scheduler] {n} notificación(es) enviada(s)")
    finally:
        db.close()


def job_purga():
    db = SessionLocal()
    try:
        n = purga(db)
        if n:
            print(f"[Tracy/Scheduler] {n} reporte(s) purgado(s)")
    finally:
        db.close()
