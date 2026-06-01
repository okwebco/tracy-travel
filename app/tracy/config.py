"""Configuración central de Tracy Travel.

Todo lee de variables de entorno con valores por defecto seguros para MODO DEMO.
Nunca crashea si faltan credenciales: degradación elegante.
"""
import os


def _env(nombre: str, defecto: str = "") -> str:
    return os.getenv(nombre, defecto).strip()


# Modo de aplicación: "tracy" activa el módulo Tracy; ausente/"finanzas" = app original
APP_MODE = _env("APP_MODE", "finanzas").lower()

# Clave de acceso a la landing pública (default shell-safe Tracy310, ADENDA v2 §D)
LANDING_PASSWORD = _env("LANDING_PASSWORD", "Tracy310")

# Token para proteger los endpoints de cron internos
CRON_TOKEN = _env("CRON_TOKEN", "")

# WhatsApp (Green API) — número emisor de Tracy
WHATSAPP_SENDER = _env("WHATSAPP_SENDER", "573126593121")

# URL pública base (para los enlaces a la página de reporte)
PUBLIC_BASE_URL = _env("PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/")

# Proveedores activos (coma-separados)
PROVEEDORES_VUELOS = [p.strip() for p in _env("PROVEEDORES_VUELOS", "travelpayouts,amadeus").split(",") if p.strip()]
PROVEEDORES_HOTELES = [p.strip() for p in _env("PROVEEDORES_HOTELES", "hotellook,amadeus").split(",") if p.strip()]

# Credenciales opcionales
TRAVELPAYOUTS_TOKEN = _env("TRAVELPAYOUTS_TOKEN", "")
TRAVELPAYOUTS_MARKER = _env("TRAVELPAYOUTS_MARKER", "")
AMADEUS_CLIENT_ID = _env("AMADEUS_CLIENT_ID", "")
AMADEUS_CLIENT_SECRET = _env("AMADEUS_CLIENT_SECRET", "")
AMADEUS_BASE = _env("AMADEUS_BASE", "https://test.api.amadeus.com").rstrip("/")

# Moneda por defecto
MONEDA_DEFECTO = _env("MONEDA_DEFECTO", "COP")

# Tiempo de vida de los reportes (horas)
try:
    REPORTE_TTL_HORAS = int(_env("REPORTE_TTL_HORAS", "48"))
except ValueError:
    REPORTE_TTL_HORAS = 48


def es_modo_tracy() -> bool:
    return APP_MODE == "tracy"
