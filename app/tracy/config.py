"""Configuración central de Tracy Travel.

Todo lee de variables de entorno con valores por defecto seguros para MODO DEMO.
Nunca crashea si faltan credenciales: degradación elegante.
"""
import os
import secrets


def _env(nombre: str, defecto: str = "") -> str:
    return os.getenv(nombre, defecto).strip()


# Modo de aplicación: "tracy" activa el módulo Tracy; ausente/"finanzas" = app original
APP_MODE = _env("APP_MODE", "finanzas").lower()

# Clave de acceso a la landing pública (default shell-safe Tracy310, ADENDA v2 §D)
LANDING_PASSWORD = _env("LANDING_PASSWORD", "Tracy310")

# Token para proteger los endpoints de cron internos.
# Si no se define, se genera uno aleatorio al arrancar (nunca queda vacío).
_cron_token_env = _env("CRON_TOKEN", "")
CRON_TOKEN = _cron_token_env if _cron_token_env else secrets.token_urlsafe(32)

# Secret para validar que los webhooks vienen de Green API y no de terceros.
WEBHOOK_SECRET = _env("WEBHOOK_SECRET", "")

# WhatsApp (Green API) — número emisor de Tracy
WHATSAPP_SENDER = _env("WHATSAPP_SENDER", "573126593121")

# URL pública base (para los enlaces a la página de reporte)
PUBLIC_BASE_URL = _env("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")

# Proveedores activos (coma-separados)
PROVEEDORES_VUELOS = [p.strip() for p in _env("PROVEEDORES_VUELOS", "travelpayouts").split(",") if p.strip()]

# Credenciales opcionales
TRAVELPAYOUTS_TOKEN = _env("TRAVELPAYOUTS_TOKEN", "")
TRAVELPAYOUTS_MARKER = _env("TRAVELPAYOUTS_MARKER", "")

# Moneda por defecto
MONEDA_DEFECTO = _env("MONEDA_DEFECTO", "COP")

# Tiempo de vida INTERNO de los reportes (horas). Al usuario le mostramos "48 h",
# pero conservamos/borramos a las 72 h (colchón de gracia).
try:
    REPORTE_TTL_HORAS = int(_env("REPORTE_TTL_HORAS", "72"))
except ValueError:
    REPORTE_TTL_HORAS = 72


def es_modo_tracy() -> bool:
    return APP_MODE == "tracy"
