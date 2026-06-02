"""Esquemas Pydantic para la API de Tracy Travel."""
from datetime import date
from typing import Optional
from pydantic import BaseModel, field_validator, model_validator

from app.tracy.modos import (
    MODOS, RASTREO_DIAS, SEGUIMIENTO_CANTIDADES, SEGUIMIENTO_FRECUENCIAS,
)


MOTIVOS = {"turismo", "negocios", "familiar", "otros"}
MONEDAS = {"COP", "USD", "EUR"}


class AccesoRequest(BaseModel):
    clave: str


class AccesoResponse(BaseModel):
    ok: bool


class PrecheckRequest(BaseModel):
    destino: str
    fecha_salida: Optional[date] = None


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
    # Tramo IDA (siempre)
    origen: str
    destino: str
    fecha_salida: Optional[date] = None
    motivo: str = "turismo"
    # Tramo VUELTA (opcional, independiente — open-jaw permitido)
    origen_vuelta: Optional[str] = None
    destino_vuelta: Optional[str] = None
    fecha_vuelta: Optional[date] = None
    flexible: bool = False
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

    @field_validator("origen_vuelta", "destino_vuelta")
    @classmethod
    def _iata_vuelta(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip().upper()
        return v or None

    @field_validator("motivo")
    @classmethod
    def _motivo(cls, v: str) -> str:
        v = (v or "turismo").strip().lower()
        if v not in MOTIVOS:
            raise ValueError(f"motivo debe ser uno de {MOTIVOS}")
        return v

    @model_validator(mode="after")
    def _validar_vuelta(self):
        # Si viene CUALQUIER campo de vuelta, deben venir los tres.
        campos = [self.origen_vuelta, self.destino_vuelta, self.fecha_vuelta]
        if any(c is not None for c in campos):
            if not all(c is not None for c in campos):
                raise ValueError(
                    "Para el tramo de vuelta se requieren origen_vuelta, "
                    "destino_vuelta y fecha_vuelta"
                )
            if self.origen_vuelta == self.destino_vuelta:
                raise ValueError("origen_vuelta y destino_vuelta no pueden ser iguales")
        return self

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
