"""Proveedor de demostración: datos deterministas para MODO DEMO y tests.

Genera ofertas reproducibles a partir de la consulta (semilla = origen+destino+fecha),
sin llamar a ninguna API externa. Permite ver el flujo completo sin credenciales.
"""
import random
from datetime import date

from app.tracy.providers.base import Proveedor
from app.tracy import catalogo


# Códigos IATA; el nombre legible se deriva con catalogo.nombre_aerolinea.
AEROLINEAS = ["AV", "LA", "G3", "CM", "P5"]


def _semilla(tramo) -> random.Random:
    base = f"{tramo.origen}{tramo.destino}{tramo.fecha_salida or ''}{date.today().isoformat()}"
    return random.Random(base)


def _fecha_str(d) -> str | None:
    return d.isoformat() if d else None


class MockProvider(Proveedor):
    nombre = "mock"
    disponible = True

    async def buscar_vuelos(self, tramo) -> list[dict]:
        # Cada búsqueda es un tramo one-way (origen → destino + fecha).
        moneda = (tramo.moneda or "COP").upper()
        base = 900_000 if moneda == "COP" else 280.0
        rnd = _semilla(tramo)
        salida = _fecha_str(tramo.fecha_salida) or "2026-07-15"
        ofertas = []
        for _ in range(5):
            factor = 1 + rnd.uniform(-0.25, 0.7)
            ofertas.append({
                "precio": round(base * factor, 2),
                "moneda": moneda,
                "aerolinea": catalogo.nombre_aerolinea(rnd.choice(AEROLINEAS)),
                "fecha_salida": salida,
                "fecha_regreso": None,
                "escalas": rnd.choice([0, 0, 1, 2]),
                "link": f"https://www.aviasales.com/search/{tramo.origen}{tramo.destino}",
                "proveedor": self.nombre,
            })
        return ofertas
