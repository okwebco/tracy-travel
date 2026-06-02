"""Proveedor de demostración: datos deterministas para MODO DEMO y tests.

Genera ofertas reproducibles a partir de la consulta (semilla = origen+destino+fecha),
sin llamar a ninguna API externa. Permite ver el flujo completo sin credenciales.
"""
import random
from datetime import date

from app.tracy.providers.base import Proveedor
from app.tracy import catalogo


AEROLINEAS = ["Avianca", "LATAM", "GOL", "Copa", "Wingo"]
HOTELES = ["Hotel Plaza", "Grand Suites", "Comfort Inn", "Boutique Centro",
           "Resort Bahía", "City Lodge", "Hostal del Mar"]


def _semilla(consulta) -> random.Random:
    base = f"{consulta.origen}{consulta.destino}{consulta.fecha_salida or ''}{date.today().isoformat()}"
    return random.Random(base)


def _fecha_str(d) -> str | None:
    return d.isoformat() if d else None


class MockProvider(Proveedor):
    nombre = "mock"
    disponible = True

    async def buscar_vuelos(self, consulta) -> list[dict]:
        moneda = (consulta.moneda or "COP").upper()
        base = 900_000 if moneda == "COP" else 280.0
        rnd = _semilla(consulta)
        # "Solo regreso" no tiene salida: usamos la fecha disponible como tramo.
        salida = _fecha_str(consulta.fecha_salida) or _fecha_str(consulta.fecha_regreso) or "2026-07-15"
        # En ida+vuelta mostramos también el regreso.
        ida_y_vuelta = getattr(consulta, "tipo_viaje", None) == "ida_regreso"
        regreso = _fecha_str(consulta.fecha_regreso) if ida_y_vuelta else None
        ofertas = []
        for _ in range(5):
            factor = 1 + rnd.uniform(-0.25, 0.7)
            ofertas.append({
                "precio": round(base * factor, 2),
                "moneda": moneda,
                "aerolinea": rnd.choice(AEROLINEAS),
                "fecha_salida": salida,
                "fecha_regreso": regreso,
                "escalas": rnd.choice([0, 0, 1, 2]),
                "link": f"https://www.aviasales.com/search/{consulta.origen}{consulta.destino}",
                "proveedor": self.nombre,
            })
        return ofertas

    async def buscar_hoteles(self, consulta) -> list[dict]:
        moneda = (consulta.moneda or "COP").upper()
        base = 250_000 if moneda == "COP" else 80.0
        rnd = _semilla(consulta)
        ciudad = catalogo.nombre(consulta.destino)
        ofertas = []
        for _ in range(5):
            factor = 1 + rnd.uniform(-0.3, 0.9)
            nombre = rnd.choice(HOTELES)
            ofertas.append({
                "precio": round(base * factor, 2),     # por noche
                "moneda": moneda,
                "nombre": nombre,
                "estrellas": rnd.choice([3, 3, 4, 4, 5]),
                "ciudad": ciudad,
                "link": f"https://search.hotellook.com/?destination={ciudad}",
                "mapa": f"https://www.google.com/maps/search/?api=1&query={nombre.replace(' ', '+')}+{ciudad.replace(' ', '+')}",
                "proveedor": self.nombre,
            })
        return ofertas
