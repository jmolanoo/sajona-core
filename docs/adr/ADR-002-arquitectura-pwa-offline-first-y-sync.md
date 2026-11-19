# ADR-002: Evolución hacia PWA Mobile-First y Offline-First con Orden Causal

## Contexto y Apartamiento de Gobernanza
El documento de gobernanza preliminar asumía operación web continua dependiente de Internet. En invernaderos, cubículos de propagación y casas malla rurales de SAJONA ADE la conectividad es intermitente o nula.

## Decisión
Se adopta arquitectura **PWA Mobile-First y Offline-First** mediante Service Worker (`vite-plugin-pwa` + Workbox `injectManifest`), almacenamiento estructurado en **IndexedDB (Dexie 4)** y motor de sincronización bidireccional con cola `outbox_mutations` reproducida en orden causal (`seq`), idempotencia (`client_mutation_id`) y control optimista de versión (`version`).

## Beneficios y Consecuencias
- Todo registro o consulta de Propagación, Planta Madre, Extracción, Transplante a Bolsa, Revisión Periódica y analítica del Dashboard opera 100% sin red.
- Requiere UI explícita de estado de conexión y modal comparativo de resolución de conflictos (`SyncCenterModal`).
