"""Lógica de valor de Tracy: construcción del payload del reporte,
frase de recomendación (3-5 palabras), total estimado y mensaje de WhatsApp.
"""
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


def calcular_total(mejor_vuelo: dict | None, mejor_hotel: dict | None,
                   noches: int | None) -> float | None:
    """Total estimado = vuelo + hotel/noche × noches."""
    total = 0.0
    tiene = False
    if mejor_vuelo:
        total += mejor_vuelo["precio"]; tiene = True
    if mejor_hotel and noches:
        total += mejor_hotel["precio"] * noches; tiene = True
    elif mejor_hotel:
        total += mejor_hotel["precio"]; tiene = True
    return round(total, 2) if tiene else None


def construir_payload(consulta, vuelos: list[dict], hoteles: list[dict],
                      mejor_precio_previo: float | None) -> dict:
    """Arma el JSON que se guarda en Reporte.payload_json y alimenta la página y el WhatsApp."""
    moneda = (consulta.moneda or config.MONEDA_DEFECTO).upper()
    mejor_vuelo = vuelos[0] if vuelos else None
    mejor_hotel = hoteles[0] if hoteles else None

    eval_temp = temporadas.evaluar(consulta.destino, consulta.fecha_salida, consulta.fecha_regreso)
    temporada_alta = eval_temp.get("temporada") == "alta"

    precio_actual = mejor_vuelo["precio"] if mejor_vuelo else (mejor_hotel["precio"] if mejor_hotel else None)
    frase = frase_recomendacion(consulta, mejor_precio_previo, precio_actual, temporada_alta)
    total = calcular_total(mejor_vuelo, mejor_hotel, consulta.noches)

    ahora = datetime.utcnow()
    return {
        "origen": consulta.origen,
        "origen_nombre": catalogo.nombre(consulta.origen),
        "destino": consulta.destino,
        "destino_nombre": catalogo.nombre(consulta.destino),
        "macro": consulta.macro,
        "motivo": consulta.motivo,
        "moneda": moneda,
        "noches": consulta.noches,
        "fecha_salida": consulta.fecha_salida.isoformat() if consulta.fecha_salida else None,
        "fecha_regreso": consulta.fecha_regreso.isoformat() if consulta.fecha_regreso else None,
        "vuelos": vuelos,
        "hoteles": hoteles,
        "total_estimado": total,
        "frase": frase,
        "temporada": eval_temp,
        "precio_referencia": precio_actual,
        "hora_visto": ahora.strftime("%H:%M"),
        "disclaimer": f"Precio visto a las {ahora.strftime('%H:%M')} UTC; puede cambiar al abrir el enlace.",
        "afiliados": "Podemos recibir comisión; no aumenta tu precio.",
    }


def mensaje_whatsapp_resumen(payload: dict, numero: str, cierre: bool = False,
                             mejor_precio_visto: float | None = None) -> str:
    """Resumen corto para WhatsApp (formato PLAN §4)."""
    moneda = payload.get("moneda", "COP")
    o = payload.get("origen_nombre", payload.get("origen"))
    d = payload.get("destino_nombre", payload.get("destino"))
    lineas = [f"🕵️ Tracy Travel — {o} → {d}"]

    vuelos = payload.get("vuelos") or []
    hoteles = payload.get("hoteles") or []
    if vuelos:
        v = vuelos[0]
        fechas = v.get("fecha_salida") or ""
        if v.get("fecha_regreso"):
            fechas = f"{fechas} → {v['fecha_regreso']}"
        lineas.append(f"Mejor vuelo: {_fmt_precio(v['precio'], moneda)} ({v.get('aerolinea','')}, {fechas})")
    if hoteles:
        h = hoteles[0]
        lineas.append(f"Mejor hotel: {_fmt_precio(h['precio'], moneda)}/noche ({h.get('nombre','')})")

    total = payload.get("total_estimado")
    if total is not None:
        lineas.append(f"Total estimado: {_fmt_precio(total, moneda)}")

    lineas.append(f"👉 {payload.get('frase','')}")
    lineas.append(f"Ver detalle (48 h): {config.PUBLIC_BASE_URL}/{numero}")

    if cierre:
        lineas.append("")
        if mejor_precio_visto is not None:
            lineas.append(f"🏁 Cierre del rastreo. Mejor precio visto: {_fmt_precio(mejor_precio_visto, moneda)}.")
        else:
            lineas.append("🏁 Cierre del rastreo.")
        lineas.append("Gracias por usar Tracy. Inicia otra consulta cuando quieras.")
    else:
        lineas.append("Responde CANCELAR para detener.")

    return "\n".join(lineas)


def mensaje_bienvenida(consulta) -> str:
    """Mensaje de activación tras el opt-in."""
    o = catalogo.nombre(consulta.origen)
    d = catalogo.nombre(consulta.destino)
    return (
        f"🕵️ ¡Hola! Soy Tracy Travel. Activé tu rastreo {o} → {d}.\n"
        f"Te avisaré en la madrugada con los mejores precios.\n\n"
        f"🔒 Nunca te pediremos dinero ni datos bancarios.\n"
        f"Responde CANCELAR cuando quieras para detener el rastreo."
    )
