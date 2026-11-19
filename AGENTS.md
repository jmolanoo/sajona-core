# Reglas de Arquitectura e Ingeniería — SAJONA Núcleo (Módulos 1–3 + Dashboard)

1. **Alcance Funcional Estricto:** El producto implementa en profundidad el ciclo nuclear definido en `Mockups_SAJONA.pdf` (Sección 3.1 a 3.3) junto con un módulo analítico transversal:
   - **Módulo Adicional:** Dashboard Analítico e Inteligencia Operativa (KPIs, gráficos SVG offline, filtros y trazabilidad genética/lote).
   - **Módulo 1:** Propagación (Siembra por lote, origen propio/comprado, control de saldo vivo y transición de estados).
   - **Módulo 2:** Planta Madre y Extracciones (Gestión individual numerada de madres, matriz de extracción de esquejes/semillas `CV-09` y derivación de lotes hijos).
   - **Módulo 3:** Transplante a Bolsa y Revisión Periódica (`CV-08` + `CV-05`: control de saldo disponible, cálculo de buenas/malas, alertas de merma > 20% y promoción automática a Planta Madre).
2. **Arquitectura Backend en 4 Capas (`sajona_core`):**
   - `domain`: entidades puras, enums, excepciones y reglas de negocio agronómicas (cero dependencias externas).
   - `application`: puertos, DTOs, RBAC, casos de uso y `SyncService`.
   - `infrastructure`: modelos SQLAlchemy, repositorios, Argon2id/JWT, auditoría append-only (`audit_logs` + `audit.jsonl`) y semilla idempotente.
   - `presentation`: routers `/api/v1/*`, DI y middleware.
   - Restricción verificada automáticamente mediante `import-linter`, `mypy --strict` y `ruff` (complejidad `<= 10`).
3. **Offline-First y Seguridad Local:**
   - Persistencia transaccional en IndexedDB (`Dexie 4`) + cola `outbox_mutations` reproducible en orden causal (`seq`) con `client_mutation_id` idempotente y `base_version` optimista.
   - Jamás almacenar contraseñas ni hashes en almacenamiento del navegador.
   - Los exportadores `.xlsx`, `.txt` y `.pdf` operan localmente desde IndexedDB.
4. **Identidad Académica Inalterable:**
   - Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software.
   - Docente Supervisor y Product Owner: Ing. Eduardo Martínez Vidal.
   - Equipo de Ingeniería (co-desarrollo horizontal): Danna Nerieth Palencia y Jairo Molano Salgado.
   - Empresa Cliente / Dominio: SAJONA ADE (NIT 900905923).
5. **Estándar Documental 4+1:**
   - Strictly Black & White (`#000000` / `#FFFFFF`), diagramas completos de las 5 vistas 4+1 **por cada uno de los 4 módulos**, redacción académica pura sin referencias a IA.
