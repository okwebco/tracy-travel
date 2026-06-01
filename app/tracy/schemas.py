"""Esquemas Pydantic para la API de Tracy Travel."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator


MACROS = {"vuelo", "hospedaje", "ambos"}
MOTIVOS = {"turismo", "negocios", "familiar", "otros"}
MODOS = {"opcion1", "opcion2"}
OPCION1_DIAS = {1, 3, 5, 8, 15, 30}


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
    whatsapp: str
    origen: str
    destino: str
    macro: str
    motivo: str = "turismo"
    fecha_salida: Optional[date] = None
    fecha_regreso: Optional[date] = None
    flexible: bool = False
    noches: Optional[int] = None
    hotel_precio_min: Optional[float] = None
    hotel_precio_max: Optional[float] = None
    moneda: str = "COP"
    modo: str
    opcion1_dia: Optional[int] = None
    opcion2_dias: Optional[int] = None

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

    @field_validator("modo")
    @classmethod
    def _modo(cls, v: str) -> str:
        v = (v or "").strip().lower()
        if v not in MODOS:
            raise ValueError(f"modo debe ser uno de {MODOS}")
        return v


class ConsultaResponse(BaseModel):
    consulta_id: int
    codigo: str
    wa_link: str
