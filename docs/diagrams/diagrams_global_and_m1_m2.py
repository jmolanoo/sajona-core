"""Definición de diagramas B&N globales y de Módulos 1 y 2 para SAJONA Núcleo."""

DIAGRAMS_PART_1: dict[str, str] = {
    "g01_contexto_global": """flowchart TB
    subgraph ACT["Actores RBAC (SAJONA ADE)"]
        direction LR
        OP["Operario de Campo"]
        JF["Jefe de Proyecto"]
        CO["Consulta / Auditoría"]
        AD["Administrador"]
    end

    subgraph PWA["Cliente PWA Mobile-First / Offline-First"]
        direction TB
        UI["React 18 + Tailwind CSS\\n(Dashboard, Propagación, Planta Madre, Transplante Bolsa)"]
        SW["Workbox Service Worker (sw.ts)\\nApp Shell Offline + Navigation Fallback"]
        IDB["IndexedDB Dexie 4 (sajona_core_db)\\n9 Tablas + Outbox Causal + Exportadores"]
        UI --> IDB
        UI -.-> SW
    end

    subgraph VPS["Infraestructura VPS Ubuntu 24.04 (Docker Compose)"]
        direction TB
        TUN["sajona-core-tunnel\\n(cloudflared TLS 1.3)"]
        NGX["sajona-core-proxy\\n(Nginx 1.27.3 no-root)"]
        API["sajona-core-backend\\n(FastAPI 4 Capas + Auditoría JSONL)"]
        PG[("sajona-core-db\\nPostgreSQL 16.6")]
        TUN --> NGX --> API --> PG
    end

    OP & JF & CO & AD --> UI
    UI <-- "HTTPS REST /api/v1/* + Sync" --> TUN
""",
    "g02_er_global": """erDiagram
    FUNCIONARIOS ||--o| USUARIOS : asignado_a
    USUARIOS ||--o{ REFRESH_TOKENS : posee
    USUARIOS ||--o{ PASSWORD_RESET_TOKENS : solicita
    VARIEDADES ||--o{ PROPAGACIONES : clasifica
    UBICACIONES ||--o{ PROPAGACIONES : aloja
    FUNCIONARIOS ||--o{ PROPAGACIONES : responsable
    PROPAGACIONES ||--o{ TRANSPLANTES_BOLSA : abastece
    UBICACIONES ||--o{ TRANSPLANTES_BOLSA : ubica
    TRANSPLANTES_BOLSA ||--o{ REVISIONES_BOLSA : evalua_cv05
    PROPAGACIONES ||--o{ LOTES_PLANTA_MADRE : origina
    TRANSPLANTES_BOLSA ||--o| LOTES_PLANTA_MADRE : promueve
    LOTES_PLANTA_MADRE ||--|{ UNIDADES_PLANTA_MADRE : contiene
    LOTES_PLANTA_MADRE ||--o{ EXTRACCIONES_MADRE : registra_cv09
    EXTRACCIONES_MADRE ||--o{ PROPAGACIONES : deriva_lote_hijo
    PROCESSED_MUTATIONS {
        string client_mutation_id PK
        string entity_type
        string operation
    }
    AUDIT_LOGS {
        string id PK
        string correlation_id
        string entity_type
        string action
    }
""",
    "g03_despliegue_vps_global": """flowchart TB
    CLI["Smartphone / Navegador PWA\\n(Workbox SW + Dexie IndexedDB)"]
    CF["Cloudflare Edge (Terminación HTTPS TLS 1.3)"]

    subgraph VPS["VPS Ubuntu 24.04 x86_64 • Docker Compose (sajona-core)"]
        direction TB
        subgraph FNET["Red sajona-core-frontend-net (bridge)"]
            direction TB
            TUN["sajona-core-tunnel\\ncloudflare/cloudflared:2026.11.1 (nonroot)"]
            PRX["sajona-core-proxy\\nnginx:1.27.3-alpine (127.0.0.1:8089 -> 8080)"]
            API["sajona-core-backend\\npython:3.12.7-slim (UID 1001 :8000)"]
            TUN --> PRX --> API
        end
        subgraph BNET["Red sajona-core-backend-net (internal: true)"]
            direction TB
            DB[("sajona-core-db\\npostgres:16.6-alpine")]
            BKP["sajona-core-backup\\npg_dump diario + restore_test.sh"]
            VOL_PG[("Vol. sajona_core_pgdata")]
            VOL_LOG[("Vol. sajona_core_audit_logs")]
            VOL_BK[("Vol. sajona_core_backups")]
            BKP --> DB
            DB --> VOL_PG
            BKP --> VOL_BK
        end
        API --> DB
        API --> VOL_LOG
    end

    CLI <-->|"HTTPS TLS 1.3"| CF <-->|"Túnel Saliente Cifrado"| TUN
""",
    # ---------------- MODULO 1: PROPAGACION ----------------
    "m1_v1_clases_er": """classDiagram
    class SyncMetadata {
        +str id
        +int version
        +datetime updated_at
        +datetime deleted_at
        +str client_mutation_id
    }
    class Variedad {
        +str nombre
        +str quimiotipo
        +int dias_vegetativo_est
        +int dias_floracion_est
    }
    class Ubicacion {
        +str nombre
        +TipoUbicacion tipo
        +int capacidad_unidades
    }
    class Propagacion {
        +str codigo_lote
        +date fecha_siembra
        +str variedad_id
        +TipoPropagacion tipo_propagacion
        +TipoIncorporacion tipo_incorporacion
        +str origen_extraccion_id
        +str proveedor
        +int cantidad_material
        +int cantidad_plantas_madre
        +int bajas_propagacion
        +EstadoLote estado_lote
    }
    class RulesPropagacion {
        <<domain service>>
        +calcular_saldo_propagacion() int
        +validar_propagacion() EstadoLote
    }
    SyncMetadata <|-- Propagacion
    Variedad "1" --> "0..*" Propagacion : clasifica
    Ubicacion "1" --> "0..*" Propagacion : alberga
    Propagacion ..> RulesPropagacion : valida
""",
    "m1_v2_componentes": """flowchart TB
    subgraph FE["Cliente PWA Offline-First"]
        direction TB
        UI["PropagacionPage.tsx (Tarjetas, Filtros, Modal)"]
        CALC["calculations.ts (calcularSaldoPropagacion)"]
        EXP["exporters.ts (Excel, TXT, PDF offline)"]
        ENG["syncEngine.ts (queueLocalMutation)"]
        IDB[("Dexie IndexedDB: propagacion + outbox")]
        UI --> CALC & EXP & ENG
        ENG --> IDB
    end
    subgraph BE["Servidor Backend FastAPI"]
        direction TB
        RTR["routers.py (entity_router + sync_router)"]
        SVC["ProduccionService (_rules_propagacion)"]
        DOM["domain/rules.py (validar_propagacion)"]
        REPO["CoreRepository + DualAuditLogger"]
        RTR --> SVC --> DOM
        SVC --> REPO
    end
    ENG <-- "POST /sync/push • GET /entities/propagacion" --> RTR
""",
    "m1_v3_actividades": """flowchart TD
    INI(["Inicio: Nuevo / Editar Lote"]) --> F1["Ingresar Id Lote, Fecha, Variedad,\\nTipo (Esqueje/Semilla/In vitro) y Cantidad"]
    F1 --> D1{"¿Incorporación\\nCOMPRADA?"}
    D1 -- "Sí" --> D2{"¿Proveedor\\ningresado?"}
    D2 -- "No" --> ERR1["Rechazar: Proveedor obligatorio"]
    D2 -- "Sí" --> D3
    D1 -- "No (PROPIA)" --> D3{"¿bajas < sembrado y\\nmadres_est <= sembrado?"}
    D3 -- "No" --> ERR2["Rechazar por regla RN-01"]
    D3 -- "Sí" --> CALC["Calcular saldo_disponible =\\ncantidad - bajas - trasplantado_bolsa"]
    CALC --> D4{"¿saldo_disponible?"}
    D4 -- "== 0" --> ESTF["Estado = FINALIZADO"]
    D4 -- "> 0 con trasplantes" --> ESTE["Estado = EN_TRANSPLANTE"]
    D4 -- "sin trasplantes" --> ESTS["Estado = SIEMBRA"]
    ESTF & ESTE & ESTS --> SAVE["Persistir en IndexedDB + Outbox / PostgreSQL"]
""",
    "m1_v4_secuencia_sync": """sequenceDiagram
    actor Op as Operario Móvil
    participant UI as PropagacionPage
    participant IDB as Dexie + Outbox
    participant SW as Workbox SW
    participant API as FastAPI SyncService
    participant DB as PostgreSQL 16

    Op->>UI: Crea lote LOT-2026-034 sin señal
    UI->>UI: Valida RN-01 (proveedor, cantidades)
    UI->>IDB: Tx atómica: put(propagacion) + add(outbox_mutations)
    IDB-->>UI: Muestra tarjeta con badge "Pendiente"
    Note over UI,API: Dispositivo recupera señal 4G / Wi-Fi
    SW-->>UI: Navegador dispara evento online
    UI->>API: POST /api/v1/sync/push (client_mutation_id, base_version=0)
    API->>DB: Verifica processed_mutations
    DB-->>API: Nueva mutación -> aplica rules.py e inserta
    API->>DB: Registra audit_logs + client_mutation_id
    API-->>IDB: status="applied", version=1 -> marca "Sincronizado"
""",
    "m1_v5_desarrollo_paquetes": """flowchart TB
    subgraph FE["frontend/src (Módulo 1)"]
        F_PG["pages/PropagacionPage.tsx"]
        F_DM["domain/calculations.ts\\ndomain/types.ts"]
        F_DB["db/schema.ts + db/syncEngine.ts"]
        F_UT["utils/exporters.ts"]
        F_PG --> F_DM
        F_PG --> F_DB
        F_PG --> F_UT
    end
    subgraph BE["backend/src/sajona_core (Módulo 1)"]
        B_PR["presentation/routers.py"]
        B_AP["application/produccion_service.py\\napplication/dto.py (PropagacionPayload)"]
        B_DO["domain/entities.py (Propagacion)\\ndomain/rules.py (validar_propagacion)"]
        B_IN["infrastructure/models.py (PropagacionModel)\\ninfrastructure/repositories.py"]
        B_PR --> B_AP --> B_DO
        B_PR --> B_IN
        B_IN --> B_AP
        B_IN --> B_DO
    end
    F_DB <-- "/api/v1/entities/propagacion + /sync" --> B_PR
""",
    "m1_v6_fisica_despliegue": """flowchart TB
    MOV["Teléfono Operario — PWA Standalone\\nIndexedDB: tabla propagacion + outbox"]
    TUN["Contenedor sajona-core-tunnel\\ncloudflare/cloudflared:2026.11.1 (TLS 1.3)"]
    PRX["Contenedor sajona-core-proxy\\nnginx:1.27.3-alpine (127.0.0.1:8089 -> 8080)"]
    API["Contenedor sajona-core-backend\\nFastAPI + Uvicorn x2 + audit.jsonl"]
    DB[("Contenedor sajona-core-db\\nPostgreSQL 16.6 (backend-net internal)")]
    MOV <-->|"HTTPS TLS 1.3"| TUN <-->|"HTTP :8080"| PRX <-->|"HTTP :8000"| API <-->|"TCP 5432"| DB
""",
    "m1_v7_casos_uso_escenarios": """flowchart TB
    subgraph RBAC["Casos de Uso RBAC — Módulo 1: Propagación"]
        direction TB
        subgraph G1["Operario / Jefe / Admin (Lectura y Escritura Offline)"]
            direction LR
            U1(["UC-M1-01 Registrar Siembra Propia/Comprada"])
            U2(["UC-M1-03 Actualizar Bajas / Atributos"])
            U3(["UC-M1-04 Enviar Saldo a Bolsa"])
        end
        subgraph G2["Todos los Roles (incluido Consulta)"]
            direction LR
            U4(["UC-M1-02 Consultar Saldo Disponible"])
            U5(["UC-M1-05 Exportar Excel / TXT / PDF"])
        end
        subgraph G3["Solo Jefe de Proyecto y Admin"]
            U6(["UC-M1-06 Eliminar Lote sin Trasplantes"])
        end
    end
    subgraph ESC["Escenario +1 Crítico — Propagación Sin Red"]
        direction LR
        S1["1. Siembra Offline\\n(IndexedDB + Outbox)"] --> S2["2. Cierre y Reapertura\\nApp desde SW"] --> S3["3. Reconexión 4G\\nPush Idempotente"] --> S4["4. Conflicto v1/v2\\nen SyncCenterModal"]
    end
    RBAC --> ESC
""",
    # ---------------- MODULO 2: PLANTA MADRE Y EXTRACCIONES ----------------
    "m2_v1_clases_er": """classDiagram
    class LotePlantaMadre {
        +str id
        +str lote_id
        +str transplante_bolsa_id
        +date fecha_establecimiento
        +int cantidad_madres_inicial
        +int cantidad_madres_activas
    }
    class UnidadPlantaMadre {
        +str id
        +str lote_madre_id
        +int numero_planta
        +str codigo_planta
        +EstadoPlantaMadre estado_planta
        +int total_esquejes
        +int total_semillas
        +date ultima_extraccion
    }
    class ExtraccionMadre {
        +str id
        +str lote_madre_id
        +date fecha_transplante_ref
        +date fecha_extraccion
        +list detalle_plantas
        +int total_esquejes
        +int total_semillas
        +str lote_hijo_codigo
    }
    class RulesPlantaMadre {
        <<domain service>>
        +validar_extraccion_madre() TotalesExtraccionMadre
    }
    LotePlantaMadre "1" *-- "1..*" UnidadPlantaMadre : agrupa
    LotePlantaMadre "1" --> "0..*" ExtraccionMadre : produce
    ExtraccionMadre ..> RulesPlantaMadre : valida CV-09
""",
    "m2_v2_componentes": """flowchart TB
    subgraph FE["Cliente PWA (Módulo Planta Madre)"]
        direction TB
        UI["PlantaMadrePage.tsx (Bloques, Unidades y Modal CV-09)"]
        CALC["calculations.ts (calcularTotalesExtraccion)"]
        ENG["syncEngine.ts (Cola Causal: Extracción + Unidades + Hijo)"]
        IDB[("Dexie IndexedDB: lotes_planta_madre, unidades, extracciones")]
        UI --> CALC & ENG
        ENG --> IDB
    end
    subgraph BE["Servidor Backend FastAPI"]
        direction TB
        RTR["routers.py"]
        SVC["ProduccionService (_update_unidades + _derive_child_lot)"]
        DOM["domain/rules.py (validar_extraccion_madre)"]
        REPO["CoreRepository + AuditLogger"]
        RTR --> SVC --> DOM
        SVC --> REPO
    end
    ENG <-- "POST /sync/push • POST /entities/extracciones_madre" --> RTR
""",
    "m2_v3_actividades": """flowchart TD
    INI(["Inicio: Crear Esqueje / Semilla (CV-09)"]) --> L1["Cargar Lote Madre y sus Unidades\\nno DESCARTADAS (#15, #16, #17, #18...)"]
    L1 --> L2["Registrar Fecha Extracción y cantidades\\nde Esquejes / Semillas por planta"]
    L2 --> V1{"¿fecha >= establecimiento\\ny suma total > 0?"}
    V1 -- "No" --> ERR["Rechazar extracción inválida"]
    V1 -- "Sí" --> SUM["Calcular totales exactos:\\nTotal Esquejes + Total Semillas"]
    SUM --> UPD["Actualizar total_esquejes, total_semillas\\ny ultima_extraccion por unidad madre"]
    UPD --> D2{"¿Derivar nuevo\\nlote hijo en Propagación?"}
    D2 -- "Sí" --> CHILD["Crear Propagación hija (PROPIA)\\nvinculada por origen_extraccion_id"]
    D2 -- "No" --> FIN(["Guardar Transacción + Auditar"])
    CHILD --> FIN
""",
    "m2_v4_secuencia_sync": """sequenceDiagram
    actor Op as Jefe / Operario
    participant UI as PlantaMadrePage (CV-09)
    participant IDB as Dexie + Outbox
    participant API as FastAPI SyncService
    participant SVC as ProduccionService
    participant DB as PostgreSQL 16

    Op->>UI: Registra extracción 37 esq. / 60 sem. + deriva lote hijo
    UI->>UI: calcularTotalesExtraccion()
    UI->>IDB: 1. CREATE extracciones_madre (seq=1)
    UI->>IDB: 2. UPDATE unidades_planta_madre (seq=2..N)
    UI->>IDB: 3. CREATE propagacion hija (seq=N+1)
    Note over UI,API: Al existir conexión o reconexión:
    IDB->>API: POST /api/v1/sync/push en orden estricto seq
    API->>SVC: Valida extracciones_madre -> unidades -> propagación hija
    SVC->>DB: Persiste cadena genética completa con FK
    DB-->>API: Commit + AuditLogs
    API-->>IDB: Todas las mutaciones status="applied"
""",
    "m2_v5_desarrollo_paquetes": """flowchart TB
    subgraph FE["frontend/src (Módulo 2)"]
        M2_PG["pages/PlantaMadrePage.tsx"]
        M2_DM["domain/calculations.ts (calcularTotalesExtraccion)"]
        M2_DB["db/schema.ts (3 tablas madre) + syncEngine.ts"]
        M2_PG --> M2_DM & M2_DB
    end
    subgraph BE["backend/src/sajona_core (Módulo 2)"]
        B2_RT["presentation/routers.py"]
        B2_AP["application/produccion_service.py\\n(_rules_extraccion_madre, _derive_child_lot_if_needed)"]
        B2_DT["application/dto.py\\n(LotePlantaMadre, UnidadPlantaMadre, ExtraccionMadre)"]
        B2_DO["domain/rules.py (validar_extraccion_madre)"]
        B2_IN["infrastructure/models.py\\n(lotes_planta_madre, unidades_planta_madre, extracciones_madre)"]
        B2_RT --> B2_AP --> B2_DT & B2_DO
        B2_RT --> B2_IN
        B2_IN --> B2_DO
    end
    M2_DB <-- "/api/v1/entities/* + /sync" --> B2_RT
""",
    "m2_v6_fisica_despliegue": """flowchart TB
    MOV["Móvil Operario — PWA\\nIndexedDB (unidades_planta_madre, extracciones_madre, propagacion)"]
    TUN["Contenedor sajona-core-tunnel (cloudflared TLS 1.3)"]
    PRX["Contenedor sajona-core-proxy (Nginx 1.27.3 no-root :8080)"]
    API["Contenedor sajona-core-backend (FastAPI Uvicorn x2 + JSONB)"]
    DB[("Contenedor sajona-core-db (PostgreSQL 16.6)\\nTablas: lotes_planta_madre, unidades_planta_madre, extracciones_madre")]
    MOV <-->|"HTTPS TLS 1.3"| TUN <--> PRX <--> API <--> DB
""",
    "m2_v7_casos_uso_escenarios": """flowchart TB
    subgraph RBAC["Casos de Uso RBAC — Módulo 2: Planta Madre"]
        direction TB
        subgraph G1["Operario / Jefe (Extracciones y Unidades)"]
            direction LR
            M2U2(["UC-M2-02 Estado Unidad #N (Activa/Reposo/Descartada)"])
            M2U3(["UC-M2-03 Matriz Extracción CV-09"])
            M2U4(["UC-M2-04 Derivar Lote Hijo a Propagación"])
        end
        subgraph G2["Jefe / Admin y Consulta (Lectura)"]
            direction LR
            M2U1(["UC-M2-01 Registrar Bloque Madre"])
            M2U5(["UC-M2-05 Historial Productivo y Exportación"])
        end
    end
    subgraph ESC["Escenario +1 Crítico — Extracción CV-09 Offline"]
        direction LR
        S1["1. Matriz #15..18\\nen IndexedDB"] --> S2["2. Actualiza Totales\\ny Crea Lote Hijo"] --> S3["3. Cola Causal seq\\nSync Push Ordenado"] --> S4["4. Auditoría Padre–Hijo\\nen PostgreSQL 16"]
    end
    RBAC --> ESC
""",
}
