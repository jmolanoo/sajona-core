# Auditoría e Ingeniería Inversa — SAJONA Núcleo (Módulos 1–3 + Dashboard)

**Cliente:** SAJONA ADE (NIT 900905923)  
**Institución Académica:** Universidad Surcolombiana (USCO) — Programa de Ingeniería de Software  
**Docente Supervisor y Product Owner:** Ing. Eduardo Martínez Vidal  
**Equipo de Ingeniería (Co-Desarrollo Horizontal):** Danna Nerieth Palencia & Jairo Molano Salgado  
**Alcance Definido:** Profundización integral en los **3 primeros módulos** del estándar visual `Mockups_SAJONA.pdf` (**3.1 Propagación**, **3.2 Planta Madre**, **3.3 Transplante Bolsa** incluyendo **Revisión Periódica `CV-05`**), más un **Módulo Adicional de Dashboard Analítico e Inteligencia Operativa** (con autenticación, catálogos relacionales, sincronización Offline-First y trazabilidad genética padre–hijo).

---

## 1. Inventario de Artefactos Auditados Relevantes al Alcance

| # | Artefacto de Origen | Hallazgo Central para el Alcance Nuclear (Módulos 1–3 + Dashboard) |
|---|---|---|
| 1 | `CONTEXT/Mockups_SAJONA.pdf` (Págs. 1–7) | Define la estructura oficial de menús y el orden exacto de los 3 primeros módulos: **3.1 Propagación** (Pág. 6), **3.2 Planta Madre** (Pág. 6–7) y **3.3 Transplante Bolsa / Planta Bolsa** (Pág. 7). Incluye Login, topbar roja con usuario/fecha, sidebar oscura y exportación `.xlsx`/`.txt`/`.pdf`. |
| 2 | `CONTEXT/CV-01_Ingresar_Sistema.docx` | Requerimientos de acceso: usuario/contraseña, enlace *¿Olvidó la contraseña?* con recuperación por correo, y administración base de usuarios y parámetros maestros (variedades y terrenos/ubicaciones). |
| 3 | `CONTEXT/CV-02_Crear_Planta_Madre.docx` y `CV-03_Listar_Plantas_Madre.docx` | Gestión individual numerada de **Plantas Madre** (`Número Planta Madre`, `Fecha Siembra`, `Lugar de Siembra`, `Observación`), acumulados individuales de `Esquejes` y `Semillas` y consultas por rango de fechas. |
| 4 | `CONTEXT/CV-04_Crear_Esquejes.docx` y `CV-09_Crear_Esquejes_Semillas_V2.docx` | Evolución desde el formulario simple V1 (`CV-04`) hacia la **matriz de extracción por lote madre** (`CV-09`): listado de lotes madre (`Lote Id`, `Fecha Siembra`, `Fecha Transplante`, `Cantidad Buenas`) y modal `Lote 30` con tabla por `Número Planta Madre` (`15, 16, 17, 18`), `Cantidad Esquejes` (`30, 0, 7, 0`), `Cantidad Semillas` (`0, 20, 0, 40`) y totales exactos `Total Lote Esquejes: 37` y `Total Lote Semillas: 60`. |
| 5 | `CONTEXT/CV-05_Revision_Esquejes..docx` | Proceso faltante en `Mockups_SAJONA.pdf`: **Revisión Periódica en Bolsa/Enraizamiento** con `Fecha Revisión`, `Fase`, rango de fechas, `Contador de Buenos`, `Contador de Malos`, marcado individual/por lote y observaciones sanitarias. |
| 6 | `CONTEXT/CV-08_propagación.docx` | Pivote al flujo por **Lote (`Lote Id`)**: creación de siembra (`Fecha Siembra`, `Cantidad`, `Lote Id`, `Tipo Propagación`: Esqueje/Semilla/In vitro, `Variedad`, `Tipo Incorporación`: Propia/Comprada) y transición directa a **Transplante** con cálculo automático de `Cantidad Malas`, `Porcentaje Malas %`, `Porcentaje Buenas %` y `Tipo Lote` (`P. Madre` / `P. Comercial`). |
| 7 | `CONTEXT/modelo_pdf_sajona.pdf` | Esquema relacional MySQL de 12 tablas; aporta la estructura base de `usuario`, `rol`, `permiso`, `funcionario`, `propagacion`, `planta_madre` y `transplante`, pero contiene defectos de cardinalidad y tipos de datos corregidos en la nueva arquitectura. |
| 8 | `CONTEXT/Prediseno.pptx` | Presupuesto histórico 2021 (`$10.800.000 COP`, Flor Opita + SENA TecnoParque), ciclo PHVA de calidad y requerimiento de reportes/analítica gerencial en tiempo real. |
| 9 | `Gobernanza ` y `SAJONA - Análisis Integral...` | Lineamientos técnicos de modularidad en 4 capas, Docker Compose aislado, imágenes fijas no-root, trazabilidad append-only (`>= 90` días), objetivos cuantitativos de calidad y meta TRL-6. |

---

## 2. Inconsistencias Críticas Resueltas en los Módulos 1–3

1. **Dependencia Invertida en Modelo ER (`transplante.tp_pm_id -> planta_madre.pm_id`):**  
   En `modelo_pdf_sajona.pdf`, todo trasplante exigía una clave foránea hacia `planta_madre`, haciendo imposible trasplantar a bolsa un lote comercial o un lote propagado de origen comprado antes de crear madres. **Resolución:** `transplantes_bolsa.lote_id` referencia directamente a `propagaciones.id`; cuando un trasplante tiene `tipo_lote = 'PLANTA_MADRE'`, habilita/genera el `lote_planta_madre` y sus `unidades_planta_madre` asociadas (`transplante_bolsa_id`).
2. **Error Aritmético y de Rotulado en `Mockups_SAJONA.pdf` pág. 7 vs `CV-09`:**  
   El mockup copia erróneamente el encabezado `Cantidad Planta Madre` y muestra `30 + 28 = 37`. **Resolución:** se conserva el diseño real de `CV-09` (`Número Planta Madre`, columna `Esquejes`, columna `Semillas`) con validación reactiva en cliente/servidor garantizando `total_esquejes == sum(item.esquejes)` y `total_semillas == sum(item.semillas)`.
3. **Omisión de Revisión Periódica (`CV-05`) y Seguimiento Individual de Madres (`CV-02/CV-03`):**  
   El PDF de mockups colapsaba todas las madres en un solo total por lote y omitía la revisión sanitaria periódica en bolsa. **Resolución:** `Módulo 2` gestiona tanto el lote madre como sus unidades numeradas (`15, 16, 17, 18...` con estado `ACTIVA`, `REPOSO`, `DESCARTADA`), y `Módulo 3` incorpora las **Revisiones Periódicas en Bolsa** (`CV-05`) con ajuste dinámico de unidades vivas y complicaciones fitosanitarias.
4. **Incompatibilidad de `usr_password VARCHAR(20)`, `pm_fecha_esquejacion NUMERIC` y Desacople `usuario`–`funcionario`:**  
   Corregidos a `password_hash VARCHAR(255)` (Argon2id), `DATE` reales y llave foránea explícita `usuarios.funcionario_id -> funcionarios.id`.
5. **Ausencia de Soporte Offline en `Gobernanza`:**  
   Mediante `ADR-002`, la aplicación web tradicional dependiente de red evoluciona hacia una **PWA Mobile-First / Offline-First** real con IndexedDB, Outbox causal, idempotencia y resolución de conflictos.

---

## 3. Reglas de Negocio Verificadas para el Núcleo Productivo (RN-01 a RN-08)

- **RN-01 (Unidad Trazable y Balance Vivo de Propagación):** Cada lote nace en `Propagación` con `codigo_lote` único y `id` UUIDv4. Su saldo disponible para trasplante a bolsa es estrictamente `cantidad_material - bajas_propagacion - sum(trasplantes_activos.cantidad_procesada)`. Cuando `saldo_disponible == 0`, el estado transiciona automáticamente a `FINALIZADO`.
- **RN-02 (Conservación Cuantitativa en Transplante a Bolsa):** Para cada operación de trasplante: `0 < cantidad_procesada <= saldo_disponible`, `0 <= cantidad_buenas <= cantidad_procesada`, `cantidad_malas = cantidad_procesada - cantidad_buenas`, `porcentaje_buenas + porcentaje_malas = 100.00%` y `fecha_transplante >= propagacion.fecha_siembra`. Si `porcentaje_malas > 20.00%`, se activa `alerta_merma = True`.
- **RN-03 (Bifurcación y Promoción a Planta Madre):** Un trasplante clasificado como `PLANTA_MADRE` genera un `LotePlantaMadre` y crea sus `cantidad_buenas` registros numerados en `unidades_planta_madre` (con numeración correlativa). Uno clasificado como `PLANTA_COMERCIAL` conserva las unidades vivas para trazabilidad y posteriores revisiones.
- **RN-04 (Integridad de Revisión Periódica en Bolsa — `CV-05`):** En cada revisión sobre un trasplante a bolsa, `contador_buenos + contador_malos == unidades_revisadas > 0`, `fecha_revision >= transplante.fecha_transplante`, y las bajas acumuladas en revisiones nunca pueden superar `cantidad_buenas` del trasplante.
- **RN-05 (Validación Matricial de Extracciones y Linaje Padre–Hijo — `CV-09`):** Una extracción en `Planta Madre` debe extraer al menos un propágulo (`total_esquejes + total_semillas > 0`), solo permite plantas no `DESCARTADA`, valida `fecha_extraccion >= fecha_transplante_ref`, actualiza los acumulados individuales de cada planta madre y permite derivar automáticamente un **nuevo lote hijo en `Propagación`** con `tipo_incorporacion = 'PROPIA'` y `origen_extraccion_id`.
- **RN-06 (Gobernanza de Inventario Madre):** Un lote madre puede ajustar el estado de unidades individuales (`ACTIVA` -> `REPOSO` / `DESCARTADA`), recalculando automáticamente `cantidad_madres_activas`.
- **RN-07 (Seguridad y Auditabilidad Inmutable):** Todas las mutaciones (en línea o sincronizadas offline) exigen permiso RBAC acorde al rol (`ADMIN`, `JEFE_PROYECTO`, `OPERARIO`, `CONSULTA`) y dejan registro append-only en `audit_logs` y archivo `audit.jsonl` con `correlation_id`. Jamás se almacenan contraseñas ni hashes en el navegador.
- **RN-08 (Consistencia Offline-First Causal e Idempotente):** Todas las operaciones de campo se ejecutan localmente sobre IndexedDB en transacción atómica y se encolan en `outbox_mutations` respetando el orden secuencial causal (`seq`) y `client_mutation_id`. Los conflictos por edición concurrente (`base_version` desactualizada) se exponen al usuario para decisión explícita sin pérdida de datos.
