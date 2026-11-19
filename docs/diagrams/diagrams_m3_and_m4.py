"""Definición de diagramas B&N de Módulos 3 y 4 (Dashboard) para SAJONA Núcleo."""

DIAGRAMS_PART_2: dict[str, str] = {
    # ---------------- MODULO 3: TRANSPLANTE A BOLSA Y REVISION PERIODICA ----------------
    "m3_v1_clases_er": """classDiagram
    class TransplanteBolsa {
        +str id
        +str lote_id
        +str codigo_transplante
        +date fecha_transplante
        +int cantidad_procesada
        +int cantidad_buenas
        +int cantidad_malas
        +Decimal porcentaje_buenas
        +Decimal porcentaje_malas
        +bool alerta_merma
        +TipoLoteTransplante tipo_lote
        +str capacidad_bolsa
    }
    class RevisionBolsa {
        +str id
        +str transplante_id
        +date fecha_revision
        +FaseBolsa fase
        +int unidades_revisadas
        +int contador_buenos
        +int contador_malos
        +str tipo_complicacion
        +EstadoSanitario estado_sanitario
    }
    class RulesBolsa {
        <<domain service>>
        +calcular_transplante_bolsa() ResultadoSupervivenciaBolsa
        +validar_revision_bolsa() int
    }
    TransplanteBolsa "1" --> "0..*" RevisionBolsa : monitorea_cv05
    TransplanteBolsa ..> RulesBolsa : valida RN-02
    RevisionBolsa ..> RulesBolsa : valida RN-04
""",
    "m3_v2_componentes": """flowchart TB
    subgraph FE["Cliente PWA (Módulo Bolsa)"]
        direction TB
        UI["TransplanteBolsaPage.tsx (Modal Bolsa + Modal CV-05)"]
        CALC["calculations.ts (calcularSupervivenciaBolsa + calcularVivasEnBolsa)"]
        ENG["syncEngine.ts (Transplante + Lote Madre + Revisión)"]
        IDB[("Dexie IndexedDB: transplante_bolsa, revisiones_bolsa, propagacion")]
        UI --> CALC & ENG
        ENG --> IDB
    end
    subgraph BE["Servidor Backend FastAPI"]
        direction TB
        RTR["routers.py"]
        SVC["ProduccionService (_rules_transplante_bolsa + _promote_transplante)"]
        DOM["domain/rules.py (calcular_transplante_bolsa, validar_revision_bolsa)"]
        REPO["CoreRepository + AuditLogger"]
        RTR --> SVC --> DOM
        SVC --> REPO
    end
    ENG <-- "POST /entities/transplante_bolsa • /revisiones_bolsa" --> RTR
""",
    "m3_v3_actividades": """flowchart TD
    INI(["Inicio: Transplante a Bolsa"]) --> S1["Seleccionar Lote Origen y consultar Saldo Disponible"]
    S1 --> V1{"¿0 < procesada <= saldo y\\n0 <= buenas <= procesada?"}
    V1 -- "No" --> ERR["Rechazar por conservación de balance (RN-02)"]
    V1 -- "Sí" --> CAL["Calcular malas = procesada - buenas\\n%Buenas y %Malas"]
    CAL --> A1{"¿%Malas > 20.00%?"}
    A1 -- "Sí" --> ALM["Activar bandera alerta_merma = True"]
    A1 -- "No" --> OKM["Supervivencia normal"]
    ALM & OKM --> T1{"¿Tipo Lote == PLANTA_MADRE?"}
    T1 -- "Sí" --> PM["Generar LotePlantaMadre + Unidades #1..N"]
    T1 -- "No" --> COM["Registrar lote en bolsa comercial"]
    PM & COM --> REV["Habilitar Revisiones Periódicas (CV-05)\\ny actualizar estado de Propagación"]
""",
    "m3_v4_secuencia_sync": """sequenceDiagram
    actor Op as Operario Móvil
    participant UI as TransplanteBolsaPage
    participant IDB as Dexie + Outbox
    participant API as FastAPI SyncService
    participant DB as PostgreSQL 16

    Op->>UI: Trasplanta 50 uds (35 buenas, 15 malas) como PLANTA_MADRE
    UI->>UI: calcularSupervivenciaBolsa() -> alerta_merma=true (30%)
    UI->>IDB: seq=1 CREATE transplante_bolsa (base_v=0)
    UI->>IDB: seq=2 UPDATE propagacion estado_lote
    UI->>IDB: seq=3 CREATE lotes_planta_madre + unidades
    Note over UI,API: Reconexión a red / reintento ante fallo HTTP
    IDB->>API: POST /api/v1/sync/push (cola causal + client_mutation_id)
    API->>DB: Valida saldo disponible y promueve cadena completa
    DB-->>API: Persistido + AuditLogs
    API-->>IDB: status="applied" (o "duplicate" en reintento)
""",
    "m3_v5_desarrollo_paquetes": """flowchart TB
    subgraph FE["frontend/src (Módulo 3)"]
        M3_PG["pages/TransplanteBolsaPage.tsx"]
        M3_DM["domain/calculations.ts\\n(calcularSupervivenciaBolsa, calcularVivasEnBolsa)"]
        M3_DB["db/schema.ts + db/syncEngine.ts"]
        M3_PG --> M3_DM & M3_DB
    end
    subgraph BE["backend/src/sajona_core (Módulo 3)"]
        B3_RT["presentation/routers.py"]
        B3_AP["application/produccion_service.py\\n(_rules_transplante_bolsa, _rules_revision_bolsa)"]
        B3_DO["domain/rules.py\\n(calcular_transplante_bolsa, validar_revision_bolsa)"]
        B3_IN["infrastructure/models.py\\n(TransplanteBolsaModel, RevisionBolsaModel)"]
        B3_RT --> B3_AP --> B3_DO
        B3_RT --> B3_IN
        B3_IN --> B3_DO
    end
    M3_DB <-- "/api/v1/entities/transplante_bolsa y revisiones_bolsa" --> B3_RT
""",
    "m3_v6_fisica_despliegue": """flowchart TB
    MOV["PWA Campo (Invernadero / Bolsa)\\nCálculos instantáneos sin latencia + IndexedDB"]
    TUN["Contenedor sajona-core-tunnel (cloudflared TLS 1.3)"]
    PRX["Contenedor sajona-core-proxy (Nginx 1.27.3 no-root :8080)"]
    API["Contenedor sajona-core-backend (FastAPI + actualización Propagación)"]
    DB[("Contenedor sajona-core-db (PostgreSQL 16.6)\\nTablas: transplantes_bolsa, revisiones_bolsa, propagaciones")]
    MOV <-->|"HTTPS TLS 1.3"| TUN <--> PRX <--> API <--> DB
""",
    "m3_v7_casos_uso_escenarios": """flowchart TB
    subgraph RBAC["Casos de Uso RBAC — Módulo 3: Transplante Bolsa y CV-05"]
        direction TB
        subgraph G1["Operario / Jefe / Admin (Operación en Bolsa)"]
            direction LR
            M3U1(["UC-M3-01 Registrar Transplante desde Saldo"])
            M3U3(["UC-M3-03 Promover a Planta Madre"])
            M3U4(["UC-M3-04 Registrar Revisión Periódica CV-05"])
        end
        subgraph G2["Todos los Roles (incluido Consulta)"]
            direction LR
            M3U2(["UC-M3-02 Visualizar Alerta Merma >20%"])
            M3U5(["UC-M3-05 Exportar Consolidado Supervivencia"])
        end
    end
    subgraph ESC["Escenario +1 Crítico — Alerta de Merma Sin Señal"]
        direction LR
        S1["1. Transplante 50 uds\\n(35 buenas / 30% merma)"] --> S2["2. Alerta >20%\\ny Saldo Prop. = 0"] --> S3["3. Promueve Madre\\ny Unidades #1..N"] --> S4["4. Sync Causal y\\nRevisión CV-05"]
    end
    RBAC --> ESC
""",
    # ---------------- MODULO 4 (ADICIONAL): DASHBOARD ANALITICO ----------------
    "m4_v1_clases_er": """classDiagram
    class DashboardSummary {
        +dict kpi_propagacion
        +dict kpi_transplante_bolsa
        +dict kpi_planta_madre
        +list alertas_merma
        +list supervivencia_por_transplante
        +list distribucion_por_variedad
    }
    class DashboardFilter {
        +date fechaInicio
        +date fechaFin
        +str variedadId
        +str tipoPropagacion
    }
    class LocalAnalyticsEngine {
        <<client analytics>>
        +computeLocalDashboardSummary() DashboardSummary
    }
    class ServerAnalyticsService {
        <<application service>>
        +get_dashboard_summary() dict
        +get_traceability() dict
    }
    DashboardFilter --> LocalAnalyticsEngine : filtra en IndexedDB
    DashboardFilter --> ServerAnalyticsService : consulta REST /dashboard
    LocalAnalyticsEngine --> DashboardSummary : produce
    ServerAnalyticsService --> DashboardSummary : produce
""",
    "m4_v2_componentes": """flowchart TB
    subgraph FE["Cliente PWA (Analítica Offline-First)"]
        direction TB
        UI["DashboardPage.tsx (KPIs, Embudo SVG, Supervivencia, Alertas)"]
        STAT["domain/dashboardStats.ts (computeLocalDashboardSummary)"]
        TRACE["components/LotTraceModal.tsx (Trazabilidad Genética 360°)"]
        EXP["utils/exporters.ts (Excel, TXT, PDF Offline)"]
        HOOKS["db/useLocalData.ts (useEntityRecords sobre 7 tablas)"]
        IDB[("Dexie IndexedDB (sajona_core_db)")]
        UI --> STAT & TRACE & EXP
        STAT --> HOOKS --> IDB
    end
    subgraph BE["Servidor Backend FastAPI"]
        direction TB
        API["routers.py (/dashboard/summary, /lotes/{id}/trazabilidad)"]
    end
    HOOKS -. "Pull Delta / Traza REST" .-> API
""",
    "m4_v3_actividades": """flowchart TD
    INI(["Inicio: Acceso al Dashboard Operativo"]) --> F1["Aplicar filtros locales (Fechas, Variedad, Tipo Prop.)"]
    F1 --> R1["Leer snapshot vivo de las 7 tablas en IndexedDB"]
    R1 --> K1["Calcular KPIs de Propagación (lotes, sembrado, saldo)"]
    R1 --> K2["Calcular KPIs de Bolsa (supervivencia %, vivas netas, alertas >20%)"]
    R1 --> K3["Calcular KPIs de Planta Madre (activas, esquejes, semillas, hijos)"]
    K1 & K2 & K3 --> G1["Renderizar Embudo SVG + Barras de Supervivencia + Trazabilidad"]
    G1 --> D1{"¿Usuario selecciona 'Ver Traza'\\no Exportar?"}
    D1 -- "Ver Traza" --> TR["Abrir LotTraceModal 360° (Padre->Bolsa->Madres->Hijos)"]
    D1 -- "Exportar" --> EX["Generar archivo Excel/TXT/PDF 100% local sin red"]
""",
    "m4_v4_secuencia_sync": """sequenceDiagram
    actor User as Jefe / Consulta
    participant UI as DashboardPage + LotTraceModal
    participant STAT as dashboardStats.ts
    participant IDB as Dexie IndexedDB
    participant Sync as syncEngine.ts
    participant API as FastAPI Backend

    User->>UI: Abre PWA (con o sin conexión a Internet)
    UI->>IDB: useEntityRecords() lee 7 colecciones locales
    IDB-->>STAT: Entrega registros sincronizados + pendientes locales
    STAT-->>UI: Renderiza KPIs, Embudo SVG y Alertas < 16 ms
    opt Hay conectividad disponible
        Sync->>API: GET /api/v1/sync/pull?since=cursor
        API-->>IDB: Actualiza deltas en tablas locales
        IDB-->>UI: suscribeSync() refresca Dashboard automáticamente
    end
""",
    "m4_v5_desarrollo_paquetes": """flowchart TB
    subgraph FE["frontend/src (Módulo 4: Dashboard)"]
        D_PG["pages/DashboardPage.tsx"]
        D_TR["components/LotTraceModal.tsx"]
        D_ST["domain/dashboardStats.ts\\n(computeLocalDashboardSummary)"]
        D_HK["db/useLocalData.ts"]
        D_EX["utils/exporters.ts (Lazy Excel/PDF/TXT)"]
        D_PG --> D_ST & D_HK & D_EX
        D_PG --> D_TR
    end
    subgraph BE["backend/src/sajona_core (Endpoints Analíticos)"]
        B_DR["presentation/routers.py\\n(/dashboard/summary, /lotes/{id}/trazabilidad)"]
        B_SV["application/produccion_service.py\\n(get_dashboard_summary, _compose_dashboard_metrics)"]
        B_RP["infrastructure/repositories.py\\n(get_lote_traceability)"]
        B_DR --> B_SV --> B_RP
    end
    D_HK <-- "Pull Incremental + Traza REST" --> B_DR
""",
    "m4_v6_fisica_despliegue": """flowchart TB
    DEV["Teléfono / PC Usuario\\nApp Shell SW + Cómputo Dashboard local en IndexedDB"]
    TUN["Contenedor sajona-core-tunnel (cloudflared TLS 1.3)"]
    PRX["Contenedor sajona-core-proxy (Nginx 1.27.3 no-root :8080)"]
    API["Contenedor sajona-core-backend (/api/v1/dashboard/summary + Pull Delta)"]
    DB[("Contenedor sajona-core-db (PostgreSQL 16.6)\\nConsultas agregadas read-only")]
    DEV <-->|"HTTPS TLS 1.3"| TUN <--> PRX <--> API <--> DB
""",
    "m4_v7_casos_uso_escenarios": """flowchart TB
    subgraph RBAC["Casos de Uso RBAC — Módulo 4: Dashboard Analítico"]
        direction TB
        subgraph G1["Todos los Roles (Operación Offline-First)"]
            direction LR
            M4U1(["UC-M4-01 Visualizar KPIs de Módulos 1–3"])
            M4U3(["UC-M4-03 Embudo SVG y Alertas >20%"])
            M4U4(["UC-M4-04 Explorar Trazabilidad 360°"])
        end
        subgraph G2["Jefe / Consulta / Admin (Reportes)"]
            direction LR
            M4U2(["UC-M4-02 Filtrar por Fechas y Variedad"])
            M4U5(["UC-M4-05 Exportar Consolidado Offline"])
        end
    end
    subgraph ESC["Escenario +1 Crítico — Analítica Desconectada"]
        direction LR
        S1["1. Cierre App\\nSin Conexión"] --> S2["2. Reapertura PWA\\nApp Shell SW"] --> S3["3. dashboardStats.ts\\nRecalcula desde IndexedDB"] --> S4["4. Descarga Excel/PDF\\n100% Local"]
    end
    RBAC --> ESC
""",
}
