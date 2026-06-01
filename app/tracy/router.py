"""API pública de Tracy: precheck de temporada y creación de consultas."""
import secrets
import urllib.parse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.tracy import config, catalogo, temporadas, modos as modos_mod
from app.tracy.models import Consulta
from app.tracy.schemas import (
    PrecheckRequest, PrecheckResponse, ConsultaCreate, ConsultaResponse,
    AccesoRequest, AccesoResponse,
)

router = APIRouter(prefix="/api/tracy", tags=["tracy"])


@router.post("/acceso", response_model=AccesoResponse)
async def acceso(req: AccesoRequest):
    """Valida la clave de acceso a la landing ANTES de mostrar el formulario.

    Compara contra LANDING_PASSWORD; rechaza cualquier otra cosa.
    """
    if (req.clave or "") != config.LANDING_PASSWORD:
        raise HTTPException(status_code=401, detail="Clave incorrecta")
    return AccesoResponse(ok=True)


@router.get("/catalogo")
async def obtener_catalogo():
    """Catálogo agrupado país → aeropuertos para los selectores dependientes.

    Origen = Colombia (sus aeropuertos). Destino = país → aeropuertos.
    """
    return {
        "origenes": catalogo.origenes_por_pais(),
        "destinos": catalogo.destinos_por_pais(),
    }


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

    # Reglas por modo (ADENDA v2)
    rastreo_dias_csv = None
    seguimiento_cantidad = None
    seguimiento_frecuencia = None

    if req.modo == "rapida":
        ejecuciones_totales = 1

    elif req.modo == "rastreo":
        marcados = modos_mod.normalizar_rastreo_dias(req.rastreo_dias or [])
        if not marcados:
            raise HTTPException(
                status_code=400,
                detail=f"Marca al menos un día de rastreo {modos_mod.RASTREO_DIAS}",
            )
        rastreo_dias_csv = ",".join(str(d) for d in marcados)
        ejecuciones_totales = len(marcados)

    else:  # seguimiento
        if req.seguimiento_cantidad not in modos_mod.SEGUIMIENTO_CANTIDADES:
            raise HTTPException(
                status_code=400,
                detail=f"seguimiento_cantidad debe estar en {sorted(modos_mod.SEGUIMIENTO_CANTIDADES)}",
            )
        if req.seguimiento_frecuencia not in modos_mod.SEGUIMIENTO_FRECUENCIAS:
            raise HTTPException(
                status_code=400,
                detail=f"seguimiento_frecuencia debe estar en {sorted(modos_mod.SEGUIMIENTO_FRECUENCIAS)}",
            )
        seguimiento_cantidad = req.seguimiento_cantidad
        seguimiento_frecuencia = req.seguimiento_frecuencia
        ejecuciones_totales = seguimiento_cantidad

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
        rastreo_dias=rastreo_dias_csv,
        seguimiento_cantidad=seguimiento_cantidad,
        seguimiento_frecuencia=seguimiento_frecuencia,
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

    return ConsultaResponse(
        consulta_id=consulta.id,
        codigo=codigo,
        wa_link=wa_link,
        modo=consulta.modo,
        resumen_entregas=modos_mod.resumen_entregas(consulta),
        entregas_totales=ejecuciones_totales,
    )
