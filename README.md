# SAJONA Núcleo PWA — Módulos 1–3 + Dashboard Analítico Offline-First

Implementación focalizada y profunda del núcleo productivo de **SAJONA ADE (NIT 900905923)**: aplicación web progresiva (**PWA Mobile-First y Offline-First**) junto con su documentación integral de arquitectura bajo el **Modelo de Vistas 4+1 de Philippe Kruchten** replicado para **cada uno de los cuatro módulos**.

- **Institución Académica:** Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software
- **Docente Supervisor y Product Owner:** Ing. Eduardo Martínez Vidal
- **Equipo de Ingeniería (Co-Desarrollo Horizontal):** Danna Nerieth Palencia | Jairo Molano Salgado
- **PWA Desplegada (HTTPS TLS 1.3):** `https://williams-wanted-genuine-productions.trycloudflare.com`
- **Origen Local VPS:** `http://127.0.0.1:8089` (aislado de entornos previos)

---

## 1. Alcance Funcional (Módulos 1–3 + Módulo 4 Dashboard)

| Módulo | Capacidades Clave e Invariantes de Dominio |
|---|---|
| **Módulo 1: Propagación** | Alta por lote (`ESQUEJE`, `SEMILLA`, `IN_VITRO`), validación de proveedor obligatorio en compras (`RN-01`), control de bajas tempranas y transición automática de estado (`SIEMBRA` -> `EN_TRANSPLANTE` -> `FINALIZADO`). |
| **Módulo 2: Planta Madre y Extracciones** | Bloques madre con unidades numeradas individuales `#1..#N` (`CV-02`/`CV-03`), matriz `CV-09` de extracción de esquejes/semillas por unidad sin exceder unidades activas (`RN-05`) y derivación automática de lotes hijos hacia Propagación. |
| **Módulo 3: Transplante a Bolsa y Revisión Periódica** | Balance de conservación `saldo_antes >= plantadas_buenas + plantadas_malas` (`CV-08`), cálculo exacto de porcentaje de supervivencia y merma con alerta visual y analítica cuando `merma > 20%` (`RN-02`), promoción a Planta Madre y seguimiento histórico mediante revisiones periódicas `CV-05` (`RN-04`). |
| **Módulo 4: Dashboard Analítico Offline-First** | KPIs en tiempo real calculados indistintamente en servidor (PostgreSQL) o en modo desconectado (IndexedDB vía `dashboardStats.ts`), filtros reactivos (`fecha_inicio`, `fecha_fin`, `variedad_id`, `tipo_propagacion`), embudo SVG de conversión agronómica, comparativa de supervivencia/merma por trasplante, modal **Traza Genética 360° (`LotTraceModal`)** y exportación offline a **Excel (.xlsx)**, **TXT** y **PDF**. |

---

## 2. Arquitectura Técnica

### Backend — Monolito Modular en 4 Capas Estrictas (`backend/src/sajona_core/`)
1. **`domain/`:** Entidades inmutables/dataclases, enumeraciones, excepciones y reglas puras agronómicas (`rules.py`) con **0 dependencias externas** (verificado con `import-linter`).
2. **`application/`:** Casos de uso (`AuthService`, `ProduccionService`, `SyncService`), contratos `Protocol` (`ports.py`), RBAC y DTOs Pydantic.
3. **`infrastructure/`:** Persistencia asíncrona SQLAlchemy 2.0 sobre PostgreSQL 16.6 (14 tablas con UUIDv4 y versionamiento optimista), hashing **Argon2id**, JWT HS256 (15 min) + Refresh opaco rotatorio en cookie `HttpOnly` y bitácora dual (BD + JSONL).
4. **`presentation/`:** Enrutadores FastAPI (`20` operaciones OpenAPI registradas), encabezados `If-Match-Version`, `X-Correlation-Id` y manejo unificado de conflictos `409 Conflict`.

### Frontend — PWA Mobile-First & Offline-First (`frontend/src/`)
- **Service Worker:** `Workbox injectManifest` (`src/sw.ts`) con estrategia precache de activos (`14` entradas, `2090.07 KiB`), actualización en segundo plano y respaldo offline completo de la SPA.
- **Almacenamiento Local y Sync Causal:** IndexedDB mediante **Dexie 4** (`sajona_core_db`) con cola transaccional `outbox_mutations` ordenada secuencialmente (`seq`), clave de idempotencia `client_mutation_id` y resolución comparativa de conflictos mediante `SyncCenterModal`.

---

## 3. Credenciales de Demostración

| Rol | Usuario | Correo | Contraseña |
|---|---|---|---|
| Administrador | `admin` | `admin@sajona.co` | `SajonaAdmin2026!` |
| Jefe de Proyecto | `jefe` | `jefe@sajona.co` | `SajonaJefe2026!` |
| Operario de Campo | `operario` | `operario@sajona.co` | `SajonaCampo2026!` |
| Auditor / Consulta | `consulta` | `consulta@sajona.co` | `SajonaAudit2026!` |

---

## 4. Documentación Entregable en el Repositorio

- **Auditoría e Ingeniería Inversa:** [`docs/01_auditoria/AUDITORIA_INGENIERIA_INVERSA.md`](./docs/01_auditoria/AUDITORIA_INGENIERIA_INVERSA.md)
- **Registros de Decisión Arquitectónica (ADRs):** [`docs/adr/`](./docs/adr/) (`ADR-001` a `ADR-005`)
- **Documento de Arquitectura 4+1 (31 Diagramas Monocromáticos B&N — Vista Completa por Módulo):**
  - Editable Word: [`docs/arquitectura_4_plus_1/SAJONA_Core_Documento_Arquitectura_4_mas_1.docx`](./docs/arquitectura_4_plus_1/SAJONA_Core_Documento_Arquitectura_4_mas_1.docx)
  - PDF Compilado: [`docs/arquitectura_4_plus_1/SAJONA_Core_Documento_Arquitectura_4_mas_1.pdf`](./docs/arquitectura_4_plus_1/SAJONA_Core_Documento_Arquitectura_4_mas_1.pdf)
- **Diagramas UML / C4 Fuente + PNG (31 PNGs B&N):** [`docs/diagrams/`](./docs/diagrams/)
- **Informe de Pruebas y Capturas Reales:** [`docs/pruebas/INFORME_EVIDENCIAS_PRUEBAS.md`](./docs/pruebas/INFORME_EVIDENCIAS_PRUEBAS.md)
- **Guía de Despliegue y Mantenimiento VPS:** [`docs/despliegue/GUIA_INSTALACION_DESPLIEGUE_MANTENIMIENTO.md`](./docs/despliegue/GUIA_INSTALACION_DESPLIEGUE_MANTENIMIENTO.md)

---

## 5. Ejecución Local Rápida

```bash
# Levantar pila completa aislada (PostgreSQL, Backend, Backup, Nginx Proxy, Túnel HTTPS)
cp .env.example .env
docker compose up -d --build

# Ejecutar calidad y pruebas del backend
cd backend && .venv/bin/ruff check src tests && .venv/bin/mypy src && .venv/bin/lint-imports && .venv/bin/pytest -v --cov=sajona_core

# Ejecutar pruebas frontend y compilación PWA
cd ../frontend && npx tsc --noEmit && npm test && npm run build
```
