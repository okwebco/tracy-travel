"""Calendario curado de temporadas y fiestas + heurística de temporada alta/baja.

Combina:
1. Eventos curados por país/ciudad (Carnaval, Réveillon, São João, verano, festivos…).
2. Heurística por meses de temporada alta genérica del destino.

Función principal: evaluar(destino, fecha_inicio, fecha_fin) ->
    {"temporada": "alta"|"media"|"baja", "eventos": [...], "sube_precio": bool, "mensaje": str}
"""
from datetime import date
from app.tracy import catalogo


# Carnaval de Brasil — fecha móvil (48 días antes del Domingo de Pascua).
# Tabla curada de fechas aproximadas del martes de Carnaval por año.
CARNAVAL_BRASIL = {
    2026: (date(2026, 2, 14), date(2026, 2, 18)),
    2027: (date(2027, 2, 6), date(2027, 2, 10)),
    2028: (date(2028, 2, 26), date(2028, 3, 1)),
    2029: (date(2029, 2, 10), date(2029, 2, 14)),
}

# Semana Santa (Colombia, fecha móvil) — rango aproximado por año.
SEMANA_SANTA = {
    2026: (date(2026, 3, 29), date(2026, 4, 5)),
    2027: (date(2027, 3, 21), date(2027, 3, 28)),
    2028: (date(2028, 4, 9), date(2028, 4, 16)),
    2029: (date(2029, 3, 25), date(2029, 4, 1)),
}


def _rango_solapa(ini_a: date, fin_a: date, ini_b: date, fin_b: date) -> bool:
    return ini_a <= fin_b and ini_b <= fin_a


def _en_meses(d: date, meses: set[int]) -> bool:
    return d.month in meses


def _eventos_pais(pais: str, ini: date, fin: date) -> list[str]:
    """Eventos curados según el país de destino que solapan con el rango de viaje."""
    eventos: list[str] = []
    pais = (pais or "").lower()

    if "brasil" in pais:
        # Carnaval (fecha móvil)
        for anio in {ini.year, fin.year}:
            rango = CARNAVAL_BRASIL.get(anio)
            if rango and _rango_solapa(ini, fin, rango[0], rango[1]):
                eventos.append("Carnaval de Brasil")
                break
        # Réveillon (Año Nuevo en Río): 28 dic – 2 ene
        if (ini.month == 12 and ini.day >= 28) or (fin.month == 1 and fin.day <= 2) or \
           (ini.month == 12 and fin.month == 1):
            eventos.append("Réveillon (Año Nuevo en Río)")
        # São João (junio, Nordeste / São Luís)
        if _en_meses(ini, {6}) or _en_meses(fin, {6}):
            eventos.append("Fiestas de São João (junio)")
        # Verano de playas (dic–feb)
        if _en_meses(ini, {12, 1, 2}) or _en_meses(fin, {12, 1, 2}):
            eventos.append("Verano brasileño (temporada de playa)")

    # Colombia como destino (también puede ser origen): Semana Santa
    if "colombia" in pais:
        for anio in {ini.year, fin.year}:
            rango = SEMANA_SANTA.get(anio)
            if rango and _rango_solapa(ini, fin, rango[0], rango[1]):
                eventos.append("Semana Santa")
                break

    return eventos


# Meses de temporada alta genérica por país (verano local / vacaciones).
TEMPORADA_ALTA_GENERICA = {
    # Hemisferio norte: verano jun–ago + fin de año
    "españa": {7, 8, 12}, "francia": {7, 8, 12}, "italia": {7, 8, 12},
    "reino unido": {7, 8, 12}, "portugal": {7, 8}, "alemania": {7, 8, 12},
    "países bajos": {7, 8}, "ee. uu.": {6, 7, 8, 12}, "canadá": {7, 8},
    "turquía": {6, 7, 8}, "egipto": {12, 1, 2}, "grecia": {6, 7, 8},
    "chipre": {6, 7, 8}, "emiratos": {12, 1, 2}, "qatar": {12, 1, 2},
    "marruecos": {7, 8}, "japón": {3, 4, 7, 8}, "tailandia": {12, 1, 2},
    "indonesia": {7, 8, 12}, "maldivas": {12, 1, 2}, "méxico": {7, 8, 12},
    "rep. dominicana": {12, 1, 2, 7}, "cuba": {12, 1, 2}, "perú": {6, 7, 8},
    "argentina": {1, 2, 7}, "brasil": {12, 1, 2}, "colombia": {6, 7, 12, 1},
}


def evaluar(destino: str, fecha_inicio: date | None, fecha_fin: date | None) -> dict:
    """Evalúa la temporada de un destino para un rango de fechas.

    Si no hay fechas, devuelve un resultado neutro ("media") sin eventos.
    """
    pais = catalogo.pais(destino) or ""
    ciudad = catalogo.nombre(destino)

    if not fecha_inicio:
        return {
            "temporada": "media",
            "eventos": [],
            "sube_precio": False,
            "mensaje": f"Sin fechas definidas para {ciudad}. Activa fechas flexibles para que Tracy busque el mejor momento.",
        }

    fin = fecha_fin or fecha_inicio
    eventos = _eventos_pais(pais, fecha_inicio, fin)

    # Heurística de meses de temporada alta
    meses_alta = TEMPORADA_ALTA_GENERICA.get(pais.lower(), set())
    en_temporada_alta = fecha_inicio.month in meses_alta or fin.month in meses_alta

    if eventos:
        temporada = "alta"
        sube_precio = True
        lista = ", ".join(eventos)
        mensaje = (
            f"Tus fechas en {ciudad} coinciden con: {lista}. "
            f"Es temporada ALTA y los precios suelen subir. ¿Continúas?"
        )
    elif en_temporada_alta:
        temporada = "alta"
        sube_precio = True
        mensaje = (
            f"Esas fechas en {ciudad} son temporada ALTA. "
            f"Los precios suelen subir. ¿Continúas?"
        )
    else:
        temporada = "media"
        sube_precio = False
        mensaje = (
            f"Esas fechas en {ciudad} son temporada media/baja. "
            f"Buen momento para encontrar precios razonables."
        )

    return {
        "temporada": temporada,
        "eventos": eventos,
        "sube_precio": sube_precio,
        "mensaje": mensaje,
    }
