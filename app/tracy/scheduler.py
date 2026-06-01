"""Registro de jobs de Tracy en APScheduler (entorno local).

En Cloud Run (escala a 0) los crons los dispara Cloud Scheduler vía HTTP;
estos jobs locales son un respaldo para desarrollo / instancias siempre activas.
Zona horaria: America/Bogota.
"""
from app.tracy import cron

ZONA = "America/Bogota"


def registrar_jobs(scheduler):
    """Añade los jobs de Tracy a un AsyncIOScheduler ya creado."""
    scheduler.add_job(cron.job_revisar, "cron", hour=0, minute=30, timezone=ZONA, id="tracy_revisar")
    scheduler.add_job(cron.job_notificar, "cron", hour=2, minute=30, timezone=ZONA, id="tracy_notificar")
    scheduler.add_job(cron.job_purga, "cron", hour=3, minute=0, timezone=ZONA, id="tracy_purga")
    print("[Tracy/Scheduler] Jobs registrados: revisar 00:30, notificar 02:30, purga 03:00 (America/Bogota)")
