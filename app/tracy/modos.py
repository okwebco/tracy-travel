"""Lógica de los 3 modos de consulta de Tracy (ADENDA v2).

- rapida      : 1 entrega inmediata, una sola vez.
- rastreo     : casillas acumulativas {1,3,5,8,15,30} días; al marcar uno se
                auto-marcan los inferiores. El día 1 = entrega inmediata; el
                resto son offsets desde la activación. Termina en el último.
- seguimiento : cantidad de rastreos (2..6) cada `frecuencia` días; el #1 es
                inmediato y los siguientes cada `frecuencia` días.

`calcular_checkpoints(...)` devuelve la lista de fechas (date) de cada entrega,
empezando por HOY (entrega inmediata #1). El cron las recorre en orden.
"""
from datetime import date, timedelta

MODOS = {"rapida", "rastreo", "seguimiento"}

# Casillas válidas de Rastreo (acumulativas).
RASTREO_DIAS = [1, 3, 5, 8, 15, 30]

# Selectores válidos de Seguimiento.
SEGUIMIENTO_CANTIDADES = {2, 3, 4, 5, 6}
SEGUIMIENTO_FRECUENCIAS = {2, 3, 5, 7, 15, 30}


def normalizar_rastreo_dias(dias) -> list[int]:
    """Normaliza y auto-marca los inferiores.

    Acepta lista de ints o CSV. Para el máximo marcado, incluye todas las
    casillas válidas <= ese máximo. Ej.: [8] -> [1,3,5,8].
    """
    if isinstance(dias, str):
        crudos = [int(x) for x in dias.split(",") if x.strip().isdigit()]
    else:
        crudos = [int(x) for x in (dias or [])]
    crudos = [d for d in crudos if d in RASTREO_DIAS]
    if not crudos:
        return []
    tope = max(crudos)
    return [d for d in RASTREO_DIAS if d <= tope]


def calcular_checkpoints(modo: str, *, desde: date | None = None,
                         rastreo_dias=None,
                         seguimiento_cantidad: int | None = None,
                         seguimiento_frecuencia: int | None = None) -> list[date]:
    """Devuelve las fechas de entrega. La primera (índice 0) es la inmediata."""
    base = desde or date.today()

    if modo == "rapida":
        return [base]

    if modo == "rastreo":
        marcados = normalizar_rastreo_dias(rastreo_dias)
        if not marcados:
            marcados = [1]
        # día 1 = inmediato (base); los demás son offsets desde la activación.
        fechas = []
        for d in marcados:
            offset = 0 if d == 1 else d
            fechas.append(base + timedelta(days=offset))
        return fechas

    if modo == "seguimiento":
        cant = seguimiento_cantidad or 2
        frec = seguimiento_frecuencia or 2
        return [base + timedelta(days=frec * i) for i in range(cant)]

    return [base]


def resumen_entregas(consulta) -> str:
    """Texto legible de cuándo recibirá el usuario sus reportes."""
    modo = consulta.modo
    if modo == "rapida":
        return "Recibirás 1 reporte ahora (entrega inmediata)."

    if modo == "rastreo":
        marcados = normalizar_rastreo_dias(consulta.rastreo_dias) or [1]
        partes = []
        for d in marcados:
            partes.append("ahora" if d == 1 else f"al día {d}")
        return "Recibirás: " + ", ".join(partes) + "."

    if modo == "seguimiento":
        cant = consulta.seguimiento_cantidad or 2
        frec = consulta.seguimiento_frecuencia or 2
        hitos = ["ahora"]
        for i in range(1, cant):
            hitos.append(f"+{frec * i} días")
        return f"Recibirás {cant} reportes: " + ", ".join(hitos) + "."

    return ""
