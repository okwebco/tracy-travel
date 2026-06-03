"""Proveedor de vuelos Travelpayouts / Aviasales.

Reutiliza la lógica del adaptador del experimento previo (app/services/vuelos.py),
adaptada al modelo Consulta de Tracy. Solo APIs oficiales, cero scraping.
"""
import httpx

from app.tracy.providers.base import Proveedor
from app.tracy import config, catalogo

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

    async def buscar_vuelos(self, tramo) -> list[dict]:
        if not self.disponible:
            return []
        # Cada búsqueda es un tramo one-way (origen → destino + fecha).
        params = {
            "origin": tramo.origen.upper(),
            "destination": tramo.destino.upper(),
            "currency": (tramo.moneda or "cop").lower(),
            "one_way": "true",
            "sorting": "price",
            "limit": 10,
            "token": config.TRAVELPAYOUTS_TOKEN,
        }
        # 1er intento: mes pedido. Si la API (solo precios cacheados) no tiene
        # datos para ese mes, 2do intento sin filtro de fecha (cualquier fecha
        # cacheada de la ruta). Amplía cobertura en rutas poco transitadas.
        fecha_tramo = tramo.fecha_salida
        ofertas: list[dict] = []
        if fecha_tramo:
            ofertas = await self._consultar({**params, "departure_at": fecha_tramo.strftime("%Y-%m")}, tramo)
        if not ofertas:
            ofertas = await self._consultar(params, tramo)
        return ofertas

    async def _consultar(self, params: dict, tramo) -> list[dict]:
        """Una llamada a la API; devuelve ofertas normalizadas (o vacío)."""
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}) as client:
                r = await client.get(API_URL, params=params)
                data = r.json()
        except Exception as e:
            print(f"[Tracy/Travelpayouts] Error ({tramo.origen}->{tramo.destino}): {e}")
            return []

        if not data.get("success"):
            print(f"[Tracy/Travelpayouts] Respuesta sin éxito: {data}")
            return []

        moneda = (tramo.moneda or "COP").upper()
        ofertas = []
        for item in data.get("data", []):
            if not item.get("price"):
                continue
            ofertas.append({
                "precio": float(item["price"]),
                "moneda": moneda,
                "aerolinea": catalogo.nombre_aerolinea(item.get("airline")),
                "fecha_salida": item.get("departure_at"),
                "fecha_regreso": item.get("return_at"),
                "escalas": item.get("transfers"),
                "link": _build_link(item.get("link")),
                "proveedor": self.nombre,
            })
        return ofertas
