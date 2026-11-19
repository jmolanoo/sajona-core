"""Secciones 4+1 detalladas por cada uno de los 4 módulos (Módulos 1–3 + Dashboard)."""

from docx import Document

from doc_helpers import add_diagram, add_p


def populate_module_sections(doc: Document):
    # =========================================================================
    # SECCION 9 — MODULO 1: PROPAGACION
    # =========================================================================
    doc.add_heading("9. Arquitectura 4+1 — Módulo 1: Propagación", level=1)
    add_p(
        doc,
        "El Módulo 1 gobierna el nacimiento de cada lote productivo (esqueje, semilla o in vitro), "
        "su origen genético (propio o comprado a vivero autorizado), el control de bajas tempranas "
        "y el cálculo en tiempo real del saldo disponible para trasplante a bolsa (RN-01).",
    )

    doc.add_heading("9.1 Vista Lógica — Propagación", level=2)
    add_diagram(
        doc,
        "m1_v1_clases_er.png",
        "Figura 4",
        "Módulo 1 (Propagación) — Diagrama de Clases y Reglas de Dominio",
        "Propagacion hereda de SyncMetadata para versionamiento optimista e idempotencia y delega "
        "su consistencia cuantitativa al servicio puro RulesPropagacion (domain/rules.py).",
    )
    add_diagram(
        doc,
        "m1_v2_componentes.png",
        "Figura 5",
        "Módulo 1 (Propagación) — Diagrama de Componentes Lógicos",
        "PropagacionPage interactúa directamente con calculations.ts para saldo vivo, exporters.ts "
        "para reportes locales y syncEngine.ts sobre IndexedDB, desacoplando la UI de la red.",
    )

    doc.add_heading("9.2 Vista de Procesos — Propagación", level=2)
    add_diagram(
        doc,
        "m1_v3_actividades.png",
        "Figura 6",
        "Módulo 1 (Propagación) — Diagrama de Actividades",
        "El flujo valida obligatoriedad de proveedor en incorporaciones COMPRADA, protege las bajas "
        "frente al saldo sembrado y determina automáticamente el estado (SIEMBRA, EN_TRANSPLANTE "
        "o FINALIZADO).",
    )
    add_diagram(
        doc,
        "m1_v4_secuencia_sync.png",
        "Figura 7",
        "Módulo 1 (Propagación) — Diagrama de Secuencia Offline y Sync",
        "Ante ausencia de conectividad, la creación se guarda en transacción atómica sobre Dexie y "
        "se replica vía POST /api/v1/sync/push en cuanto el dispositivo recupera cobertura.",
    )

    doc.add_heading("9.3 Vista de Desarrollo — Propagación", level=2)
    add_diagram(
        doc,
        "m1_v5_desarrollo_paquetes.png",
        "Figura 8",
        "Módulo 1 (Propagación) — Diagrama de Paquetes y Capas de Código",
        "Correspondencia exacta entre módulos frontend/src y las cuatro capas del backend "
        "sajona_core, manteniendo domain libre de dependencias externas.",
    )

    doc.add_heading("9.4 Vista Física — Propagación", level=2)
    add_diagram(
        doc,
        "m1_v6_fisica_despliegue.png",
        "Figura 9",
        "Módulo 1 (Propagación) — Diagrama Físico de Ejecución en VPS",
        "Recorrido físico desde el almacenamiento IndexedDB en el smartphone a través de túnel "
        "TLS 1.3, proxy Nginx no-root y Uvicorn hasta la tabla propagaciones en PostgreSQL 16.",
    )

    doc.add_heading("9.5 Vista de Escenarios (+1) — Propagación", level=2)
    add_diagram(
        doc,
        "m1_v7_casos_uso_escenarios.png",
        "Figura 10",
        "Módulo 1 (Propagación) — Casos de Uso RBAC y Escenario +1 Offline",
        "Segregación estricta de permisos por rol y validación end-to-end de siembra desconectada, "
        "reapertura sin red, sincronización y resolución de conflictos concurrentes.",
    )

    # =========================================================================
    # SECCION 10 — MODULO 2: PLANTA MADRE Y EXTRACCIONES
    # =========================================================================
    doc.add_heading("10. Arquitectura 4+1 — Módulo 2: Planta Madre y Extracciones", level=1)
    add_p(
        doc,
        "El Módulo 2 implementa la gestión granular de bloques y plantas madre numeradas (#1..#N), "
        "superando la omisión de unidades individuales del mockup histórico y materializando la "
        "matriz de extracción de esquejes y semillas fiel a CV-09 con derivación genética directa "
        "de nuevos lotes hijos en Propagación (RN-05 y RN-06).",
    )

    doc.add_heading("10.1 Vista Lógica — Planta Madre", level=2)
    add_diagram(
        doc,
        "m2_v1_clases_er.png",
        "Figura 11",
        "Módulo 2 (Planta Madre) — Diagrama de Clases y Submodelo CV-09",
        "LotePlantaMadre compone sus UnidadPlantaMadre numeradas y enlaza las extracciones "
        "cronológicas validadas por RulesPlantaMadre.",
    )
    add_diagram(
        doc,
        "m2_v2_componentes.png",
        "Figura 12",
        "Módulo 2 (Planta Madre) — Diagrama de Componentes Lógicos",
        "La vista matricial calcula sumatorias en vivo en cliente y sincroniza en secuencia causal "
        "la extracción, la actualización de acumulados por unidad madre y el lote hijo generado.",
    )

    doc.add_heading("10.2 Vista de Procesos — Planta Madre", level=2)
    add_diagram(
        doc,
        "m2_v3_actividades.png",
        "Figura 13",
        "Módulo 2 (Planta Madre) — Diagrama de Actividades CV-09 e Hijos",
        "Excluye plantas en estado DESCARTADA, verifica totalidad positiva de propágulos, suma de "
        "forma exacta esquejes/semillas y permite derivar automáticamente un lote PROPIA en Módulo 1.",
    )
    add_diagram(
        doc,
        "m2_v4_secuencia_sync.png",
        "Figura 14",
        "Módulo 2 (Planta Madre) — Diagrama de Secuencia Causal Padre–Hijo",
        "El orden estricto por secuencia (seq) en outbox_mutations garantiza que la extracción y "
        "sus unidades madre se persistan en PostgreSQL antes del nuevo lote hijo derivado.",
    )

    doc.add_heading("10.3 Vista de Desarrollo — Planta Madre", level=2)
    add_diagram(
        doc,
        "m2_v5_desarrollo_paquetes.png",
        "Figura 15",
        "Módulo 2 (Planta Madre) — Diagrama de Paquetes y Dependencias",
        "Organización modular en PlantaMadrePage.tsx y las capas backend para LotePlantaMadre, "
        "UnidadPlantaMadre y ExtraccionMadre.",
    )

    doc.add_heading("10.4 Vista Física — Planta Madre", level=2)
    add_diagram(
        doc,
        "m2_v6_fisica_despliegue.png",
        "Figura 16",
        "Módulo 2 (Planta Madre) — Diagrama Físico de Despliegue",
        "Distribución física de tablas JSON/relacionales en IndexedDB y PostgreSQL 16 detrás de "
        "la red backend aislada.",
    )

    doc.add_heading("10.5 Vista de Escenarios (+1) — Planta Madre", level=2)
    add_diagram(
        doc,
        "m2_v7_casos_uso_escenarios.png",
        "Figura 17",
        "Módulo 2 (Planta Madre) — Casos de Uso RBAC y Escenario +1",
        "Casos de uso operativos sobre bloques, cambios de estado por unidad y ejecución desconectada "
        "de extracciones con herencia genética.",
    )

    # =========================================================================
    # SECCION 11 — MODULO 3: TRANSPLANTE A BOLSA Y REVISION PERIODICA
    # =========================================================================
    doc.add_heading("11. Arquitectura 4+1 — Módulo 3: Transplante a Bolsa y Revisión Periódica", level=1)
    add_p(
        doc,
        "El Módulo 3 enlaza el saldo disponible de Propagación hacia las fases de bolsa y "
        "aclimatación (CV-08), aplica el cálculo contable estricto de supervivencia y alerta "
        "automática ante merma > 20% (RN-02), promueve lotes clasificados como PLANTA_MADRE al "
        "Módulo 2 (RN-03) e incorpora el seguimiento fitosanitario de Revisión Periódica CV-05 (RN-04).",
    )

    doc.add_heading("11.1 Vista Lógica — Transplante a Bolsa", level=2)
    add_diagram(
        doc,
        "m3_v1_clases_er.png",
        "Figura 18",
        "Módulo 3 (Transplante Bolsa) — Diagrama de Clases y Revisión CV-05",
        "Modela TransplanteBolsa con sus porcentajes NUMERIC(5,2), bandera alerta_merma y su "
        "asociación uno-a-muchos hacia RevisionBolsa.",
    )
    add_diagram(
        doc,
        "m3_v2_componentes.png",
        "Figura 19",
        "Módulo 3 (Transplante Bolsa) — Diagrama de Componentes Lógicos",
        "TransplanteBolsaPage integra cálculo instantáneo de supervivencia y revisiones con "
        "actualización automática del estado de Propagación y promoción a Planta Madre.",
    )

    doc.add_heading("11.2 Vista de Procesos — Transplante a Bolsa", level=2)
    add_diagram(
        doc,
        "m3_v3_actividades.png",
        "Figura 20",
        "Módulo 3 (Transplante Bolsa) — Diagrama de Actividades y Merma >20%",
        "Impide superar el saldo disponible del lote origen, evalúa el umbral del 20% de merma, "
        "bifurca según Tipo Lote (PLANTA_MADRE vs PLANTA_COMERCIAL) y habilita revisiones CV-05.",
    )
    add_diagram(
        doc,
        "m3_v4_secuencia_sync.png",
        "Figura 21",
        "Módulo 3 (Transplante Bolsa) — Diagrama de Secuencia Offline y Promoción",
        "Secuencia transaccional offline y push causal ordenado: creación de trasplante, actualización "
        "del estado en Propagación y generación de bloque madre con unidades numeradas.",
    )

    doc.add_heading("11.3 Vista de Desarrollo — Transplante a Bolsa", level=2)
    add_diagram(
        doc,
        "m3_v5_desarrollo_paquetes.png",
        "Figura 22",
        "Módulo 3 (Transplante Bolsa) — Diagrama de Paquetes y Capas",
        "Mapeo entre TransplanteBolsaPage.tsx, domain/calculations.ts, rules.py y los modelos "
        "relacionales TransplanteBolsaModel / RevisionBolsaModel.",
    )

    doc.add_heading("11.4 Vista Física — Transplante a Bolsa", level=2)
    add_diagram(
        doc,
        "m3_v6_fisica_despliegue.png",
        "Figura 23",
        "Módulo 3 (Transplante Bolsa) — Diagrama Físico de Despliegue",
        "Flujo de ejecución en invernaderos/casas malla con persistencia local inmediata y respaldo "
        "transaccional en PostgreSQL 16.",
    )

    doc.add_heading("11.5 Vista de Escenarios (+1) — Transplante a Bolsa", level=2)
    add_diagram(
        doc,
        "m3_v7_casos_uso_escenarios.png",
        "Figura 24",
        "Módulo 3 (Transplante Bolsa) — Casos de Uso RBAC y Escenario +1",
        "Cobertura funcional por rol y escenario crítico de registro de trasplante con 30% de "
        "merma y promoción a planta madre en condiciones de desconexión.",
    )

    # =========================================================================
    # SECCION 12 — MODULO 4 (ADICIONAL): DASHBOARD ANALITICO
    # =========================================================================
    doc.add_heading("12. Arquitectura 4+1 — Módulo 4 (Adicional): Dashboard Analítico", level=1)
    add_p(
        doc,
        "El Dashboard Analítico consolida en tiempo real —tanto en línea como completamente sin "
        "conexión sobre IndexedDB— el desempeño cuantitativo de los tres módulos operativos: "
        "embudo de conversión agronómica SVG, barras comparativas de supervivencia frente al "
        "umbral de merma, distribución por variedad, trazabilidad genética 360° por lote y "
        "exportación local en Excel, TXT y PDF.",
    )

    doc.add_heading("12.1 Vista Lógica — Dashboard", level=2)
    add_diagram(
        doc,
        "m4_v1_clases_er.png",
        "Figura 25",
        "Módulo 4 (Dashboard) — Clases y Modelos de Agregación Analítica",
        "Simetría estructural entre DashboardSummary generado en backend (/api/v1/dashboard/summary) "
        "y computeLocalDashboardSummary() en cliente offline.",
    )
    add_diagram(
        doc,
        "m4_v2_componentes.png",
        "Figura 26",
        "Módulo 4 (Dashboard) — Componentes Lógicos Offline-First",
        "DashboardPage.tsx combina filtros reactivos, hooks de lectura local sobre siete tablas "
        "Dexie, el inspector LotTraceModal y exportación diferida.",
    )

    doc.add_heading("12.2 Vista de Procesos — Dashboard", level=2)
    add_diagram(
        doc,
        "m4_v3_actividades.png",
        "Figura 27",
        "Módulo 4 (Dashboard) — Diagrama de Actividades Analíticas",
        "Aplica filtros de fecha/variedad/tipo, agrega KPIs en memoria local, dibuja gráficos SVG "
        "nativos sin dependencias externas de red y habilita trazabilidad 360° o exportación.",
    )
    add_diagram(
        doc,
        "m4_v4_secuencia_sync.png",
        "Figura 28",
        "Módulo 4 (Dashboard) — Secuencia de Lectura Local y Pull Delta",
        "El Dashboard responde instantáneamente (< 16 ms) desde IndexedDB incluso tras pérdida total "
        "de señal y se refresca automáticamente mediante subscribeSync() tras cada Pull incremental.",
    )

    doc.add_heading("12.3 Vista de Desarrollo — Dashboard", level=2)
    add_diagram(
        doc,
        "m4_v5_desarrollo_paquetes.png",
        "Figura 29",
        "Módulo 4 (Dashboard) — Diagrama de Paquetes y Capas de Código",
        "Componentes reactivos DashboardPage.tsx, LotTraceModal.tsx, dashboardStats.ts y los "
        "endpoints /api/v1/dashboard/summary y /api/v1/lotes/{lote_id}/trazabilidad.",
    )

    doc.add_heading("12.4 Vista Física — Dashboard", level=2)
    add_diagram(
        doc,
        "m4_v6_fisica_despliegue.png",
        "Figura 30",
        "Módulo 4 (Dashboard) — Diagrama Físico de Despliegue",
        "Ejecución híbrida cliente-servidor donde los gráficos y exportadores operan en la CPU del "
        "teléfono sobre el App Shell precacheado sin consumir tráfico innecesario.",
    )

    doc.add_heading("12.5 Vista de Escenarios (+1) — Dashboard", level=2)
    add_diagram(
        doc,
        "m4_v7_casos_uso_escenarios.png",
        "Figura 31",
        "Módulo 4 (Dashboard) — Casos de Uso RBAC y Escenario +1 Desconectado",
        "Demuestra que la consulta analítica, inspección de trazabilidad padre-hijo y descarga de "
        "reportes en Excel/PDF continúan operativas incluso después de cerrar y reabrir la PWA offline.",
    )
