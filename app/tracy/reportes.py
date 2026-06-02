"""Página de reporte GET /{numero} y robots.txt.

Renderiza el reporte más reciente no expirado de un número, server-side,
con noindex (meta + header X-Robots-Tag). Si no hay/expiró → página "expiró".
"""
import json
import re
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.tracy.models import Reporte

router = APIRouter(tags=["tracy-reporte"])

_NOINDEX_HEADERS = {"X-Robots-Tag": "noindex", "Cache-Control": "no-store"}


def robots_txt() -> PlainTextResponse:
    return PlainTextResponse("User-agent: *\nDisallow: /\n")


def _esc(v) -> str:
    s = "" if v is None else str(v)
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;"))


def _fmt_precio(valor, moneda) -> str:
    if valor is None:
        return "—"
    moneda = (moneda or "COP").upper()
    if moneda == "COP":
        partes, s = [], str(int(round(float(valor))))
        while len(s) > 3:
            partes.insert(0, s[-3:]); s = s[:-3]
        partes.insert(0, s)
        return f"${' '.join(partes)} COP"
    return f"{moneda} {float(valor):,.2f}"


def _pagina_expirado() -> HTMLResponse:
    html = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Tracy Travel</title>
<style>body{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;
display:flex;min-height:100vh;align-items:center;justify-content:center;margin:0;text-align:center}
.c{max-width:420px;padding:32px}h1{font-size:48px;margin:0}</style></head>
<body><div class="c"><h1>🕵️</h1><h2>Tu reporte expiró o no existe</h2>
<p>Los reportes de Tracy se borran a las 48 horas por privacidad.
Inicia una nueva consulta cuando quieras.</p></div></body></html>"""
    return HTMLResponse(html, status_code=404, headers=_NOINDEX_HEADERS)


def _tarjeta_vuelo(v: dict, moneda: str) -> str:
    fechas = _esc(v.get("fecha_salida") or "")
    if v.get("fecha_regreso"):
        fechas += f" → {_esc(v['fecha_regreso'])}"
    escalas = v.get("escalas")
    escalas_txt = "Directo" if escalas == 0 else (f"{escalas} escala(s)" if escalas else "")
    return f"""<div class="card">
      <div class="precio">{_fmt_precio(v.get('precio'), moneda)}</div>
      <div class="meta">{_esc(v.get('aerolinea') or '')} · {fechas} · {escalas_txt}</div>
    </div>"""


def _render(payload: dict, creado: datetime) -> str:
    moneda = payload.get("moneda", "COP")
    o = _esc(payload.get("origen_nombre") or payload.get("origen"))
    d = _esc(payload.get("destino_nombre") or payload.get("destino"))
    nombre_completo = _esc((str(payload.get("nombre") or "") + " " + str(payload.get("apellido") or "")).strip())
    tipo_viaje_lbl = {"ida": "Solo ida", "regreso": "Solo regreso", "ida_regreso": "Ida y regreso"}.get(
        payload.get("tipo_viaje") or "ida_regreso", "Ida y regreso")
    vuelos = payload.get("vuelos") or []

    bloques = []
    if vuelos:
        bloques.append("<h3>✈️ Top 3 vuelos</h3>" + "".join(_tarjeta_vuelo(v, moneda) for v in vuelos))
    else:
        bloques.append('<div class="aviso">✈️ No encontramos vuelos para estas fechas en este momento. '
                       'Prueba con otras fechas o inicia otra consulta.</div>')

    temporada = payload.get("temporada") or {}
    temp_html = ""
    if temporada.get("mensaje"):
        temp_html = f'<div class="aviso">📅 {_esc(temporada["mensaje"])}</div>'

    frase = _esc(payload.get("frase") or "")
    disclaimer = _esc(payload.get("disclaimer") or "")

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex">
<title>Tracy Travel — {o} → {d}</title>
<style>
:root{{color-scheme:dark}}
body{{font-family:system-ui,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:0 0 40px}}
.wrap{{max-width:560px;margin:0 auto;padding:20px}}
header{{text-align:center;padding:24px 0 8px}}
h1{{font-size:22px;margin:6px 0}}
.ruta{{color:#94a3b8}}
.frase{{display:inline-block;background:#16a34a;color:#fff;font-weight:800;
border-radius:999px;padding:10px 22px;margin:12px 0;font-size:20px;letter-spacing:.3px}}
.aviso{{background:#1e293b;border-left:4px solid #f59e0b;padding:12px;border-radius:8px;margin:14px 0;font-size:15px}}
h3{{margin:22px 0 10px;border-bottom:1px solid #334155;padding-bottom:6px}}
.card{{background:#1e293b;border-radius:12px;padding:14px;margin:10px 0}}
.precio{{font-size:22px;font-weight:700;color:#38bdf8}}
.meta{{color:#cbd5e1;margin:6px 0 0;font-size:14px}}
.hola{{color:#94a3b8;font-size:13px;font-weight:400;margin:2px 0}}
.tipo{{color:#94a3b8;font-size:13px}}
footer{{margin-top:26px;color:#64748b;font-size:12px;text-align:center;line-height:1.6}}
footer a.creditos{{color:#3b82f6;text-decoration:underline}}
</style></head>
<body><div class="wrap">
<header>
  <div style="font-size:40px">🕵️</div>
  <h1>Tracy Travel</h1>
  {f'<div class="hola">¡Hola {nombre_completo}!</div>' if nombre_completo else ''}
  <div class="ruta">{o} → {d}</div>
  <div class="tipo">{tipo_viaje_lbl}</div>
  <div class="frase">{frase}</div>
</header>
{temp_html}
{''.join(bloques)}
<footer>
  <div>{disclaimer}</div>
  <div>Reporte generado {_esc(creado.strftime('%Y-%m-%d %H:%M'))} UTC · se borra a las 48 h.</div>
  <div><a class="creditos" href="http://okweb.co/jhoveloro/tracy-travel" target="_blank" rel="noopener nofollow">Tracy Travel | Crea Ok Web ® | 2026</a></div>
</footer>
</div></body></html>"""


def pagina_reporte(numero: str, db: Session) -> HTMLResponse:
    numero = re.sub(r"\D", "", numero or "")
    if not numero:
        return _pagina_expirado()
    reporte = (db.query(Reporte)
               .filter(Reporte.numero == numero, Reporte.expires_at > datetime.utcnow())
               .order_by(Reporte.created_at.desc())
               .first())
    if not reporte:
        return _pagina_expirado()
    try:
        payload = json.loads(reporte.payload_json)
    except Exception:
        return _pagina_expirado()
    return HTMLResponse(_render(payload, reporte.created_at), headers=_NOINDEX_HEADERS)


@router.get("/{numero}", response_class=HTMLResponse)
async def ver_reporte(numero: str, db: Session = Depends(get_db)):
    return pagina_reporte(numero, db)
