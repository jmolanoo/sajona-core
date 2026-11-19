"""Secciones institucionales, portada, TOC y arquitectura global de SAJONA Núcleo."""

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt

from doc_helpers import (
    BLACK,
    FONT_SANS,
    add_bullets,
    add_bw_table,
    add_diagram,
    add_dotted_index_line,
    add_p,
)

TOC_TITLES: list[tuple[int, str]] = [
    (1, "1. Introducción"),
    (1, "2. Propósito y Alcance"),
    (1, "3. Contexto del Sistema"),
    (1, "4. Antecedentes, Auditoría e Ingeniería Inversa"),
    (1, "5. Objetivos Arquitectónicos y ASR"),
    (1, "6. Restricciones y Decisiones Tecnológicas"),
    (1, "7. Descripción General de la Arquitectura"),
    (1, "8. Modelo de Datos Unificado y Despliegue Global"),
    (1, "9. Arquitectura 4+1 — Módulo 1: Propagación"),
    (2, "9.1 Vista Lógica — Propagación"),
    (2, "9.2 Vista de Procesos — Propagación"),
    (2, "9.3 Vista de Desarrollo — Propagación"),
    (2, "9.4 Vista Física — Propagación"),
    (2, "9.5 Vista de Escenarios (+1) — Propagación"),
    (1, "10. Arquitectura 4+1 — Módulo 2: Planta Madre y Extracciones"),
    (2, "10.1 Vista Lógica — Planta Madre"),
    (2, "10.2 Vista de Procesos — Planta Madre"),
    (2, "10.3 Vista de Desarrollo — Planta Madre"),
    (2, "10.4 Vista Física — Planta Madre"),
    (2, "10.5 Vista de Escenarios (+1) — Planta Madre"),
    (1, "11. Arquitectura 4+1 — Módulo 3: Transplante a Bolsa y Revisión Periódica"),
    (2, "11.1 Vista Lógica — Transplante a Bolsa"),
    (2, "11.2 Vista de Procesos — Transplante a Bolsa"),
    (2, "11.3 Vista de Desarrollo — Transplante a Bolsa"),
    (2, "11.4 Vista Física — Transplante a Bolsa"),
    (2, "11.5 Vista de Escenarios (+1) — Transplante a Bolsa"),
    (1, "12. Arquitectura 4+1 — Módulo 4 (Adicional): Dashboard Analítico"),
    (2, "12.1 Vista Lógica — Dashboard"),
    (2, "12.2 Vista de Procesos — Dashboard"),
    (2, "12.3 Vista de Desarrollo — Dashboard"),
    (2, "12.4 Vista Física — Dashboard"),
    (2, "12.5 Vista de Escenarios (+1) — Dashboard"),
    (1, "13. Estrategia Offline-First y Consistencia Causal"),
    (1, "14. Seguridad, Autenticación y Auditoría"),
    (1, "15. Decisiones Arquitectónicas (ADRs)"),
    (1, "16. Estrategia de Pruebas y Validación Real"),
    (1, "17. Rendimiento, Escalabilidad y Mantenibilidad"),
    (1, "18. Conclusiones"),
    (1, "19. Referencias Bibliográficas y Anexos Técnicos"),
]

FIG_TITLES: list[str] = [
    "Figura 1. Diagrama de Contexto Sistémico de SAJONA Núcleo PWA",
    "Figura 2. Modelo Entidad-Relación Global de SAJONA Núcleo (14 Tablas)",
    "Figura 3. Topología Física Global de Despliegue en VPS (Docker Compose)",
    "Figura 4. Módulo 1 (Propagación) — Diagrama de Clases y Reglas de Dominio",
    "Figura 5. Módulo 1 (Propagación) — Diagrama de Componentes Lógicos",
    "Figura 6. Módulo 1 (Propagación) — Diagrama de Actividades",
    "Figura 7. Módulo 1 (Propagación) — Diagrama de Secuencia Offline y Sync",
    "Figura 8. Módulo 1 (Propagación) — Diagrama de Paquetes y Capas de Código",
    "Figura 9. Módulo 1 (Propagación) — Diagrama Físico de Ejecución en VPS",
    "Figura 10. Módulo 1 (Propagación) — Casos de Uso RBAC y Escenario +1 Offline",
    "Figura 11. Módulo 2 (Planta Madre) — Diagrama de Clases y Submodelo CV-09",
    "Figura 12. Módulo 2 (Planta Madre) — Diagrama de Componentes Lógicos",
    "Figura 13. Módulo 2 (Planta Madre) — Diagrama de Actividades CV-09 e Hijos",
    "Figura 14. Módulo 2 (Planta Madre) — Diagrama de Secuencia Causal Padre–Hijo",
    "Figura 15. Módulo 2 (Planta Madre) — Diagrama de Paquetes y Dependencias",
    "Figura 16. Módulo 2 (Planta Madre) — Diagrama Físico de Despliegue",
    "Figura 17. Módulo 2 (Planta Madre) — Casos de Uso RBAC y Escenario +1",
    "Figura 18. Módulo 3 (Transplante Bolsa) — Diagrama de Clases y Revisión CV-05",
    "Figura 19. Módulo 3 (Transplante Bolsa) — Diagrama de Componentes Lógicos",
    "Figura 20. Módulo 3 (Transplante Bolsa) — Diagrama de Actividades y Merma >20%",
    "Figura 21. Módulo 3 (Transplante Bolsa) — Diagrama de Secuencia Offline y Promoción",
    "Figura 22. Módulo 3 (Transplante Bolsa) — Diagrama de Paquetes y Capas",
    "Figura 23. Módulo 3 (Transplante Bolsa) — Diagrama Físico de Despliegue",
    "Figura 24. Módulo 3 (Transplante Bolsa) — Casos de Uso RBAC y Escenario +1",
    "Figura 25. Módulo 4 (Dashboard) — Clases y Modelos de Agregación Analítica",
    "Figura 26. Módulo 4 (Dashboard) — Componentes Lógicos Offline-First",
    "Figura 27. Módulo 4 (Dashboard) — Diagrama de Actividades Analíticas",
    "Figura 28. Módulo 4 (Dashboard) — Secuencia de Lectura Local y Pull Delta",
    "Figura 29. Módulo 4 (Dashboard) — Diagrama de Paquetes y Capas de Código",
    "Figura 30. Módulo 4 (Dashboard) — Diagrama Físico de Despliegue",
    "Figura 31. Módulo 4 (Dashboard) — Casos de Uso RBAC y Escenario +1 Desconectado",
]

TBL_TITLES: list[str] = [
    "Tabla 1. Brechas y defectos de ingeniería inversa resueltos en los Módulos 1–3.",
    "Tabla 2. Requisitos Arquitectónicamente Significativos (ASR).",
    "Tabla 3. Contenedores Docker de producción aislados en VPS.",
    "Tabla 4. Registro de Decisiones Arquitectónicas (ADR-001 a ADR-005).",
    "Tabla 5. Resultados consolidados de pruebas y validación sobre software real.",
    "Tabla 6. Contratos HTTP REST v1 implementados y verificados en OpenAPI.",
]


def build_cover(doc: Document):
    for text, size, space in (
        ("UNIVERSIDAD SURCOLOMBIANA", 15, 4),
        ("FACULTAD DE INGENIERÍA — PROGRAMA DE INGENIERÍA DE SOFTWARE", 11.5, 24),
        ("DOCUMENTO DE ARQUITECTURA DE SOFTWARE (MODELO 4+1)", 19, 10),
        (
            "SAJONA NÚCLEO: PWA MOBILE-FIRST Y OFFLINE-FIRST PARA PROPAGACIÓN, "
            "PLANTA MADRE, TRANSPLANTE A BOLSA Y DASHBOARD ANALÍTICO",
            12.5,
            22,
        ),
    ):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(space)
        r = p.add_run(text)
        r.font.name = FONT_SANS
        r.font.size = Pt(size)
        r.bold = True
        r.font.color.rgb = BLACK

    add_bw_table(
        doc,
        ["Atributo Institucional", "Especificación Oficial"],
        [
            ["Proyecto", "SAJONA Núcleo PWA — Módulos 1–3 + Dashboard (TRL-6)"],
            ["Empresa Propietaria del Dominio", "SAJONA ADE (NIT 900905923)"],
            ["Institución Académica", "Universidad Surcolombiana (USCO) — Ingeniería de Software"],
            ["Equipo de Ingeniería (Co-Desarrollo Horizontal)", "Danna Nerieth Palencia  |  Jairo Molano Salgado"],
            ["Docente Supervisor y Product Owner", "Ing. Eduardo Martínez Vidal"],
            ["Estándar de Documentación", "Modelo de Vistas 4+1 de Philippe Kruchten (vista completa por módulo)"],
            ["Versión y Fecha", "Versión 1.0 — 19 de noviembre de 2026"],
        ],
        col_widths=[2.5, 4.15],
    )

    pl = doc.add_paragraph()
    pl.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pl.paragraph_format.space_before = Pt(32)
    r = pl.add_run("Neiva, Huila — Colombia\nNoviembre de 2026")
    r.font.name = FONT_SANS
    r.font.size = Pt(11)
    r.bold = True
    r.font.color.rgb = BLACK
    doc.add_page_break()


def build_toc_and_indices(
    doc: Document,
    toc_pages: dict[str, int] | None,
    fig_pages: dict[str, int] | None,
    tbl_pages: dict[str, int] | None,
):
    h = doc.add_heading("Tabla de Contenido", level=1)
    h.paragraph_format.space_before = Pt(0)
    h.paragraph_format.space_after = Pt(6)
    for lvl, title in TOC_TITLES:
        pg = str(toc_pages.get(title, "00")) if toc_pages else "00"
        add_dotted_index_line(
            doc,
            title,
            pg,
            indent=0.0 if lvl == 1 else 0.25,
            bold=(lvl == 1),
            size=9.5 if lvl == 1 else 9.0,
        )
    doc.add_page_break()

    hf = doc.add_heading("Índice de Figuras y Tablas", level=1)
    hf.paragraph_format.space_before = Pt(0)
    hf.paragraph_format.space_after = Pt(6)
    for ft in FIG_TITLES:
        pg = str(fig_pages.get(ft, "00")) if fig_pages else "00"
        add_dotted_index_line(doc, ft, pg, indent=0.0, bold=False, size=8.5)
    for tt in TBL_TITLES:
        pg = str(tbl_pages.get(tt, "00")) if tbl_pages else "00"
        add_dotted_index_line(doc, tt, pg, indent=0.0, bold=True, size=8.5)
    doc.add_page_break()


def populate_global_sections(doc: Document, asr_p95_str: str):
    doc.add_heading("1. Introducción", level=1)
    add_p(
        doc,
        "Este documento especifica la arquitectura de software implementada para SAJONA Núcleo, la "
        "evolución focalizada del sistema de trazabilidad de cannabis medicinal de SAJONA ADE "
        "(NIT 900905923) concentrada con profundidad de lógica de negocio en los tres primeros "
        "módulos productivos definidos en la especificación visual oficial (Propagación, Planta Madre "
        "y Transplante a Bolsa con Revisión Periódica), complementados con un módulo adicional de "
        "Dashboard Analítico Offline-First. Toda la solución se materializó bajo el modelo 4+1 de "
        "Philippe Kruchten, desagregando de forma explícita las cinco vistas arquitectónicas tanto "
        "a nivel sistémico como individualmente para cada uno de los cuatro módulos implementados.",
    )

    doc.add_heading("2. Propósito y Alcance", level=1)
    add_p(
        doc,
        "El propósito del sistema es resolver con rigor transaccional, cuantitativo y fenológico "
        "la etapa nuclear de multiplicación genética y enraizamiento en campo sin depender de "
        "cobertura continua de red, sirviendo de referencia técnica verificable para el Programa de "
        "Ingeniería de Software de la Universidad Surcolombiana.",
    )
    add_bullets(
        doc,
        [
            (
                "Alcance Funcional Implementado (3 Módulos + Dashboard):",
                "Módulo 1 (Propagación por lotes con saldo disponible vivo); Módulo 2 (Planta Madre "
                "numerada individualmente #1..#N, matriz CV-09 de extracción de esquejes/semillas y "
                "derivación automática de lotes hijos en Propagación); Módulo 3 (Transplante a Bolsa "
                "con conservación de balance, alerta automática de merma >20%, promoción a Planta Madre "
                "y Revisión Periódica CV-05); y Módulo 4 (Dashboard Analítico Offline-First con embudo "
                "SVG, barras de supervivencia, trazabilidad 360° padre-hijo y exportación local).",
            ),
            (
                "Capacidades Transversales de Soporte:",
                "Autenticación Argon2id + JWT/Refresh HttpOnly, recuperación de contraseña, RBAC "
                "(ADMIN, JEFE_PROYECTO, OPERARIO, CONSULTA), catálogos maestros de Variedades y "
                "Ubicaciones, motor de sincronización causal Offline-First (IndexedDB Dexie 4 + "
                "Outbox) y bitácora append-only en PostgreSQL y archivo JSONL.",
            ),
        ],
    )

    doc.add_heading("3. Contexto del Sistema", level=1)
    add_p(
        doc,
        "Las operaciones en propagación, cubículos, casas malla e invernaderos requieren captura "
        "inmediata desde teléfonos móviles en zonas rurales donde la señal celular es intermitente. "
        "La Figura 1 sintetiza la interacción entre los perfiles operativos, el cliente PWA autónomo "
        "y el backend contenedorizado en la VPS.",
    )
    add_diagram(
        doc,
        "g01_contexto_global.png",
        "Figura 1",
        "Diagrama de Contexto Sistémico de SAJONA Núcleo PWA",
        "La Figura 1 delimita la frontera operativa del cliente PWA instalable (Workbox + Dexie 4) "
        "frente a los servicios desplegados tras un túnel TLS 1.3 en la VPS.",
    )

    doc.add_heading("4. Antecedentes, Auditoría e Ingeniería Inversa", level=1)
    add_p(
        doc,
        "Durante la fase previa de auditoría documental y visual sobre Mockups_SAJONA.pdf (págs. "
        "1–7), historias CV-01 a CV-09, modelo_pdf_sajona.pdf, Prediseno.pptx y Gobernanza, se "
        "identificaron cinco inconsistencias críticas en los módulos 1 a 3 que fueron corregidas en "
        "esta implementación:",
    )
    add_bw_table(
        doc,
        ["Hallazgo Auditado", "Artefacto Origen", "Impacto Técnico", "Solución Implementada"],
        [
            [
                "FK invertida transplante -> planta_madre",
                "modelo_pdf_sajona.pdf",
                "Impide trasplantar lotes previos al bloque madre.",
                "transplantes_bolsa.lote_id apunta a propagaciones.id.",
            ],
            [
                "Error aritmético (30+28 != 37) y rótulo en modal Madre",
                "Mockups pág. 7 vs CV-09",
                "Inconsistencia en totales de esquejes y semillas.",
                "Matriz fiel a CV-09 con totales calculados en dominio.",
            ],
            [
                "Omisión de Revisión Periódica en Bolsa y unidades madre",
                "Mockups vs CV-02/CV-05",
                "Sin ajuste de mortalidad post-trasplante ni historial individual.",
                "Tablas revisiones_bolsa y unidades_planta_madre activas.",
            ],
            [
                "usr_password VARCHAR(20) y falta de FK a funcionario",
                "modelo_pdf_sajona.pdf",
                "Inviable para hashes seguros y trazabilidad de actor.",
                "VARCHAR(255) Argon2id + FK usuarios.funcionario_id.",
            ],
            [
                "Dependencia online continua",
                "Gobernanza 2026",
                "Bloqueo operativo en invernadero sin señal.",
                "PWA Offline-First causal vía ADR-002.",
            ],
        ],
        col_widths=[1.6, 1.3, 1.75, 2.0],
        caption="Tabla 1. Brechas y defectos de ingeniería inversa resueltos en los Módulos 1–3.",
    )

    doc.add_heading("5. Objetivos Arquitectónicos y ASR", level=1)
    add_bw_table(
        doc,
        ["ID", "Atributo", "Escenario y Umbral", "Verificación"],
        [
            ["ASR-01", "Offline-First Total", "Alta/edición de lotes, bolsa y extracciones sin red + reapertura.", "Vitest IndexedDB + Playwright offline E2E."],
            ["ASR-02", "Rendimiento API", "Latencia p95 <= 500 ms y 0% error nominal.", f"Benchmark HTTP ({asr_p95_str})."],
            ["ASR-03", "Integridad Biológica", "Conservación estricta de saldos e idempotencia en Outbox.", "Unitarias dominio + tests sync push."],
            ["ASR-04", "Seguridad y RBAC", "Cero contraseñas locales; rechazo 403 ante escalamiento.", "Tests RBAC + Cookie HttpOnly + Argon2id."],
            ["ASR-05", "Accesibilidad Móvil", "Touch >= 44 px y 0 violaciones críticas WCAG.", "Playwright @axe-core en móvil/escritorio."],
        ],
        col_widths=[0.7, 1.4, 2.4, 2.15],
        caption="Tabla 2. Requisitos Arquitectónicamente Significativos (ASR).",
    )

    doc.add_heading("6. Restricciones y Decisiones Tecnológicas", level=1)
    add_p(
        doc,
        "El servidor opera sobre Python 3.12, FastAPI 0.115.6, SQLAlchemy 2.0 asíncrono y PostgreSQL "
        "16.6 organizados en cuatro capas estrictas (domain, application, infrastructure, presentation). "
        "La PWA emplea React 18, TypeScript estricto, Tailwind CSS, Workbox injectManifest (src/sw.ts) "
        "y Dexie 4 sobre IndexedDB, desplegándose tras Nginx 1.27.3 no-root y túnel cloudflared TLS 1.3.",
    )

    doc.add_heading("7. Descripción General de la Arquitectura", level=1)
    add_p(
        doc,
        "SAJONA Núcleo adopta un estilo Cliente Autónomo Offline-First + Monolito Modular en Capas. "
        "El cliente ejecuta validaciones de dominio en espejo (calculations.ts y dashboardStats.ts), "
        "persiste transacciones locales en IndexedDB y delega al backend la autoridad transaccional, "
        "resolución idempotente de mutaciones secuenciales (seq) y control optimista de versiones.",
    )

    doc.add_heading("8. Modelo de Datos Unificado y Despliegue Global", level=1)
    add_diagram(
        doc,
        "g02_er_global.png",
        "Figura 2",
        "Modelo Entidad-Relación Global de SAJONA Núcleo (14 Tablas)",
        "El esquema global corrige las dependencias circulares heredadas y soporta claves primarias "
        "UUIDv4, control de versiones optimista (version), soft-delete (deleted_at) y genealogía "
        "bidireccional padre -> extracción -> hijo.",
    )
    add_diagram(
        doc,
        "g03_despliegue_vps_global.png",
        "Figura 3",
        "Topología Física Global de Despliegue en VPS (Docker Compose)",
        "La red sajona-core-backend-net se configura como internal: true aislando completamente a "
        "PostgreSQL y al servicio de copias de seguridad respecto a Internet.",
    )
    add_bw_table(
        doc,
        ["Servicio Docker", "Imagen Base Fija", "Usuario", "Redes / Exposición", "Persistencia y Límites"],
        [
            ["sajona-core-db", "postgres:16.6-alpine", "postgres", "backend-net (internal)", "1.0 CPU, 512M | sajona_core_pgdata"],
            ["sajona-core-backend", "python:3.12.7-slim", "sajona (1001)", "backend-net + frontend-net", "1.0 CPU, 512M | sajona_core_audit_logs"],
            ["sajona-core-backup", "postgres:16.6-alpine", "postgres", "backend-net (internal)", "0.25 CPU, 128M | sajona_core_backups"],
            ["sajona-core-proxy", "nginx:1.27.3-alpine", "nginx (8080)", "frontend-net (127.0.0.1:8089)", "0.50 CPU, 256M | Bundle PWA"],
            ["sajona-core-tunnel", "cloudflare/cloudflared:2026.11.1", "nonroot", "frontend-net", "0.25 CPU, 128M | TLS 1.3"],
        ],
        col_widths=[1.25, 1.5, 1.0, 1.45, 1.45],
        caption="Tabla 3. Contenedores Docker de producción aislados en VPS.",
    )
