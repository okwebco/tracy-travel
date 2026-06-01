"""Proveedor de vuelos Travelpayouts / Aviasales.

Reutiliza la lógica del adaptador del experimento previo (app/services/vuelos.py),
adaptada al modelo Consulta de Tracy. Solo APIs oficiales, cero scraping.
"""
import httpx

from app.tracy.providers.base import Proveedor
from app.tracy import config

AVIASALES_BASE = "https://www.aviasales.com"
API_URL = "https://api.travelpayouts.com/aviasales/v3/prices_for_dates"


def _build_link(path: str | None) -> str | None:
    if not path:
        return None
    url = path if path.startswith("http") else AVIASALES_BASE + path
    if config.TRAVELPAYOUTS_MARKER and "marker=" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}marker={config.TRAVELPAYOUTS_MARKER}"
    return url


class TravelpayoutsProvider(Proveedor):
    nombre = "travelpayouts"

    @property
    def disponible(self) -> bool:
        return bool(config.TRAVELPAYOUTS_TOKEN)

    async def buscar_vuelos(self, consulta) -> list[dict]:
        if not self.disponible:
            return []
        params = {
            "origin": consulta.origen.upper(),
            "destination": consulta.destino.upper(),
            "currency": (consulta.moneda or "cop").lower(),
            "one_way": "false" if consulta.fecha_regreso else "true",
            "sorting": "price",
            "limit": 10,
            "token": config.TRAVELPAYOUTS_TOKEN,
        }
        if consulta.fecha_salida:
            params["departure_at"] = consulta.fecha_salida.strftime("%Y-%m")

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(API_URL, params=params)
                data = r.json()
        except Exception as e:
            print(f"[Tracy/Travelpayouts] Error ({consulta.origen}->{consulta.destino}): {e}")
            return []

        if not data.get("success"):
            print(f"[Tracy/Travelpayouts] Respuesta sin éxito: {data}")
            return []

        moneda = (consulta.moneda or "COP").upper()
        ofertas = []
        for item in data.get("data", []):
            if not item.get("price"):
                continue
            ofertas.append({
                "precio": float(item["price"]),
                "moneda": moneda,
                "aerolinea": item.get("airline"),
                "fecha_salida": item.get("departure_at"),
                "fecha_regreso": item.get("return_at"),
                "escalas": item.get("transfers"),
                "link": _build_link(item.get("link")),
                "proveedor": self.nombre,
            })
        return ofertas
