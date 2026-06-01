# Tracy Travel

Tracy Travel es un rastreador de precios de **vuelos** y **hospedaje** con cara
de asistente. Desde una landing pública el usuario elige origen, destino, fechas
y modo de seguimiento; Tracy confirma la suscripción por WhatsApp (opt-in),
revisa precios cada día y envía un reporte con las mejores ofertas, enlazando a
una página de reporte que se autodestruye a las 48 horas.

Funciona en **MODO DEMO** sin ninguna credencial: los proveedores degradan a
datos de ejemplo (mock) y los envíos de WhatsApp se registran en consola.

## Componentes

- **Landing** (`/`): formulario público con catálogo de orígenes/destinos.
- **API** (`/api/tracy`): precheck de temporada y creación de consultas.
- **Webhook** (`/api/webhook/whatsapp`): opt-in por código y `CANCELAR` (Green API).
- **Crons** (`/api/internal/cron/{revisar,notificar,purga}`): protegidos por
  header `X-Cron-Token`. También se ejecutan vía APScheduler en local.
- **Reporte** (`/{numero}`): página server-side del último reporte vigente del
  número, con `noindex`.
- **Proveedores**: Travelpayouts, Hotellook, Amadeus y mock (demo).

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

- Los proveedores de vuelos/hoteles devuelven datos mock.
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
| `PROVEEDORES_VUELOS` / `PROVEEDORES_HOTELES` | Proveedores activos. |
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
