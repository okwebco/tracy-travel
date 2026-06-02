"""Esquemas Pydantic para la API de Tracy Travel."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator

from app.tracy.modos import (
    MODOS, RASTREO_DIAS, SEGUIMIENTO_CANTIDADES, SEGUIMIENTO_FRECUENCIAS,
)


MACROS = {"vuelo", "hospedaje", "ambos"}
MOTIVOS = {"turismo", "negocios", "familiar", "otros"}
MONEDAS = {"COP", "USD", "EUR"}
TIPOS_VIAJE = {"ida", "regreso", "ida_regreso"}


class AccesoRequest(BaseModel):
    clave: str


class AccesoResponse(BaseModel):
    ok: bool


class PrecheckRequest(BaseModel):
    destino: str
    fecha_salida: Optional[date] = None
    fecha_regreso: Optional[date] = None


class PrecheckResponse(BaseModel):
    temporada: str
    eventos: list[str]
    sube_precio: bool
    mensaje: str


class ConsultaCreate(BaseModel):
    clave: str                       # LANDING_PASSWORD
    nombre: str
    apellido: str
    whatsapp: str
    origen: str
    destino: str
    macro: str
    motivo: str = "turismo"
    tipo_viaje: str = "ida_regreso"
    fecha_salida: Optional[date] = None
    fecha_regreso: Optional[date] = None
    flexible: bool = False
    noches: Optional[int] = None
    hotel_precio_min: Optional[float] = None
    hotel_precio_max: Optional[float] = None
    moneda: str = "COP"
    modo: str
    # Rastreo: lista de días marcados (acumulativos), p. ej. [1,3,5,8].
    rastreo_dias: Optional[list[int]] = None
    # Seguimiento: cantidad de rastreos (2..6) y frecuencia en días.
    seguimiento_cantidad: Optional[int] = None
    seguimiento_frecuencia: Optional[int] = None

    @field_validator("nombre", "apellido")
    @classmethod
    def _nombre_apellido(cls, v: str) -> str:
        v = (v or "").strip()
        if len(v) < 2:
            raise ValueError("Nombre y apellido son obligatorios")
        return v

    @field_validator("whatsapp")
    @classmethod
    def _limpiar_whatsapp(cls, v: str) -> str:
        # Dejar solo dígitos
        digitos = "".join(c for c in (v or "") if c.isdigit())
        if len(digitos) < 10:
            raise ValueError("Número de WhatsApp inválido")
        return digitos

    @field_validator("origen", "destino")
    @classmethod
    def _iata(cls, v: str) -> str:
        return (v or "").strip().upper()

    @field_validator("macro")
    @classmethod
    def _macro(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in MACROS:
            raise ValueError(f"macro debe ser uno de {MACROS}")
        return v

    @field_validator("motivo")
    @classmethod
    def _motivo(cls, v: str) -> str:
        v = (v or "turismo").strip().lower()
        if v not in MOTIVOS:
            raise ValueError(f"motivo debe ser uno de {MOTIVOS}")
        return v

    @field_validator("tipo_viaje")
    @classmethod
    def _tipo_viaje(cls, v: str) -> str:
        v = (v or "ida_regreso").strip().lower()
        if v not in TIPOS_VIAJE:
            raise ValueError(f"tipo_viaje debe ser uno de {TIPOS_VIAJE}")
        return v

    @field_validator("modo")
    @classmethod
    def _modo(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in MODOS:
            raise ValueError(f"modo debe ser uno de {MODOS}")
        return v

    @field_validator("moneda")
    @classmethod
    def _moneda(cls, v: str) -> str:
        v = (v or "COP").strip().upper()
        if v not in MONEDAS:
            raise ValueError(f"moneda debe ser una de {MONEDAS}")
        return v


class ConsultaResponse(BaseModel):
    consulta_id: int
    codigo: str
    wa_link: str
    modo: str
    resumen_entregas: str          # texto legible: "ahora, al día 3, al día 5…"
    entregas_totales: int
