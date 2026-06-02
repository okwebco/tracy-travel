"""Agregador multi-proveedor de vuelos.

Lee PROVEEDORES_VUELOS, llama a los proveedores activos (los que tengan
credencial). Si ninguno está disponible, usa el proveedor mock.
Normaliza, ordena por precio y devuelve el Top 3.

Cada búsqueda es one-way para UN tramo (origen → destino + fecha). Un viaje
con vuelta se resuelve buscando dos tramos por separado.
"""
from app.tracy import config
from app.tracy.providers.mock import MockProvider
from app.tracy.providers.travelpayouts import TravelpayoutsProvider


_REGISTRO = {
    "travelpayouts": TravelpayoutsProvider,
    "mock": MockProvider,
}

_MOCK = MockProvider()


class Tramo:
    """Objeto mínimo que consumen los proveedores para buscar UN tramo one-way.

    Expone los atributos que esperan los proveedores: origen, destino,
    fecha_salida, moneda. Toda búsqueda es one-way.
    """

    def __init__(self, origen: str, destino: str, fecha_salida, moneda: str):
        self.origen = origen
        self.destino = destino
        self.fecha_salida = fecha_salida
        self.moneda = moneda


def _instanciar(nombres: list[str]) -> list:
    provs = []
    for n in nombres:
        cls = _REGISTRO.get(n.strip().lower())
        if cls:
            provs.append(cls())
    return provs


async def _buscar_tramo(tramo: Tramo) -> list[dict]:
    reales = [p for p in _instanciar(config.PROVEEDORES_VUELOS) if getattr(p, "disponible", False)]
    # En producción (hay proveedor real) NO se usa mock: si no hay datos se
    # devuelve vacío. Mejor "sin vuelos" que ofertas falsas con enlaces rotos.
    # El mock solo aplica en MODO DEMO (sin ninguna credencial real).
    activos = reales if reales else [_MOCK]
    resultados: list[dict] = []
    for p in activos:
        try:
            resultados.extend(await p.buscar_vuelos(tramo))
        except Exception as e:
            print(f"[Tracy/Aggregator] {p.nombre} vuelos falló: {e}")
    resultados.sort(key=lambda o: o["precio"])
    return resultados[:3]


async def buscar_tramo(origen: str, destino: str, fecha_salida, moneda: str) -> list[dict]:
    """Busca un tramo one-way (origen → destino en fecha) y devuelve el Top 3."""
    return await _buscar_tramo(Tramo(origen, destino, fecha_salida, moneda))


async def buscar_vuelos(consulta) -> dict:
    """Busca los tramos de una consulta.

    Devuelve {"vuelos_ida": [...], "vuelos_vuelta": [...] | None}.
    La IDA siempre se busca; la VUELTA solo si la consulta tiene tramo de vuelta.
    """
    moneda = consulta.moneda or config.MONEDA_DEFECTO
    vuelos_ida = await buscar_tramo(consulta.origen, consulta.destino,
                                    consulta.fecha_salida, moneda)
    vuelos_vuelta = None
    if getattr(consulta, "origen_vuelta", None) and getattr(consulta, "destino_vuelta", None):
        vuelos_vuelta = await buscar_tramo(consulta.origen_vuelta, consulta.destino_vuelta,
                                           consulta.fecha_vuelta, moneda)
    return {"vuelos_ida": vuelos_ida, "vuelos_vuelta": vuelos_vuelta}
