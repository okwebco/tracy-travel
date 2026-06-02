"""Lógica de valor de Tracy: construcción del payload del reporte,
frase de recomendación (3-5 palabras) y mensaje de WhatsApp. Solo vuelos.

El viaje se modela por TRAMOS one-way:
  - IDA   (siempre): origen → destino + fecha_salida.
  - VUELTA (opcional, independiente / open-jaw): origen_vuelta → destino_vuelta
           + fecha_vuelta.
Cada tramo se busca por separado y produce su propia lista Top 3.
"""
import re
from datetime import datetime

from app.tracy import catalogo, temporadas, config


def _fmt_precio(valor: float | None, moneda: str) -> str:
    if valor is None:
        return "—"
    moneda = (moneda or "COP").upper()
    if moneda == "COP":
        partes, s = [], str(int(round(valor)))
        while len(s) > 3:
            partes.insert(0, s[-3:]); s = s[:-3]
        partes.insert(0, s)
        return f"${' '.join(partes)} COP"
    return f"{moneda} {valor:,.2f}"


def frase_recomendacion(consulta, mejor_precio: float | None,
                        precio_actual: float | None, temporada_alta: bool) -> str:
    """Heurística de la frase 3-5 palabras.

    - Temporada alta/fiesta → 'Sube por temporada'
    - Precio <= mínimo histórico visto → 'Cómpralo ya'
    - Bajó respecto al anterior → 'Buen precio, considera'
    - Subió o estable → 'Aún puede bajar'
    """
    if temporada_alta:
        return "Sube por temporada"
    if precio_actual is None:
        return "Aún puede bajar"
    if mejor_precio is None or precio_actual <= mejor_precio:
        return "Cómpralo ya"
    if precio_actual < mejor_precio:
        return "Buen precio, considera"
    return "Aún puede bajar"


def construir_payload(consulta, resultado: dict,
                      mejor_precio_previo: float | None) -> dict:
    """Arma el JSON que se guarda en Reporte.payload_json.

    `resultado` es el dict del aggregator: {"vuelos_ida": [...], "vuelos_vuelta": [...] | None}.
    Alimenta la página de reporte y el mensaje de WhatsApp.
    """
    moneda = (consulta.moneda or config.MONEDA_DEFECTO).upper()
    vuelos_ida = resultado.get("vuelos_ida") or []
    vuelos_vuelta = resultado.get("vuelos_vuelta")

    mejor_ida = vuelos_ida[0] if vuelos_ida else None

    eval_temp = temporadas.evaluar(consulta.destino, consulta.fecha_salida, None)
    temporada_alta = eval_temp.get("temporada") == "alta"

    # El precio de referencia (para la heurística e histórico) es el más barato
    # de la ida (tramo principal).
    precio_actual = mejor_ida["precio"] if mejor_ida else None
    frase = frase_recomendacion(consulta, mejor_precio_previo, precio_actual, temporada_alta)

    hay_vuelta = bool(getattr(consulta, "origen_vuelta", None) and getattr(consulta, "destino_vuelta", None))

    ahora = datetime.utcnow()
    return {
        "nombre": consulta.nombre,
        "apellido": consulta.apellido,
        # Tramo IDA
        "origen": consulta.origen,
        "origen_nombre": catalogo.nombre(consulta.origen),
        "origen_pais": catalogo.pais_de(consulta.origen),
        "destino": consulta.destino,
        "destino_nombre": catalogo.nombre(consulta.destino),
        "destino_pais": catalogo.pais_de(consulta.destino),
        "fecha_salida": consulta.fecha_salida.isoformat() if consulta.fecha_salida else None,
        "vuelos_ida": vuelos_ida,
        # Tramo VUELTA (None si no aplica)
        "tiene_vuelta": hay_vuelta,
        "origen_vuelta": consulta.origen_vuelta if hay_vuelta else None,
        "origen_vuelta_nombre": catalogo.nombre(consulta.origen_vuelta) if hay_vuelta else None,
        "origen_vuelta_pais": catalogo.pais_de(consulta.origen_vuelta) if hay_vuelta else None,
        "destino_vuelta": consulta.destino_vuelta if hay_vuelta else None,
        "destino_vuelta_nombre": catalogo.nombre(consulta.destino_vuelta) if hay_vuelta else None,
        "destino_vuelta_pais": catalogo.pais_de(consulta.destino_vuelta) if hay_vuelta else None,
        "fecha_vuelta": consulta.fecha_vuelta.isoformat() if hay_vuelta and consulta.fecha_vuelta else None,
        "vuelos_vuelta": vuelos_vuelta,
        # Comunes
        "motivo": consulta.motivo,
        "moneda": moneda,
        "frase": frase,
        "temporada": eval_temp,
        "precio_referencia": precio_actual,
        "hora_visto": ahora.strftime("%H:%M"),
        "disclaimer": f"Precio visto a las {ahora.strftime('%H:%M')} UTC; puede variar.",
    }


def _fmt_fecha_wa(valor) -> str:
    """Formatea una fecha ISO a 'YYYY-MM-DD HH:MM' (sin segundos ni zona).

    Si el dato es solo fecha (sin hora), lo muestra tal cual.
    """
    if not valor:
        return ""
    s = str(valor).strip()
    base = re.sub(r"(Z|[+-]\d{2}:?\d{2})$", "", s)
    try:
        dt = datetime.fromisoformat(base)
    except ValueError:
        return s
    if "T" not in s and " " not in base:
        return dt.strftime("%Y-%m-%d")
    return dt.strftime("%Y-%m-%d %H:%M")


def _escalas_n(v: dict) -> int:
    e = v.get("escalas")
    try:
        return int(e)
    except (TypeError, ValueError):
        return 0


def _bloque_tramo_wa(ruta: str, titulo_etiqueta: str, vuelos: list, moneda: str,
                     frase: str, etiqueta_sin_vuelos: str) -> list[str]:
    """Genera las líneas de un tramo (bloque independiente) para WhatsApp.

    ruta: 'Pereira → São Luís'.
    titulo_etiqueta: 'IDA' o 'REGRESO'.
    frase: recomendación (se muestra junto al destino si hay vuelos).
    etiqueta_sin_vuelos: 'la ida' / 'el regreso'.
    """
    if not vuelos:
        return [f"{ruta}: No encontramos vuelos para {etiqueta_sin_vuelos} en estas fechas."]
    v = vuelos[0]
    aero = (v.get("aerolinea") or "").strip()
    fecha = _fmt_fecha_wa(v.get("fecha_salida"))
    return [
        f"{ruta}: 👉 *{frase}*",  # *…* = negrita en WhatsApp
        f"{titulo_etiqueta} por {aero} desde {_fmt_precio(v.get('precio'), moneda)}",
        f"→ {fecha}",
        f"Escala(s): {_escalas_n(v)}",
    ]


def mensaje_whatsapp_resumen(payload: dict, numero: str, cierre: bool = False,
                             mejor_precio_visto: float | None = None) -> str:
    """Resumen corto para WhatsApp (formato §5), por tramos."""
    moneda = payload.get("moneda", "COP")
    o = payload.get("origen_nombre", payload.get("origen"))
    d = payload.get("destino_nombre", payload.get("destino"))
    frase = payload.get("frase", "")
    nombre = (payload.get("nombre") or "").strip()

    saludo = (f"Hola {nombre}, soy Tracy 🕵️ Travel ✈️" if nombre
              else "Hola, soy Tracy 🕵️ Travel ✈️")
    lineas = [saludo, "", "Tu investigación de vuelo:", ""]

    # Bloque IDA
    lineas += _bloque_tramo_wa(f"{o} → {d}", "IDA",
                               payload.get("vuelos_ida") or [], moneda, frase, "la ida")

    # Bloque REGRESO (solo si hay tramo)
    if payload.get("tiene_vuelta"):
        ov = payload.get("origen_vuelta_nombre", payload.get("origen_vuelta"))
        dv = payload.get("destino_vuelta_nombre", payload.get("destino_vuelta"))
        lineas.append("")
        lineas += _bloque_tramo_wa(f"{ov} → {dv}", "REGRESO",
                                   payload.get("vuelos_vuelta") or [], moneda, frase, "el regreso")

    lineas.append("")
    lineas.append(f"Ver detalle en {config.PUBLIC_BASE_URL}/{numero}")
    lineas.append("~Se autodestruye en 48 horas~")  # ~…~ = tachado en WhatsApp

    if cierre:
        lineas.append("")
        lineas.append("Gracias por investigar con")
        lineas.append("Tracy 🕵️ Travel ✈️")
        lineas.append("tracy.okweb.co")
    else:
        lineas.append("Responde CANCELAR para detener.")

    return "\n".join(lineas)


def mensaje_bienvenida(consulta) -> str:
    """Mensaje de activación tras el opt-in (formato §5)."""
    o = catalogo.nombre(consulta.origen)
    op = catalogo.pais_de(consulta.origen)
    d = catalogo.nombre(consulta.destino)
    dp = catalogo.pais_de(consulta.destino)
    nombre = (consulta.nombre or "").strip()
    saludo = f"¡Hola {nombre}!" if nombre else "¡Hola!"

    lineas = [
        saludo,
        "Soy Tracy 🕵️ Travel ✈️",
        "",
        "Activé tu investigación de vuelos:",
        f"De: *{o}* ({op})",
        f"A: *{d}* ({dp})",
    ]

    if getattr(consulta, "origen_vuelta", None) and getattr(consulta, "destino_vuelta", None):
        ov = catalogo.nombre(consulta.origen_vuelta)
        ovp = catalogo.pais_de(consulta.origen_vuelta)
        dv = catalogo.nombre(consulta.destino_vuelta)
        dvp = catalogo.pais_de(consulta.destino_vuelta)
        lineas.append(f"Regreso: De *{ov}* ({ovp}) A *{dv}* ({dvp})")

    lineas += [
        "",
        "Recibe ya tu primer reporte 👇",
    ]
    return "\n".join(lineas)
