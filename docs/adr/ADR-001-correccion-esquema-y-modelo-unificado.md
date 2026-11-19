# ADR-001: Alcance Nuclear Estricto (Módulos 1–3 + Dashboard) y Corrección Relacional

## Contexto y Limitación Original
La especificación completa histórica abarca ocho módulos, mientras `modelo_pdf_sajona.pdf` presenta fallas críticas: dependencia invertida `transplante.tp_pm_id -> planta_madre`, fechas tipadas como `NUMERIC`, contraseñas `VARCHAR(20)` y ausencia de revisión periódica (`CV-05`) o extracciones granulares por planta (`CV-09`).

## Decisión
Enfocar SAJONA Núcleo en profundidad matemática y operativa exclusivamente sobre los 3 primeros módulos de `Mockups_SAJONA.pdf` (**Propagación**, **Planta Madre y Extracciones**, **Transplante a Bolsa y Revisiones Periódicas**) más un **Dashboard Analítico Offline-First**, corrigiendo el esquema relacional en PostgreSQL 16 con claves primarias UUIDv4 y trazabilidad bidireccional padre -> extracción -> hijo.

## Consecuencias
- Permite profundizar en el balance biológico por lote, la gestión unitaria de plantas madre y el flujo genético circular sin dispersión en etapas posteriores.
- Garantiza creación offline de árboles genéticos completos sin colisión de identificadores secuenciales.
