"""Tracy Travel — aplicación FastAPI autónoma.

Rastreador de precios de vuelos con landing pública, webhook de
WhatsApp (Green API), crons internos y página de reporte server-side.

Funciona en MODO DEMO sin credenciales: los proveedores degradan a datos mock.
"""
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, PlainTextResponse
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv
import json
import os

load_dotenv()

from app.database import engine, Base, get_db

# APP_MODE se mantiene solo por compatibilidad; este repo es siempre Tracy.
APP_MODE = os.getenv("APP_MODE", "tracy").strip().lower()

scheduler = AsyncIOScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Importar modelos de Tracy para que create_all genere sus tablas.
    from app.tracy import models as _tracy_models  # noqa: F401
    Base.metadata.create_all(bind=engine)

    # Registrar y arrancar los jobs de Tracy (revisar / notificar / purga).
    from app.tracy.scheduler import registrar_jobs
    registrar_jobs(scheduler)
    scheduler.start()
    print(f"[Tracy] Aplicación iniciada. APP_MODE={APP_MODE}")

    yield

    scheduler.shutdown()


app = FastAPI(title="Tracy Travel", version="0.1.0", lifespan=lifespan)

# Routers de Tracy
from app.tracy.router import router as tracy_router
from app.tracy.webhook import router as tracy_webhook
from app.tracy.cron import router as tracy_cron

app.include_router(tracy_router)
app.include_router(tracy_webhook)
app.include_router(tracy_cron)

app.mount("/static", StaticFiles(directory="static"), name="static")


_NO_CACHE = {"Cache-Control": "no-cache, no-store, must-revalidate", "Pragma": "no-cache"}


@app.get("/health")
async def health():
    return {"ok": True, "modo": APP_MODE, "version": "solo-vuelos-7"}


def _landing_tracy() -> HTMLResponse:
    """Sirve la landing de Tracy inyectando los catálogos agrupados por país."""
    from app.tracy import catalogo
    with open("static/tracy/index.html", encoding="utf-8") as f:
        html = f.read()
    origenes = catalogo.origenes_por_pais()
    destinos = catalogo.destinos_por_pais()
    html = html.replace("{{ORIGENES}}", json.dumps(origenes, ensure_ascii=False))
    html = html.replace("{{DESTINOS}}", json.dumps(destinos, ensure_ascii=False))
    return HTMLResponse(html, headers=_NO_CACHE)


from app.tracy.reportes import pagina_reporte


@app.get("/")
async def root():
    return _landing_tracy()


@app.get("/robots.txt")
async def robots():
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


@app.get("/{numero}", response_class=HTMLResponse)
async def reporte(numero: str, db=Depends(get_db)):
    # Página de reporte por número (no choca con /api ni /static, ya montados arriba).
    return pagina_reporte(numero, db)
