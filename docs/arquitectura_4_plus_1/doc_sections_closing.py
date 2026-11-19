"""Secciones de cierre (13 a 19) del Documento 4+1 de SAJONA Núcleo PWA."""

from docx import Document

from doc_helpers import add_bullets, add_bw_table, add_p


def populate_closing_sections(doc: Document):
    # =========================================================================
    # SECCION 13 — ESTRATEGIA OFFLINE-FIRST Y CONSISTENCIA CAUSAL
    # =========================================================================
    doc.add_heading("13. Estrategia Offline-First y Consistencia Causal", level=1)
    add_p(
        doc,
        "La operación agrícola de SAJONA ADE en cubículos de propagación y casas malla requiere "
        "autonomía total frente a interrupciones de cobertura celular o Wi-Fi. SAJONA Núcleo "
        "implementa un motor Offline-First determinista sustentado en cuatro pilares técnicos:",
    )
    add_bullets(
        doc,
        [
            (
                "Service Worker injectManifest (src/sw.ts):",
                "Workbox pre-almacena en caché local 14 recursos esenciales del shell PWA "
                "(2090.07 KiB) y aplica estrategia Network-First con respaldo offline para "
                "navegación SPA, garantizando reapertura instantánea sin red.",
            ),
            (
                "IndexedDB Transaccional (Dexie 4 — sajona_core_db):",
                "Persiste catálogos, variedades, ubicaciones, propagaciones, bloques y unidades "
                "de planta madre, extracciones CV-09, transplantes a bolsa, revisiones CV-05, "
                "perfiles de sesión en ventana de gracia, cola outbox_mutations y conflictos "
                "sync_conflicts.",
            ),
            (
                "Cola Causal Secuencial (seq) e Idempotencia:",
                "Cada escritura offline recibe un client_mutation_id (UUIDv4) y un entero "
                "monótono seq almacenado en outbox_mutations. Al reconectar, SyncEngine invoca "
                "POST /api/v1/sync/push enviando el lote ordenado causalmente para permitir "
                "cadenas padre -> extracción -> hijo dentro de una única desconexión.",
            ),
            (
                "Supresión Selectiva de Efectos Secundarios y SyncCenterModal:",
                "Cuando source='OFFLINE_SYNC', el servidor omite la generación automática del "
                "lote hijo de extracción y la reescritura de unidades (evitando colisión de "
                "versión contra las mutaciones ya encoladas por el cliente), mientras sincroniza "
                "el estado de propagación tras trasplante sin emitir doble mutación desde campo. "
                "Cualquier divergencia HTTP 409 pasa a sync_conflicts para resolución manual "
                "comparativa en SyncCenterModal.",
            ),
        ],
    )

    # =========================================================================
    # SECCION 14 — SEGURIDAD, AUTENTICACION Y AUDITORIA
    # =========================================================================
    doc.add_heading("14. Seguridad, Autenticación y Auditoría", level=1)
    add_p(
        doc,
        "El modelo de seguridad adopta controles alineados con OWASP ASVS nivel 2 adaptados a "
        "escenarios móviles desconectados:",
    )
    add_bullets(
        doc,
        [
            (
                "Cifrado de Credenciales (Argon2id):",
                "Las contraseñas en PostgreSQL se almacenan mediante hash Argon2id (memoria "
                "configurable y sal única por usuario), corrigiendo el defecto heredado VARCHAR(20) "
                "del esquema histórico.",
            ),
            (
                "Tokens Duales y Mutex de Renovación:",
                "Access Token JWT HS256 de vida corta (15 minutos en memoria) combinado con "
                "Refresh Token opaco rotatorio de un solo uso en cookie HttpOnly, SameSite=Lax "
                "y atributo Secure sobre HTTPS. El cliente serializa renovaciones concurrentes "
                "mediante un mutex único para prevenir carreras de revocación.",
            ),
            (
                "Cero Secretos Locales en Offline:",
                "IndexedDB conserva únicamente el perfil público (usuario, correo, rol y nombre) "
                "junto con el límite temporal offline_grace_until; jamás se almacenan contraseñas, "
                "hashes ni Refresh Tokens en almacenamiento accesible vía JavaScript.",
            ),
            (
                "Control RBAC y Bitácora Dual Append-Only:",
                "Cuatro roles diferenciados (ADMIN, JEFE_PROYECTO, OPERARIO, CONSULTA) protegen "
                "todas las rutas REST y acciones en UI. Cada creación, actualización, borrado "
                "lógico, inicio de sesión y conflicto queda trazado con X-Correlation-Id en la "
                "tabla auditoria_eventos y en registros rotativos JSONL.",
            ),
        ],
    )

    # =========================================================================
    # SECCION 15 — DECISIONES ARQUITECTONICAS (ADRs)
    # =========================================================================
    doc.add_heading("15. Decisiones Arquitectónicas (ADRs)", level=1)
    add_p(
        doc,
        "Las decisiones estructurales que rigen a SAJONA Núcleo se documentaron formalmente bajo "
        "plantilla ADR en el repositorio del proyecto y se sintetizan en la Tabla 4.",
    )
    add_bw_table(
        doc,
        ["ID ADR", "Título de la Decisión", "Decisión Adoptada", "Impacto / Trade-off"],
        [
            [
                "ADR-001",
                "Alcance Nuclear Módulos 1–3 + Dashboard y Corrección Relacional",
                "Concentrar la ingeniería en Propagación, Planta Madre y Transplante a Bolsa + Dashboard, con esquema UUIDv4 de 14 tablas sin FK invertida.",
                "Profundidad total en reglas biológicas (RN-01..RN-06) y trazabilidad bidireccional padre -> hijo offline.",
            ],
            [
                "ADR-002",
                "PWA Mobile-First y Offline-First con Orden Causal",
                "Evolucionar el sistema web tradicional hacia PWA con Workbox injectManifest, Dexie 4 y cola outbox_mutations ordenada por seq.",
                "Operación continua sin conectividad en invernaderos; introduce gestión explícita de conflictos HTTP 409 en UI.",
            ],
            [
                "ADR-003",
                "Monolito Modular en 4 Capas y Reglas Espejo",
                "Backend Python 3.12 / FastAPI separado en domain, application, infrastructure y presentation validado con import-linter.",
                "Cero latencia entre módulos, p95 local < 10 ms y reglas puras espejo en TS (calculations.ts) y Python (rules.py).",
            ],
            [
                "ADR-004",
                "Despliegue Aislado Docker y Túnel HTTPS TLS 1.3",
                "5 contenedores dedicados (db, backend, backup, proxy no-root 127.0.0.1:8089, túnel cloudflared) con red backend-net internal: true.",
                "Aislamiento completo frente a despliegues previos y origen seguro HTTPS requerido por Service Workers PWA.",
            ],
            [
                "ADR-005",
                "Sesión Híbrida Online/Offline, RBAC y Bitácora Dual",
                "Argon2id + JWT 15 min + Refresh HttpOnly rotatorio + ventana de gracia offline sin secretos locales + auditoría PostgreSQL/JSONL.",
                "Cumplimiento OWASP ASVS y continuidad operativa en campo sin exigir re-login online tras cada apertura.",
            ],
        ],
        col_widths=[0.75, 1.55, 2.35, 2.0],
        caption="Tabla 4. Registro de Decisiones Arquitectónicas (ADR-001 a ADR-005).",
    )

    # =========================================================================
    # SECCION 16 — ESTRATEGIA DE PRUEBAS Y VALIDACION REAL
    # =========================================================================
    doc.add_heading("16. Estrategia de Pruebas y Validación Real", level=1)
    add_p(
        doc,
        "La verificación integral combinó análisis estático estricto, pruebas unitarias sobre "
        "invariantes matemáticos puros, pruebas de integración API con SQLAlchemy asíncrono, "
        "pruebas unitarias Offline-First en cliente y validación End-to-End con navegador real "
        "contra el entorno HTTPS desplegado en VPS (incluyendo simulación real de desconexión "
        "y reconexión de red). La Tabla 5 resume los resultados exactos obtenidos tras el último "
        "ajuste de código e interfaz.",
    )
    add_bw_table(
        doc,
        ["Nivel / Herramienta", "Cobertura y Alcance Real", "Resultado Observado Exacto"],
        [
            [
                "Lint y Complejidad Backend (ruff check)",
                "Reglas de estilo, complejidad ciclomática <= 10 y FastAPI B008 en src/ y tests/",
                "All checks passed! (0 advertencias ni errores)",
            ],
            [
                "Tipado Estricto Backend (mypy src)",
                "Verificación estática de tipos estricta sobre la totalidad de módulos Python",
                "Success: no issues found in 26 source files",
            ],
            [
                "Fronteras de Capas (import-linter)",
                "Contrato de capas (4 capas) y dominio puro sin dependencias externas",
                "45 archivos, 138 deps | Contracts: 2 kept, 0 broken",
            ],
            [
                "Suite Backend (pytest --cov)",
                "Pruebas unitarias RN-01..RN-06 + integración API, RBAC, sync causal y 409",
                "13 passed in 5.99s | Cobertura 96% global (100% en domain/ y routers.py)",
            ],
            [
                "Tipado y Unitarias PWA (tsc + Vitest)",
                "Reglas TS espejo, KPIs Dashboard local, IndexedDB Dexie outbox y conflictos",
                "tsc exit 0 | Test Files 1 passed, Tests 3 passed in 453 ms",
            ],
            [
                "Seguridad Dependencias PWA (npm audit)",
                "Auditoría de dependencias de producción (--omit=dev --audit-level=high)",
                "0 vulnerabilidades críticas o altas (2 moderadas transitivas en uuid/exceljs)",
            ],
            [
                "E2E HTTPS en VPS (Playwright + Axe)",
                "Login, Módulos 1–3 + Dashboard offline, reapertura, auto-sync, 409 y WCAG",
                "1 passed (12.2s) contra https://williams-wanted-genuine-productions.trycloudflare.com (0 violaciones críticas WCAG)",
            ],
            [
                "Benchmark HTTP GET /api/v1/dashboard/summary",
                "50 peticiones autenticadas en origen VPS y 20 sobre túnel público HTTPS",
                "Origen (50 req): errors=0, p50=6.17 ms, p95=7.41 ms, max=62.18 ms | HTTPS (20 req): errors=0, p50=264.13 ms, p95=315.18 ms",
            ],
            [
                "Backup y Restore PostgreSQL 16",
                "Generación backup.sh + validación de integridad SQL restore_test.sh",
                "Archivo sajona_core_20261119T031504Z.sql.gz | OK: 14 sentencias CREATE TABLE verificadas",
            ],
        ],
        col_widths=[1.75, 2.35, 2.55],
        caption="Tabla 5. Resultados consolidados de pruebas y validación sobre software real.",
    )

    # =========================================================================
    # SECCION 17 — RENDIMIENTO, ESCALABILIDAD Y MANTENIBILIDAD
    # =========================================================================
    doc.add_heading("17. Rendimiento, Escalabilidad y Mantenibilidad", level=1)
    add_p(
        doc,
        "En optimización de carga móvil, Vite 6.0.3 (1852 módulos compilados en 7.24 s) produce "
        "un paquete inicial liviano compuesto por el chunk principal JavaScript "
        "index-BvLiDP2f.js de 354.48 kB (104.79 kB transferidos vía gzip) y la hoja de estilos "
        "CSS de 20.74 kB (4.43 kB gzip). Las librerías pesadas de generación de reportes "
        "(exceljs.min de 938.61 kB y jspdf.es.min de 390.44 kB) se cargan bajo demanda mediante "
        "dynamic import(), evitando penalizar el arranque en dispositivos rurales de gama media.",
    )
    add_p(
        doc,
        "En servidor, el procesamiento asíncrono sobre FastAPI y SQLAlchemy 2 alcanza una "
        "mediana de 6.17 ms y un percentil 95 de 7.41 ms sobre el proxy Nginx de la VPS "
        "(315.18 ms p95 de extremo a extremo incluyendo salto TLS externo vía túnel), holgadamente "
        "por debajo del umbral ASR-02 (<= 500 ms). Desde el punto de vista de mantenibilidad, "
        "la separación estricta en 4 capas verificada automáticamente en CI/CD permite añadir "
        "módulos subsecuentes (Campo, Secado, Curado) agregando nuevas entidades y routers sin "
        "alterar la estabilidad de los Módulos 1–3 ni del núcleo de sincronización.",
    )

    # =========================================================================
    # SECCION 18 — CONCLUSIONES
    # =========================================================================
    doc.add_heading("18. Conclusiones", level=1)
    add_p(
        doc,
        "SAJONA Núcleo materializa una evolución arquitectónica integral para SAJONA ADE, "
        "transformando un legado con defectos de esquema y ausencia de soporte sin red en una PWA "
        "Offline-First probada en entorno real (TRL-6). Al focalizar la implementación en los "
        "tres primeros módulos productivos (Propagación, Planta Madre con matriz CV-09 y "
        "Transplante a Bolsa con alertas >20% y revisiones CV-05) más un Dashboard Analítico "
        "completo con trazabilidad genética 360°, se logró exactitud matemática del 100% en las "
        "reglas de dominio y sincronización causal verificada sin conectividad.",
    )
    add_p(
        doc,
        "La documentación mediante el Modelo 4+1 de Philippe Kruchten aplicado de forma granular "
        "por cada módulo (31 diagramas UML/C4 monocromáticos en total) dota a la Universidad "
        "Surcolombiana y a SAJONA ADE de un plano verificable entre código fuente, contrato "
        "REST, esquema PostgreSQL/IndexedDB y topología de despliegue en contenedores aislados.",
    )

    # =========================================================================
    # SECCION 19 — REFERENCIAS BIBLIOGRAFICAS Y ANEXOS TECNICOS
    # =========================================================================
    doc.add_heading("19. Referencias Bibliográficas y Anexos Técnicos", level=1)
    add_bullets(
        doc,
        [
            (
                "Kruchten, P. (1995):",
                "The 4+1 View Model of Architecture. IEEE Software, 12(6), 42–50.",
            ),
            (
                "Fielding, R. T. (2000):",
                "Architectural Styles and the Design of Network-based Software Architectures "
                "(Doctoral dissertation, University of California, Irvine).",
            ),
            (
                "Kleppmann, M. (2017):",
                "Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, "
                "and Maintainable Systems. O'Reilly Media.",
            ),
            (
                "OWASP Foundation (2023):",
                "Application Security Verification Standard (ASVS) v4.0.3 y Password Storage "
                "Cheat Sheet (Argon2id, RFC 9106).",
            ),
            (
                "Artefactos Internos SAJONA ADE:",
                "Mockups_SAJONA.pdf (Secciones 3.1–3.3), modelo_pdf_sajona.pdf y Documento de "
                "Auditoria e Ingenieria Inversa (docs/01_auditoria/AUDITORIA_INGENIERIA_INVERSA.md).",
            ),
        ],
    )
    add_bw_table(
        doc,
        ["Método y Ruta REST (/api/v1/...)", "Propósito Funcional", "Autenticación y RBAC"],
        [
            ["GET /health | GET /api/v1/health", "Sonda de disponibilidad API y SELECT 1 en PostgreSQL.", "Público"],
            ["POST /api/v1/auth/login", "Emisión de JWT (15 min) + cookie HttpOnly Refresh opaco.", "Credenciales Argon2id"],
            ["POST /api/v1/auth/refresh", "Rotación atómica de Refresh Token de un solo uso.", "Cookie HttpOnly"],
            ["POST /api/v1/auth/logout | GET /me", "Revocación de sesión o lectura de perfil vigente.", "Bearer JWT"],
            ["POST /api/v1/auth/password-reset/*", "Solicitud y confirmación de restablecimiento de clave.", "Rate limit + token único"],
            ["GET /api/v1/dashboard/summary", "KPIs Módulos 1–3, embudo y series por filtros analíticos.", "Todos los roles autenticados"],
            ["GET /api/v1/lotes/{id}/trazabilidad", "Árbol 360° Propagación -> Madres -> Hijos -> Bolsa -> CV-05.", "Todos los roles autenticados"],
            ["GET /api/v1/entities/{entity_type}", "Listado incremental por entidad o filtro de lote/madre.", "Todos los roles autenticados"],
            ["POST /api/v1/entities/{entity_type}", "Alta transaccional con ejecución de reglas RN-01..RN-06.", "ADMIN, JEFE, OPERARIO"],
            ["PUT /api/v1/entities/{entity_type}/{id}", "Edición con control optimista If-Match-Version / 409.", "ADMIN, JEFE (y parcial OPERARIO)"],
            ["DELETE /api/v1/entities/{entity_type}/{id}", "Borrado lógico (deleted_at) auditado por versión.", "ADMIN, JEFE_PROYECTO"],
            ["POST /api/v1/sync/push | GET /sync/pull", "Replay causal idempotente (seq) y descarga delta (since).", "Roles de escritura / autenticados"],
            ["GET|POST|PATCH /api/v1/admin/users*", "Administración de usuarios, roles y activación.", "Exclusivo ADMIN (403 resto)"],
            ["GET /api/v1/admin/audit-logs", "Consulta de eventos append-only con X-Correlation-Id.", "Exclusivo ADMIN (403 resto)"],
        ],
        col_widths=[2.15, 2.85, 1.65],
        caption="Tabla 6. Contratos HTTP REST v1 implementados y verificados en OpenAPI.",
    )
