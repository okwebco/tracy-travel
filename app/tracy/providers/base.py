"""Interfaz común de los proveedores de Tracy.

Cada proveedor implementa, según aplique:
    async def buscar_vuelos(consulta) -> list[dict]
        dict: precio, moneda, aerolinea, fecha_salida, fecha_regreso, escalas, link, proveedor
    async def buscar_hoteles(consulta) -> list[dict]
        dict: precio, moneda, nombre, estrellas, ciudad, link, mapa, proveedor

Un proveedor que no soporte un tipo devuelve [] para ese método.
La propiedad `disponible` indica si tiene credenciales para operar.
"""


class Proveedor:
    nombre = "base"
    disponible = True

    async def buscar_vuelos(self, consulta) -> list[dict]:
        return []

    async def buscar_hoteles(self, consulta) -> list[dict]:
        return []
