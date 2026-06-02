"""Lógica de valor de Tracy: construcción del payload del reporte,
frase de recomendación (3-5 palabras) y mensaje de WhatsApp. Solo vuelos.
"""
import re
from datetime import datetime

from app.tracy import catalogo, temporadas, config

TIPO_VIAJE_LABEL = {
    "ida": "Solo ida",
    "regreso": "Solo regreso",
    "ida_regreso": "Ida y regreso",
}


def tipo_viaje_label(tipo: str | None) -> str:
    return TIPO_VIAJE_LABEL.get(tipo or "ida_regreso", "Ida y regreso")


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


def construir_payload(consulta, vuelos: list[dict],
                      mejor_precio_previo: float | None) -> dict:
    """Arma el JSON que se guarda en Reporte.payload_json y alimenta la página y el WhatsApp."""
    moneda = (consulta.moneda or config.MONEDA_DEFECTO).upper()
    mejor_vuelo = vuelos[0] if vuelos else None

    eval_temp = temporadas.evaluar(consulta.destino, consulta.fecha_salida, consulta.fecha_regreso)
    temporada_alta = eval_temp.get("temporada") == "alta"

    precio_actual = mejor_vuelo["precio"] if mejor_vuelo else None
    frase = frase_recomendacion(consulta, mejor_precio_previo, precio_actual, temporada_alta)

    ahora = datetime.utcnow()
    return {
        "nombre": consulta.nombre,
        "apellido": consulta.apellido,
        "origen": consulta.origen,
        "origen_nombre": catalogo.nombre(consulta.origen),
        "destino": consulta.destino,
        "destino_nombre": catalogo.nombre(consulta.destino),
        "motivo": consulta.motivo,
        "tipo_viaje": consulta.tipo_viaje,
        "moneda": moneda,
        "fecha_salida": consulta.fecha_salida.isoformat() if consulta.fecha_salida else None,
        "fecha_regreso": consulta.fecha_regreso.isoformat() if consulta.fecha_regreso else None,
        "vuelos": vuelos,
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


def mensaje_whatsapp_resumen(payload: dict, numero: str, cierre: bool = False,
                             mejor_precio_visto: float | None = None) -> str:
    """Resumen corto para WhatsApp (formato §5)."""
    moneda = payload.get("moneda", "COP")
    o = payload.get("origen_nombre", payload.get("origen"))
    d = payload.get("destino_nombre", payload.get("destino"))
    nombre = (payload.get("nombre") or "").strip()
    tipo_viaje = payload.get("tipo_viaje") or "ida_regreso"

    saludo = (f"Hola {nombre}, soy Tracy 🕵️ Travel ✈️" if nombre
              else "Hola, soy Tracy 🕵️ Travel ✈️")
    lineas = [saludo, f"{o} → {d}", ""]

    vuelos = payload.get("vuelos") or []
    if vuelos:
        v = vuelos[0]
        aero = v.get("aerolinea", "") or ""
        salida = _fmt_fecha_wa(v.get("fecha_salida"))
        regreso = _fmt_fecha_wa(v.get("fecha_regreso"))
        escalas = v.get("escalas")
        escalas_txt = "Directo" if escalas == 0 else (f"{escalas} escala(s)" if escalas else "")

        def _con_escalas(txt: str) -> str:
            return f"{txt} · {escalas_txt}" if escalas_txt else txt

        lineas.append(f"Mejor vuelo: {_fmt_precio(v['precio'], moneda)}")
        if tipo_viaje == "ida":
            lineas.append(f"→ {aero}, {_con_escalas(salida)}")
        elif tipo_viaje == "regreso":
            ref = regreso or salida
            lineas.append(f"→ {aero}, {_con_escalas(ref)}")
        else:  # ida_regreso
            lineas.append(f"→ {aero}, {salida}")
            if regreso:
                lineas.append(f"→ {_con_escalas(regreso)}")
            elif escalas_txt:
                lineas[-1] = f"→ {aero}, {_con_escalas(salida)}"
        lineas.append("")
        lineas.append(f"👉 *{payload.get('frase','')}*")  # *…* = negrita en WhatsApp
    else:
        lineas.append("No encontramos vuelos para estas fechas ahora.")

    lineas.append("")
    lineas.append(f"Ver detalle en {config.PUBLIC_BASE_URL}/{numero}")
    lineas.append("(Disponible 48 horas)")

    if cierre:
        lineas.append("")
        lineas.append("Gracias por usar")
        lineas.append("Tracy 🕵️ Travel ✈️")
        lineas.append("tracy.okweb.co")
    else:
        lineas.append("Responde CANCELAR para detener.")

    return "\n".join(lineas)


def mensaje_bienvenida(consulta) -> str:
    """Mensaje de activación tras el opt-in (en filas)."""
    o = catalogo.nombre(consulta.origen)
    d = catalogo.nombre(consulta.destino)
    nombre = (consulta.nombre or "").strip()
    saludo = f"¡Hola {nombre}!" if nombre else "¡Hola!"
    return (
        f"{saludo}\n"
        f"Soy Tracy 🕵️ Travel ✈️\n"
        f"\n"
        f"Activé tu consulta:\n"
        f"{o} → {d}.\n"
        f"\n"
        f"Recibirás ya tu primer reporte 👇 (entrega inmediata)."
    )
