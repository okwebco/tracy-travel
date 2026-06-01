"""API pública de Tracy: precheck de temporada y creación de consultas."""
import secrets
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.tracy import config, catalogo, temporadas
from app.tracy.models import Consulta
from app.tracy.schemas import (
    PrecheckRequest, PrecheckResponse, ConsultaCreate, ConsultaResponse, OPCION1_DIAS,
)

router = APIRouter(prefix="/api/tracy", tags=["tracy"])


@router.post("/precheck", response_model=PrecheckResponse)
async def precheck(req: PrecheckRequest):
    """Evalúa temporada/fiestas para destino + fechas (se muestra antes de confirmar)."""
    if not catalogo.es_destino_valido(req.destino):
        raise HTTPException(status_code=400, detail="Destino no está en el catálogo")
    resultado = temporadas.evaluar(req.destino.upper(), req.fecha_salida, req.fecha_regreso)
    return resultado


@router.post("/consultas", response_model=ConsultaResponse)
async def crear_consulta(req: ConsultaCreate, db: Session = Depends(get_db)):
    # Clave de acceso
    if req.clave != config.LANDING_PASSWORD:
        raise HTTPException(status_code=401, detail="Clave incorrecta")

    # Validar catálogo
    if not catalogo.es_origen_valido(req.origen):
        raise HTTPException(status_code=400, detail="Origen no válido (debe ser un aeropuerto de Colombia)")
    if not catalogo.es_destino_valido(req.destino):
        raise HTTPException(status_code=400, detail="Destino no está en el catálogo")

    # Reglas por modo
    if req.modo == "opcion1":
        if req.opcion1_dia not in OPCION1_DIAS:
            raise HTTPException(status_code=400, detail=f"opcion1_dia debe estar en {sorted(OPCION1_DIAS)}")
        ejecuciones_totales = 1
    else:  # opcion2
        if not req.opcion2_dias or not (1 <= req.opcion2_dias <= 8):
            raise HTTPException(status_code=400, detail="opcion2_dias debe estar entre 1 y 8")
        ejecuciones_totales = req.opcion2_dias

    # Hospedaje requiere noches si macro incluye hotel
    if req.macro in ("hospedaje", "ambos") and not req.noches:
        raise HTTPException(status_code=400, detail="Indica el número de noches para hospedaje")

    codigo = secrets.token_hex(3).upper()  # 6 chars

    consulta = Consulta(
        whatsapp=req.whatsapp,
        origen=req.origen,
        destino=req.destino,
        macro=req.macro,
        motivo=req.motivo,
        fecha_salida=req.fecha_salida,
        fecha_regreso=req.fecha_regreso,
        flexible=req.flexible,
        noches=req.noches,
        hotel_precio_min=req.hotel_precio_min,
        hotel_precio_max=req.hotel_precio_max,
        moneda=(req.moneda or config.MONEDA_DEFECTO).upper(),
        modo=req.modo,
        opcion1_dia=req.opcion1_dia,
        opcion2_dias=req.opcion2_dias,
        estado="pendiente_optin",
        codigo_optin=codigo,
        ejecuciones_totales=ejecuciones_totales,
        ejecuciones_hechas=0,
    )
    db.add(consulta)
    db.commit()
    db.refresh(consulta)

    texto = f"Hola Tracy, activa {codigo}"
    wa_link = f"https://wa.me/{config.WHATSAPP_SENDER}?text={urllib.parse.quote(texto)}"

    return ConsultaResponse(consulta_id=consulta.id, codigo=codigo, wa_link=wa_link)
