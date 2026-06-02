# Tracy Travel

Tracy Travel es un rastreador de precios de **vuelos** con cara
de asistente. Desde una landing pública el usuario elige origen, destino, fechas
(tipo de viaje: ida / regreso / ida y regreso) y modo de seguimiento; Tracy
confirma la suscripción por WhatsApp (opt-in), revisa precios cada día y envía
un reporte con las mejores ofertas, enlazando a una página de reporte que se
autodestruye a las 48 horas.

Funciona en **MODO DEMO** sin ninguna credencial: los proveedores degradan a
datos de ejemplo (mock) y los envíos de WhatsApp se registran en consola.

## Componentes

- **Landing** (`/`): formulario público mobile-first. Pide la clave de acceso
  (validada en `POST /api/tracy/acceso`) antes de mostrar el formulario.
- **API** (`/api/tracy`): `acceso` (valida clave), `catalogo` (país→aeropuertos),
  `precheck` (temporada) y `consultas` (creación).
- **Webhook** (`/api/webhook/whatsapp`): opt-in por código y `CANCELAR` (Green API).
  Al activar una consulta de Rastreo o Seguimiento se genera y envía el primer
  reporte de inmediato (entrega #1).

### Modos de consulta (el usuario elige uno)

- **Consulta rápida** (`rapida`): 1 búsqueda inmediata, una sola vez.
- **Rastreo** (`rastreo`): casillas acumulativas `{1,3,5,8,15,30}` días; informa
  en cada día marcado (día 1 = inmediato). Marcar un día auto-marca los inferiores.
- **Seguimiento** (`seguimiento`): cantidad `{2..6}` × frecuencia cada
  `{2,3,5,7,15,30}` días; el #1 es inmediato y luego cada N días.
- **Crons** (`/api/internal/cron/{revisar,notificar,purga}`): protegidos por
  header `X-Cron-Token`. También se ejecutan vía APScheduler en local.
- **Reporte** (`/{numero}`): página server-side del último reporte vigente del
  número, con `noindex`.
- **Proveedores** (vuelos): Travelpayouts, Amadeus y mock (demo).

## Ejecutar en local

```bash
python -m venv .venv && source .venv/bin/activate   # opcional
pip install -r requirements.txt
cp .env.example .env                                # opcional; sin él corre en DEMO
uvicorn app.main:app --port 8000
```

Abre http://localhost:8000 para la landing y http://localhost:8000/health para
el healthcheck.

### Modo demo (sin credenciales)

Si no configuras `GREEN_API_*` ni tokens de proveedores, Tracy sigue funcionando:

- Los proveedores de vuelos devuelven datos mock.
- Los mensajes de WhatsApp no se envían: se imprimen en consola.
- Si `CRON_TOKEN` está vacío, los endpoints de cron se permiten sin token.

## Variables de entorno

Ver [`.env.example`](.env.example). Las principales:

| Variable | Descripción |
| --- | --- |
| `DATABASE_URL` | SQLite local por defecto (`sqlite:///./tracy.db`). |
| `GREEN_API_INSTANCE_ID` / `GREEN_API_TOKEN` | Credenciales de Green API. |
| `WHATSAPP_SENDER` | Número emisor de Tracy. |
| `LANDING_PASSWORD` | Clave de acceso para crear consultas. |
| `PUBLIC_BASE_URL` | Base de los enlaces de reporte. |
| `CRON_TOKEN` | Protege los crons internos. |
| `PROVEEDORES_VUELOS` | Proveedores de vuelos activos. |
| `TRAVELPAYOUTS_TOKEN` / `TRAVELPAYOUTS_MARKER` | Travelpayouts (marker 734957). |
| `AMADEUS_CLIENT_ID` / `AMADEUS_CLIENT_SECRET` / `AMADEUS_BASE` | Amadeus Self-Service. |
| `MONEDA_DEFECTO` | Moneda por defecto (`COP`). |
| `REPORTE_TTL_HORAS` | Vida de los reportes (48 h). |

## Despliegue con Docker

```bash
docker build -t tracy-travel .
docker run -p 8080:8080 --env-file .env tracy-travel
```

El contenedor expone el puerto `8080` (`uvicorn app.main:app`).
