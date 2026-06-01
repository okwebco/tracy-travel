"""Proveedor de hoteles Hotellook (Travelpayouts).

Usa el mismo TRAVELPAYOUTS_TOKEN. Endpoints:
  - lookup.json  → resolver el id/location de la ciudad
  - cache.json   → precios cacheados por ciudad y fechas
Cero scraping. Mapa por hotel vía Google Maps.

Nota: los parámetros exactos deben verificarse en la doc de Travelpayouts;
ante cualquier fallo de red/contrato, el proveedor degrada a [] sin crashear.
"""
import httpx

from app.tracy.providers.base import Proveedor
from app.tracy import config, catalogo

LOOKUP_URL = "https://engine.hotellook.com/api/v2/lookup.json"
CACHE_URL = "https://engine.hotellook.com/api/v2/cache.json"


def _mapa(nombre: str, ciudad: str) -> str:
    q = f"{nombre} {ciudad}".replace(" ", "+")
    return f"https://www.google.com/maps/search/?api=1&query={q}"


class HotellookProvider(Proveedor):
    nombre = "hotellook"

    @property
    def disponible(self) -> bool:
        return bool(config.TRAVELPAYOUTS_TOKEN)

    async def buscar_hoteles(self, consulta) -> list[dict]:
        if not self.disponible:
            return []

        ciudad = catalogo.nombre(consulta.destino)
        moneda = (consulta.moneda or "COP").lower()
        check_in = consulta.fecha_salida.isoformat() if consulta.fecha_salida else None
        check_out = consulta.fecha_regreso.isoformat() if consulta.fecha_regreso else None

        params = {
            "location": ciudad,
            "currency": moneda,
            "limit": 10,
            "token": config.TRAVELPAYOUTS_TOKEN,
        }
        if check_in:
            params["checkIn"] = check_in
        if check_out:
            params["checkOut"] = check_out

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                r = await client.get(CACHE_URL, params=params)
                data = r.json()
        except Exception as e:
            print(f"[Tracy/Hotellook] Error ({consulta.destino}): {e}")
            return []

        if not isinstance(data, list):
            print(f"[Tracy/Hotellook] Respuesta inesperada: {data}")
            return []

        ofertas = []
        for item in data:
            precio = item.get("priceFrom") or item.get("priceAvg")
            if not precio:
                continue
            nombre = item.get("hotelName") or "Hotel"
            ofertas.append({
                "precio": float(precio),
                "moneda": (consulta.moneda or "COP").upper(),
                "nombre": nombre,
                "estrellas": item.get("stars"),
                "ciudad": ciudad,
                "link": f"https://search.hotellook.com/?destination={ciudad}",
                "mapa": _mapa(nombre, ciudad),
                "proveedor": self.nombre,
            })

        # Filtro por rango de precio del hotel (por noche)
        mn = consulta.hotel_precio_min
        mx = consulta.hotel_precio_max
        if mn is not None:
            ofertas = [o for o in ofertas if o["precio"] >= mn]
        if mx is not None:
            ofertas = [o for o in ofertas if o["precio"] <= mx]
        return ofertas
