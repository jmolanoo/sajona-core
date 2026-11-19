# Guía de Instalación, Despliegue y Mantenimiento — SAJONA Núcleo PWA

## 1. Arquitectura de Despliegue y Aislamiento

El proyecto **SAJONA Núcleo** (Módulos 1–3: Propagación, Planta Madre y Transplante a Bolsa + Dashboard Analítico) se despliega de forma totalmente independiente mediante [`docker-compose.yml`](../../docker-compose.yml), sin interferir con otros servicios de la VPS:

| Servicio | Imagen Base Fija | Usuario | Redes Docker | Puertos / Volúmenes |
| :--- | :--- | :--- | :--- | :--- |
| `sajona-core-db` | `postgres:16.6-alpine` | `postgres` | `sajona-core-backend-net` (`internal: true`) | Volumen `sajona_core_pgdata` (PostgreSQL 16). |
| `sajona-core-backend` | `python:3.12.7-slim` | `sajona` (`UID 1001`) | `backend-net` + `frontend-net` | API REST FastAPI `:8000`, volumen `sajona_core_audit_logs`. |
| `sajona-core-backup` | `postgres:16.6-alpine` | `postgres` | `sajona-core-backend-net` (`internal: true`) | Respaldo automático cada 24h (retención 14), volumen `sajona_core_backups`. |
| `sajona-core-proxy` | `nginx:1.27.3-alpine` | `nginx` (`:8080`) | `sajona-core-frontend-net` | Enlace loopback `127.0.0.1:8089:8080`, sirve App Shell PWA y proxy `/api/*`. |
| `sajona-core-tunnel` | `cloudflare/cloudflared:2026.11.1` | `nonroot` | `sajona-core-frontend-net` | Túnel saliente HTTPS TLS 1.3 hacia Edge Cloudflare. |

---

## 2. Instalación Desde Cero

1. **Preparar variables de entorno:**
   ```bash
   cp .env.example .env
   ```
   Asignar valores criptográficos reales para `POSTGRES_PASSWORD`, `DATABASE_URL` y `JWT_SECRET_KEY` (mínimo 32 caracteres). Nunca versionar `.env`.

2. **Construir y levantar contenedores:**
   ```bash
   docker compose up -d --build
   ```

3. **Verificar salud y URL HTTPS:**
   ```bash
   docker ps --format "table {{.Names}}\t{{.Status}}"
   curl -fsS http://127.0.0.1:8089/health
   docker logs sajona-core-tunnel 2>&1 | grep -oE "https://[a-zA-Z0-9.-]+\.trycloudflare\.com" | tail -n 1
   ```

---

## 3. Reglas PWA y Seguridad en Nginx

El archivo [`docker/proxy/nginx.conf`](../../docker/proxy/nginx.conf) configura:
- `location = /sw.js` con `Cache-Control: no-cache, no-store, must-revalidate` para actualización inmediata del Service Worker Workbox.
- `location = /manifest.webmanifest` con tipo `application/manifest+json`.
- `location /assets/` con caché inmutable de 1 año (`immutable`).
- Reenvío de `X-Forwarded-Proto $http_x_forwarded_proto` hacia FastAPI para emisión de cookies `HttpOnly; SameSite=Lax; Secure` sobre HTTPS.
- Cabeceras `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy` y `Permissions-Policy`.

---

## 4. Copias de Seguridad, Restauración y Actualizaciones

- **Respaldo manual inmediato y verificación DDL:**
  ```bash
  docker exec sajona-core-backup /usr/local/bin/backup.sh
  docker exec sajona-core-backup /usr/local/bin/restore_test.sh
  ```
- **Restauración desde respaldo comprimido:**
  ```bash
  docker compose stop sajona-core-backend
  docker exec -i sajona-core-db sh -c 'gunzip -c | psql -U sajona_core -d sajona_core' < <archivo.sql.gz>
  docker compose start sajona-core-backend
  ```
- **Inspección de bitácora append-only:**
  ```bash
  docker exec sajona-core-backend tail -n 50 /app/audit_logs/audit.jsonl
  ```
- **Actualización sin pérdida de datos:** los volúmenes nombrados `sajona_core_pgdata`, `sajona_core_audit_logs` y `sajona_core_backups` persisten ante `docker compose up -d --build`.
