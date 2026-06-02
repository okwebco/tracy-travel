"""Interfaz común de los proveedores de vuelos de Tracy.

Cada proveedor implementa:
    async def buscar_vuelos(consulta) -> list[dict]
        dict: precio, moneda, aerolinea, fecha_salida, fecha_regreso, escalas, link, proveedor

La propiedad `disponible` indica si tiene credenciales para operar.
"""


class Proveedor:
    nombre = "base"
    disponible = True

    async def buscar_vuelos(self, consulta) -> list[dict]:
        return []
