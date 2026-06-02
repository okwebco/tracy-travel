"""Proveedor Amadeus Self-Service (vuelos), opcional.

Solo se activa si AMADEUS_CLIENT_ID y AMADEUS_CLIENT_SECRET están presentes.
OAuth2 client_credentials con cacheo de token (~30 min). Degrada a [] ante fallos.
"""
import time
import httpx

from app.tracy.providers.base import Proveedor
from app.tracy import config


class AmadeusProvider(Proveedor):
    nombre = "amadeus"

    _token: str | None = None
    _token_exp: float = 0.0

    @property
    def disponible(self) -> bool:
        return bool(config.AMADEUS_CLIENT_ID and config.AMADEUS_CLIENT_SECRET)

    async def _obtener_token(self) -> str | None:
        if self._token and time.time() < self._token_exp:
            return self._token
        url = f"{config.AMADEUS_BASE}/v1/security/oauth2/token"
        datos = {
            "grant_type": "client_credentials",
            "client_id": config.AMADEUS_CLIENT_ID,
            "client_secret": config.AMADEUS_CLIENT_SECRET,
        }
        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}) as client:
                r = await client.post(url, data=datos,
                                      headers={"Content-Type": "application/x-www-form-urlencoded"})
                payload = r.json()
        except Exception as e:
            print(f"[Tracy/Amadeus] Error obteniendo token: {e}")
            return None
        token = payload.get("access_token")
        if not token:
            print(f"[Tracy/Amadeus] Sin access_token: {payload}")
            return None
        self._token = token
        self._token_exp = time.time() + min(payload.get("expires_in", 1800), 1800) - 60
        return token

    async def buscar_vuelos(self, consulta) -> list[dict]:
        if not self.disponible:
            return []
        token = await self._obtener_token()
        if not token:
            return []
        url = f"{config.AMADEUS_BASE}/v2/shopping/flight-offers"
        params = {
            "originLocationCode": consulta.origen.upper(),
            "destinationLocationCode": consulta.destino.upper(),
            "adults": 1,
            "currencyCode": (consulta.moneda or "COP").upper(),
            "max": 10,
        }
        if consulta.fecha_salida:
            params["departureDate"] = consulta.fecha_salida.isoformat()
        else:
            return []  # Amadeus requiere fecha exacta
        if consulta.fecha_regreso:
            params["returnDate"] = consulta.fecha_regreso.isoformat()

        try:
            async with httpx.AsyncClient(timeout=25.0, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}) as client:
                r = await client.get(url, params=params,
                                     headers={"Authorization": f"Bearer {token}"})
                data = r.json()
        except Exception as e:
            print(f"[Tracy/Amadeus] Error vuelos: {e}")
            return []

        ofertas = []
        for of in data.get("data", []):
            try:
                precio = float(of["price"]["grandTotal"])
                itin = of["itineraries"][0]
                segs = itin["segments"]
                salida = segs[0]["departure"]["at"][:10]
                regreso = None
                if len(of["itineraries"]) > 1:
                    regreso = of["itineraries"][1]["segments"][0]["departure"]["at"][:10]
                aerolinea = segs[0].get("carrierCode")
                escalas = len(segs) - 1
            except (KeyError, IndexError, ValueError):
                continue
            ofertas.append({
                "precio": precio,
                "moneda": (consulta.moneda or "COP").upper(),
                "aerolinea": aerolinea,
                "fecha_salida": salida,
                "fecha_regreso": regreso,
                "escalas": escalas,
                "link": "https://www.amadeus.com",
                "proveedor": self.nombre,
            })
        return ofertas
