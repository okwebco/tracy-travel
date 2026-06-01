"""Agregador multi-proveedor.

Lee PROVEEDORES_VUELOS / PROVEEDORES_HOTELES, llama a los proveedores activos
(los que tengan credencial). Si ninguno está disponible, usa el proveedor mock.
Normaliza, ordena por precio y devuelve el Top 3 de cada tipo.
"""
from app.tracy import config
from app.tracy.providers.mock import MockProvider
from app.tracy.providers.travelpayouts import TravelpayoutsProvider
from app.tracy.providers.hotellook import HotellookProvider
from app.tracy.providers.amadeus import AmadeusProvider


_REGISTRO = {
    "travelpayouts": TravelpayoutsProvider,
    "hotellook": HotellookProvider,
    "amadeus": AmadeusProvider,
    "mock": MockProvider,
}

_MOCK = MockProvider()


def _instanciar(nombres: list[str]) -> list:
    provs = []
    for n in nombres:
        cls = _REGISTRO.get(n.strip().lower())
        if cls:
            provs.append(cls())
    return provs


async def buscar_vuelos(consulta) -> list[dict]:
    activos = [p for p in _instanciar(config.PROVEEDORES_VUELOS) if getattr(p, "disponible", False)]
    if not activos:
        activos = [_MOCK]
    resultados: list[dict] = []
    for p in activos:
        try:
            resultados.extend(await p.buscar_vuelos(consulta))
        except Exception as e:
            print(f"[Tracy/Aggregator] {p.nombre} vuelos falló: {e}")
    if not resultados:
        # Degradación: si los proveedores reales no devolvieron nada, usar mock
        resultados = await _MOCK.buscar_vuelos(consulta)
    resultados.sort(key=lambda o: o["precio"])
    return resultados[:3]


async def buscar_hoteles(consulta) -> list[dict]:
    activos = [p for p in _instanciar(config.PROVEEDORES_HOTELES) if getattr(p, "disponible", False)]
    if not activos:
        activos = [_MOCK]
    resultados: list[dict] = []
    for p in activos:
        try:
            resultados.extend(await p.buscar_hoteles(consulta))
        except Exception as e:
            print(f"[Tracy/Aggregator] {p.nombre} hoteles falló: {e}")
    if not resultados:
        resultados = await _MOCK.buscar_hoteles(consulta)
    resultados.sort(key=lambda o: o["precio"])
    return resultados[:3]
