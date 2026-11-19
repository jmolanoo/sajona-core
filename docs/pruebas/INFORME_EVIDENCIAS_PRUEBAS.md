# Informe de Pruebas, Evidencias Reales y Validación — SAJONA Núcleo PWA

- **Proyecto:** SAJONA Núcleo — Módulos 1–3 + Dashboard Analítico Offline-First
- **Versión:** 1.0 (TRL-6)
- **Empresa Propietaria del Dominio:** SAJONA ADE (NIT 900905923)
- **Institución Académica:** Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software
- **Docente Supervisor y Product Owner:** Ing. Eduardo Martínez Vidal
- **Equipo de Ingeniería (Co-Desarrollo Horizontal):** Danna Nerieth Palencia | Jairo Molano Salgado
- **Entorno Vivo Verificado:** `https://williams-wanted-genuine-productions.trycloudflare.com` (Nginx TLS origin `http://127.0.0.1:8089`)

---

## 1. Resumen Ejecutivo de Validación

Todas las pruebas se ejecutaron después del último ajuste de interfaz y despliegue en contenedores Docker sobre la VPS. Ninguna métrica reportada corresponde a mocks falsos de éxito en producción: la suite backend ejercita lógica de dominio pura y API real sobre SQLAlchemy asíncrono, mientras que las pruebas End-to-End, benchmark de latencia y verificación de respaldos operan directamente contra la pila desplegada (`sajona-core-db`, `sajona-core-backend`, `sajona-core-proxy`, `sajona-core-backup`, `sajona-core-tunnel`).

| Capa / Herramienta | Alcance Verificado | Resultado Observado |
|---|---|---|
| **Ruff (`ruff check src tests`)** | Estilo, complejidad ciclomática (<= 10), lint (`B008`) | `All checks passed!` (0 errores) |
| **Mypy (`mypy src`)** | Chequeo de tipos estricto en 26 archivos fuente | `Success: no issues found in 26 source files` |
| **Import Linter (`lint-imports`)** | 45 archivos, 138 dependencias, 2 contratos de capas | `Contracts: 2 kept, 0 broken.` |
| **Pytest + Coverage** | Reglas puras (RN-01..RN-06), RBAC, auth, sync causal, conflictos | `13 passed in 5.99s` \| Cobertura total **96%** (Dominio **100%**) |
| **TypeScript (`tsc --noEmit`)** | Tipado estricto en cliente PWA React + Dexie + Domain mirror | Compilación limpia (`exit 0`) |
| **Vitest (`offlineCore.test.ts`)** | Reglas TS, KPIs locales del Dashboard, Outbox IndexedDB y conflictos | `1 passed (1)` \| `3 passed (3)` en `453 ms` |
| **Vite + Workbox (`npm run build`)** | Bundle PWA + Service Worker `injectManifest` | `1852` módulos \| Chunk principal `354.48 kB` (`gzip 104.79 kB`) \| SW precache `14` entradas (`2090.07 KiB`) |
| **Auditoría `npm audit --omit=dev --audit-level=high`** | Dependencias de producción PWA | `0` vulnerabilidades altas/críticas (`2` moderadas en `uuid` < 11.1.1 transitivo de `exceljs`) |
| **Playwright E2E + Axe WCAG (HTTPS Vivo)** | Login, flujo offline en Módulos 1–3 + Dashboard, reapertura, auto-sync, conflictos y WCAG | `1 passed (12.2s)` (`11.5s` escenario) contra `https://williams-wanted-genuine-productions.trycloudflare.com` |
| **Benchmark API (`GET /api/v1/dashboard/summary`)** | 50 peticiones autenticadas en origen VPS + 20 en túnel HTTPS | VPS Origen: `errors=0`, `p50=6.17 ms`, `p95=7.41 ms`, `max=62.18 ms`<br>Túnel HTTPS: `errors=0`, `p50=264.13 ms`, `p95=315.18 ms`, `max=414.84 ms` |
| **Backup y Restore (`sajona-core-backup`)** | Respaldo lógico comprimido + validación de esquema SQL | `/backups/sajona_core_20261119T031504Z.sql.gz` \| `OK: 14 sentencias CREATE TABLE verificadas.` |

---

## 2. Detalle de Casos Verificados en Backend (Pytest + Coverage)

```text
tests/integration/test_admin_and_edges.py::test_admin_usuarios_logout_me_y_errores PASSED
tests/integration/test_admin_and_edges.py::test_soft_delete_recalculo_unidad_descartada_y_sync_rechazos PASSED
tests/integration/test_admin_and_edges.py::test_actualizaciones_404_409_y_pull_incremental PASSED
tests/integration/test_api_and_sync.py::test_health_y_openapi_contratos PASSED
tests/integration/test_api_and_sync.py::test_auth_rotacion_refresh_reset_y_rbac PASSED
tests/integration/test_api_and_sync.py::test_ciclo_integral_3_modulos_y_dashboard PASSED
tests/integration/test_api_and_sync.py::test_offline_sync_idempotencia_y_conflictos PASSED
tests/unit/test_domain_rules.py::test_rn01_saldo_y_estado_propagacion PASSED
tests/unit/test_domain_rules.py::test_rn01_propagacion_validaciones_borde PASSED
tests/unit/test_domain_rules.py::test_rn02_transplante_bolsa_calcula_supervivencia_y_alerta_merma PASSED
tests/unit/test_domain_rules.py::test_rn02_transplante_bolsa_rechaza_saldo_cero_o_fechas_invalidas PASSED
tests/unit/test_domain_rules.py::test_rn04_revision_periodica_cv05_conserva_vivas_y_rechaza_bordes PASSED
tests/unit/test_domain_rules.py::test_rn05_extraccion_madre_cv09_exacta_y_bordes PASSED
TOTAL: 1688 stmts, 74 miss, 96% coverage
```

Cobertura en dominio (`src/sajona_core/domain/`): `entities.py` **100%**, `enums.py` **100%**, `exceptions.py` **100%**, `rules.py` **100%**. Presentación (`routers.py`) **100%**.

---

## 3. Prueba End-to-End en Producción (Playwright + Axe WCAG)

Ejecutada mediante `E2E_BASE_URL="https://williams-wanted-genuine-productions.trycloudflare.com" npx playwright test --reporter=list`:
1. Autenticación online contra PostgreSQL con rol `JEFE_PROYECTO` (`jefe`), rotación de sesión y descarga inicial en IndexedDB (`pullIncremental`).
2. Desconexión simulada (`context.setOffline(true)`): visualización inmediata del indicador **Sin conexión** y banner offline.
3. Creación offline de lote en **Módulo 1 (Propagación)** (`LOT-CORE-*`), promoción a **Módulo 2 (Planta Madre)**, registro de extracción **CV-09** (`total_esquejes`, `total_semillas`, lote hijo derivado), registro en **Módulo 3 (Transplante a Bolsa)** con verificación de alerta de **Merma >20%**, y consulta analítica offline en **Módulo 4 (Dashboard)** incluyendo `LotTraceModal`.
4. Recarga y reapertura de la PWA estando offline para verificar persistencia local y continuidad de sesión dentro de ventana de gracia.
5. Reconexión (`context.setOffline(false)`): sincronización automática en orden causal (`seq`), verificación de estado `• Sincronizado`, gestión de conflictos (`SyncCenterModal`) y auditoría de accesibilidad (`@axe-core/playwright`) sin violaciones críticas.

---

## 4. Evidencias Visuales Capturadas sobre la Instancia Viva

| Evidencia | Archivo | Escenario Demostrado |
|---|---|---|
| Login Móvil | [`01_login_mobile.png`](./screenshots/01_login_mobile.png) | Viewport 390×844, formulario accesible y accesos de demostración por rol |
| Dashboard Móvil | [`02_dashboard_mobile.png`](./screenshots/02_dashboard_mobile.png) | Navegación inferior de 4 módulos, filtros analíticos y tarjetas KPI |
| Propagación Offline Móvil | [`03_propagacion_offline_mobile.png`](./screenshots/03_propagacion_offline_mobile.png) | Indicador superior **Sin conexión**, banner Offline-First y tarjetas móviles sin desborde |
| Dashboard Escritorio | [`04_dashboard_desktop.png`](./screenshots/04_dashboard_desktop.png) | Embudo SVG de conversión agronómica, barras de supervivencia/merma y exportación Excel/TXT/PDF |
| Planta Madre Escritorio | [`05_planta_madre_desktop.png`](./screenshots/05_planta_madre_desktop.png) | Unidades numeradas `#15..#18`, selector de estado (`ACTIVA`/`REPOSO`) y traza padre -> hijo (`LOT-2026-033`) |
| Transplante Bolsa Escritorio | [`06_transplante_bolsa_desktop.png`](./screenshots/06_transplante_bolsa_desktop.png) | Tarjetas `TP-LOT30-01` (91.84% supervivencia) y `TP-LOT31-01` (`Merma >20%` alerta 26.67%), cuadrícula `2x2` limpia |

---

## 5. Verificación de Respaldo, Restauración y Contenedores Aislados

```text
[backup] Respaldo generado: /backups/sajona_core_20261119T031504Z.sql.gz
[restore-test] Validando integridad gzip y SQL en /backups/latest.sql.gz...
[restore-test] OK: 14 sentencias CREATE TABLE verificadas.
```

Todos los contenedores (`sajona-core-proxy`, `sajona-core-backend`, `sajona-core-db`, `sajona-core-backup`, `sajona-core-tunnel`) permanecen operando de manera aislada frente al entorno previo `sajona` (`127.0.0.1:8088`).
